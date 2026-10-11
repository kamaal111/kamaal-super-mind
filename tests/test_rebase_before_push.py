"""Exercise the pre-push rebase against isolated local Git repositories."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills/pull-request/scripts/rebase-before-push.py"
)


class RebaseBeforePushTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="rebase-before-push-")
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.remote = root / "remote.git"
        self.upstream = root / "upstream"
        self.work = root / "work"
        self.env = dict(
            os.environ,
            GIT_CONFIG_NOSYSTEM="1",
            GIT_CONFIG_GLOBAL=os.devnull,
            GIT_TERMINAL_PROMPT="0",
            GIT_AUTHOR_NAME="Test",
            GIT_AUTHOR_EMAIL="test@example.test",
            GIT_COMMITTER_NAME="Test",
            GIT_COMMITTER_EMAIL="test@example.test",
        )
        self.git(root, "init", "--bare", "--initial-branch=main", str(self.remote))
        self.git(root, "clone", str(self.remote), str(self.upstream))
        (self.upstream / "shared.txt").write_text("initial\n")
        self.git(self.upstream, "add", ".")
        self.git(self.upstream, "commit", "-m", "Initial")
        self.git(self.upstream, "push", "origin", "main")
        self.git(root, "clone", str(self.remote), str(self.work))
        self.git(self.work, "switch", "-c", "feature")
        (self.work / "feature.txt").write_text("feature\n")
        self.git(self.work, "add", ".")
        self.git(self.work, "commit", "-m", "Feature")
        self.original_head = self.git(self.work, "rev-parse", "HEAD")
        (self.upstream / "main.txt").write_text("latest main\n")
        self.git(self.upstream, "add", ".")
        self.git(self.upstream, "commit", "-m", "Advance main")
        self.git(self.upstream, "push", "origin", "main")
        self.latest_main = self.git(self.upstream, "rev-parse", "HEAD")

    def git(self, cwd, *args):
        return subprocess.run(
            ["git", *args],
            cwd=cwd,
            env=self.env,
            check=True,
            text=True,
            capture_output=True,
        ).stdout.strip()

    def invoke(self, *args):
        return subprocess.run(
            [sys.executable, "-B", str(SCRIPT), "--branch", "feature", *args],
            cwd=self.work,
            env=self.env,
            check=False,
            text=True,
            capture_output=True,
        )

    def assert_unchanged(self):
        self.assertEqual(self.git(self.work, "rev-parse", "HEAD"), self.original_head)

    def test_fetches_new_main_rebases_and_does_not_publish(self):
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["base"], self.latest_main)
        self.assertNotEqual(data["head"], self.original_head)
        self.assertEqual(self.git(self.work, "rev-parse", "HEAD^"), self.latest_main)
        self.assertEqual((self.work / "feature.txt").read_text(), "feature\n")
        self.assertEqual((self.work / "main.txt").read_text(), "latest main\n")
        self.assertEqual(self.git(self.work, "status", "--porcelain"), "")
        self.assertEqual(
            self.git(self.remote, "for-each-ref", "--format=%(refname)", "refs/heads"),
            "refs/heads/main",
        )

    def test_repeated_invocation_preserves_rebased_head(self):
        first = self.invoke()
        second = self.invoke()
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(
            json.loads(first.stdout)["head"], json.loads(second.stdout)["head"]
        )

    def test_does_not_rewrite_other_branches_when_update_refs_is_configured(self):
        self.git(self.work, "branch", "other")
        self.git(self.work, "config", "rebase.updateRefs", "true")
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.git(self.work, "rev-parse", "other"), self.original_head)

    def test_rejects_unfinished_merge_before_fetch(self):
        self.git(self.work, "fetch", "origin")
        self.git(self.work, "merge", "--no-commit", "--no-ff", "origin/main")
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unfinished Git operation", result.stderr)
        self.assertTrue((self.work / ".git/MERGE_HEAD").exists())
        self.assert_unchanged()

    def test_rejects_untracked_work_without_stashing(self):
        (self.work / "untracked.txt").write_text("keep\n")
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("clean", result.stderr)
        self.assertEqual((self.work / "untracked.txt").read_text(), "keep\n")
        self.assertEqual(self.git(self.work, "stash", "list"), "")
        self.assert_unchanged()

    def test_rejects_staged_work_even_with_autostash_configured(self):
        self.git(self.work, "config", "rebase.autoStash", "true")
        (self.work / "feature.txt").write_text("keep staged\n")
        self.git(self.work, "add", ".")
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(
            self.git(self.work, "diff", "--cached", "--name-only"), "feature.txt"
        )
        self.assert_unchanged()

    def test_rejects_wrong_branch_without_switching(self):
        result = self.invoke("--branch", "other")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("already be checked out", result.stderr)
        self.assertEqual(self.git(self.work, "branch", "--show-current"), "feature")
        self.assert_unchanged()

    def test_rejects_main(self):
        self.git(self.work, "switch", "main")
        head = self.git(self.work, "rev-parse", "HEAD")
        result = self.invoke("--branch", "main")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Select a PR branch", result.stderr)
        self.assertEqual(self.git(self.work, "rev-parse", "HEAD"), head)

    def test_rejects_detached_head(self):
        self.git(self.work, "switch", "--detach")
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("detached HEAD", result.stderr)
        self.assert_unchanged()

    def test_fetch_failure_preserves_branch(self):
        self.git(self.work, "remote", "set-url", "origin", str(self.remote / "missing"))
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assert_unchanged()

    def test_custom_remote(self):
        self.git(self.work, "remote", "rename", "origin", "upstream")
        result = self.invoke("--remote", "upstream")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["remote"], "upstream")
        self.assertEqual(self.git(self.work, "rev-parse", "HEAD^"), self.latest_main)

    def test_discovers_renamed_sole_remote_and_default_branch_with_stale_local_head(
        self,
    ):
        self.git(self.work, "remote", "rename", "origin", "company")
        self.git(self.remote, "branch", "-m", "main", "trunk")
        self.git(self.remote, "symbolic-ref", "HEAD", "refs/heads/trunk")
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["remote"], "company")
        self.assertEqual(data["base_branch"], "trunk")
        self.assertEqual(self.git(self.work, "rev-parse", "HEAD^"), self.latest_main)

    def test_prefers_branch_remote_over_another_remote_and_push_remote(self):
        self.git(self.work, "remote", "rename", "origin", "company")
        self.git(self.work, "remote", "add", "fork", str(self.remote / "missing"))
        self.git(self.work, "config", "branch.feature.remote", "company")
        self.git(self.work, "config", "branch.feature.pushRemote", "fork")
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["remote"], "company")
        self.assertEqual(self.git(self.work, "rev-parse", "HEAD^"), self.latest_main)

    def test_multiple_remotes_without_branch_remote_require_override(self):
        self.git(self.work, "remote", "add", "company", str(self.remote))
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("specify --remote", result.stderr)
        self.assert_unchanged()

    def test_explicit_remote_resolves_ambiguity_and_overrides_branch_remote(self):
        self.git(self.work, "remote", "add", "company", str(self.remote))
        self.git(self.work, "config", "branch.feature.remote", "missing")
        result = self.invoke("--remote", "company")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["remote"], "company")

    def test_missing_remote_requires_override_without_rebase(self):
        self.git(self.work, "remote", "remove", "origin")
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("specify --remote", result.stderr)
        self.assert_unchanged()

    def test_local_branch_remote_is_not_silently_replaced(self):
        self.git(self.work, "config", "branch.feature.remote", ".")
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--remote", result.stderr)
        self.assert_unchanged()

    def test_unadvertised_default_branch_requires_explicit_base(self):
        self.git(self.remote, "symbolic-ref", "HEAD", "refs/heads/missing")
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("specify --base-branch", result.stderr)
        self.assert_unchanged()

    def test_explicit_base_works_without_advertised_default(self):
        self.git(self.remote, "symbolic-ref", "HEAD", "refs/heads/missing")
        result = self.invoke("--base-branch", "main")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["base_branch"], "main")
        self.assertEqual(self.git(self.work, "rev-parse", "HEAD^"), self.latest_main)

    def test_rejects_discovered_default_branch_even_when_named_trunk(self):
        self.git(self.remote, "branch", "-m", "main", "trunk")
        self.git(self.remote, "symbolic-ref", "HEAD", "refs/heads/trunk")
        self.git(self.work, "switch", "-c", "trunk")
        result = self.invoke("--branch", "trunk")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Select a PR branch", result.stderr)
        self.assert_unchanged()

    def test_gitbutler_workspace_is_rejected_before_fetch(self):
        self.git(self.work, "switch", "-c", "gitbutler/workspace")
        old_base = self.git(self.work, "rev-parse", "origin/main")
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("GitButler workspace", result.stderr)
        self.assertEqual(self.git(self.work, "rev-parse", "origin/main"), old_base)
        self.assert_unchanged()

    def test_conflict_is_preserved_and_unfinished_rebase_is_rejected(self):
        (self.work / "shared.txt").write_text("feature conflict\n")
        self.git(self.work, "add", ".")
        self.git(self.work, "commit", "-m", "Change shared on feature")
        (self.upstream / "shared.txt").write_text("main conflict\n")
        self.git(self.upstream, "add", ".")
        self.git(self.upstream, "commit", "-m", "Change shared on main")
        self.git(self.upstream, "push", "origin", "main")
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Do not push", result.stderr)
        self.assertEqual(
            self.git(self.work, "diff", "--name-only", "--diff-filter=U"), "shared.txt"
        )
        self.assertTrue((self.work / ".git/rebase-merge").is_dir())
        second = self.invoke()
        self.assertNotEqual(second.returncode, 0)
        self.assertTrue((self.work / ".git/rebase-merge").is_dir())


if __name__ == "__main__":
    unittest.main()
