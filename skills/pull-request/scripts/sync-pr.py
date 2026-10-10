#!/usr/bin/env python3
"""Synchronize an existing GitHub PR with its single published commit."""

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def run(*args):
    return subprocess.run(
        args, check=True, text=True, capture_output=True
    ).stdout


def pr_text(message):
    title, _, body = message.partition('\n')
    lines = body.splitlines()
    # Only remove sign-offs in the final trailer block, not prose or examples.
    end = len(lines)
    while end and not lines[end - 1].strip():
        end -= 1
    start = end
    while start and re.match(r'^[A-Za-z0-9-]+:\s+\S', lines[start - 1]):
        start -= 1
    if start < end and (start == 0 or not lines[start - 1].strip()):
        lines[start:end] = [
            line for line in lines[start:end]
            if not re.match(r'^Signed-off-by:', line, re.IGNORECASE)
        ]
    return {'title': title, 'body': '\n'.join(lines).strip('\n')}


def read_pr(pr):
    return json.loads(run(
        'gh', 'pr', 'view', pr, '--json', 'commits,headRefOid,title,body,url'
    ))


def require_head(pr, sha):
    if len(pr['commits']) != 1:
        raise ValueError('PR must contain exactly one commit.')
    if pr['headRefOid'] != sha:
        raise ValueError('PR head differs from the selected commit; publish it first.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pr', nargs='?', help='PR number or URL')
    parser.add_argument('--commit', required=True, help='Exact intended commit/ref')
    parser.add_argument('--preview', action='store_true', help='Print JSON without editing')
    args = parser.parse_args()
    if not args.preview and not args.pr:
        parser.error('a PR is required unless --preview is used')
    sha = run('git', 'rev-parse', '--verify', f'{args.commit}^{{commit}}').strip()
    text = pr_text(run('git', 'show', '-s', '--format=%B', sha))
    if args.preview:
        print(json.dumps(text, ensure_ascii=False, indent=2))
        return
    pr = read_pr(args.pr)
    require_head(pr, sha)
    if any(pr[key] != text[key] for key in text):
        with tempfile.TemporaryDirectory(prefix='sync-pr-') as directory:
            body_file = Path(directory) / 'body.md'
            body_file.write_text(text['body'], encoding='utf-8')
            run('gh', 'pr', 'edit', args.pr, '--title', text['title'],
                '--body-file', str(body_file))
    updated = read_pr(args.pr)
    require_head(updated, sha)
    if any(updated[key] != text[key] for key in text):
        raise ValueError('PR title or body does not match the commit after editing.')
    print(updated['url'])


if __name__ == '__main__':
    try:
        main()
    except (subprocess.CalledProcessError, ValueError, OSError) as error:
        print(getattr(error, 'stderr', None) or str(error), file=sys.stderr)
        sys.exit(1)
