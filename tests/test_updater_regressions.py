import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class UpdaterRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "bitos_update_manager.py").read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source, filename="bitos_update_manager.py")
        manager = next(
            node for node in cls.tree.body
            if isinstance(node, ast.ClassDef) and node.name == "UpdateManager"
        )
        method = next(
            node for node in manager.body
            if isinstance(node, ast.FunctionDef) and node.name == "_create_restart_script"
        )
        assignment = next(
            node for node in ast.walk(method)
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "script" for target in node.targets)
        )
        cls.restart_script = ast.literal_eval(assignment.value)

    def test_embedded_restart_script_compiles(self):
        compile(self.restart_script, "<BITOS restart installer>", "exec")

    def test_restart_script_has_no_undefined_error_counter(self):
        self.assertNotIn("if errors > 0", self.restart_script)
        self.assertIn("if updated == 0", self.restart_script)

    def test_update_download_has_security_guards(self):
        self.assertIn("allow_redirects=True", self.source)
        self.assertIn("final_url.hostname not in allowed_hosts", self.source)
        self.assertIn("os.replace(part_path, filepath)", self.source)

    def test_installer_uses_transactional_rollback(self):
        self.assertIn("rollback_dir", self.restart_script)
        self.assertIn("for dst, backup, had_original in reversed(replaced)", self.restart_script)
        self.assertNotIn("extractall(", self.restart_script)


if __name__ == "__main__":
    unittest.main()
