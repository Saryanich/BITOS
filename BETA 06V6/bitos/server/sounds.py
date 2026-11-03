"""BITOS application sound service using the bundled WAV files."""
from __future__ import annotations

import json
import os
import platform
import subprocess
import threading
from pathlib import Path

try:
    import winsound
except ImportError:  # Non-Windows fallback is optional.
    winsound = None


class SoundManager:
    SOUND_FILES = {
        "startup": "startup.wav",
        "logon": "logon.wav",
        "login": "logon.wav",
        "logoff": "logoff.wav",
        "shutdown": "shutdown.wav",
        "error": "error.wav",
        "notification": "notification.wav",
        "success": "success.wav",
        "succes": "success.wav",
        "warning": "warning.wav",
        "usb_connect": "usb_connect.wav",
        "usb_disconnect": "usb_disconnect.wav",
        "click": "click.wav",
    }

    def __init__(self, bitos):
        self.bitos = bitos
        self.sound_dir = Path(bitos.system_paths["sounds"])
        self.config_file = Path(bitos.system_paths["config"]) / "sound.json"
        self.enabled = True
        self._load()

    def _load(self):
        try:
            if self.config_file.exists():
                data = json.loads(self.config_file.read_text(encoding="utf-8"))
                self.enabled = bool(data.get("enabled", True))
        except Exception:
            self.enabled = True

    def save(self):
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            temp = self.config_file.with_suffix(".json.tmp")
            temp.write_text(json.dumps({"enabled": self.enabled}, ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(temp, self.config_file)
        except Exception as exc:
            mgr = getattr(self.bitos, "error_manager", None)
            if mgr and self.bitos.ui_manager.logs_enabled:
                mgr._log_warning("SoundManager", str(exc))

    def set_enabled(self, enabled: bool):
        self.enabled = bool(enabled)
        self.save()
        if self.enabled:
            self.play("success")
        return self.enabled

    def toggle(self):
        return self.set_enabled(not self.enabled)

    def play(self, name: str) -> bool:
        if not self.enabled:
            return False
        filename = self.SOUND_FILES.get(str(name).lower(), "notification.wav")
        path = self.sound_dir / filename
        if not path.is_file():
            # Compatibility with the misspelled sound file in earlier builds.
            if filename == "success.wav" and (self.sound_dir / "succes.wav").is_file():
                path = self.sound_dir / "succes.wav"
            else:
                return False
        try:
            if winsound is not None:
                # SND_ASYNC keeps the UI thread free; the OS handles playback.
                winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
                return True
            if platform.system() == "Darwin":
                subprocess.Popen(["afplay", str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
            if platform.system() == "Linux":
                player = "paplay"
                subprocess.Popen([player, str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
        except Exception:
            return False
        return False

    def stop(self):
        try:
            if winsound is not None:
                winsound.PlaySound(None, winsound.SND_PURGE)
        except Exception:
            pass
