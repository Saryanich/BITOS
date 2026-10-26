"""BITOS update manager.

The updater is isolated from the large Tkinter application module so it can be
reviewed and tested independently. The actual install still requires Windows
runtime testing before being considered production-ready.
"""
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime
import tkinter as tk
from tkinter import messagebox

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    requests = None
    REQUESTS_AVAILABLE = False


def safe_version_token(value):
    """Возвращает безопасный фрагмент имени файла для версии обновления."""
    token = re.sub(r"[^A-Za-z0-9._-]", "_", str(value or "unknown"))
    token = token.strip("._-")
    return (token or "unknown")[:80]


class UpdateManager:
    """
    Менеджер обновлений BITOS
    Простая и надежная версия без бекапов
    """
    
    def __init__(self, bitos_instance):
        self.bitos = bitos_instance
        
        # Версии
        self.current_version_raw = bitos_instance.version if hasattr(bitos_instance, 'version') else "06V6"
        self.current_version = self._normalize_version(self.current_version_raw)
        
        # GitHub API
        self.repo_url = "https://api.github.com/repos/Saryanich/BITOS/releases/latest"
        
        # Состояние
        self.latest_version = None
        self.latest_version_raw = None
        self.download_url = None
        self.release_notes = None
        self.update_available = False
        self.is_downloading = False
        self.is_installing = False
        self.download_progress = 0
        self.error_message = None
        self.check_in_progress = False
        self.last_check_time = None
        
        # Пути
        self.base_path = bitos_instance.base_path
        self.temp_dir = os.path.join(bitos_instance.system_paths["temp"], "updates")
        self.backup_dir = os.path.join(bitos_instance.system_paths["temp"], "backups")
        self.restart_script = os.path.join(bitos_instance.base_path, "System", "restart.pyw")
        self.update_status_file = os.path.join(bitos_instance.system_paths["config"], "update_status.json")
        
        # Создаем папки
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Создаем/обновляем скрипт перезапуска
        # (пересоздаём всегда, чтобы исправления логики установки
        # доходили и до систем, где скрипт уже был создан ранее)
        self._create_restart_script()
        
        # Загружаем статус
        self.status = self._load_status()
        
        # Ищем главное окно для after()
        self._root = self._find_root()
        
        print(f"[UpdateManager] ✅ Инициализирован (v{self.current_version_raw})")
    
    # ==================== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ====================
    
    def _find_root(self):
        """Поиск главного окна tkinter"""
        # Пробуем разные варианты
        for attr in ['root', 'window', 'master', 'main_window', 'app', 'gui', 'tk_root']:
            if hasattr(self.bitos, attr):
                obj = getattr(self.bitos, attr)
                if hasattr(obj, 'after'):
                    print(f"[UpdateManager] ✅ Найдено главное окно: {attr}")
                    return obj
        
        # Если не нашли - пробуем найти через tkinter
        try:
            import tkinter as tk
            if tk._default_root:
                print("[UpdateManager] ✅ Используем tk._default_root")
                return tk._default_root
        except:
            pass
        
        print("[UpdateManager] ⚠️ Главное окно не найдено, callback будут вызываться напрямую")
        return None
    
    def _normalize_version(self, version):
        """Нормализация версии для сравнения"""
        v = str(version).replace('v', '').replace('V', '.').replace('_', '.').strip()
        parts = v.split('.')
        normalized = []
        for part in parts:
            try:
                normalized.append(str(int(part)))
            except ValueError:
                normalized.append(part)
        return '.'.join(normalized)
    
    def _parse_version_parts(self, version):
        """Разбор версии на части"""
        normalized = self._normalize_version(version)
        parts = normalized.split('.')
        result = []
        for p in parts:
            try:
                result.append(int(p))
            except ValueError:
                result.append(p)
        return result
    
    def _compare_versions(self, v1, v2):
        """Сравнение версий: 1 если v1 > v2, -1 если v1 < v2, 0 если равны"""
        parts1 = self._parse_version_parts(v1)
        parts2 = self._parse_version_parts(v2)
        
        for i in range(max(len(parts1), len(parts2))):
            p1 = parts1[i] if i < len(parts1) else 0
            p2 = parts2[i] if i < len(parts2) else 0
            
            if isinstance(p1, int) and isinstance(p2, int):
                if p1 > p2:
                    return 1
                elif p1 < p2:
                    return -1
            else:
                s1 = str(p1).lower()
                s2 = str(p2).lower()
                if s1 > s2:
                    return 1
                elif s1 < s2:
                    return -1
        return 0
    
    def _load_status(self):
        """Загрузка статуса обновлений"""
        if os.path.exists(self.update_status_file):
            try:
                with open(self.update_status_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_status(self):
        """Сохранение статуса обновлений"""
        try:
            with open(self.update_status_file, 'w', encoding='utf-8') as f:
                json.dump(self.status, f, indent=4, ensure_ascii=False)
        except:
            pass
    
    def _safe_callback(self, callback, *args):
        """Безопасный вызов callback"""
        if not callback:
            return
        
        try:
            if self._root and hasattr(self._root, 'after'):
                self._root.after(0, lambda c=callback, a=args: c(*a))
            else:
                callback(*args)
        except Exception as e:
            print(f"[UpdateManager] Ошибка callback: {e}")
            try:
                callback(*args)
            except:
                pass
    
    def _create_restart_script(self):
        """Создание скрипта для установки обновления после перезапуска"""
        script = '''# -*- coding: utf-8 -*-
import os, sys, time, shutil, zipfile, subprocess, platform, stat

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMP_DIR = os.path.join(BASE_PATH, "System", "Temp", "updates")

def main():
    print("=" * 50)
    print("УСТАНОВКА ОБНОВЛЕНИЯ BITOS")
    print("=" * 50)
    
    # Ждем чтобы основная программа закрылась
    print("\\nОжидание 10 секунд...")
    for i in range(10, 0, -1):
        print(f"Осталось {i} сек...", end='\\r')
        time.sleep(1)
    print("\\n")
    
    # Берём только тот архив, который передал менеджер обновлений.
    # Не выбираем случайный старый ZIP по времени изменения.
    requested_zip = os.environ.get("BITOS_UPDATE_ZIP", "")
    if requested_zip:
        zip_path = os.path.abspath(requested_zip)
        if (os.path.commonpath([os.path.abspath(TEMP_DIR), zip_path]) != os.path.abspath(TEMP_DIR)
                or not zip_path.lower().endswith(".zip") or not os.path.isfile(zip_path)):
            raise RuntimeError("Путь к архиву обновления недопустим")
    else:
        zip_files = [f for f in os.listdir(TEMP_DIR) if f.lower().endswith(".zip")]
        if len(zip_files) != 1:
            raise RuntimeError("Нельзя однозначно определить архив обновления; повторите скачивание")
        zip_path = os.path.join(TEMP_DIR, zip_files[0])
    print("📦 Найден файл: " + os.path.basename(zip_path))
    
    # Извлекаем архив
    extract_path = os.path.join(TEMP_DIR, "extracted")
    if os.path.exists(extract_path):
        shutil.rmtree(extract_path)
    os.makedirs(extract_path)
    
    print("📦 Проверка и извлечение обновления...")
    with zipfile.ZipFile(zip_path, 'r') as z:
        infos = z.infolist()
        if not infos or len(infos) > 20000:
            raise RuntimeError("Архив пуст или содержит слишком много элементов")
        total_size = 0
        for info in infos:
            name = info.filename.replace("\\\\", "/")
            parts = name.split("/")
            mode = (info.external_attr >> 16) & 0o170000
            if (name.startswith("/") or (parts and ":" in parts[0]) or
                    any(part in ("..", "") for part in parts[:-1]) or
                    mode == stat.S_IFLNK):
                raise RuntimeError("Недопустимый путь в архиве: " + info.filename)
            if info.file_size > 256 * 1024 * 1024:
                raise RuntimeError("Файл в архиве превышает 256 МБ: " + info.filename)
            total_size += info.file_size
            if total_size > 1024 * 1024 * 1024:
                raise RuntimeError("Распакованный архив превышает лимит 1 ГБ")
        for info in infos:
            target = os.path.realpath(os.path.join(extract_path, *info.filename.replace("\\\\", "/").split("/")))
            if os.path.commonpath([os.path.realpath(extract_path), target]) != os.path.realpath(extract_path):
                raise RuntimeError("Путь выходит за пределы архива: " + info.filename)
            z.extract(info, extract_path)

    roots = [
        os.path.join(extract_path, item) for item in os.listdir(extract_path)
        if os.path.isdir(os.path.join(extract_path, item)) and
        not os.path.islink(os.path.join(extract_path, item))
    ]
    if len(roots) != 1:
        raise RuntimeError("В архиве должна находиться ровно одна корневая папка проекта")
    code_path = roots[0]
    print("📁 Папка с кодом: " + os.path.basename(code_path))

    # Сначала резервируем старые элементы, затем меняем. При сбое выполняем откат.
    print("\\n⚙️ Установка файлов...")
    rollback_dir = os.path.join(TEMP_DIR, "rollback_" + str(int(time.time())))
    os.makedirs(rollback_dir, exist_ok=True)
    replaced = []
    updated = 0
    try:
        for item in os.listdir(code_path):
            if item == "System":
                print("  ⏭ Пропущено: System/ (настройки сохранены)")
                continue
            src = os.path.join(code_path, item)
            dst = os.path.join(BASE_PATH, item)
            backup = os.path.join(rollback_dir, item)
            if os.path.islink(src) or os.path.islink(dst):
                raise RuntimeError("Символические ссылки запрещены: " + item)
            had_original = os.path.lexists(dst)
            if had_original:
                if os.path.isdir(dst):
                    shutil.copytree(dst, backup, symlinks=True)
                else:
                    shutil.copy2(dst, backup)
            replaced.append((dst, backup, had_original))
            if os.path.isdir(dst):
                shutil.rmtree(dst)
            elif os.path.lexists(dst):
                os.remove(dst)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
            print("  ✅ " + item)
            updated += 1
    except Exception as install_error:
        print("  ❌ Ошибка установки, выполняется откат: " + str(install_error))
        for dst, backup, had_original in reversed(replaced):
            try:
                if os.path.isdir(dst) and not os.path.islink(dst):
                    shutil.rmtree(dst)
                elif os.path.lexists(dst):
                    os.remove(dst)
                if had_original and os.path.lexists(backup):
                    if os.path.isdir(backup) and not os.path.islink(backup):
                        shutil.copytree(backup, dst, symlinks=True)
                    else:
                        shutil.copy2(backup, dst)
            except Exception as rollback_error:
                print("  ❌ Откат не удался для " + os.path.basename(dst) + ": " + str(rollback_error))
        raise
    
    print(f"\\n{'=' * 50}")
    print(f"✅ Установлено: {updated} файлов")
    if errors > 0:
        print(f"❌ Ошибок: {errors}")
        raise RuntimeError("Обновление завершилось с ошибками")
    print(f"{'=' * 50}")
    
    # Удаляем архив и временные файлы
    try:
        os.remove(zip_path)
        if os.path.exists(extract_path):
            shutil.rmtree(extract_path)
    except:
        pass
    
    # Перезагрузка
    print("\\n🔄 Перезагрузка через 5 секунд...")
    time.sleep(5)
    
    try:
        if platform.system() == "Windows":
            subprocess.Popen(["shutdown", "/r", "/t", "3", "/f"])
        else:
            subprocess.Popen(["reboot"])
    except Exception as e:
        print(f"❌ Не удалось перезагрузить: {e}")
        print("Пожалуйста, перезагрузите систему вручную.")
        input("Нажмите Enter для выхода...")
    
    sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        input("\\nНажмите Enter для выхода...")
        sys.exit(1)
'''
        try:
            with open(self.restart_script, 'w', encoding='utf-8') as f:
                f.write(script)
            print(f"[UpdateManager] ✅ Скрипт перезапуска создан: {self.restart_script}")
        except Exception as e:
            print(f"[UpdateManager] ❌ Ошибка создания скрипта: {e}")
    
    # ==================== ОСНОВНЫЕ МЕТОДЫ ====================
    
    def check_for_updates(self, callback=None):
        """
        Проверка обновлений
        callback(available, version, url, notes, error)
        """
        if self.check_in_progress:
            if callback:
                callback(False, None, None, None, "Проверка уже выполняется")
            return False
        
        self.check_in_progress = True
        self.error_message = None
        
        if not REQUESTS_AVAILABLE:
            self.error_message = "Библиотека requests не установлена"
            self.check_in_progress = False
            if callback:
                callback(False, None, None, None, self.error_message)
            return False
        
        def check_thread():
            try:
                print("[UpdateManager] 🔍 Проверка обновлений...")
                headers = {
                    "Accept": "application/vnd.github+json",
                    "User-Agent": "BITOS-UpdateManager"
                }
                response = requests.get(self.repo_url, timeout=10, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    latest_tag_raw = data.get("tag_name", "").replace("v", "").strip()
                    self.latest_version_raw = latest_tag_raw
                    self.latest_version = self._normalize_version(latest_tag_raw)
                    self.download_url = data.get("zipball_url")
                    self.release_notes = data.get("body", "Нет описания")
                    
                    print(f"[UpdateManager] Текущая: {self.current_version_raw}")
                    print(f"[UpdateManager] Последняя: {latest_tag_raw}")
                    
                    if self._compare_versions(self.latest_version, self.current_version) > 0:
                        self.update_available = True
                        print(f"[UpdateManager] ✅ Доступно обновление!")
                        
                        self.status['update_available'] = True
                        self.status['latest_version'] = latest_tag_raw
                        self.status['checked_at'] = datetime.now().isoformat()
                        self._save_status()
                        
                        self.last_check_time = datetime.now()
                        self.check_in_progress = False
                        
                        if callback:
                            self._safe_callback(callback, True, latest_tag_raw, self.download_url, self.release_notes, None)
                    else:
                        self.update_available = False
                        print(f"[UpdateManager] ✅ Система актуальна")
                        
                        self.status['update_available'] = False
                        self.status['checked_at'] = datetime.now().isoformat()
                        self._save_status()
                        
                        self.last_check_time = datetime.now()
                        self.check_in_progress = False
                        
                        if callback:
                            self._safe_callback(callback, False, None, None, None, None)
                else:
                    self.error_message = f"Ошибка API: {response.status_code}"
                    print(f"[UpdateManager] ❌ {self.error_message}")
                    self.check_in_progress = False
                    if callback:
                        self._safe_callback(callback, False, None, None, None, self.error_message)
                    
            except Exception as e:
                self.error_message = f"Ошибка проверки: {str(e)}"
                print(f"[UpdateManager] ❌ {self.error_message}")
                self.check_in_progress = False
                if callback:
                    self._safe_callback(callback, False, None, None, None, self.error_message)
        
        thread = threading.Thread(target=check_thread, daemon=True)
        thread.start()
        return True
    
    def download_update(self, progress_callback=None, complete_callback=None):
        """
        Скачивание обновления
        progress_callback(percent, status_text)
        complete_callback(success, filepath, error)
        """
        if not self.download_url:
            if complete_callback:
                complete_callback(False, None, "Нет URL для скачивания")
            return
        
        if self.is_downloading:
            if complete_callback:
                complete_callback(False, None, "Скачивание уже выполняется")
            return
        
        self.is_downloading = True
        self.download_progress = 0
        
        if progress_callback:
            progress_callback(0, "Начинаем скачивание...")
        
        def download_thread():
            try:
                filename = f"bitos_update_{safe_version_token(self.latest_version_raw)}.zip"
                filepath = os.path.join(self.temp_dir, filename)
                
                print(f"[UpdateManager] 📥 Скачивание: {filename}")
                
                from urllib.parse import urlparse
                allowed_hosts = {
                    "api.github.com", "github.com", "codeload.github.com",
                    "objects.githubusercontent.com", "release-assets.githubusercontent.com"
                }
                parsed = urlparse(self.download_url)
                if parsed.scheme != "https" or parsed.hostname not in allowed_hosts:
                    raise ValueError("Недоверенный адрес обновления")
                headers = {"User-Agent": "BITOS-UpdateManager"}
                part_path = filepath + ".part"
                max_download_size = 1024 * 1024 * 1024
                with requests.get(self.download_url, stream=True, timeout=(10, 60),
                                  headers=headers, allow_redirects=True) as response:
                    response.raise_for_status()
                    final_url = urlparse(response.url)
                    if final_url.scheme != "https" or final_url.hostname not in allowed_hosts:
                        raise ValueError("Перенаправление ведёт на недоверенный адрес")
                    total_size = int(response.headers.get("content-length", 0) or 0)
                    if total_size > max_download_size:
                        raise ValueError("Архив обновления превышает лимит 1 ГБ")
                    downloaded = 0
                    last_reported_percent = -1
                    with open(part_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=65536):
                            if not chunk:
                                continue
                            downloaded += len(chunk)
                            if downloaded > max_download_size:
                                raise ValueError("Загрузка превышает лимит 1 ГБ")
                            f.write(chunk)
                            if total_size > 0:
                                percent = min(99, int(downloaded * 100 / total_size))
                                self.download_progress = percent
                                if percent != last_reported_percent and progress_callback:
                                    last_reported_percent = percent
                                    self._safe_callback(progress_callback, percent, f"Скачивание: {percent}%")
                            else:
                                self.download_progress = min(99, self.download_progress + 1)
                                if progress_callback:
                                    self._safe_callback(
                                        progress_callback, self.download_progress,
                                        f"Скачано: {downloaded / (1024 * 1024):.1f} МБ"
                                    )
                import zipfile
                with zipfile.ZipFile(part_path, "r") as archive:
                    entries = archive.infolist()
                    if not entries or len(entries) > 20000:
                        raise ValueError("Архив пуст или содержит слишком много элементов")
                    if sum(info.file_size for info in entries) > 1024 * 1024 * 1024:
                        raise ValueError("Распакованный архив превышает лимит 1 ГБ")
                    if any(info.file_size > 256 * 1024 * 1024 for info in entries):
                        raise ValueError("Файл в архиве превышает лимит 256 МБ")
                os.replace(part_path, filepath)
                self.is_downloading = False
                self.download_progress = 100
                self.status["download_path"] = filepath
                self._save_status()
                if progress_callback:
                    self._safe_callback(progress_callback, 100, "Скачивание завершено")
                if complete_callback:
                    self._safe_callback(complete_callback, True, filepath, None)
                    
            except Exception as e:
                self.is_downloading = False
                try:
                    if "part_path" in locals() and os.path.exists(part_path):
                        os.remove(part_path)
                except OSError:
                    pass
                print(f"[UpdateManager] ❌ Ошибка скачивания: {e}")
                if complete_callback:
                    self._safe_callback(complete_callback, False, None, str(e))
        
        thread = threading.Thread(target=download_thread, daemon=True)
        thread.start()
    
    def install_update(self):
        """
        Установка обновления
        Возвращает True если установка запущена
        """
        if self.is_installing:
            messagebox.showinfo("Информация", "Установка уже выполняется")
            return False
        
        # Ищем файл обновления
        filepath = None
        if self.latest_version_raw:
            candidate = os.path.join(self.temp_dir, f"bitos_update_{safe_version_token(self.latest_version_raw)}.zip")
            if os.path.exists(candidate):
                filepath = candidate
        
        if not filepath:
            messagebox.showerror(
                "Ошибка",
                "Архив именно этой версии не найден. Повторите скачивание обновления."
            )
            return False
        
        # Запрашиваем подтверждение
        if not messagebox.askyesno(
            "Установка обновления",
            f"Установить обновление v{self.latest_version_raw}?\n\n"
            "⚠️ ВНИМАНИЕ:\n"
            "• Система будет перезагружена\n"
            "• Ваши настройки будут сохранены\n"
            "• Личные файлы не будут затронуты\n\n"
            "Продолжить?"
        ):
            return False
        
        self.is_installing = True
        
        try:
            # Запускаем скрипт обновления
            restart_env = os.environ.copy()
            restart_env["BITOS_UPDATE_ZIP"] = os.path.abspath(filepath)
            if platform.system() == "Windows":
                subprocess.Popen(
                    [sys.executable, self.restart_script],
                    env=restart_env,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )
            else:
                subprocess.Popen([sys.executable, self.restart_script], env=restart_env)
            
            # Закрываем приложение
            self._close_application()
            return True
            
        except Exception as e:
            self.is_installing = False
            messagebox.showerror("Ошибка", f"Не удалось запустить установку:\n{e}")
            return False
    
    def _close_application(self):
        """Корректное закрытие приложения"""
        try:
            import tkinter as tk
            if tk._default_root:
                tk._default_root.destroy()
        except:
            pass
        
        try:
            sys.exit(0)
        except:
            os._exit(0)
    
    # ==================== ДОПОЛНИТЕЛЬНЫЕ МЕТОДЫ ====================
    
    def get_status(self):
        """Получение статуса"""
        return {
            'current_version': self.current_version_raw,
            'latest_version': self.latest_version_raw,
            'update_available': self.update_available,
            'is_downloading': self.is_downloading,
            'is_installing': self.is_installing,
            'download_progress': self.download_progress,
            'last_check': self.last_check_time,
            'error': self.error_message
        }
    
    def get_update_info(self):
        """Получение информации об обновлении"""
        return {
            'version': self.latest_version_raw,
            'download_url': self.download_url,
            'release_notes': self.release_notes,
            'available': self.update_available
        }
    
    def is_update_available(self):
        """Проверка доступности обновления"""
        return self.update_available
    
    def get_download_path(self):
        """Возвращает только архив версии, для которой проверено обновление."""
        if not self.latest_version_raw:
            return None
        expected = os.path.join(
            self.temp_dir,
            "bitos_update_%s.zip" % safe_version_token(self.latest_version_raw)
        )
        if os.path.isfile(expected):
            return expected
        return None
    
    def clear_download(self):
        """Удаляет только временные файлы загрузки, сохраняя резервные копии отката."""
        try:
            for name in os.listdir(self.temp_dir):
                path = os.path.join(self.temp_dir, name)
                is_download_artifact = (
                    name.lower().endswith(".zip") or
                    name.lower().endswith(".zip.part") or
                    name == "extracted"
                )
                if not is_download_artifact:
                    continue
                try:
                    if os.path.islink(path):
                        os.remove(path)
                    elif os.path.isfile(path):
                        os.remove(path)
                    elif os.path.isdir(path):
                        shutil.rmtree(path)
                except OSError as cleanup_error:
                    print(f"[UpdateManager] ⚠️ Не удалось удалить {name}: {cleanup_error}")
            
            self.download_progress = 0
            self.update_available = False
            self.status["download_path"] = None
            self._save_status()
            print("[UpdateManager] ✅ Временные файлы обновления очищены; откаты сохранены")
            return True
        except Exception as e:
            print(f"[UpdateManager] ❌ Ошибка очистки: {e}")
            return False
