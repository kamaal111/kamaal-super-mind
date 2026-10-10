"""Offline checks for PR message synchronization."""

import importlib.util
import io
import json
import subprocess
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/pull-request/scripts/sync-pr.py'
spec = importlib.util.spec_from_file_location('sync_pr', SCRIPT)
sync_pr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync_pr)
SHA = 'a' * 40
MESSAGE = 'A precise title\n\n**Summary**\nKeep `formatting`.\n\nSigned-off-by: Test <test@example.com>\n'
TEXT = {'title': 'A precise title', 'body': '**Summary**\nKeep `formatting`.'}


def pr(**overrides):
    data = {'commits': [{'oid': SHA}], 'headRefOid': SHA,
            'title': 'Old title', 'body': 'Old body', 'url': 'https://example.test/pr/1'}
    data.update(overrides)
    return data


class SyncPrTests(unittest.TestCase):
    def invoke(self, responses, *args):
        output = io.StringIO()
        with patch.object(sync_pr, 'run', side_effect=responses) as command:
            with patch('sys.argv', [str(SCRIPT), *args]), redirect_stdout(output):
                sync_pr.main()
        return output.getvalue(), command

    def test_preview_removes_signoff_and_keeps_markdown_without_github_calls(self):
        output, command = self.invoke([SHA, MESSAGE], '--preview', '--commit', SHA)
        self.assertEqual(json.loads(output), TEXT)
        self.assertEqual(command.call_count, 2)
        self.assertEqual(command.call_args_list[0].args[0], 'git')
        self.assertEqual(command.call_args_list[1].args[0], 'git')

    def test_removes_all_signoffs_but_keeps_other_trailers(self):
        message = 'Title\n\nBody\n\nSigned-off-by: A <a@example.com>\nReviewed-by: B\nSigned-off-by: C <c@example.com>\n'
        self.assertEqual(sync_pr.pr_text(message),
                         {'title': 'Title', 'body': 'Body\n\nReviewed-by: B'})

    def test_keeps_signoff_text_inside_a_code_example(self):
        message = 'Title\n\n```text\nSigned-off-by: Example\n```\n'
        self.assertEqual(sync_pr.pr_text(message)['body'],
                         '```text\nSigned-off-by: Example\n```')

    def test_sync_sends_exact_body_file_and_verifies_result(self):
        sent = {}

        def edit(*args):
            sent['args'] = args
            sent['body'] = Path(args[-1]).read_text()
            return ''

        responses = [SHA, MESSAGE, json.dumps(pr()), edit, json.dumps(pr(**TEXT))]

        def respond(*args):
            response = responses.pop(0)
            if callable(response):
                return response(*args)
            return response

        output, command = self.invoke(respond, '1', '--commit', SHA)
        self.assertEqual(sent['args'][:-1],
                         ('gh', 'pr', 'edit', '1', '--title', TEXT['title'], '--body-file'))
        self.assertEqual(sent['body'], TEXT['body'])
        self.assertEqual(output.strip(), pr()['url'])
        self.assertEqual(command.call_count, 5)

    def test_already_synchronized_pr_is_not_edited(self):
        output, command = self.invoke(
            [SHA, MESSAGE, json.dumps(pr(**TEXT)), json.dumps(pr(**TEXT))],
            '1', '--commit', SHA)
        self.assertEqual(command.call_count, 4)
        self.assertEqual(output.strip(), pr()['url'])

    def test_rejects_multiple_commits_before_editing(self):
        with self.assertRaisesRegex(ValueError, 'exactly one commit'):
            self.invoke([SHA, MESSAGE, json.dumps(pr(commits=[{}, {}]))],
                        '1', '--commit', SHA)

    def test_rejects_unpublished_commit_before_editing(self):
        with self.assertRaisesRegex(ValueError, 'publish it first'):
            self.invoke([SHA, MESSAGE, json.dumps(pr(headRefOid='b' * 40))],
                        '1', '--commit', SHA)

    def test_reports_failed_edit_without_retrying(self):
        failure = subprocess.CalledProcessError(1, 'gh', stderr='edit denied')
        with self.assertRaises(subprocess.CalledProcessError):
            self.invoke([SHA, MESSAGE, json.dumps(pr()), failure],
                        '1', '--commit', SHA)

    def test_rejects_title_or_body_mismatch_after_editing(self):
        with self.assertRaisesRegex(ValueError, 'does not match'):
            self.invoke([SHA, MESSAGE, json.dumps(pr()), '', json.dumps(pr())],
                        '1', '--commit', SHA)


if __name__ == '__main__':
    unittest.main()
