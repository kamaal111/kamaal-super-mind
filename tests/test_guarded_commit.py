"""Exercise commit failures through the helper and real Git workspace files."""

import fcntl
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "skills/gitbutler-session-commit/scripts/commit-selected.sh"


class GuardedCommitTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.git("init", "--quiet")
        self.git("config", "user.name", "Test User")
        self.git("config", "user.email", "test@example.com")
        self.file = self.root / "work.txt"
        self.file.write_text("committed\n")
        self.git("add", "work.txt")
        self.git("commit", "--quiet", "-m", "initial")
        self.git("branch", "-m", "gitbutler/workspace")
        self.file.write_text("precious work\n")
        self.message = self.root / "message.txt"
        self.message.write_text("fix: preserve work\n")
        self.bin = self.root / "bin"
        self.bin.mkdir()
        mock = self.bin / "but"
        mock.write_text(
            "#!/usr/bin/env python3\n"
            "import os, pathlib, subprocess, sys\n"
            "p = pathlib.Path('calls.txt')\n"
            "with p.open('a') as out: out.write(repr(sys.argv[1:])+'\\n')\n"
            "if sys.argv[1:] == ['status', '--json']: sys.exit(0)\n"
            "if sys.argv[1:] == ['commit', '--help']:\n"
            "    print('[CHANGES]...'); sys.exit(0)\n"
            "mode = os.environ.get('COMMIT_TEST_MODE', 'fail')\n"
            "target = pathlib.Path('work.txt')\n"
            "if mode == 'revert': target.write_text('committed\\n')\n"
            "if mode == 'delete': target.unlink()\n"
            "if mode == 'newer': target.write_text('newer edit\\n')\n"
            "if mode == 'head-change':\n"
            "    subprocess.run(['git', 'update-ref', 'HEAD', 'HEAD^'], check=True)\n"
            "    target.write_text('committed\\n')\n"
            "if mode == 'success': sys.exit(0)\n"
            "sys.exit(23)\n"
        )
        mock.chmod(0o755)

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.root)

    def run_helper(self, mode="fail"):
        return subprocess.run(
            [str(HELPER), "new-task-branch", str(self.message), "selected-id"],
            cwd=self.root,
            env={
                **os.environ,
                "PATH": f"{self.bin}:{os.environ['PATH']}",
                "COMMIT_TEST_MODE": mode,
            },
            text=True,
            capture_output=True,
            check=False,
        )

    def backup(self):
        backups = list(
            (self.root / ".git/kamaal-super-mind").glob("recovery-*/workspace.json")
        )
        self.assertEqual(len(backups), 1)
        return json.loads(backups[0].read_text())

    def test_existing_index_lock_prevents_every_gitbutler_call(self):
        lock = self.root / ".git/index.lock"
        lock.write_text("owned elsewhere")
        result = self.run_helper()
        self.assertEqual(result.returncode, 1)
        self.assertFalse((self.root / "calls.txt").exists())
        self.assertEqual(lock.read_text(), "owned elsewhere")
        self.assertEqual(self.file.read_text(), "precious work\n")

    def test_another_helper_holds_shared_commit_lock(self):
        directory = self.root / ".git/kamaal-super-mind"
        directory.mkdir()
        with (directory / "commit.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = self.run_helper()
        self.assertEqual(result.returncode, 1)
        self.assertIn("Another protected GitButler commit", result.stderr)
        self.assertFalse((self.root / "calls.txt").exists())

    def test_failed_commit_restores_file_reverted_to_head(self):
        result = self.run_helper("revert")
        self.assertEqual(result.returncode, 23)
        self.assertEqual(self.file.read_text(), "precious work\n")
        self.assertIn("Recovered lost workspace content: work.txt", result.stderr)
        self.assertEqual(
            bytes.fromhex(self.backup()["files"]["work.txt"]["before"]["data"]),
            b"precious work\n",
        )

    def test_failed_commit_restores_deleted_file_and_executable_mode(self):
        self.file.chmod(0o755)
        result = self.run_helper("delete")
        self.assertEqual(result.returncode, 23)
        self.assertEqual(self.file.read_text(), "precious work\n")
        self.assertEqual(self.file.stat().st_mode & 0o777, 0o755)

    def test_failed_commit_preserves_a_newer_edit_and_original_backup(self):
        result = self.run_helper("newer")
        self.assertEqual(result.returncode, 23)
        self.assertEqual(self.file.read_text(), "newer edit\n")
        self.assertIn("Preserved differing content: work.txt", result.stderr)
        self.assertEqual(
            bytes.fromhex(self.backup()["files"]["work.txt"]["before"]["data"]),
            b"precious work\n",
        )

    def test_success_targets_new_branch_and_only_explicit_change_ids(self):
        result = self.run_helper("success")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(self.file.read_text(), "precious work\n")
        calls = (self.root / "calls.txt").read_text()
        self.assertIn(
            "['commit', '--branch', 'new-task-branch', '--message', "
            "'fix: preserve work', 'selected-id']",
            calls,
        )
        self.assertNotIn("Commit failed", result.stderr)
        self.assertIn("work.txt", self.backup()["files"])

    def test_failure_without_content_loss_leaves_work_and_retains_backup(self):
        result = self.run_helper()
        self.assertEqual(result.returncode, 23)
        self.assertEqual(self.file.read_text(), "precious work\n")
        self.assertIn("Recovery copy retained", result.stderr)
        self.assertIn("work.txt", self.backup()["files"])

    def test_failed_commit_restores_a_removed_untracked_file(self):
        self.git("rm", "--cached", "work.txt")
        self.git("commit", "--quiet", "-m", "untrack fixture")
        result = self.run_helper("delete")
        self.assertEqual(result.returncode, 23)
        self.assertEqual(self.file.read_text(), "precious work\n")
        self.assertIsNone(self.backup()["files"]["work.txt"]["baseline"])

    def test_failed_commit_restores_a_removed_symlink_without_reading_its_target(self):
        self.file.unlink()
        self.file.symlink_to("outside-target")
        result = self.run_helper("delete")
        self.assertEqual(result.returncode, 23)
        self.assertTrue(self.file.is_symlink())
        self.assertEqual(os.readlink(self.file), "outside-target")
        self.assertEqual(
            self.backup()["files"]["work.txt"]["before"],
            {"kind": "symlink", "target": "outside-target"},
        )

    def test_backup_records_a_preexisting_deletion_without_resurrecting_it(self):
        self.file.unlink()
        result = self.run_helper()
        self.assertEqual(result.returncode, 23)
        self.assertFalse(self.file.exists())
        self.assertEqual(
            self.backup()["files"]["work.txt"]["before"], {"kind": "missing"}
        )

    def test_failure_after_head_changes_keeps_current_content_and_backup(self):
        self.git("commit", "--allow-empty", "--quiet", "-m", "second fixture")
        result = self.run_helper("head-change")
        self.assertEqual(result.returncode, 23)
        self.assertEqual(self.file.read_text(), "committed\n")
        self.assertIn("HEAD changed", result.stderr)
        self.assertEqual(
            bytes.fromhex(self.backup()["files"]["work.txt"]["before"]["data"]),
            b"precious work\n",
        )

    def test_recovery_directory_is_private(self):
        result = self.run_helper()
        self.assertEqual(result.returncode, 23)
        backups = list((self.root / ".git/kamaal-super-mind").glob("recovery-*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].stat().st_mode & 0o777, 0o700)
