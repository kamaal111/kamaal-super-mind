"""Install and remove only this plugin's native Cursor hook entries."""

import json
import os
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "lib/cursor_hooks.py"


class CursorHooksTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="cursor-hook-config-")
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.plugin = self.home / "plugin with spaces and 'quotes' $dollars"
        self.config = self.home / ".cursor/hooks.json"
        self.config.parent.mkdir()

    def invoke(self, action, check=True):
        return subprocess.run(
            [sys.executable, str(SCRIPT), action, str(self.plugin)],
            env={**os.environ, "HOME": str(self.home)},
            capture_output=True,
            text=True,
            check=check,
        )

    def read(self):
        return json.loads(self.config.read_text())

    def test_install_preserves_existing_hooks_and_is_idempotent(self):
        existing = {
            "version": 1,
            "extra": "keep",
            "hooks": {"stop": [{"command": "other"}]},
        }
        self.config.write_text(json.dumps(existing))
        self.invoke("install")
        self.invoke("install")

        result = self.read()

        self.assertEqual(result["extra"], "keep")
        self.assertEqual(result["hooks"]["stop"][0], {"command": "other"})
        self.assertEqual(len(result["hooks"]["stop"]), 2)
        self.assertEqual(len(result["hooks"]["beforeSubmitPrompt"]), 1)
        self.assertIsNone(result["hooks"]["stop"][1]["loop_limit"])

    def test_command_quotes_the_install_path_and_targets_shared_handler(self):
        self.invoke("install")
        command = self.read()["hooks"]["stop"][0]["command"]

        self.assertEqual(
            shlex.split(command),
            ["python3", str(self.plugin / "hooks/duplication_review.py"), "cursor"],
        )

    def test_uninstall_preserves_unrelated_entries_and_settings(self):
        self.config.write_text(
            json.dumps({"version": 1, "hooks": {"stop": [{"command": "other"}]}})
        )
        self.invoke("install")
        self.invoke("uninstall")
        self.invoke("uninstall")

        self.assertEqual(
            self.read(), {"version": 1, "hooks": {"stop": [{"command": "other"}]}}
        )

    def test_uninstall_without_config_does_not_create_one(self):
        self.invoke("uninstall")

        self.assertFalse(self.config.exists())

    def test_invalid_json_is_preserved_and_reported(self):
        original = "{invalid json\n"
        self.config.write_text(original)

        result = self.invoke("install", check=False)

        self.assertEqual(result.returncode, 1)
        self.assertIn("Cursor hooks configuration", result.stderr)
        self.assertEqual(self.config.read_text(), original)

    def test_invalid_event_array_is_preserved(self):
        original = json.dumps({"version": 1, "hooks": {"stop": {"command": "other"}}})
        self.config.write_text(original)

        result = self.invoke("install", check=False)

        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.config.read_text(), original)

    def test_symlinked_configuration_is_preserved(self):
        target = self.home / "shared.json"
        target.write_text('{"version": 1, "hooks": {}}')
        self.config.symlink_to(target)

        result = self.invoke("install", check=False)

        self.assertEqual(result.returncode, 1)
        self.assertTrue(self.config.is_symlink())
        self.assertEqual(target.read_text(), '{"version": 1, "hooks": {}}')

    def test_manifests_select_host_hooks_without_cursor_plugin_registration(self):
        codex = json.loads((ROOT / ".codex-plugin/plugin.json").read_text())
        claude = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
        cursor = json.loads((ROOT / ".cursor-plugin/plugin.json").read_text())

        self.assertEqual(codex["hooks"], "./hooks/codex.json")
        self.assertEqual(claude["hooks"], "./hooks/claude.json")
        self.assertNotIn("hooks", cursor)
        self.assertFalse((ROOT / "hooks/hooks.json").exists())


if __name__ == "__main__":
    unittest.main()
