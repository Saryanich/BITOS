import os
import sys
import queue
import threading
import traceback
import functools
from datetime import datetime

class ErrorManager:
    """Централизованный регистратор ошибок и логов тестов в System/Logs"""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self, bitos=None):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self.bitos = bitos
        self.error_count = 0
        self.warning_count = 0
        self.info_count = 0
        self._queue = queue.Queue()
        self.is_running = True
        self._writer_thread = None
        
        if bitos and hasattr(bitos, 'system_paths'):
            self.logs_path = bitos.system_paths["logs"]
        else:
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.logs_path = os.path.join(base, "system", "Logs")
        os.makedirs(self.logs_path, exist_ok=True)
        
        self.error_log = os.path.join(self.logs_path, "error.log")
        self.console_log = os.path.join(self.logs_path, "console.log")
        self.events_log = os.path.join(self.logs_path, "events.log")
        self.test_log = os.path.join(self.logs_path, "test.txt")
        
        self._start_writer()

    def _start_writer(self):
        if not getattr(getattr(self.bitos, "ui_manager", None), "logs_enabled", True):
            self.is_running = False
            return
        def loop():
            pending = {}
            while self.is_running or not self._queue.empty():
                interval = getattr(getattr(self.bitos, "ui_manager", None), "log_flush_interval", 0.0)
                try:
                    target_file, msg = self._queue.get(timeout=interval if interval > 0 else 0.2)
                    if target_file is None:
                        self._flush_pending(pending)
                        if not self.is_running:
                            break
                        continue
                    pending.setdefault(target_file, []).append(msg)
                    if interval <= 0:
                        self._flush_pending(pending)
                except queue.Empty:
                    self._flush_pending(pending)
                except Exception:
                    pass
            self._flush_pending(pending)
        self._writer_thread = threading.Thread(target=loop, daemon=True, name="BITOS-ErrorLog")
        self._writer_thread.start()

    @staticmethod
    def _flush_pending(pending):
        for target_file, messages in list(pending.items()):
            if not messages:
                continue
            try:
                with open(target_file, "a", encoding="utf-8") as f:
                    f.writelines(messages)
            except Exception:
                pass
            pending[target_file] = []

    def refresh_profile(self):
        """Disable or resume the log writer together with the selected profile."""
        should_run = bool(getattr(getattr(self.bitos, "ui_manager", None), "logs_enabled", True))
        thread = self._writer_thread
        if should_run and (thread is None or not thread.is_alive()):
            self.is_running = True
            self._start_writer()
        elif not should_run and self.is_running:
            self.is_running = False
            self._queue.put((None, None))
            if thread and thread.is_alive():
                thread.join(timeout=1.0)
            self._writer_thread = None

    def _can_log(self):
        return getattr(getattr(self.bitos, "ui_manager", None), "logs_enabled", True)

    def _log_error(self, err_type, msg, tb=""):
        if not self._can_log():
            return
        self.error_count += 1
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        text = f"[{ts}] [ERROR] [{err_type}] {msg}\n"
        if tb:
            text += f"Traceback:\n{tb}\n"
        self._queue.put((self.error_log, text))

    def _log_warning(self, wtype, msg):
        if not self._can_log():
            return
        self.warning_count += 1
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self._queue.put((self.events_log, f"[{ts}] [WARNING] [{wtype}] {msg}\n"))

    def _log_info(self, msg):
        if not self._can_log():
            return
        self.info_count += 1
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self._queue.put((self.events_log, f"[{ts}] [INFO] {msg}\n"))

    def _log_console(self, text, is_error=False):
        if not self._can_log():
            return
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        prefix = "[STDERR]" if is_error else "[STDOUT]"
        self._queue.put((self.console_log, f"[{ts}] {prefix} {text.strip()}\n"))

    def log_test(self, passed: bool, test_name: str, error=None):
        if not self._can_log():
            return
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        status = "PASS" if passed else "FAIL"
        err_str = f": {error}" if error else ""
        entry = f"[{ts}] [{status}] {test_name}{err_str}\n"
        self._queue.put((self.test_log, entry))

    def stop(self):
        """Drain queued log records and stop the background writer."""
        self.is_running = False
        worker = getattr(self, "_writer_thread", None)
        if worker and worker.is_alive():
            self._queue.put((None, None))
            worker.join(timeout=1.0)

    def get_statistics(self):
        return {
            'total_errors': self.error_count,
            'warnings': self.warning_count,
            'info_messages': self.info_count,
            'is_running': self.is_running
        }

def safe_call(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            mgr = ErrorManager._instance
            if mgr:
                mgr._log_error(func.__name__, str(e), traceback.format_exc())
            return None
    return wrapper

def init_error_manager(bitos=None):
    return ErrorManager(bitos)
