"""Exercise hook lifecycles against real Git repositories and isolated state."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "hooks/duplication_review.py"


class DuplicationReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="duplication-hooks-")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.work = self.directory / "project with spaces"
        self.work.mkdir()
        self.env = dict(
            os.environ,
            XDG_CACHE_HOME=str(self.directory / "cache"),
            GIT_CONFIG_NOSYSTEM="1",
            GIT_CONFIG_GLOBAL=os.devnull,
            GIT_AUTHOR_NAME="Test",
            GIT_AUTHOR_EMAIL="test@example.test",
            GIT_COMMITTER_NAME="Test",
            GIT_COMMITTER_EMAIL="test@example.test",
        )
        self.env.pop("KAMAAL_SUPER_MIND_DUPLICATION_REVIEW", None)
        self.git("init", "--initial-branch=main")
        self.source = self.work / "source.py"
        self.source.write_text("value = 1\n")
        self.git("add", ".")
        self.git("commit", "-m", "Initial")

    def git(self, *args):
        return subprocess.run(
            ["git", *args],
            cwd=self.work,
            env=self.env,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def invoke(
        self, event, host="codex", session="session-1", via_config=False, **fields
    ):
        payload = {
            "hook_event_name": event,
            "session_id": session,
            "conversation_id": session,
            "cwd": str(self.work),
            "workspace_roots": [str(self.work)],
            "prompt": "Implement the feature",
            **fields,
        }
        command = [sys.executable, str(SCRIPT), host]
        environment = self.env
        if via_config:
            plugin = self.directory / "plugin with spaces 'and' $dollars"
            plugin.symlink_to(ROOT, target_is_directory=True)
            manifest = json.loads((plugin / f".{host}-plugin/plugin.json").read_text())
            configuration = json.loads((plugin / manifest["hooks"]).read_text())
            command = configuration["hooks"][event][0]["hooks"][0]["command"]
            environment = {
                **self.env,
                "PLUGIN_ROOT": str(plugin),
                "CLAUDE_PLUGIN_ROOT": str(plugin),
            }
        result = subprocess.run(
            command,
            shell=via_config,
            input=json.dumps(payload),
            env=environment,
            text=True,
            capture_output=True,
            check=True,
        )
        return json.loads(result.stdout)

    def test_many_edits_trigger_one_review_and_review_edits_do_not_recurse(self):
        self.invoke("UserPromptSubmit")
        self.source.write_text("value = 2\n")
        self.source.write_text("value = 3\n")
        review = self.invoke("Stop")
        self.source.write_text("value = 4\n")

        self.assertEqual(review["decision"], "block")
        self.assertIn("refactor-pr-duplication/SKILL.md", review["reason"])
        self.assertIn("completed", review["reason"])
        self.assertEqual(self.invoke("Stop", stop_hook_active=True), {})

    def test_new_real_request_can_trigger_another_review(self):
        self.invoke("UserPromptSubmit")
        self.source.write_text("value = 2\n")
        self.invoke("Stop")
        self.invoke("UserPromptSubmit", prompt="Implement another feature")
        self.source.write_text("value = 3\n")

        self.assertEqual(self.invoke("Stop")["decision"], "block")

    def test_synthetic_review_prompt_preserves_guard(self):
        self.invoke("UserPromptSubmit", host="claude")
        self.source.write_text("value = 2\n")
        review = self.invoke("Stop", host="claude")
        self.invoke("UserPromptSubmit", host="claude", prompt=review["reason"])
        self.source.write_text("value = 3\n")

        self.assertEqual(self.invoke("Stop", host="claude"), {})

    def test_committed_changes_trigger_review_with_clean_worktree(self):
        initial = self.git("rev-parse", "HEAD")
        self.invoke("UserPromptSubmit")
        self.source.write_text("value = 2\n")
        self.git("add", ".")
        self.git("commit", "-m", "Feature")

        review = self.invoke("Stop")

        self.assertEqual(self.git("status", "--porcelain"), "")
        self.assertIn(initial, review["reason"])

    def test_preexisting_dirty_files_alone_do_not_trigger_review(self):
        self.source.write_text("value = 2\n")
        (self.work / "existing.py").write_text("existing = True\n")
        self.invoke("UserPromptSubmit")

        self.assertEqual(self.invoke("Stop"), {})

    def test_changes_to_already_dirty_file_are_detected(self):
        self.source.write_text("value = 2\n")
        self.invoke("UserPromptSubmit")
        self.source.write_text("value = 3\n")

        review = self.invoke("Stop")

        self.assertEqual(review["decision"], "block")
        self.assertIn("source.py", review["reason"])
        self.assertEqual(self.source.read_text(), "value = 3\n")

    def test_untracked_file_changes_are_detected_without_index_changes(self):
        new_file = self.work / "new.py"
        new_file.write_text("new = 1\n")
        self.invoke("UserPromptSubmit")
        new_file.write_text("new = 2\n")

        self.assertEqual(self.invoke("Stop")["decision"], "block")
        self.assertEqual(self.git("diff", "--cached"), "")

    def test_ignored_artifacts_do_not_trigger_review(self):
        (self.work / ".gitignore").write_text("build/\n")
        self.invoke("UserPromptSubmit")
        (self.work / "build").mkdir()
        (self.work / "build/output").write_text("artifact")

        self.assertEqual(self.invoke("Stop"), {})

    def test_missing_baseline_does_not_trigger_review(self):
        self.source.write_text("value = 2\n")

        self.assertEqual(self.invoke("Stop"), {})

    def test_aborted_cursor_turn_does_not_trigger_review(self):
        self.invoke("beforeSubmitPrompt", host="cursor")
        self.source.write_text("value = 2\n")

        self.assertEqual(self.invoke("stop", host="cursor", status="aborted"), {})

    def test_cursor_followup_does_not_reset_guard_even_if_generation_changes(self):
        accepted = self.invoke("beforeSubmitPrompt", host="cursor")
        self.source.write_text("value = 2\n")
        review = self.invoke("stop", host="cursor", status="completed")
        self.invoke(
            "beforeSubmitPrompt", host="cursor", prompt=review["followup_message"]
        )
        self.source.write_text("value = 3\n")

        self.assertEqual(accepted, {"continue": True})
        self.assertIn("refactor-pr-duplication", review["followup_message"])
        self.assertEqual(self.invoke("stop", host="cursor", loop_count=1), {})

    def test_cursor_workspace_root_is_used_instead_of_user_hooks_cwd(self):
        self.invoke("beforeSubmitPrompt", host="cursor", cwd=str(self.directory))
        self.source.write_text("value = 2\n")

        result = self.invoke("stop", host="cursor", cwd=str(self.directory))

        self.assertIn("followup_message", result)

    def test_sessions_and_hosts_have_independent_baselines(self):
        self.invoke("UserPromptSubmit", session="first")
        self.source.write_text("value = 2\n")
        self.invoke("UserPromptSubmit", session="second")
        self.invoke("UserPromptSubmit", host="claude", session="first")

        self.assertEqual(self.invoke("Stop", session="first")["decision"], "block")
        self.assertEqual(self.invoke("Stop", session="second"), {})
        self.assertEqual(self.invoke("Stop", host="claude", session="first"), {})

    def test_concurrent_stop_events_request_only_one_review(self):
        self.invoke("UserPromptSubmit")
        self.source.write_text("value = 2\n")
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: self.invoke("Stop"), range(2)))

        self.assertEqual(
            sum(result.get("decision") == "block" for result in results), 1
        )

    def test_malformed_input_reports_error_and_allows_stop(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "codex"],
            input="not json",
            env=self.env,
            text=True,
            capture_output=True,
            check=True,
        )

        self.assertEqual(json.loads(result.stdout), {})
        self.assertIn("duplication review hook", result.stderr)

    def test_cursor_baseline_error_explicitly_allows_user_prompt(self):
        result = self.invoke(
            "beforeSubmitPrompt", host="cursor", workspace_roots="invalid"
        )

        self.assertEqual(result, {"continue": True})

    def test_non_repository_does_not_trigger_review(self):
        self.invoke("UserPromptSubmit", cwd=str(self.directory), workspace_roots=[])

        self.assertEqual(
            self.invoke("Stop", cwd=str(self.directory), workspace_roots=[]), {}
        )

    def test_plan_mode_does_not_trigger_review(self):
        self.invoke("UserPromptSubmit")
        self.source.write_text("value = 2\n")

        self.assertEqual(self.invoke("Stop", permission_mode="plan"), {})

    def test_staged_changes_trigger_review(self):
        self.invoke("UserPromptSubmit")
        self.source.write_text("value = 2\n")
        self.git("add", ".")

        self.assertEqual(self.invoke("Stop")["decision"], "block")
        self.assertEqual(self.git("diff"), "")

    def test_empty_repository_can_review_first_new_file(self):
        empty = self.directory / "empty"
        empty.mkdir()
        subprocess.run(
            ["git", "init", str(empty)], env=self.env, check=True, capture_output=True
        )
        self.invoke("UserPromptSubmit", cwd=str(empty))
        (empty / "first.py").write_text("first = 1\n")

        review = self.invoke("Stop", cwd=str(empty))

        self.assertEqual(review["decision"], "block")
        self.assertIn('"head": null', review["reason"])

    def test_cursor_multi_root_workspace_reviews_changed_second_repository(self):
        second = self.directory / "second"
        second.mkdir()
        subprocess.run(
            ["git", "init", str(second)], env=self.env, check=True, capture_output=True
        )
        roots = [str(self.work), str(second)]
        self.invoke("beforeSubmitPrompt", host="cursor", workspace_roots=roots)
        (second / "new.py").write_text("new = 1\n")

        review = self.invoke("stop", host="cursor", workspace_roots=roots)

        self.assertIn(str(second), review["followup_message"])
        self.assertNotIn(str(self.work), review["followup_message"])

    def test_untracked_symlink_does_not_hash_its_external_target(self):
        target = self.directory / "outside"
        target.write_text("before")
        (self.work / "link").symlink_to(target)
        self.invoke("UserPromptSubmit")
        target.write_text("after")

        self.assertEqual(self.invoke("Stop"), {})

    def test_disable_environment_prevents_review(self):
        self.env["KAMAAL_SUPER_MIND_DUPLICATION_REVIEW"] = "0"
        self.invoke("UserPromptSubmit")
        self.source.write_text("value = 2\n")

        self.assertEqual(self.invoke("Stop"), {})

    def test_failed_new_baseline_cannot_reuse_previous_request_baseline(self):
        self.invoke("UserPromptSubmit")
        self.source.write_text("value = 2\n")
        binary = shutil.which("git")
        binaries = self.directory / "bin"
        binaries.mkdir()
        wrapper = binaries / "git"
        wrapper.write_text(
            f"#!{sys.executable}\n"
            "import os, sys\n"
            "if 'diff' in sys.argv: sys.exit(1)\n"
            f"os.execv({binary!r}, [{binary!r}, *sys.argv[1:]])\n"
        )
        wrapper.chmod(0o755)
        self.env["PATH"] = f"{binaries}{os.pathsep}{self.env['PATH']}"
        state = next((self.directory / "cache/kamaal-super-mind/hooks").glob("*.json"))
        self.invoke("UserPromptSubmit")
        wrapper.unlink()

        self.assertEqual(state.read_text(), "")
        self.assertEqual(self.invoke("Stop"), {})

    def test_codex_manifest_command_runs_from_quoted_plugin_root(self):
        self.invoke("UserPromptSubmit", via_config=True)
        self.source.write_text("value = 2\n")

        self.assertEqual(self.invoke("Stop")["decision"], "block")

    def test_claude_manifest_stop_command_requests_skill_in_current_context(self):
        self.invoke("UserPromptSubmit", host="claude")
        self.source.write_text("value = 2\n")

        review = self.invoke("Stop", host="claude", via_config=True)

        self.assertEqual(review["decision"], "block")
        self.assertIn("refactor-pr-duplication/SKILL.md", review["reason"])

    def test_corrupt_state_does_not_block_completion_and_next_request_recovers(self):
        self.invoke("UserPromptSubmit")
        self.source.write_text("value = 2\n")
        state = next((self.directory / "cache/kamaal-super-mind/hooks").glob("*.json"))
        state.write_text("invalid")
        result = self.invoke("Stop")
        self.invoke("UserPromptSubmit")
        self.source.write_text("value = 3\n")

        self.assertEqual(result, {})
        self.assertEqual(self.invoke("Stop")["decision"], "block")


if __name__ == "__main__":
    unittest.main()
