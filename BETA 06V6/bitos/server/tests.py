import os
import threading
from datetime import datetime
from bitos.server.security import TrashManager, SecurityManager
from bitos.server.updates import BipInstaller, UpdateManager
from bitos.ui.manager import UIManager
from bitos.server.errors import ErrorManager

def _already_tested_today(test_file):
    if not os.path.exists(test_file):
        return False
    try:
        today_str = datetime.now().strftime("%Y-%m-%d")
        with open(test_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        for line in reversed(lines[-25:]):
            if today_str in line and "[INFO] Итого:" in line:
                return True
    except Exception:
        pass
    return False

def run_all_tests(bitos):
    """Автоматический запуск тестов без блокировки UI, отчет в System/Logs/test.txt"""
    err_mgr = ErrorManager._instance or ErrorManager(bitos)
    test_file = os.path.join(bitos.system_paths["logs"], "test.txt")
    
    if _already_tested_today(test_file):
        return

    def runner():
        passed_count = 0
        failed_count = 0
        
        tests = [
            ("UIManager.get_sizes", lambda: isinstance(bitos.ui_manager.get_sizes(), dict)),
            ("UIManager.get_fonts", lambda: isinstance(bitos.ui_manager.get_fonts(), dict)),
            ("UIManager.get_colors", lambda: "bg" in bitos.ui_manager.get_colors("Базовая")),
            ("UIManager.set_touch_mode", lambda: (bitos.ui_manager.set_touch_mode(bitos.ui_manager.touch_mode), True)[1]),
            ("SecurityManager.log_audit", lambda: (bitos.security.log_audit("AutoTest Triggered"), True)[1]),
            ("SecurityManager.get_session_summary", lambda: "duration" in bitos.security.get_session_summary()),
            ("TrashManager.get_trash_items", lambda: isinstance(TrashManager(bitos).get_trash_items(), list)),
            ("BipInstaller.load_installed", lambda: isinstance(BipInstaller(None, bitos).load_installed(), dict)),
            ("UpdateManager._normalize_version", lambda: UpdateManager(bitos)._normalize_version("06V6") == "6.6"),
            ("UpdateManager._compare_versions", lambda: UpdateManager(bitos)._compare_versions("2.0", "1.0") == 1),
            ("ErrorManager.get_statistics", lambda: "total_errors" in err_mgr.get_statistics()),
        ]

        for name, test_fn in tests:
            try:
                res = test_fn()
                if res:
                    passed_count += 1
                    err_mgr.log_test(True, name)
                else:
                    failed_count += 1
                    err_mgr.log_test(False, name, "False returned")
            except Exception as e:
                failed_count += 1
                err_mgr.log_test(False, name, str(e))

        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        summary = f"[{ts}] [INFO] Итого: {passed_count} PASS, {failed_count} FAIL, 0 SKIP\n"
        with open(test_file, 'a', encoding='utf-8') as f:
            f.write(summary)

    threading.Thread(target=runner, daemon=True, name="BootTests").start()
