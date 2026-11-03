"""Lightweight battery and removable-drive monitor for BITOS.

Polling is scheduled on the UI thread, while device queries run in the adaptive
worker pool. The 75% and 100% profiles do not poll automatically; the taskbar
battery indicator can still request a one-shot manual check.
"""
from __future__ import annotations

import ctypes
import os
import threading
from typing import Optional


class SystemMonitor:
    def __init__(self, bitos):
        self.bitos = bitos
        self._after_id = None
        self._stopped = False
        self._inflight = False
        self._lock = threading.Lock()
        self._previous_drives = None

    def start(self):
        self._stopped = False
        self.refresh_profile()

    def _cancel_timer(self):
        root = getattr(self.bitos, "ui_root", None)
        if self._after_id is not None and root is not None:
            try:
                root.after_cancel(self._after_id)
            except Exception:
                pass
        self._after_id = None

    def refresh_profile(self):
        self._cancel_timer()
        if self._stopped:
            return
        interval = self.bitos.ui_manager.system_check_interval_ms
        root = getattr(self.bitos, "ui_root", None)
        if interval is not None and root is not None:
            try:
                self._after_id = root.after(interval, self._tick)
            except Exception:
                self._after_id = None

    def _tick(self):
        self._after_id = None
        if self._stopped:
            return
        self.check_now(force=False)
        self.refresh_profile()

    def check_now(self, force: bool = True) -> bool:
        """Start a one-shot check. ``force=False`` marks it as automatic work."""
        if self._stopped:
            return False
        with self._lock:
            if self._inflight:
                return False
            self._inflight = True
        future = self.bitos.task_manager.submit(
            self._collect_state,
            automatic=not force,
            on_success=self._apply_state,
            on_error=self._on_error,
        )
        if future is None:
            with self._lock:
                self._inflight = False
            return False
        return True

    @staticmethod
    def _collect_state():
        return {
            "battery": SystemMonitor._read_battery(),
            "drives": SystemMonitor._read_removable_drives(),
        }

    @staticmethod
    def _read_battery() -> Optional[dict]:
        if os.name == "nt":
            try:
                class SYSTEM_POWER_STATUS(ctypes.Structure):
                    _fields_ = [
                        ("ACLineStatus", ctypes.c_byte),
                        ("BatteryFlag", ctypes.c_byte),
                        ("BatteryLifePercent", ctypes.c_byte),
                        ("Reserved1", ctypes.c_byte),
                        ("BatteryLifeTime", ctypes.c_ulong),
                        ("BatteryFullLifeTime", ctypes.c_ulong),
                    ]
                status = SYSTEM_POWER_STATUS()
                if ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(status)):
                    percent = int(status.BatteryLifePercent)
                    return {
                        "percent": percent if 0 <= percent <= 100 else None,
                        "ac": status.ACLineStatus == 1,
                        "charging": bool(status.BatteryFlag & 8),
                    }
            except Exception:
                return None
        try:
            import psutil  # Optional; Windows API above is preferred.
            battery = psutil.sensors_battery()
            if battery is not None:
                return {"percent": int(battery.percent), "ac": bool(battery.power_plugged),
                        "charging": bool(battery.power_plugged)}
        except Exception:
            pass
        return None

    @staticmethod
    def _read_removable_drives() -> list[str]:
        drives = []
        if os.name == "nt":
            try:
                mask = ctypes.windll.kernel32.GetLogicalDrives()
                for index in range(26):
                    if mask & (1 << index):
                        root = f"{chr(65 + index)}:\\"
                        if ctypes.windll.kernel32.GetDriveTypeW(ctypes.c_wchar_p(root)) == 2:
                            drives.append(root)
            except Exception:
                pass
        else:
            try:
                import psutil
                for part in psutil.disk_partitions(all=False):
                    if "removable" in (part.opts or "").lower():
                        drives.append(part.mountpoint)
            except Exception:
                pass
        return sorted(set(drives))

    def _apply_state(self, state: dict):
        with self._lock:
            self._inflight = False
        if self._stopped:
            return
        desktop = getattr(self.bitos, "desktop_instance", None)
        if desktop is not None:
            try:
                desktop.taskbar.update_system_status(state.get("battery"))
            except Exception:
                pass
        current = set(state.get("drives") or [])
        if self._previous_drives is not None:
            added = sorted(current - self._previous_drives)
            removed = sorted(self._previous_drives - current)
            center = getattr(desktop, "notification_center", None) if desktop else None
            if center:
                for drive in added:
                    center.add_notification("USB-накопитель подключён", drive, icon="🔌", category="device")
                for drive in removed:
                    center.add_notification("USB-накопитель отключён", drive, icon="🔌", category="device")
        self._previous_drives = current

    def _on_error(self, error: Exception):
        with self._lock:
            self._inflight = False
        manager = getattr(self.bitos, "error_manager", None)
        if manager and self.bitos.ui_manager.logs_enabled:
            manager._log_warning("SystemMonitor", str(error))

    def stop(self):
        self._stopped = True
        self._cancel_timer()
