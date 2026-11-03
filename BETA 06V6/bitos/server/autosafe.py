"""UI-thread autosave scheduler that obeys all BITOS optimization tiers."""

class AutoSafe:
    """Save user desktop state at the rate selected by the optimization profile.

    Tk objects are read only on the UI thread. At 75% and 100% periodic saves
    are disabled; the state is still saved on explicit close/logout actions.
    """
    def __init__(self, bitos, desktop):
        self.bitos = bitos
        self.desktop = desktop
        self.is_running = True
        self._after_id = None
        self.refresh_profile()

    def refresh_profile(self):
        self._cancel_timer()
        if not self.is_running:
            return
        interval = self.bitos.ui_manager.autosave_interval_ms
        root = getattr(self.bitos, "ui_root", None)
        if interval is not None and root is not None:
            try:
                self._after_id = root.after(interval, self._tick)
            except Exception:
                self._after_id = None

    def _cancel_timer(self):
        root = getattr(self.bitos, "ui_root", None)
        if self._after_id is not None and root is not None:
            try:
                root.after_cancel(self._after_id)
            except Exception:
                pass
        self._after_id = None

    def _tick(self):
        self._after_id = None
        if not self.is_running:
            return
        self.save_all()
        self.refresh_profile()

    def save_all(self):
        if not self.desktop:
            return
        try:
            self.desktop.save_widgets()
            self.desktop.save_desktop_shortcuts()
            self.desktop.save_theme(self.desktop.current_theme)
        except Exception as exc:
            mgr = getattr(self.bitos, "error_manager", None)
            if mgr and self.bitos.ui_manager.logs_enabled:
                mgr._log_warning("AutoSafe", str(exc))

    def stop(self, force_save=True):
        self.is_running = False
        self._cancel_timer()
        if force_save:
            self.save_all()
