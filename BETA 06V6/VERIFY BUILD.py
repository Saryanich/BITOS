# -*- coding: utf-8 -*-
"""Offline sanity check for the BITOS 11.02 BETA package."""
from __future__ import annotations
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
PACKAGE = ROOT / "bitos"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    errors: list[str] = []
    required = [
        PACKAGE / "main.pyw", PACKAGE / "server" / "core.py",
        PACKAGE / "server" / "workers.py", PACKAGE / "server" / "sounds.py",
        PACKAGE / "ui" / "windows.py", PACKAGE / "ui" / "manager.py",
        PACKAGE / "system" / "BITOSterm.pyw",
    ]
    for path in required:
        if not path.is_file():
            errors.append(f"Не найден файл: {path.relative_to(ROOT)}")

    try:
        from bitos.ui.manager import UIManager
        manager = UIManager()
        expected = {
            0: (1000, 1000, True, True, True),
            25: (1000, 1000, True, True, True),
            50: (1000, 10000, True, True, True),
            75: (60000, None, False, True, True),
            100: (None, None, False, False, False),
        }
        for level, values in expected.items():
            manager.optimization_level = level
            actual = (manager.clock_interval_ms, manager.system_check_interval_ms,
                      manager.widgets_enabled, manager.logs_enabled, manager.wallpaper_enabled)
            if actual != values:
                errors.append(f"Профиль {level}%: ожидалось {values}, получено {actual}")
    except Exception as exc:
        errors.append(f"Проверка профилей: {exc}")

    config = PACKAGE / "system" / "Config"
    try:
        widgets = json.loads((config / "widgets.json").read_text(encoding="utf-8"))
        if widgets != []:
            errors.append("widgets.json должен начинаться с пустого списка")
    except Exception as exc:
        errors.append(f"Проверка widgets.json: {exc}")

    for name in ("buinw1.png", "buinw2.png", "buinw3.png", "buinw4.png"):
        if not (config / "wallpapers" / name).is_file():
            errors.append(f"Нет встроенных обоев: {name}")
    sounds = PACKAGE / "system" / "Sounds"
    for name in ("startup.wav", "logon.wav", "click.wav", "notification.wav", "success.wav", "error.wav"):
        if not (sounds / name).is_file():
            errors.append(f"Нет системного звука: {name}")

    if errors:
        print("BITOS 11.02 BETA: ПРОВЕРКА НЕ ПРОЙДЕНА")
        for item in errors:
            print(" -", item)
        return 1
    print("BITOS 11.02 BETA: базовая проверка пройдена")
    print(" - структура ui/server/system: OK")
    print(" - 5 профилей оптимизации: OK")
    print(" - виджеты по умолчанию пустые: OK")
    print(" - встроенные обои и WAV-звуки: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
