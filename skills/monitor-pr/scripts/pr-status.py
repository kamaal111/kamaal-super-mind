#!/usr/bin/env python3
"""Read checks for one expected GitHub PR head; never mutate the PR."""

import argparse
import json
import subprocess
import sys


def check_status(check):
    if check['__typename'] == 'CheckRun':
        state = check['status']
        if state in {'QUEUED', 'IN_PROGRESS', 'WAITING', 'PENDING', 'REQUESTED'}:
            bucket = 'pending'
        elif state == 'COMPLETED':
            state = check['conclusion']
            if state in {'SUCCESS', 'NEUTRAL', 'SKIPPED'}:
                bucket = 'pass'
            elif state in {'FAILURE', 'TIMED_OUT', 'CANCELLED', 'ACTION_REQUIRED',
                           'STARTUP_FAILURE', 'STALE'}:
                bucket = 'fail'
            else:
                raise ValueError(f'Unknown check conclusion: {state}')
        else:
            raise ValueError(f'Unknown check status: {state}')
        name, link = check['name'], check.get('detailsUrl')
    elif check['__typename'] == 'StatusContext':
        state = check['state']
        if state in {'PENDING', 'EXPECTED'}:
            bucket = 'pending'
        elif state == 'SUCCESS':
            bucket = 'pass'
        elif state in {'ERROR', 'FAILURE'}:
            bucket = 'fail'
        else:
            raise ValueError(f'Unknown status context state: {state}')
        name, link = check['context'], check.get('targetUrl')
    else:
        raise ValueError(f"Unknown check type: {check['__typename']}")
    return {'name': name, 'state': state, 'bucket': bucket, 'link': link}


def snapshot(pr, sha):
    if pr['state'] not in {'OPEN', 'CLOSED', 'MERGED'}:
        raise ValueError(f"Unknown PR state: {pr['state']}")
    if pr['headRefOid'] != sha:
        raise ValueError('PR head changed; reconcile branch ownership before continuing.')
    checks = [check_status(check) for check in (pr['statusCheckRollup'] or [])]
    buckets = {check['bucket'] for check in checks}
    if pr['state'] != 'OPEN':
        status = 'closed'
    elif 'fail' in buckets:
        status = 'failed'
    elif not checks or 'pending' in buckets:
        status = 'pending'
    else:
        status = 'passed'
    return {'url': pr['url'], 'head': sha, 'status': status, 'checks': checks}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pr', help='PR number or URL')
    parser.add_argument('--commit', required=True, help='Full expected published head SHA')
    args = parser.parse_args()
    response = subprocess.run(
        ['gh', 'pr', 'view', args.pr, '--json',
         'url,state,headRefOid,statusCheckRollup'],
        check=True, text=True, capture_output=True, timeout=60,
    )
    print(json.dumps(snapshot(json.loads(response.stdout), args.commit), indent=2))


if __name__ == '__main__':
    try:
        main()
    except (subprocess.SubprocessError, ValueError, OSError, KeyError, TypeError) as error:
        print(getattr(error, 'stderr', None) or str(error), file=sys.stderr)
        sys.exit(1)
