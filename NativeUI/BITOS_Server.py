# -*- coding: utf-8 -*-
"""BITOS 06V6 / 21.01 BETA — background service for the native Win32 UI.

Protocol: one JSON request per stdin line; one JSON response/event per stdout line.
No UI toolkit is imported here. Keep stdout reserved for protocol messages.
"""
from __future__ import annotations

import concurrent.futures
import ctypes
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

APP_VERSION = "06V6"
APP_BUILD = "21.01 BETA"
APP_NAME = "BITOS"
REPOSITORY = "Saryanich/BITOS"
RELEASE_API = f"https://api.github.com/repos/{REPOSITORY}/releases/latest"
OPTIMIZATION_LEVELS = (0, 25, 50, 75, 100)
MAX_UPDATE_SIZE = 1024 * 1024 * 1024
MAX_EXTRACTED_SIZE = 2 * 1024 * 1024 * 1024


def _utc_stamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _safe_name(value: str, *, max_len: int = 120) -> str:
    name = str(value or "").strip()
    if not name or name in {".", ".."} or any(ch in name for ch in ("/", "\\", "\0")):
        raise ValueError("Недопустимое имя файла или папки")
    if len(name) > max_len or any(ord(ch) < 32 for ch in name):
        raise ValueError("Имя файла слишком длинное или содержит управляющие символы")
    return name


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + f".{os.getpid()}.{threading.get_ident()}.tmp")
    payload = json.dumps(value, ensure_ascii=False, indent=4).encode("utf-8")
    try:
        with open(temp, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
        # Best-effort directory metadata flush (not supported on all platforms).
        try:
            fd = os.open(str(path.parent), os.O_RDONLY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
        except OSError:
            pass
    finally:
        try:
            temp.unlink(missing_ok=True)
        except OSError:
            pass


def _version_parts(value: str) -> tuple:
    text = str(value or "").strip().lower()
    if text.startswith("v"):
        text = text[1:]
    tokens = re.findall(r"\d+|[a-z]+", text)
    return tuple((0, int(token)) if token.isdigit() else (1, token) for token in tokens)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_extract(zip_path: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    total = 0
    root = destination.resolve()
    with zipfile.ZipFile(zip_path, "r") as archive:
        bad = archive.testzip()
        if bad:
            raise ValueError(f"Повреждённый файл внутри архива: {bad}")
        infos = archive.infolist()
        if not infos:
            raise ValueError("Архив обновления пуст")
        for info in infos:
            raw = info.filename.replace("\\", "/")
            posix = PurePosixPath(raw)
            if posix.is_absolute() or any(part in ("", ".", "..") for part in posix.parts):
                raise ValueError("Архив содержит недопустимый путь")
            if re.match(r"^[A-Za-z]:", raw):
                raise ValueError("Архив содержит абсолютный путь")
            total += max(0, info.file_size)
            if total > MAX_EXTRACTED_SIZE:
                raise ValueError("Распакованный архив превышает допустимый размер")
            target = (destination / Path(*posix.parts)).resolve()
            if root != target and root not in target.parents:
                raise ValueError("Обнаружен выход за пределы каталога обновления")
        archive.extractall(destination)


class BITOSService:
    def __init__(self, base_dir: Path):
        self.base = base_dir.resolve()
        self.system = self.base / "System"
        self.config_dir = self.system / "Config"
        self.security_dir = self.system / "Security"
        self.logs_dir = self.system / "Logs"
        self.temp_dir = self.system / "Temp"
        self.desktop_root = self.system / "DesktopFile"
        self.config_path = self.config_dir / "system.cfg"
        self.pin_path = self.security_dir / "pin.hash"
        self.users_path = self.config_dir / "users.db"
        self.icons_path = self.config_dir / "icons.json"
        self.shortcuts_path = self.config_dir / "desktop_shortcuts.json"
        self.update_dir = self.temp_dir / "updates"
        self.update_status_path = self.config_dir / "update_status.json"
        self.lock = threading.RLock()
        self.output_lock = threading.Lock()
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=3, thread_name_prefix="BITOS-worker")
        self.executor_workers = 3
        self.current_user = "User"
        self.session_started = time.time()
        self.failed_attempts = 0
        self.lock_until = 0.0
        self.max_attempts = 5
        self.lock_seconds = 60
        self.config: dict[str, Any] = {}
        self.update: dict[str, Any] = {}
        self.running = True
        self._initialize()

    def _initialize(self) -> None:
        for folder in (self.config_dir, self.security_dir, self.logs_dir, self.temp_dir, self.desktop_root, self.update_dir):
            folder.mkdir(parents=True, exist_ok=True)
        self.config = self._read_json(self.config_path, {})
        defaults = {
            "version": APP_VERSION,
            "build": APP_BUILD,
            "os_name": APP_NAME,
            "first_boot": _utc_stamp(),
            "last_boot": _utc_stamp(),
            "boot_count": 0,
            "default_user": "User",
            "use_virtual_desktop": True,
            "optimization_percent": 0,
            "ui_backend": "Win32 + Direct2D",
        }
        changed = False
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
                changed = True
        # Never let stale metadata silently overwrite the release identity.
        if self.config.get("version") != APP_VERSION:
            self.config["version"] = APP_VERSION
            changed = True
        if self.config.get("build") != APP_BUILD:
            self.config["build"] = APP_BUILD
            changed = True
        level = self.config.get("optimization_percent", 0)
        if level not in OPTIMIZATION_LEVELS:
            self.config["optimization_percent"] = min(OPTIMIZATION_LEVELS, key=lambda x: abs(x - self._as_int(level, 0)))
            changed = True
        self.config["last_boot"] = _utc_stamp()
        self.config["boot_count"] = self._as_int(self.config.get("boot_count"), 0) + 1
        changed = True
        if changed:
            _atomic_json(self.config_path, self.config)
        self.update = self._read_json(self.update_status_path, {})
        if not self.pin_path.exists() or not self.pin_path.read_text(encoding="utf-8", errors="ignore").strip():
            self._save_pin("1234")
        if not self.users_path.exists():
            _atomic_json(self.users_path, {
                "User": {
                    "created": _utc_stamp(), "last_login": None, "is_admin": True,
                    "home": str(Path.home()), "virtual_desktop": str(self.desktop_root / "User"),
                    "use_virtual_desktop": True,
                }
            })
        (self.desktop_root / "User").mkdir(parents=True, exist_ok=True)
        if not self.icons_path.exists():
            _atomic_json(self.icons_path, {"shortcuts": [], "widgets": [], "theme": "Базовая", "wallpaper": None})
        self._apply_optimization_profile(self.config.get("optimization_percent", 0), startup=True)
        self._log("boot", f"Boot service started; version={APP_VERSION}; build={APP_BUILD}")

    def _apply_optimization_profile(self, value: Any, startup: bool = False) -> None:
        """Apply measurable server-side limits for optional background concurrency."""
        level = self._as_int(value, 0)
        worker_count = {0: 4, 25: 3, 50: 2, 75: 2, 100: 1}.get(level, 3)
        if worker_count == self.executor_workers:
            return
        old = self.executor
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=worker_count, thread_name_prefix="BITOS-worker")
        self.executor_workers = worker_count
        old.shutdown(wait=False)
        self._log("boot", f"Optimization profile applied: {level}% (background workers={worker_count})")

    @staticmethod
    def _as_int(value: Any, fallback: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return fallback

    @staticmethod
    def _read_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
        try:
            with open(path, "r", encoding="utf-8") as stream:
                data = json.load(stream)
            return data if isinstance(data, dict) else default
        except (OSError, ValueError, TypeError):
            return default.copy()

    def _log(self, channel: str, message: str) -> None:
        try:
            (self.logs_dir / f"{channel}.log").parent.mkdir(parents=True, exist_ok=True)
            with open(self.logs_dir / f"{channel}.log", "a", encoding="utf-8") as stream:
                stream.write(f"[{_utc_stamp()}] {message}\n")
        except OSError:
            pass

    def _pin_hash(self, pin: str) -> str:
        return hashlib.sha256(pin.encode("utf-8")).hexdigest()

    def _save_pin(self, pin: str) -> None:
        self.security_dir.mkdir(parents=True, exist_ok=True)
        temp = self.pin_path.with_suffix(".tmp")
        with open(temp, "w", encoding="ascii") as stream:
            stream.write(self._pin_hash(pin))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, self.pin_path)

    def _get_pin_hash(self) -> str:
        try:
            value = self.pin_path.read_text(encoding="ascii").strip()
            if value:
                return value
        except OSError:
            pass
        self._save_pin("1234")
        return self._pin_hash("1234")

    def _desktop_path(self, username: str | None = None) -> Path:
        name = username or self.current_user
        path = (self.desktop_root / _safe_name(name, max_len=32)).resolve()
        root = self.desktop_root.resolve()
        if path != root and root not in path.parents:
            raise ValueError("Недопустимый каталог рабочего стола")
        path.mkdir(parents=True, exist_ok=True)
        return path

    def boot(self, request_id: Any) -> None:
        stages = (
            (15, "Проверка системных каталогов"),
            (38, "Загрузка конфигурации и профиля производительности"),
            (64, "Проверка параметров авторизации"),
            (86, "Подготовка виртуального рабочего стола"),
        )
        for progress, label in stages:
            # Each report follows completion of the corresponding actual step.
            if progress == 15:
                for folder in (self.config_dir, self.security_dir, self.logs_dir, self.temp_dir, self.desktop_root):
                    folder.mkdir(parents=True, exist_ok=True)
            elif progress == 38:
                self.config = self._read_json(self.config_path, self.config)
            elif progress == 64:
                self._get_pin_hash()
            elif progress == 86:
                self._desktop_path("User")
            self.emit({"id": request_id, "ok": True, "event": "boot_progress", "progress": progress, "status": label})
        self.emit({"id": request_id, "ok": True, "event": "boot_complete", "version": APP_VERSION, "build": APP_BUILD,
                   "optimization": self.config.get("optimization_percent", 0)})

    def login(self, request_id: Any, username: str, pin: str) -> None:
        name = str(username or "").strip()
        pin_value = str(pin or "").strip()
        now = time.time()
        with self.lock:
            if now < self.lock_until:
                self.emit({"id": request_id, "ok": False, "event": "login_result", "error": f"Вход заблокирован ещё на {int(self.lock_until - now) + 1} сек."})
                return
            if not name or len(name) > 32 or any(ord(ch) < 32 for ch in name):
                self.emit({"id": request_id, "ok": False, "event": "login_result", "error": "Введите корректное имя пользователя (до 32 символов)."})
                return
            if not re.fullmatch(r"\d{4,8}", pin_value):
                self.emit({"id": request_id, "ok": False, "event": "login_result", "error": "PIN должен содержать от 4 до 8 цифр."})
                return
            ok = hashlib.sha256(pin_value.encode("utf-8")).hexdigest() == self._get_pin_hash()
            self._log("access", f"LOGIN_ATTEMPT user={name!r} result={'SUCCESS' if ok else 'FAILED'}")
            if not ok:
                self.failed_attempts += 1
                remaining = self.max_attempts - self.failed_attempts
                if self.failed_attempts >= self.max_attempts:
                    self.lock_until = now + self.lock_seconds
                    self.failed_attempts = 0
                    self._log("security", f"BRUTE_FORCE_LOCK user={name!r} seconds={self.lock_seconds}")
                    error = f"Слишком много попыток. Вход заблокирован на {self.lock_seconds} сек."
                else:
                    error = f"Неверный PIN. Осталось попыток: {remaining}."
                self.emit({"id": request_id, "ok": False, "event": "login_result", "error": error})
                return
            self.failed_attempts = 0
            self.current_user = name
            desktop = self._desktop_path(name)
            users = self._read_json(self.users_path, {})
            entry = users.get(name, {}) if isinstance(users.get(name, {}), dict) else {}
            entry.setdefault("created", _utc_stamp())
            entry.update({"last_login": _utc_stamp(), "home": str(Path.home()), "virtual_desktop": str(desktop), "use_virtual_desktop": True})
            users[name] = entry
            _atomic_json(self.users_path, users)
            self.session_started = time.time()
            self._log("access", f"USER_LOGIN user={name!r} desktop={desktop}")
            self.emit({"id": request_id, "ok": True, "event": "login_result", "username": name})

    def desktop_state(self, request_id: Any) -> None:
        desktop = self._desktop_path()
        items = []
        try:
            for entry in sorted(desktop.iterdir(), key=lambda p: (not p.is_dir(), p.name.casefold())):
                items.append({"name": entry.name, "kind": "folder" if entry.is_dir() else "file", "size": entry.stat().st_size if entry.is_file() else 0})
        except OSError as exc:
            self.emit({"id": request_id, "ok": False, "event": "desktop_state", "error": str(exc)})
            return
        shortcuts = []
        try:
            raw = json.loads(self.shortcuts_path.read_text(encoding="utf-8")) if self.shortcuts_path.exists() else []
            if isinstance(raw, list):
                for item in raw:
                    if isinstance(item, dict):
                        shortcuts.append({k: item.get(k) for k in ("text", "icon", "command", "grid_x", "grid_y", "icon_id")})
        except (OSError, ValueError):
            pass
        self.emit({"id": request_id, "ok": True, "event": "desktop_state", "username": self.current_user,
                   "items": items, "shortcuts": shortcuts, "theme": self.config.get("theme", "Базовая"),
                   "optimization": self.config.get("optimization_percent", 0)})

    def set_optimization(self, request_id: Any, value: Any, reboot: bool = False) -> None:
        try:
            selected = int(value)
            if selected not in OPTIMIZATION_LEVELS:
                raise ValueError("Допустимые уровни: 0, 25, 50, 75, 100")
            with self.lock:
                updated = dict(self.config)
                updated["optimization_percent"] = selected
                updated["optimization_applied_at"] = _utc_stamp()
                updated["ui_backend"] = "Win32 + Direct2D"
                _atomic_json(self.config_path, updated)
                # Re-read to verify that the requested state was persisted.
                verified = self._read_json(self.config_path, {})
                if verified.get("optimization_percent") != selected:
                    raise OSError("Проверка сохранённой настройки не пройдена")
                self.config = verified
                self._apply_optimization_profile(selected)
            self._log("audit", f"OPTIMIZATION_PROFILE={selected}% reboot={bool(reboot)}")
            self.emit({"id": request_id, "ok": True, "event": "optimization_saved", "optimization": selected, "reboot_requested": bool(reboot)})
            if reboot and not self._restart_windows():
                self.emit({"id": request_id, "ok": False, "event": "restart_failed", "error": "Профиль сохранён, но Windows не удалось перезагрузить автоматически."})
        except Exception as exc:
            self.emit({"id": request_id, "ok": False, "event": "optimization_saved", "error": f"Не удалось сохранить профиль. Перезагрузка отменена: {exc}"})

    def _restart_windows(self) -> bool:
        if os.name != "nt":
            self._log("error", "Restart requested on non-Windows platform; ignored")
            return False
        try:
            subprocess.Popen(["shutdown.exe", "/r", "/t", "0", "/f"], creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            return True
        except OSError as exc:
            self._log("error", f"Windows restart failed: {exc}")
            return False

    def create_item(self, request_id: Any, name: str, kind: str, content: str = "") -> None:
        try:
            safe = _safe_name(name)
            if kind not in ("file", "folder"):
                raise ValueError("Тип объекта должен быть file или folder")
            base = self._desktop_path()
            target = base / safe
            if target.exists():
                raise FileExistsError("Объект с таким именем уже существует")
            if kind == "folder":
                target.mkdir()
            else:
                with open(target, "x", encoding="utf-8") as stream:
                    stream.write(str(content or ""))
            self._log("files", f"CREATE_{kind.upper()} user={self.current_user!r} path={target}")
            self.emit({"id": request_id, "ok": True, "event": "item_created", "name": safe, "kind": kind})
        except Exception as exc:
            self.emit({"id": request_id, "ok": False, "event": "item_created", "error": str(exc)})

    def delete_item(self, request_id: Any, name: str) -> None:
        try:
            safe = _safe_name(name)
            target = self._desktop_path() / safe
            if not target.exists():
                raise FileNotFoundError("Объект не найден")
            trash = self.desktop_root / ".trash" / self.current_user
            trash.mkdir(parents=True, exist_ok=True)
            destination = trash / f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{safe}"
            shutil.move(str(target), str(destination))
            self._log("files", f"MOVE_TO_TRASH user={self.current_user!r} path={target}")
            self.emit({"id": request_id, "ok": True, "event": "item_deleted", "name": safe})
        except Exception as exc:
            self.emit({"id": request_id, "ok": False, "event": "item_deleted", "error": str(exc)})

    def open_item(self, request_id: Any, name: str) -> None:
        try:
            safe = _safe_name(name)
            target = self._desktop_path() / safe
            if not target.exists():
                raise FileNotFoundError("Объект не найден")
            if os.name == "nt":
                os.startfile(str(target))  # type: ignore[attr-defined]
            else:
                subprocess.Popen(["xdg-open", str(target)])
            self._log("files", f"OPEN user={self.current_user!r} path={target}")
            self.emit({"id": request_id, "ok": True, "event": "item_opened", "name": safe})
        except Exception as exc:
            self.emit({"id": request_id, "ok": False, "event": "item_opened", "error": str(exc)})

    def set_pin(self, request_id: Any, old_pin: str, new_pin: str) -> None:
        try:
            if not re.fullmatch(r"\d{4,8}", str(new_pin or "")):
                raise ValueError("Новый PIN должен содержать от 4 до 8 цифр")
            if hashlib.sha256(str(old_pin).encode()).hexdigest() != self._get_pin_hash():
                raise ValueError("Текущий PIN указан неверно")
            self._save_pin(str(new_pin))
            self._log("security", f"PIN_CHANGED user={self.current_user!r}")
            self.emit({"id": request_id, "ok": True, "event": "pin_changed"})
        except Exception as exc:
            self.emit({"id": request_id, "ok": False, "event": "pin_changed", "error": str(exc)})

    def check_updates(self, request_id: Any) -> None:
        def work() -> None:
            try:
                request = urllib.request.Request(RELEASE_API, headers={"Accept": "application/vnd.github+json", "User-Agent": "BITOS-UpdateManager/21.01"})
                with urllib.request.urlopen(request, timeout=15) as response:
                    if response.status != 200:
                        raise RuntimeError(f"GitHub API вернул HTTP {response.status}")
                    release = json.loads(response.read(8 * 1024 * 1024).decode("utf-8"))
                tag = str(release.get("tag_name") or "").strip()
                url = str(release.get("zipball_url") or "").strip()
                if not tag or not url or not url.startswith("https://api.github.com/repos/Saryanich/BITOS/"):
                    raise ValueError("GitHub не вернул корректную ссылку на архив релиза")
                newer = _version_parts(tag) > _version_parts(APP_VERSION)
                self.update = {"latest_version": tag, "download_url": url, "release_notes": str(release.get("body") or "Нет описания"),
                               "update_available": newer, "checked_at": _utc_stamp(), "download_path": None}
                _atomic_json(self.update_status_path, self.update)
                self.emit({"id": request_id, "ok": True, "event": "update_check_complete", "available": newer,
                           "version": tag, "notes": self.update["release_notes"][:12000]})
            except Exception as exc:
                self.emit({"id": request_id, "ok": False, "event": "update_check_complete", "error": str(exc)})
        self.executor.submit(work)

    def download_update(self, request_id: Any) -> None:
        def work() -> None:
            part = self.update_dir / "update.zip.part"
            final = self.update_dir / "update.zip"
            digest = hashlib.sha256()
            total = 0
            try:
                url = str(self.update.get("download_url") or "")
                if not url.startswith("https://api.github.com/repos/Saryanich/BITOS/"):
                    raise ValueError("Сначала проверьте наличие обновлений")
                req = urllib.request.Request(url, headers={"User-Agent": "BITOS-UpdateManager/21.01"})
                with urllib.request.urlopen(req, timeout=30) as response, open(part, "wb") as output:
                    expected = self._as_int(response.headers.get("Content-Length"), 0)
                    if expected > MAX_UPDATE_SIZE:
                        raise ValueError("Архив обновления превышает допустимый размер")
                    while True:
                        chunk = response.read(1024 * 256)
                        if not chunk:
                            break
                        total += len(chunk)
                        if total > MAX_UPDATE_SIZE:
                            raise ValueError("Архив обновления превышает допустимый размер")
                        output.write(chunk)
                        digest.update(chunk)
                        if expected:
                            pct = min(99, int(total * 100 / expected))
                            self.emit({"id": request_id, "ok": True, "event": "update_download_progress", "progress": pct, "bytes": total})
                    output.flush()
                    os.fsync(output.fileno())
                if total <= 0:
                    raise ValueError("Сервер вернул пустой архив")
                with zipfile.ZipFile(part, "r") as archive:
                    if archive.testzip():
                        raise ValueError("Контрольная проверка ZIP не пройдена")
                    if sum(max(0, x.file_size) for x in archive.infolist()) > MAX_EXTRACTED_SIZE:
                        raise ValueError("Размер распакованного архива слишком велик")
                os.replace(part, final)
                self.update.update({"download_path": str(final), "sha256": digest.hexdigest(), "download_size": total, "downloaded_at": _utc_stamp()})
                _atomic_json(self.update_status_path, self.update)
                self.emit({"id": request_id, "ok": True, "event": "update_download_complete", "path": str(final),
                           "sha256": digest.hexdigest(), "bytes": total})
            except Exception as exc:
                try:
                    part.unlink(missing_ok=True)
                except OSError:
                    pass
                self.emit({"id": request_id, "ok": False, "event": "update_download_complete", "error": str(exc)})
        self.executor.submit(work)

    def apply_update(self, request_id: Any) -> None:
        """Install after the server/UI exits; use backup + rollback per changed file."""
        archive_path = Path(str(self.update.get("download_path") or self.update_dir / "update.zip"))
        if not archive_path.is_file():
            self.emit({"id": request_id, "ok": False, "event": "update_install_ready", "error": "Архив обновления не найден"})
            return
        try:
            actual = _sha256_file(archive_path)
            expected = str(self.update.get("sha256") or "")
            if not expected or actual != expected:
                raise ValueError("Контрольная сумма архива не совпадает с сохранённой")
            stage = self.update_dir / "stage"
            shutil.rmtree(stage, ignore_errors=True)
            _safe_extract(archive_path, stage)
            candidates = [p for p in stage.iterdir() if p.is_dir()]
            code_root = candidates[0] if len(candidates) == 1 else stage
            # Launch this same file in a detached helper. The helper waits until
            # the GUI and service release their handles, then performs the swap.
            command = [sys.executable, str(Path(__file__).resolve()), "--apply-update", str(code_root), str(self.base), str(self.update_dir)]
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "DETACHED_PROCESS", 0)
            subprocess.Popen(command, cwd=str(self.base), creationflags=flags if os.name == "nt" else 0,
                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True)
            self.emit({"id": request_id, "ok": True, "event": "update_install_ready", "message": "Пакет проверен. Установщик запущен; приложение будет закрыто."})
        except Exception as exc:
            self.emit({"id": request_id, "ok": False, "event": "update_install_ready", "error": str(exc)})

    def emit(self, response: dict[str, Any]) -> None:
        with self.output_lock:
            sys.stdout.write(json.dumps(response, ensure_ascii=False, separators=(",", ":")) + "\n")
            sys.stdout.flush()

    def handle(self, request: dict[str, Any]) -> None:
        request_id = request.get("id")
        command = str(request.get("command") or "")
        try:
            if command == "boot":
                self.boot(request_id)
            elif command == "login":
                self.executor.submit(self.login, request_id, str(request.get("username") or ""), str(request.get("pin") or ""))
            elif command == "desktop_state":
                self.desktop_state(request_id)
            elif command == "set_optimization":
                self.set_optimization(request_id, request.get("value"), False)
            elif command == "save_and_reboot":
                self.set_optimization(request_id, request.get("value"), True)
            elif command == "create_item":
                self.create_item(request_id, str(request.get("name") or ""), str(request.get("kind") or ""), str(request.get("content") or ""))
            elif command == "delete_item":
                self.delete_item(request_id, str(request.get("name") or ""))
            elif command == "open_item":
                self.open_item(request_id, str(request.get("name") or ""))
            elif command == "set_pin":
                self.set_pin(request_id, str(request.get("old_pin") or ""), str(request.get("new_pin") or ""))
            elif command == "check_updates":
                self.check_updates(request_id)
            elif command == "download_update":
                self.download_update(request_id)
            elif command == "apply_update":
                self.apply_update(request_id)
            elif command == "open_app":
                app = str(request.get("app") or "")
                commands = {"explorer": ["explorer.exe"], "calculator": ["calc.exe"], "notepad": ["notepad.exe"],
                            "terminal": ["cmd.exe"], "paint": ["mspaint.exe"], "settings": ["control.exe"]}
                if app not in commands or os.name != "nt":
                    raise ValueError("Это приложение недоступно на данной платформе")
                if app == "explorer":
                    subprocess.Popen(["explorer.exe", str(self._desktop_path())], close_fds=True)
                else:
                    subprocess.Popen(commands[app], close_fds=True)
                self.emit({"id": request_id, "ok": True, "event": "app_launched", "app": app})
            elif command == "logout":
                self._log("access", f"USER_LOGOUT user={self.current_user!r}")
                self.current_user = "User"
                self.emit({"id": request_id, "ok": True, "event": "logout"})
            elif command == "shutdown":
                self._log("access", f"SHUTDOWN requested user={self.current_user!r}")
                if os.name == "nt":
                    subprocess.Popen(["shutdown.exe", "/s", "/t", "0", "/f"], creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                self.emit({"id": request_id, "ok": True, "event": "shutdown_started"})
            elif command == "get_settings":
                self.emit({"id": request_id, "ok": True, "event": "settings", "optimization": self.config.get("optimization_percent", 0),
                           "version": APP_VERSION, "build": APP_BUILD})
            elif command == "quit":
                self.emit({"id": request_id, "ok": True, "event": "quit"})
                self.running = False
            else:
                raise ValueError(f"Неизвестная команда: {command}")
        except Exception as exc:
            self.emit({"id": request_id, "ok": False, "event": "error", "error": str(exc)})


def _apply_update_helper(source: Path, target: Path, update_dir: Path) -> int:
    """Transactional updater helper; does not delete unrelated destination files."""
    time.sleep(3.0)
    source = source.resolve()
    target = target.resolve()
    backup_root = update_dir / "backup" / datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root.mkdir(parents=True, exist_ok=True)
    excluded = {"System", ".git", "venv", ".venv", "__pycache__", "$RECYCLE.BIN"}
    changed: list[tuple[Path, Path | None]] = []
    try:
        files = [p for p in source.rglob("*") if p.is_file() and not any(part in excluded for part in p.relative_to(source).parts)]
        for item in files:
            relative = item.relative_to(source)
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            backup = None
            if destination.exists():
                backup = backup_root / relative
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(destination, backup)
            changed.append((destination, backup))
            tmp = destination.with_name(destination.name + f".{os.getpid()}.new")
            shutil.copy2(item, tmp)
            os.replace(tmp, destination)
        (update_dir / "install_result.json").write_text(json.dumps({"success": True, "files": len(changed), "time": _utc_stamp()}, ensure_ascii=False, indent=2), encoding="utf-8")
        native_candidates = (target / "NativeUI" / "BITOS_NativeUI.exe", target / "BITOS_NativeUI.exe")
        native_shell = next((candidate for candidate in native_candidates if candidate.is_file()), None)
        if os.name == "nt" and native_shell is not None:
            try:
                subprocess.Popen([str(native_shell)], cwd=str(native_shell.parent), close_fds=True)
            except OSError:
                pass
        return 0
    except Exception as exc:
        rollback_errors = []
        for destination, backup in reversed(changed):
            try:
                if backup and backup.exists():
                    shutil.copy2(backup, destination)
                else:
                    destination.unlink(missing_ok=True)
            except OSError as rollback_exc:
                rollback_errors.append(str(rollback_exc))
        result = {"success": False, "error": str(exc), "rollback_errors": rollback_errors, "time": _utc_stamp()}
        try:
            (update_dir / "install_result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            pass
        return 1


def run_pipe_service() -> int:
    script_dir = Path(__file__).resolve().parent
    # Keep System/Config, Security and DesktopFile beside the original BITOS
    # installation even though the replacement UI sources live in NativeUI/.
    project_root = script_dir.parent if script_dir.name.casefold() == "nativeui" else script_dir
    service = BITOSService(project_root)
    for raw in sys.stdin:
        if not service.running:
            break
        try:
            request = json.loads(raw)
            if not isinstance(request, dict):
                raise ValueError("Ожидался JSON-объект")
        except Exception as exc:
            service.emit({"id": None, "ok": False, "event": "protocol_error", "error": str(exc)})
            continue
        service.handle(request)
    service.executor.shutdown(wait=False)
    return 0


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--apply-update":
        if len(sys.argv) != 5:
            raise SystemExit(2)
        raise SystemExit(_apply_update_helper(Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])))
    raise SystemExit(run_pipe_service())
