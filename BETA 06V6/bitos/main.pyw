# -*- coding: utf-8 -*-
"""BITOS 11.02 launcher."""
from __future__ import annotations

import os
import sys
import traceback

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(PACKAGE_DIR)
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)


def main() -> int:
    try:
        from bitos.server.core import BITOS
        BITOS().run()
        return 0
    except Exception:
        details = traceback.format_exc()
        try:
            log_dir = os.path.join(PACKAGE_DIR, "system", "Logs")
            os.makedirs(log_dir, exist_ok=True)
            with open(os.path.join(log_dir, "startup_error.log"), "a", encoding="utf-8") as stream:
                stream.write(details + "\n")
        except Exception:
            pass
        try:
            import tkinter.messagebox as messagebox
            messagebox.showerror("BITOS — ошибка запуска", details)
        except Exception:
            print(details, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
