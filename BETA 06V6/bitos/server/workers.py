"""Adaptive background work manager for BITOS.

Long-running I/O is executed outside Tk's main thread.  UI callbacks are
marshalled back through the live Tk root.  Automatic work is blocked at the
75% and 100% survival profiles; explicitly user-started jobs remain usable.
"""
from __future__ import annotations

import os
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any, Callable, Optional


class BackgroundTaskManager:
    def __init__(self, bitos):
        self.bitos = bitos
        self._executor: Optional[ThreadPoolExecutor] = None
        self._lock = threading.RLock()
        self._futures: set[Future] = set()
        self._closed = False
        self._workers = self._detect_worker_count()

    @staticmethod
    def _available_memory_mb() -> Optional[int]:
        try:
            if os.name == "nt":
                import ctypes
                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                    ]
                state = MEMORYSTATUSEX()
                state.dwLength = ctypes.sizeof(state)
                if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(state)):
                    return int(state.ullTotalPhys / (1024 * 1024))
            if hasattr(os, "sysconf"):
                pages = os.sysconf("SC_PHYS_PAGES")
                page_size = os.sysconf("SC_PAGE_SIZE")
                return int(pages * page_size / (1024 * 1024))
        except Exception:
            pass
        return None

    def _detect_worker_count(self) -> int:
        level = self.bitos.ui_manager.get_optimization_level()
        cpu = max(1, os.cpu_count() or 1)
        ram_mb = self._available_memory_mb()
        # Keep one logical core free on multi-core systems and adapt to RAM.
        hardware_cap = max(1, cpu - 1) if cpu > 1 else 1
        if ram_mb is not None:
            if ram_mb <= 2500:
                hardware_cap = min(hardware_cap, 1)
            elif ram_mb <= 5000:
                hardware_cap = min(hardware_cap, 2)
        tier_cap = {0: 4, 25: 3, 50: 2, 75: 1, 100: 1}.get(level, 1)
        return max(1, min(hardware_cap, tier_cap))

    @property
    def automatic_tasks_enabled(self) -> bool:
        return self.bitos.ui_manager.get_optimization_level() < 75 and not self._closed

    @property
    def active_count(self) -> int:
        with self._lock:
            return sum(not f.done() for f in self._futures)

    def refresh_profile(self) -> None:
        """Recalculate worker cap after the optimization slider changes."""
        with self._lock:
            self._workers = self._detect_worker_count()
            if self._executor is not None and self.active_count == 0:
                self._executor.shutdown(wait=False, cancel_futures=False)
                self._executor = None

    def submit(
        self,
        function: Callable[..., Any],
        *args: Any,
        automatic: bool = False,
        on_success: Optional[Callable[[Any], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
        **kwargs: Any,
    ) -> Optional[Future]:
        """Submit work. ``automatic=True`` obeys the 75/100% auto-task lockout."""
        if automatic and not self.automatic_tasks_enabled:
            return None
        with self._lock:
            if self._closed:
                return None
            if self._executor is None:
                self._executor = ThreadPoolExecutor(
                    max_workers=self._workers,
                    thread_name_prefix="BITOS-Worker",
                )
            future = self._executor.submit(function, *args, **kwargs)
            self._futures.add(future)

        def finished(done: Future) -> None:
            with self._lock:
                self._futures.discard(done)
            try:
                result = done.result()
            except Exception as exc:
                if on_error:
                    self._dispatch(on_error, exc)
            else:
                if on_success:
                    self._dispatch(on_success, result)

        future.add_done_callback(finished)
        return future

    def _dispatch(self, callback: Callable, *args: Any) -> None:
        root = getattr(self.bitos, "ui_root", None)
        if root is not None:
            try:
                if root.winfo_exists():
                    root.after(0, lambda: callback(*args))
                    return
            except Exception:
                pass
        # A callback that touches Tk must never be invoked on a worker thread.
        # If the UI has gone away, discard it rather than touching destroyed UI.

    def shutdown(self, wait: bool = False) -> None:
        with self._lock:
            self._closed = True
            executor, self._executor = self._executor, None
        if executor is not None:
            executor.shutdown(wait=wait, cancel_futures=True)
