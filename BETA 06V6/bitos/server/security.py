import os
import json
import shutil
import hashlib
import queue
import threading
import time
from datetime import datetime

try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False

class SecurityManager:
    """Журналирование, аудит и безопасность входа"""
    def __init__(self, bitos):
        self.bitos = bitos
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.logs_path = bitos.system_paths["logs"]
        os.makedirs(self.logs_path, exist_ok=True)
        
        self.log_files = {
            "access": os.path.join(self.logs_path, "access.log"),
            "error": os.path.join(self.logs_path, "error.log"),
            "audit": os.path.join(self.logs_path, "audit.log"),
            "apps": os.path.join(self.logs_path, "applications.log"),
            "files": os.path.join(self.logs_path, "files.log"),
            "security": os.path.join(self.logs_path, "security.log"),
        }
        self._log_queue = queue.Queue()
        self._writer_running = bool(getattr(getattr(bitos, "ui_manager", None), "logs_enabled", True))
        self._writer_thread = None
        if self._writer_running:
            self._writer_thread = threading.Thread(target=self._log_writer, name="BITOS-SecurityLog", daemon=True)
            self._writer_thread.start()
        self.session_stats = {
            'start_time': datetime.now(),
            'apps_launched': [],
            'files_accessed': [],
            'files_deleted': [],
            'files_moved': [],
            'folders_created': [],
            'shortcuts_created': [],
            'shortcuts_deleted': [],
            'errors': [],
            'security_events': []
        }
        self.log_audit(f"SESSION_START: User {bitos.current_user} session={self.session_id}")

    def _write_log(self, name, msg):
        if not getattr(getattr(self.bitos, "ui_manager", None), "logs_enabled", True):
            return
        path = self.log_files.get(name)
        if not path:
            return
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            self._log_queue.put_nowait((path, f"[{ts}] {msg}\n"))
        except Exception:
            pass

    def _log_writer(self):
        """Write logs off the UI thread; at 50% flush the batch every five seconds."""
        pending = {}
        while self._writer_running or not self._log_queue.empty():
            interval = getattr(self.bitos.ui_manager, "log_flush_interval", 0.0)
            timeout = interval if interval > 0 else 0.15
            try:
                path, line = self._log_queue.get(timeout=timeout)
                if path is None:
                    self._flush_logs(pending)
                    if not self._writer_running:
                        break
                    continue
                pending.setdefault(path, []).append(line)
                if interval <= 0:
                    self._flush_logs(pending)
            except queue.Empty:
                self._flush_logs(pending)
        self._flush_logs(pending)

    def refresh_profile(self):
        """Start or stop disk logging immediately when the optimization tier changes."""
        should_run = bool(self.bitos.ui_manager.logs_enabled)
        thread = self._writer_thread
        if should_run and (thread is None or not thread.is_alive()):
            self._writer_running = True
            self._writer_thread = threading.Thread(target=self._log_writer, name="BITOS-SecurityLog", daemon=True)
            self._writer_thread.start()
        elif not should_run and self._writer_running:
            self._writer_running = False
            self._log_queue.put((None, None))
            if thread and thread.is_alive():
                thread.join(timeout=1.0)
            self._writer_thread = None

    @staticmethod
    def _flush_logs(pending):
        for path, lines in list(pending.items()):
            if not lines:
                continue
            try:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "a", encoding="utf-8") as f:
                    f.writelines(lines)
            except Exception:
                pass
            pending[path] = []

    def stop(self):
        self._writer_running = False
        if self._writer_thread and self._writer_thread.is_alive():
            self._log_queue.put((None, None))
            self._writer_thread.join(timeout=1.0)

    def log_access(self, user, action, result, details=""):
        self._write_log("access", f"USER:{user} ACTION:{action} RESULT:{result} {details}".strip())

    def log_error(self, module, err, details=""):
        self.session_stats['errors'].append({'time': datetime.now(), 'module': module, 'err': str(err)})
        self._write_log("error", f"MODULE:{module} ERROR:{err} {details}".strip())

    def log_audit(self, msg):
        self._write_log("audit", msg)

    def log_app_launch(self, app_name, user):
        self.session_stats['apps_launched'].append({'time': datetime.now(), 'app': app_name})
        self._write_log("apps", f"USER:{user} LAUNCHED:{app_name}")

    def log_file_access(self, user, path, action):
        self.session_stats['files_accessed'].append({'time': datetime.now(), 'path': path, 'action': action})
        self._write_log("files", f"USER:{user} ACTION:{action} PATH:{path}")

    def log_file_delete(self, user, path, permanent=False):
        act = "PERMANENT_DELETE" if permanent else "MOVE_TO_TRASH"
        self.session_stats['files_deleted'].append({'time': datetime.now(), 'path': path, 'perm': permanent})
        self._write_log("files", f"USER:{user} {act}:{path}")

    def log_file_move(self, user, src, dst):
        self.session_stats['files_moved'].append({'time': datetime.now(), 'src': src, 'dst': dst})
        self._write_log("files", f"USER:{user} MOVE:{src} -> {dst}")

    def log_folder_create(self, user, path):
        self.session_stats['folders_created'].append({'time': datetime.now(), 'path': path})
        self._write_log("files", f"USER:{user} CREATE_FOLDER:{path}")

    def log_security_event(self, ev_type, details):
        self.session_stats['security_events'].append({'time': datetime.now(), 'type': ev_type, 'details': details})
        self._write_log("security", f"SECURITY:{ev_type} {details}")

    def log_shortcut_create(self, user, app, pos):
        self.session_stats['shortcuts_created'].append({'time': datetime.now(), 'app': app, 'pos': pos})
        self._write_log("apps", f"USER:{user} CREATE_SHORTCUT:{app} POS:{pos}")

    def log_shortcut_delete(self, user, app):
        self.session_stats['shortcuts_deleted'].append({'time': datetime.now(), 'app': app})
        self._write_log("apps", f"USER:{user} DELETE_SHORTCUT:{app}")

    def log_theme_change(self, user, old_t, new_t):
        self._write_log("audit", f"USER:{user} THEME_CHANGE:{old_t} -> {new_t}")

    def log_pin_change(self, user):
        self._write_log("security", f"USER:{user} PIN_CHANGED")

    def log_login_attempt(self, user, success, ip="localhost"):
        status = "SUCCESS" if success else "FAILED"
        self._write_log("access", f"LOGIN_ATTEMPT USER:{user} STATUS:{status} IP:{ip}")
        if not success:
            self.log_security_event("FAILED_LOGIN", f"User:{user} IP:{ip}")

    def log_logout(self, user):
        self._write_log("access", f"USER:{user} LOGOUT")

    def log_shutdown(self, user):
        self._write_log("access", f"USER:{user} SHUTDOWN")

    def log_reboot(self, user):
        self._write_log("access", f"USER:{user} REBOOT")

    def get_session_summary(self):
        return {
            'duration': str(datetime.now() - self.session_stats['start_time']).split('.')[0],
            'apps_launched': len(self.session_stats['apps_launched']),
            'files_accessed': len(self.session_stats['files_accessed']),
            'files_deleted': len(self.session_stats['files_deleted']),
            'errors': len(self.session_stats['errors']),
            'security_events': len(self.session_stats['security_events'])
        }

class TrashManager:
    """Менеджер корзины BITOS"""
    def __init__(self, bitos):
        self.bitos = bitos
        self.trash_path = os.path.join(bitos.system_paths["temp"], "Trash")
        self.trash_info_path = os.path.join(self.trash_path, "trash_info.json")
        os.makedirs(self.trash_path, exist_ok=True)
        self.trash_items = self.load_trash_info()

    def load_trash_info(self):
        if os.path.exists(self.trash_info_path):
            try:
                with open(self.trash_info_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_trash_info(self):
        try:
            with open(self.trash_info_path, 'w', encoding='utf-8') as f:
                json.dump(self.trash_items, f, indent=4, ensure_ascii=False)
        except Exception:
            pass

    def get_size(self, path):
        if os.path.isfile(path):
            return os.path.getsize(path)
        elif os.path.isdir(path):
            total = 0
            for root, _, files in os.walk(path):
                for f in files:
                    try:
                        total += os.path.getsize(os.path.join(root, f))
                    except Exception:
                        pass
            return total
        return 0

    def move_to_trash(self, paths):
        moved = []
        for path in paths:
            if not os.path.exists(path):
                continue
            base = os.path.basename(path)
            trash_name = base
            counter = 1
            while os.path.exists(os.path.join(self.trash_path, trash_name)):
                name, ext = os.path.splitext(base)
                trash_name = f"{name}_{counter}{ext}"
                counter += 1
            dst = os.path.join(self.trash_path, trash_name)
            try:
                shutil.move(path, dst)
                item = {
                    'original_path': path,
                    'trash_name': trash_name,
                    'deleted_time': datetime.now().isoformat(),
                    'is_dir': os.path.isdir(dst),
                    'size': self.get_size(dst)
                }
                self.trash_items[trash_name] = item
                moved.append(item)
                if self.bitos and hasattr(self.bitos, 'security'):
                    self.bitos.security.log_file_delete(self.bitos.current_user, path, permanent=False)
            except Exception:
                pass
        self.save_trash_info()
        return moved

    def restore_item(self, trash_name):
        if trash_name not in self.trash_items:
            return False, "Файл не найден в базе корзины"
        item = self.trash_items[trash_name]
        orig = item['original_path']
        src = os.path.join(self.trash_path, trash_name)
        if not os.path.exists(src):
            del self.trash_items[trash_name]
            self.save_trash_info()
            return False, "Файл физически отсутствует в корзине"
        if os.path.exists(orig):
            b, e = os.path.splitext(orig)
            c = 1
            while os.path.exists(f"{b}_restored_{c}{e}"):
                c += 1
            orig = f"{b}_restored_{c}{e}"
        try:
            os.makedirs(os.path.dirname(orig), exist_ok=True)
            shutil.move(src, orig)
            del self.trash_items[trash_name]
            self.save_trash_info()
            return True, orig
        except Exception as e:
            return False, str(e)

    def delete_permanently(self, trash_name):
        if trash_name not in self.trash_items:
            return False, "Файл не найден в базе"
        p = os.path.join(self.trash_path, trash_name)
        try:
            if os.path.exists(p):
                if os.path.isdir(p):
                    shutil.rmtree(p)
                else:
                    os.remove(p)
            del self.trash_items[trash_name]
            self.save_trash_info()
            return True, "Удалено навсегда"
        except Exception as e:
            return False, str(e)

    def empty_trash(self):
        try:
            for name in list(self.trash_items.keys()):
                p = os.path.join(self.trash_path, name)
                if os.path.exists(p):
                    if os.path.isdir(p):
                        shutil.rmtree(p)
                    else:
                        os.remove(p)
            self.trash_items.clear()
            self.save_trash_info()
            return True, "Корзина очищена"
        except Exception as e:
            return False, str(e)

    def get_trash_items(self):
        items = []
        for name, info in self.trash_items.items():
            info['trash_name'] = name
            items.append(info)
        items.sort(key=lambda x: x.get('deleted_time', ''), reverse=True)
        return items

class InputBlocker:
    """Блокировка системных клавиш Windows (чит-код: 5x CapsLock + 2x Tab)"""
    def __init__(self):
        self.blocking = False
        self.available = KEYBOARD_AVAILABLE
        self.caps_count = 0
        self.tab_count = 0
        self.TARGET_CAPS = 5
        self.TARGET_TAB = 2
        self.hooks = []

    def start_blocking(self):
        if not self.available:
            return
        try:
            self.stop_blocking()
            blocked_keys = [
                'win', 'left windows', 'right windows',
                'alt+tab', 'alt+f4', 'ctrl+esc',
                'win+d', 'win+r', 'win+l', 'win+e'
            ]
            for k in blocked_keys:
                try:
                    keyboard.add_hotkey(k, lambda: None, suppress=True)
                    self.hooks.append(k)
                except Exception:
                    pass
            keyboard.add_hotkey('caps lock', self._on_caps, suppress=False)
            self.hooks.append('caps lock')
            keyboard.add_hotkey('tab', self._on_tab, suppress=False)
            self.hooks.append('tab')
            self.blocking = True
        except Exception:
            self.blocking = False

    def _on_caps(self):
        if self.blocking:
            self.caps_count += 1
            self._check_unlock()

    def _on_tab(self):
        if self.blocking:
            self.tab_count += 1
            self._check_unlock()

    def _check_unlock(self):
        if self.caps_count >= self.TARGET_CAPS and self.tab_count >= self.TARGET_TAB:
            self.stop_blocking()

    def stop_blocking(self):
        if not self.available:
            return
        try:
            keyboard.unhook_all()
            self.hooks.clear()
            self.blocking = False
            self.caps_count = 0
            self.tab_count = 0
        except Exception:
            pass

    def is_active(self):
        return self.blocking
