#!/usr/bin/env python3
"""Read a GitHub PR's local diff scope without fetching or changing files."""

import argparse
import json
import os
import re
import subprocess
import sys

PR_FIELDS = "url,state,baseRefName,baseRefOid,headRefName,headRefOid"
HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", re.MULTILINE)


def run(*args):
    return subprocess.run(
        args,
        check=True,
        text=True,
        capture_output=True,
        timeout=60,
        env=dict(os.environ, LC_ALL="C", GIT_OPTIONAL_LOCKS="0"),
    ).stdout


def read_pr(pr, repo):
    args = ["gh", "pr", "view", pr, "--json", PR_FIELDS]
    if repo:
        args.extend(["--repo", repo])
    data = json.loads(run(*args))
    for field in ("baseRefOid", "headRefOid"):
        if not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", data[field]):
            raise ValueError(f"PR has no valid {field}.")
    return data


def local_commit(ref):
    try:
        return run(
            "git", "rev-parse", "--verify", "--end-of-options", f"{ref}^{{commit}}"
        ).strip()
    except subprocess.CalledProcessError as error:
        raise ValueError(
            f"Commit {ref!r} is unavailable locally. Fetch the required PR "
            "history using the repository workflow, then rerun."
        ) from error


def changed_files(base, head):
    options = (
        "--no-ext-diff",
        "--no-textconv",
        "--no-color",
        "--no-relative",
        "--ignore-submodules=none",
        "--find-renames",
    )
    fields = run(
        "git", "diff", *options, "--name-status", "-z", base, head, "--"
    ).split("\0")
    files = []
    index = 0
    while index < len(fields) - 1:
        status, path = fields[index : index + 2]
        index += 2
        old_path = None
        if status.startswith("R"):
            old_path = path
            path = fields[index]
            index += 1
        paths = [
            f":(top,literal){name}" for name in (old_path, path) if name is not None
        ]
        diff = run(
            "git",
            "diff",
            *options,
            "--unified=0",
            "--inter-hunk-context=0",
            base,
            head,
            "--",
            *paths,
        )
        ranges = [
            {
                "base": {"start": int(old), "count": int(old_count or 1)},
                "head": {"start": int(new), "count": int(new_count or 1)},
            }
            for old, old_count, new, new_count in HUNK.findall(diff)
        ]
        files.append(
            {
                "path": path,
                "previous_path": old_path,
                "status": status,
                "binary": any(
                    line.startswith("Binary files ") for line in diff.splitlines()
                ),
                "ranges": ranges,
            }
        )
    return files


def context(pr, commit, repo=None):
    root = run("git", "rev-parse", "--show-toplevel").strip()
    before = read_pr(pr, repo)
    head = local_commit(commit)
    if head != before["headRefOid"]:
        raise ValueError("Selected local commit differs from the published PR head.")
    base = local_commit(before["baseRefOid"])
    try:
        ancestors = run("git", "merge-base", "--all", base, head).splitlines()
    except subprocess.CalledProcessError as error:
        raise ValueError(
            "No local merge base; fetch sufficient PR history and rerun."
        ) from error
    if len(ancestors) != 1:
        raise ValueError(
            "Multiple merge bases; reconcile the PR history before review."
        )
    merge_base = ancestors[0]
    files = changed_files(merge_base, head)
    after = read_pr(pr, repo)
    if before != after:
        raise ValueError(
            "PR changed while collecting context; rerun for its new state."
        )
    if local_commit(commit) != head:
        raise ValueError("Selected local ref changed while collecting context; rerun.")
    return {
        "url": before["url"],
        "state": before["state"],
        "repository_root": root,
        "base": {"branch": before["baseRefName"], "sha": base},
        "head": {"branch": before["headRefName"], "sha": head},
        "merge_base": merge_base,
        "working_tree_dirty": bool(run("git", "status", "--porcelain")),
        "files": files,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pr", help="PR number or URL")
    parser.add_argument(
        "--commit", required=True, help="Selected local PR head ref or SHA"
    )
    parser.add_argument("--repo", help="Explicit GitHub repository (OWNER/REPO)")
    args = parser.parse_args()
    print(json.dumps(context(args.pr, args.commit, args.repo), indent=2))


if __name__ == "__main__":
    try:
        main()
    except (
        subprocess.SubprocessError,
        ValueError,
        OSError,
        KeyError,
        TypeError,
    ) as error:
        print(getattr(error, "stderr", None) or str(error), file=sys.stderr)
        sys.exit(1)
