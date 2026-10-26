# -*- coding: utf-8 -*-
"""BITOS 06V6 launcher. Runtime definitions are loaded in order into one namespace.

The shared namespace intentionally preserves the original application's global
references while code is being separated into independently maintained files.
"""
from pathlib import Path
import sys

APP_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = APP_DIR.parent
MODULE_DIR = APP_DIR / "modules"

if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

# Preserve the previous data-root behavior: System/ stays beside the repository,
# not inside the source-code directory.
runtime = {
    "__name__": "__main__",
    "__file__": str(REPOSITORY_ROOT / "__BITOS_RUNTIME__.pyw"),
    "__package__": None,
}

MODULE_FILES = (
    "security_and_files.py",
    "file_explorer_apps.py",
    "desktop_shell.py",
    "system_core_widgets.py",
    "diagnostics_audio.py",
    "settings_recovery.py",
    "multi_monitor.py",
)

for module_name in MODULE_FILES:
    source_file = MODULE_DIR / module_name
    source_text = source_file.read_text(encoding="utf-8")
    compiled = compile(source_text, str(source_file), "exec")
    exec(compiled, runtime, runtime)

if not runtime.get("BITOS"):
    raise RuntimeError("BITOS core class was not loaded")

bitos = runtime["BITOS"]()
