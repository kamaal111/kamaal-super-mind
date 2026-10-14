"""Read PR context against real local Git history and an offline GitHub CLI."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills/refactor-pr-duplication/scripts/pr-context.py"
)


class PrContextTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="pr-context-")
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.work = root / "work"
        self.work.mkdir()
        binaries = root / "bin"
        binaries.mkdir()
        self.responses = root / "responses.json"
        self.calls = root / "calls.json"
        gh = binaries / "gh"
        gh.write_text(
            f"#!{sys.executable}\n"
            "import json, os, sys\n"
            "from pathlib import Path\n"
            "log = Path(os.environ['CONTEXT_CALLS'])\n"
            "calls = json.loads(log.read_text()) if log.exists() else []\n"
            "assert sys.argv[1:3] == ['pr', 'view'], sys.argv\n"
            "responses = json.loads(Path(os.environ['CONTEXT_RESPONSES']).read_text())\n"
            "response = responses[min(len(calls), len(responses) - 1)]\n"
            "calls.append(sys.argv[1:])\n"
            "log.write_text(json.dumps(calls))\n"
            "print(json.dumps(response))\n"
        )
        gh.chmod(0o755)
        self.env = dict(
            os.environ,
            PATH=f"{binaries}{os.pathsep}{os.environ['PATH']}",
            CONTEXT_RESPONSES=str(self.responses),
            CONTEXT_CALLS=str(self.calls),
            GIT_CONFIG_NOSYSTEM="1",
            GIT_CONFIG_GLOBAL=os.devnull,
            GIT_AUTHOR_NAME="Test",
            GIT_AUTHOR_EMAIL="test@example.test",
            GIT_COMMITTER_NAME="Test",
            GIT_COMMITTER_EMAIL="test@example.test",
        )
        self.git("init", "--initial-branch=main")
        (self.work / "shared.txt").write_text("one\ntwo\nthree\nfour\nfive\n")
        self.base = self.commit("Initial")
        self.git("switch", "-c", "feature")
        (self.work / "shared.txt").write_text(
            "one\nchanged\nthree\nfour\nchanged again\n"
        )
        self.head = self.commit("Feature")
        self.pr = {
            "url": "https://github.com/example/project/pull/1",
            "state": "OPEN",
            "baseRefName": "main",
            "baseRefOid": self.base,
            "headRefName": "feature",
            "headRefOid": self.head,
        }

    def git(self, *args):
        return subprocess.run(
            ["git", *args],
            cwd=self.work,
            env=self.env,
            check=True,
            text=True,
            capture_output=True,
        ).stdout.strip()

    def commit(self, message):
        self.git("add", ".")
        self.git("commit", "-m", message)
        return self.git("rev-parse", "HEAD")

    def invoke(self, *args, responses=None, cwd=None):
        self.responses.write_text(json.dumps(responses or [self.pr]))
        return subprocess.run(
            [sys.executable, "-B", str(SCRIPT), "1", "--commit", "feature", *args],
            cwd=cwd or self.work,
            env=self.env,
            check=False,
            text=True,
            capture_output=True,
        )

    def test_reports_separate_hunks_without_changing_dirty_worktree_or_refs(self):
        (self.work / "shared.txt").write_text("uncommitted work\n")
        (self.work / "untracked.txt").write_text("keep\n")
        status = self.git("status", "--porcelain")
        refs = self.git("show-ref")
        result = self.invoke("--repo", "example/project")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["base"], {"branch": "main", "sha": self.base})
        self.assertEqual(data["head"], {"branch": "feature", "sha": self.head})
        self.assertEqual(data["merge_base"], self.base)
        self.assertTrue(data["working_tree_dirty"])
        self.assertEqual(
            data["files"],
            [
                {
                    "path": "shared.txt",
                    "previous_path": None,
                    "status": "M",
                    "binary": False,
                    "ranges": [
                        {
                            "base": {"start": 2, "count": 1},
                            "head": {"start": 2, "count": 1},
                        },
                        {
                            "base": {"start": 5, "count": 1},
                            "head": {"start": 5, "count": 1},
                        },
                    ],
                }
            ],
        )
        self.assertEqual(self.git("show-ref"), refs)
        self.assertEqual(self.git("status", "--porcelain"), status)
        self.assertEqual((self.work / "shared.txt").read_text(), "uncommitted work\n")
        self.assertEqual((self.work / "untracked.txt").read_text(), "keep\n")
        self.assertEqual(
            json.loads(self.calls.read_text())[0][-2:], ["--repo", "example/project"]
        )

    def test_uses_merge_base_excluding_unrelated_changes_on_base_branch(self):
        self.git("switch", "main")
        (self.work / "base-only.txt").write_text("not in PR\n")
        self.pr["baseRefOid"] = self.commit("Advance base")
        self.git("switch", "feature")
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["merge_base"], self.base)
        self.assertEqual([file["path"] for file in data["files"]], ["shared.txt"])

    def test_reports_rename_add_delete_binary_and_unusual_paths_from_subdirectory(self):
        self.git("switch", "main")
        (self.work / "delete.txt").write_text("remove\n")
        (self.work / "rename.txt").write_text("preserve\n")
        self.base = self.commit("Add base files")
        self.pr["baseRefOid"] = self.base
        self.git("switch", "feature")
        self.git("rebase", "main")
        (self.work / "delete.txt").unlink()
        (self.work / "rename.txt").rename(self.work / "renamed.txt")
        (self.work / "tab\tline\n[1].txt").write_text("new\n")
        (self.work / "blob.bin").write_bytes(b"\x00binary")
        self.pr["headRefOid"] = self.commit("Various changes")
        subdir = self.work / "nested"
        subdir.mkdir()
        self.git("config", "diff.relative", "true")
        result = self.invoke(cwd=subdir)
        self.assertEqual(result.returncode, 0, result.stderr)
        files = {file["path"]: file for file in json.loads(result.stdout)["files"]}
        self.assertEqual(files["renamed.txt"]["previous_path"], "rename.txt")
        self.assertEqual(files["renamed.txt"]["status"], "R100")
        self.assertEqual(files["renamed.txt"]["ranges"], [])
        self.assertTrue(files["blob.bin"]["binary"])
        self.assertEqual(files["blob.bin"]["ranges"], [])
        self.assertEqual(files["delete.txt"]["status"], "D")
        self.assertEqual(
            files["delete.txt"]["ranges"],
            [{"base": {"start": 1, "count": 1}, "head": {"start": 0, "count": 0}}],
        )
        self.assertEqual(
            files["tab\tline\n[1].txt"]["ranges"],
            [{"base": {"start": 0, "count": 0}, "head": {"start": 1, "count": 1}}],
        )

    def test_rejects_selected_branch_that_does_not_match_published_head(self):
        self.pr["headRefOid"] = self.base
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("differs from the published PR head", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_rejects_missing_local_base_with_actionable_error(self):
        self.pr["baseRefOid"] = "a" * 40
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unavailable locally", result.stderr)
        self.assertIn("Fetch", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_rejects_histories_without_a_common_ancestor(self):
        self.git("switch", "--orphan", "unrelated")
        (self.work / "other.txt").write_text("unrelated history\n")
        self.pr["baseRefOid"] = self.commit("Unrelated root")
        self.git("switch", "feature")
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("No local merge base", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_rejects_pr_retargeted_during_collection(self):
        after = dict(self.pr, baseRefName="other")
        result = self.invoke(responses=[self.pr, after])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PR changed", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_accepts_explicit_commit_when_workspace_head_is_another_branch(self):
        self.git("switch", "-c", "gitbutler/workspace", "main")
        result = self.invoke("--commit", self.head)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["head"]["sha"], self.head)
        self.assertEqual(self.git("branch", "--show-current"), "gitbutler/workspace")

    def test_reports_empty_diff(self):
        self.pr["baseRefOid"] = self.head
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["files"], [])


if __name__ == "__main__":
    unittest.main()
