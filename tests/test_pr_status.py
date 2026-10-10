"""Offline checks for the PR monitoring snapshot helper."""

import importlib.util
import io
import json
import subprocess
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/monitor-pr/scripts/pr-status.py'
spec = importlib.util.spec_from_file_location('pr_status', SCRIPT)
pr_status = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pr_status)
SHA = 'a' * 40
URL = 'https://example.test/pr/1'


def run(status='COMPLETED', conclusion='SUCCESS', **overrides):
    data = {'__typename': 'CheckRun', 'name': 'Tests', 'status': status,
            'conclusion': conclusion, 'detailsUrl': 'https://example.test/run/2'}
    data.update(overrides)
    return data


def context(state='SUCCESS'):
    return {'__typename': 'StatusContext', 'context': 'Build', 'state': state,
            'targetUrl': 'https://example.test/build/3'}


def pr(checks, **overrides):
    data = {'url': URL, 'state': 'OPEN', 'headRefOid': SHA,
            'statusCheckRollup': checks}
    data.update(overrides)
    return data


class PrStatusTests(unittest.TestCase):
    def test_all_successful_checks_pass_and_include_diagnostic_links(self):
        result = pr_status.snapshot(pr([run(), context()]), SHA)
        self.assertEqual(result, {
            'url': URL, 'head': SHA, 'status': 'passed', 'checks': [
                {'name': 'Tests', 'state': 'SUCCESS', 'bucket': 'pass',
                 'link': 'https://example.test/run/2'},
                {'name': 'Build', 'state': 'SUCCESS', 'bucket': 'pass',
                 'link': 'https://example.test/build/3'},
            ],
        })

    def test_neutral_and_skipped_checks_do_not_prevent_success(self):
        result = pr_status.snapshot(
            pr([run(), run(conclusion='NEUTRAL'), run(conclusion='SKIPPED')]), SHA)
        self.assertEqual(result['status'], 'passed')

    def test_no_checks_is_pending_instead_of_success(self):
        self.assertEqual(pr_status.snapshot(pr([]), SHA)['status'], 'pending')

    def test_null_rollup_is_pending_instead_of_success(self):
        self.assertEqual(pr_status.snapshot(pr(None), SHA)['status'], 'pending')

    def test_each_unfinished_check_state_keeps_successful_checks_pending(self):
        for state in ['QUEUED', 'IN_PROGRESS', 'WAITING', 'PENDING', 'REQUESTED']:
            with self.subTest(state=state):
                result = pr_status.snapshot(pr([run(), run(state, '')]), SHA)
                self.assertEqual(result['status'], 'pending')

    def test_each_failed_conclusion_takes_priority_over_pending_checks(self):
        for conclusion in ['FAILURE', 'TIMED_OUT', 'CANCELLED', 'ACTION_REQUIRED',
                           'STARTUP_FAILURE', 'STALE']:
            with self.subTest(conclusion=conclusion):
                result = pr_status.snapshot(
                    pr([run('IN_PROGRESS', ''), run(conclusion=conclusion)]), SHA)
                self.assertEqual(result['status'], 'failed')

    def test_pending_legacy_statuses_are_not_success(self):
        for state in ['EXPECTED', 'PENDING']:
            with self.subTest(state=state):
                result = pr_status.snapshot(pr([run(), context(state)]), SHA)
                self.assertEqual(result['status'], 'pending')

    def test_failed_legacy_statuses_are_failures(self):
        for state in ['ERROR', 'FAILURE']:
            with self.subTest(state=state):
                result = pr_status.snapshot(pr([run(), context(state)]), SHA)
                self.assertEqual(result['status'], 'failed')

    def test_closed_and_merged_prs_stop_instead_of_repairing_failed_checks(self):
        for state in ['CLOSED', 'MERGED']:
            with self.subTest(state=state):
                result = pr_status.snapshot(
                    pr([run(conclusion='FAILURE')], state=state), SHA)
                self.assertEqual(result['status'], 'closed')

    def test_changed_head_cannot_report_a_stale_pass(self):
        with self.assertRaisesRegex(ValueError, 'PR head changed'):
            pr_status.snapshot(pr([run()], headRefOid='b' * 40), SHA)

    def test_unknown_data_cannot_report_success(self):
        for check in [run(status='UNKNOWN'), run(conclusion='UNKNOWN'),
                      context('UNKNOWN'), run(__typename='Unknown')]:
            with self.subTest(check=check):
                with self.assertRaisesRegex(ValueError, 'Unknown'):
                    pr_status.snapshot(pr([check]), SHA)

    def test_cli_prints_one_read_only_snapshot_of_the_requested_pr(self):
        output = io.StringIO()
        response = subprocess.CompletedProcess([], 0, json.dumps(pr([run()])), '')
        with patch('sys.argv', [str(SCRIPT), '1', '--commit', SHA]), \
                patch.object(pr_status.subprocess, 'run', return_value=response) as command, \
                redirect_stdout(output):
            pr_status.main()
        self.assertEqual(json.loads(output.getvalue())['status'], 'passed')
        command.assert_called_once_with(
            ['gh', 'pr', 'view', '1', '--json', 'url,state,headRefOid,statusCheckRollup'],
            check=True, text=True, capture_output=True, timeout=60)

    def test_api_errors_propagate_without_printing_a_success_snapshot(self):
        output = io.StringIO()
        failure = subprocess.CalledProcessError(1, 'gh', stderr='access denied')
        with patch('sys.argv', [str(SCRIPT), '1', '--commit', SHA]), \
                patch.object(pr_status.subprocess, 'run', side_effect=failure), \
                redirect_stdout(output):
            with self.assertRaises(subprocess.CalledProcessError):
                pr_status.main()
        self.assertEqual(output.getvalue(), '')


if __name__ == '__main__':
    unittest.main()
