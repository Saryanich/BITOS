import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "06V6"
MODULES = APP / "modules"
EXPECTED_MODULES = (
    "security_and_files.py",
    "file_explorer_apps.py",
    "desktop_shell.py",
    "system_core_widgets.py",
    "diagnostics_audio.py",
    "settings_recovery.py",
    "multi_monitor.py",
)


class ModularLayoutTests(unittest.TestCase):
    def test_launcher_and_all_ordered_modules_exist(self):
        self.assertTrue((APP / "main.pyw").is_file())
        for name in EXPECTED_MODULES:
            with self.subTest(module=name):
                self.assertTrue((MODULES / name).is_file())

    def test_launcher_load_order_matches_declared_modules(self):
        launcher = (APP / "main.pyw").read_text(encoding="utf-8")
        positions = [launcher.index('"' + name + '"') for name in EXPECTED_MODULES]
        self.assertEqual(positions, sorted(positions))

    def test_core_and_entry_classes_are_present(self):
        source = "\n".join(
            (MODULES / name).read_text(encoding="utf-8")
            for name in EXPECTED_MODULES
        )
        for declaration in (
            "class LoginScreen:",
            "class SecurityManager:",
            "class ModernFileExplorer:",
            "class Desktop:",
            "class BITOS:",
            "class SettingsWindow:",
            "class MultiMonitorManager:",
        ):
            with self.subTest(declaration=declaration):
                self.assertIn(declaration, source)

    def test_old_monolithic_entrypoint_is_removed(self):
        self.assertFalse((ROOT / "BITOS 06V6.pyw").exists())

    def test_launcher_has_explicit_startup(self):
        launcher = (APP / "main.pyw").read_text(encoding="utf-8")
        self.assertIn('bitos = runtime["BITOS"]()', launcher)


if __name__ == "__main__":
    unittest.main()
