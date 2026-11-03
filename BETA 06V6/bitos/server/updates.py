import os
import sys
import json
import time
import shutil
import zipfile
import threading
import subprocess
import platform
import re
import sys
from datetime import datetime

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

class BipInstaller:
    """Установщик .bip пакетов"""
    def __init__(self, parent, bitos):
        self.parent = parent
        self.bitos = bitos
        self.apps_path = os.path.join(bitos.system_paths["root"], "Apps")
        self.installed_db = os.path.join(self.apps_path, "installed.json")
        self.start_menu_db = os.path.join(bitos.system_paths["config"], "start_menu_apps.json")
        os.makedirs(self.apps_path, exist_ok=True)
        self.installed_apps = self.load_installed()
        self.start_menu_apps = self.load_start_menu_apps()

    def _association_db(self):
        return os.path.join(self.bitos.system_paths["config"], "bip_file_associations.json")

    def get_file_associations(self):
        try:
            with open(self._association_db(), "r", encoding="utf-8") as stream:
                data = json.load(stream)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    @staticmethod
    def normalize_extensions(value):
        parts = value if isinstance(value, (list, tuple, set)) else re.split(r"[,;\s]+", str(value or ""))
        result = []
        for item in parts:
            ext = str(item).strip().lower()
            if not ext:
                continue
            if not ext.startswith("."):
                ext = "." + ext
            if re.fullmatch(r"\.[a-z0-9][a-z0-9._+-]{0,15}", ext) and ext not in result:
                result.append(ext)
        return result

    def _save_file_associations(self, associations):
        path = self._association_db()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as stream:
            json.dump(associations, stream, indent=2, ensure_ascii=False)
        os.replace(tmp, path)

    def _register_file_handlers(self, app_id, metadata):
        """Metadata: file_handlers: .docx=words.open;.xlsx=table.open"""
        raw = metadata.get("file_handlers", "")
        if not raw:
            return []
        associations = self.get_file_associations()
        registered = []
        for item in re.split(r"[;,]+", str(raw)):
            if not item.strip() or "=" not in item:
                continue
            extension, command = item.split("=", 1)
            extensions = self.normalize_extensions(extension)
            command = command.strip()
            if not extensions or not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", command):
                continue
            for ext in extensions:
                associations[ext] = {"app_id": app_id, "command": command}
                registered.append(ext)
        if registered:
            self._save_file_associations(associations)
        return registered

    def launch_for_file(self, file_path):
        ext = os.path.splitext(str(file_path))[1].lower()
        association = self.get_file_associations().get(ext)
        if isinstance(association, str):
            app_id, command = association, ""
        elif isinstance(association, dict):
            app_id, command = association.get("app_id", ""), association.get("command", "")
        else:
            return False, "Для этого расширения не назначено BIP-приложение"
        return self.launch_app(app_id, file_path=file_path, command=command)

    def load_installed(self):
        if os.path.exists(self.installed_db):
            try:
                with open(self.installed_db, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_installed(self):
        try:
            with open(self.installed_db, 'w', encoding='utf-8') as f:
                json.dump(self.installed_apps, f, indent=4, ensure_ascii=False)
        except Exception:
            pass

    def load_start_menu_apps(self):
        if os.path.exists(self.start_menu_db):
            try:
                with open(self.start_menu_db, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def save_start_menu_apps(self):
        try:
            with open(self.start_menu_db, 'w', encoding='utf-8') as f:
                json.dump(self.start_menu_apps, f, indent=4, ensure_ascii=False)
        except Exception:
            pass

    def get_start_menu_apps(self):
        """Return installed shortcuts only when their app still exists."""
        result = []
        for item in self.start_menu_apps:
            if not isinstance(item, dict):
                continue
            app_id = str(item.get('id', ''))
            if app_id in self.installed_apps:
                info = self.installed_apps[app_id]
                result.append({'id': app_id, 'name': info.get('name', item.get('name', app_id)),
                               'icon': info.get('icon', item.get('icon', '📦'))})
        return result

    def add_to_desktop(self, app_id):
        """Create a persistent desktop shortcut for a BIP app."""
        info = self.installed_apps.get(app_id)
        if not info:
            return False, 'Приложение не установлено'
        shortcut_file = os.path.join(self.bitos.system_paths['config'], 'desktop_shortcuts.json')
        try:
            try:
                with open(shortcut_file, 'r', encoding='utf-8') as stream:
                    shortcuts = json.load(stream)
                if not isinstance(shortcuts, list):
                    shortcuts = []
            except Exception:
                shortcuts = []
            if any(item.get('command') == f'bip:{app_id}' for item in shortcuts if isinstance(item, dict)):
                return True, 'Ярлык уже существует'
            occupied = {(item.get('grid_x', 0), item.get('grid_y', 0))
                        for item in shortcuts if isinstance(item, dict)}
            gx, gy = 0, 0
            while (gx, gy) in occupied:
                gx += 1
                if gx >= 10:
                    gx, gy = 0, gy + 1
            shortcuts.append({'icon': info.get('icon', '📦'), 'text': info.get('name', app_id),
                              'grid_x': gx, 'grid_y': gy, 'icon_id': f'{app_id}_{int(datetime.now().timestamp())}',
                              'command': f'bip:{app_id}'})
            with open(shortcut_file, 'w', encoding='utf-8') as stream:
                json.dump(shortcuts, stream, indent=2, ensure_ascii=False)
            return True, 'Ярлык добавлен'
        except Exception as exc:
            return False, str(exc)

    def install_bip(self, bip_path):
        if not os.path.exists(bip_path) or not bip_path.endswith('.bip'):
            return False, "Файл не найден или не является .bip"
        try:
            with open(bip_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            metadata = {}
            code = ""
            in_meta, in_code = False, False
            for line in content.splitlines():
                if line.strip() == '---METADATA---':
                    in_meta, in_code = True, False
                    continue
                elif line.strip() == '---CODE---':
                    in_meta, in_code = False, True
                    continue
                if in_meta and ':' in line:
                    k, v = line.split(':', 1)
                    metadata[k.strip()] = v.strip()
                elif in_code:
                    code += line + '\n'
            
            app_id = str(metadata.get('id', '')).strip()
            if not app_id or not re.fullmatch(r'[A-Za-z0-9_.-]{1,64}', app_id) or app_id in {'.', '..'}:
                return False, "Некорректный ID приложения в метаданных"
            main_name = str(metadata.get('main', 'main.pyw')).replace('\\', '/')
            if main_name.startswith('/') or any(part in ('..', '') for part in main_name.split('/')):
                return False, "Некорректный путь главного файла приложения"
            app_dir = os.path.abspath(os.path.join(self.apps_path, app_id))
            if os.path.commonpath([self.apps_path, app_dir]) != os.path.abspath(self.apps_path):
                return False, "Недопустимый путь приложения"
            os.makedirs(app_dir, exist_ok=True)
            main_path = os.path.abspath(os.path.join(app_dir, main_name))
            if os.path.commonpath([app_dir, main_path]) != app_dir:
                return False, "Главный файл выходит за пределы папки приложения"
            os.makedirs(os.path.dirname(main_path), exist_ok=True)
            with open(os.path.join(app_dir, 'package.json'), 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=4, ensure_ascii=False)
            with open(main_path, 'w', encoding='utf-8') as f:
                f.write(code)
            self.installed_apps[app_id] = {
                'name': metadata.get('name', app_id),
                'version': metadata.get('version', '1.0'),
                'icon': metadata.get('icon', '📦'),
                'main': main_name,
                'path': app_dir
            }
            self.save_installed()
            self.add_to_start_menu(app_id, self.installed_apps[app_id]['name'], self.installed_apps[app_id]['icon'])
            metadata['_registered_file_handlers'] = self._register_file_handlers(app_id, metadata)
            return True, metadata
        except Exception as e:
            return False, str(e)

    def add_to_start_menu(self, app_id, name, icon):
        for a in self.start_menu_apps:
            if a.get('id') == app_id:
                return
        self.start_menu_apps.append({'id': app_id, 'name': name, 'icon': icon})
        self.save_start_menu_apps()

    def launch_app(self, app_id, file_path=None, command=None):
        if app_id not in self.installed_apps:
            return False, "Приложение не найдено"
        info = self.installed_apps[app_id]
        p = os.path.join(info['path'], info['main'])
        if not os.path.exists(p):
            return False, "Исполняемый файл приложения отсутствует"
        try:
            if os.name == "nt":
                creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                args = [sys.executable, p]
                if command:
                    args.extend(["--bip-command", str(command)])
                if file_path:
                    args.extend(["--bip-file", os.path.abspath(file_path)])
                subprocess.Popen(args, creationflags=creationflags,
                                 cwd=info.get('path') or self.apps_path)
            else:
                args = [sys.executable, p]
                if command:
                    args.extend(["--bip-command", str(command)])
                if file_path:
                    args.extend(["--bip-file", os.path.abspath(file_path)])
                subprocess.Popen(args, cwd=info.get('path') or self.apps_path)
            return True, f"Запущено {info['name']}"
        except Exception as e:
            return False, str(e)

class UpdateManager:
    """Менеджер обновлений BITOS через GitHub Releases"""
    def __init__(self, bitos):
        self.bitos = bitos
        self.current_version_raw = getattr(bitos, 'version', "06V6")
        self.current_version = self._normalize_version(self.current_version_raw)
        self.repo_url = "https://api.github.com/repos/Saryanich/BITOS/releases/latest"
        self.latest_version = None
        self.latest_version_raw = None
        self.download_url = None
        self.release_notes = None
        self.update_available = False
        self.is_downloading = False
        self.is_installing = False
        self.download_progress = 0
        self.check_in_progress = False
        
        self.temp_dir = os.path.join(bitos.system_paths["temp"], "updates")
        self.status_file = os.path.join(bitos.system_paths["config"], "update_status.json")
        os.makedirs(self.temp_dir, exist_ok=True)
        self.status = self._load_status()

    def _normalize_version(self, version):
        v = str(version).replace('v', '').replace('V', '.').replace('_', '.').strip()
        parts = v.split('.')
        norm = []
        for p in parts:
            try:
                norm.append(str(int(p)))
            except ValueError:
                norm.append(p)
        return '.'.join(norm)

    def _parse_version_parts(self, version):
        parts = self._normalize_version(version).split('.')
        res = []
        for p in parts:
            try:
                res.append(int(p))
            except ValueError:
                res.append(p)
        return res

    def _compare_versions(self, v1, v2):
        p1, p2 = self._parse_version_parts(v1), self._parse_version_parts(v2)
        for i in range(max(len(p1), len(p2))):
            a = p1[i] if i < len(p1) else 0
            b = p2[i] if i < len(p2) else 0
            if isinstance(a, int) and isinstance(b, int):
                if a > b: return 1
                if a < b: return -1
            else:
                sa, sb = str(a).lower(), str(b).lower()
                if sa > sb: return 1
                if sa < sb: return -1
        return 0

    def _load_status(self):
        if os.path.exists(self.status_file):
            try:
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_status(self):
        try:
            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump(self.status, f, indent=4, ensure_ascii=False)
        except Exception:
            pass

    def check_for_updates(self, callback=None):
        """Manual update check. Network I/O runs on BITOS's adaptive worker pool."""
        if not REQUESTS_AVAILABLE:
            if callback:
                callback(False, None, None, None, "requests не установлен")
            return None
        if self.check_in_progress:
            return None
        self.check_in_progress = True

        def run():
            response = requests.get(self.repo_url, timeout=8, headers={"User-Agent": "BITOS-Updater"})
            if response.status_code != 200:
                raise RuntimeError(f"HTTP {response.status_code}")
            data = response.json()
            tag = data.get("tag_name", "").replace("v", "").strip()
            latest = self._normalize_version(tag)
            download_url = data.get("zipball_url")
            notes = data.get("body", "")
            available = self._compare_versions(latest, self.current_version) > 0
            return available, tag, download_url, notes

        def completed(result):
            self.check_in_progress = False
            available, tag, download_url, notes = result
            self.latest_version_raw = tag
            self.latest_version = self._normalize_version(tag)
            self.download_url = download_url
            self.release_notes = notes
            self.update_available = available
            self.status.update({"update_available": available, "latest_version": tag,
                                "checked_at": datetime.now().isoformat()})
            self._save_status()
            if callback:
                callback(available, tag, download_url, notes, None)

        def failed(exc):
            self.check_in_progress = False
            if callback:
                callback(False, None, None, None, str(exc))

        manager = getattr(self.bitos, "task_manager", None)
        if manager:
            return manager.submit(run, on_success=completed, on_error=failed)
        def legacy_worker():
            try: completed(run())
            except Exception as exc: failed(exc)
        threading.Thread(target=legacy_worker, daemon=True, name="BITOS-UpdateCheck").start()
        return True

    def download_update(self, progress_callback=None, complete_callback=None):
        """Download a release ZIP on an adaptive worker; UI callbacks are marshalled."""
        if not self.download_url or not REQUESTS_AVAILABLE:
            if complete_callback:
                complete_callback(False, None, "Нет URL загрузки или requests")
            return None
        if self.is_downloading:
            return None
        self.is_downloading = True

        def run():
            fn = f"update_{self.latest_version_raw or 'latest'}.zip"
            fp = os.path.join(self.temp_dir, fn)
            response = requests.get(self.download_url, stream=True, timeout=30)
            response.raise_for_status()
            total = int(response.headers.get("content-length", 0) or 0)
            downloaded = 0
            last_report = -1
            with open(fp, "wb") as output:
                for chunk in response.iter_content(chunk_size=128 * 1024):
                    if not chunk:
                        continue
                    output.write(chunk)
                    downloaded += len(chunk)
                    if total > 0 and progress_callback:
                        value = int(downloaded * 100 / total)
                        if value != last_report:
                            last_report = value
                            self.download_progress = value
                            manager = getattr(self.bitos, "task_manager", None)
                            if manager: manager._dispatch(progress_callback, value, f"Загрузка: {value}%")
                            else: progress_callback(value, f"Загрузка: {value}%")
            return fp

        def completed(fp):
            self.is_downloading = False
            self.download_progress = 100
            if complete_callback:
                complete_callback(True, fp, None)

        def failed(exc):
            self.is_downloading = False
            if complete_callback:
                complete_callback(False, None, str(exc))

        manager = getattr(self.bitos, "task_manager", None)
        if manager:
            return manager.submit(run, on_success=completed, on_error=failed)
        def legacy_worker():
            try: completed(run())
            except Exception as exc: failed(exc)
        threading.Thread(target=legacy_worker, daemon=True, name="BITOS-UpdateDownload").start()
        return True

    def install_update(self):
        """Строгий запуск внешнего restart.pyw для применения обновления"""
        restart_script = os.path.join(self.bitos.system_paths["root"], "restart.pyw")
        if os.path.exists(restart_script):
            subprocess.Popen([sys.executable, restart_script])
            sys.exit(0)
        return False
