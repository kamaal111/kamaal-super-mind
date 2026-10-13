"""Offline checks for the merge-conflict inspection helper, using real repos."""

import contextlib
import importlib.util
import io
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills/resolve-merge-conflicts/scripts/conflicts.py"
)
spec = importlib.util.spec_from_file_location("conflicts", SCRIPT)
conflicts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(conflicts)

ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "T",
    "GIT_AUTHOR_EMAIL": "t@example.test",
    "GIT_COMMITTER_NAME": "T",
    "GIT_COMMITTER_EMAIL": "t@example.test",
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_SYSTEM": os.devnull,
}
USER_SUBJECT = "feat(collab): share modal (FORMS-1)"


def git(repo, *args, check=True):
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        env=ENV,
        check=check,
        capture_output=True,
        text=True,
    )


def commit(repo, name, text, message):
    (Path(repo) / name).write_text(text)
    git(repo, "add", name)
    git(repo, "commit", "-q", "-m", message)


def call(repo, *argv):
    buffer, errors = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(errors):
        code = conflicts.main(["--repo", str(repo), *argv])
    output = buffer.getvalue()
    return code, json.loads(output) if output else None


class RepoCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        git(self.repo, "init", "-q", "-b", "main")
        commit(self.repo, "a.txt", "one\ntwo\nthree\n", "base")
        commit(self.repo, "keep.txt", "keep\n", "keep")
        git(self.repo, "checkout", "-q", "-b", "feature")
        commit(self.repo, "a.txt", "one\nTWO-feature\nthree\n", USER_SUBJECT)
        git(self.repo, "checkout", "-q", "main")
        commit(self.repo, "a.txt", "one\ntwo-main\nthree\n", "main change")


class MergeTests(RepoCase):
    def setUp(self):
        super().setUp()
        git(self.repo, "checkout", "-q", "feature")
        git(self.repo, "merge", "main", check=False)

    def test_state_reports_merge_sides_and_conflicts(self):
        code, report = call(self.repo, "state")
        self.assertEqual(code, 0)
        self.assertEqual(report["operation"], "merge")
        self.assertIn("incoming", report["sides"]["theirs"])
        [entry] = report["conflicts"]
        self.assertEqual(entry["path"], "a.txt")
        self.assertEqual(entry["kind"], "both-modified")
        self.assertEqual(entry["hunks"], 1)
        self.assertFalse(entry["needs_decision"])

    def test_hunks_rebuild_base_from_stages(self):
        _, [report] = call(self.repo, "hunks")
        self.assertEqual(report["source"], "stages")
        [hunk] = report["hunks"]
        self.assertEqual(hunk["ours"], ["TWO-feature"])
        self.assertEqual(hunk["theirs"], ["two-main"])
        self.assertEqual(hunk["base"], ["two"])
        self.assertEqual(hunk["hint"], "both-changed")

    def test_hunks_unknown_path_is_an_error(self):
        code, report = call(self.repo, "hunks", "nope.txt")
        self.assertEqual(code, 2)
        self.assertIsNone(report)

    def test_intent_finds_user_commit_on_ours_side(self):
        code, report = call(self.repo, "intent", USER_SUBJECT)
        self.assertEqual(code, 0)
        [found] = report["commits"]
        self.assertTrue(found["on_ours_side"])
        self.assertFalse(found["on_theirs_side"])
        self.assertEqual(found["touches_conflicts"], ["a.txt"])
        self.assertTrue(report["history"]["a.txt"]["theirs_commits"])

    def test_intent_missing_commit_exits_three(self):
        code, report = call(self.repo, "intent", "does not exist")
        self.assertEqual(code, 3)
        self.assertFalse(report["found_user_commit"])

    def test_backup_copies_conflicted_files_into_git_dir(self):
        _, report = call(self.repo, "backup")
        self.assertEqual(report["files"], ["a.txt"])
        backup = Path(report["backup_dir"]) / "a.txt"
        self.assertIn("<<<<<<<", backup.read_text())
        self.assertIn(".git", report["backup_dir"])

    def test_verify_fails_until_markers_are_removed(self):
        _, state = call(self.repo, "state")
        sha = state["head"]["sha"]
        code, report = call(self.repo, "verify", "--head", sha)
        self.assertEqual(code, 1)
        self.assertEqual(report["markers_remaining"][0]["path"], "a.txt")
        (self.repo / "a.txt").write_text("one\nmerged\nthree\n")
        code, report = call(self.repo, "verify", "--head", sha)
        self.assertEqual(code, 0)
        self.assertEqual(report["marker_free"], ["a.txt"])

    def test_verify_flags_moved_head(self):
        (self.repo / "a.txt").write_text("one\nmerged\nthree\n")
        code, report = call(self.repo, "verify", "--head", "0" * 40)
        self.assertEqual(code, 1)
        self.assertIn("HEAD moved", report["problems"][0])

    def test_verify_flags_unterminated_hunk(self):
        (self.repo / "a.txt").write_text("<<<<<<< ours\nx\n=======\ny\n")
        code, report = call(self.repo, "verify")
        self.assertEqual(code, 1)
        self.assertTrue(report["markers_remaining"][0]["errors"])


class RebaseTests(RepoCase):
    def test_rebase_flips_sides(self):
        git(self.repo, "checkout", "-q", "feature")
        git(self.repo, "rebase", "main", check=False)
        _, report = call(self.repo, "state")
        self.assertEqual(report["operation"], "rebase")
        self.assertIn("upstream", report["sides"]["ours"])
        self.assertIn("your commit", report["sides"]["theirs"])
        self.assertEqual(report["incoming"]["subject"], USER_SUBJECT)
        _, intent = call(self.repo, "intent", USER_SUBJECT)
        [found] = intent["commits"]
        self.assertTrue(found["on_theirs_side"])
        self.assertFalse(found["on_ours_side"])


class StructuralTests(RepoCase):
    def test_delete_modify_needs_decision(self):
        git(self.repo, "checkout", "-q", "-b", "deleter", "main~1")
        git(self.repo, "rm", "-q", "a.txt")
        git(self.repo, "commit", "-q", "-m", "delete a")
        git(self.repo, "merge", "main", check=False)
        _, report = call(self.repo, "state")
        [entry] = report["conflicts"]
        self.assertEqual(entry["kind"], "deleted-by-us")
        self.assertTrue(entry["needs_decision"])
        code, verdict = call(self.repo, "verify")
        self.assertEqual(code, 0)
        self.assertEqual(verdict["needs_decision"][0]["path"], "a.txt")


class ParserTests(unittest.TestCase):
    def test_parses_diff3_and_ignores_stray_separator_lines(self):
        text = (
            "Title\n=======\n"
            "<<<<<<< HEAD\nours\n||||||| base\norig\n=======\ntheirs\n>>>>>>> topic\n"
        )
        hunks, errors = conflicts.parse_conflicts(text)
        self.assertEqual(errors, [])
        [hunk] = hunks
        self.assertEqual(hunk["start_line"], 3)
        self.assertEqual(hunk["base"], ["orig"])
        self.assertEqual(hunk["theirs_label"], "topic")

    def test_respects_longer_marker_size_and_crlf(self):
        text = "<<<<<<<<< a\r\nx\r\n=========\r\ny\r\n>>>>>>>>> b\r\n"
        hunks, errors = conflicts.parse_conflicts(text)
        self.assertEqual(errors, [])
        self.assertEqual(len(hunks), 1)

    def test_hints(self):
        self.assertEqual(conflicts.hint_for(["a"], None, ["a"]), "identical")
        self.assertEqual(conflicts.hint_for(["a"], ["a"], ["b"]), "take-theirs")
        self.assertEqual(conflicts.hint_for(["a"], ["b"], ["b"]), "take-ours")
        self.assertEqual(conflicts.hint_for(["a  b"], None, ["a b"]), "whitespace-only")
        self.assertEqual(conflicts.hint_for([], ["x"], ["y"]), "one-side-empty")


if __name__ == "__main__":
    unittest.main()
