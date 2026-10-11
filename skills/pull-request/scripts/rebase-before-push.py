#!/usr/bin/env python3
"""Rebase a clean PR branch onto the remote's freshly fetched default branch."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

DETECTOR = (
    Path(__file__).resolve().parents[2]
    / "gitbutler-cli/scripts/detect-workspace-mode.sh"
)


def run(*args):
    return subprocess.run(
        args,
        check=True,
        text=True,
        capture_output=True,
        env=dict(os.environ, GIT_TERMINAL_PROMPT="0"),
    ).stdout.strip()


def read_config(key):
    try:
        return run("git", "config", "--get", key)
    except subprocess.CalledProcessError as error:
        if error.returncode != 1:
            raise
        return None


def select_remote(branch, remote):
    remotes = run("git", "remote").splitlines()
    if remote is None:
        remote = read_config(f"branch.{branch}.remote")
    if remote is None:
        if len(remotes) != 1:
            raise ValueError("Remote is ambiguous or missing; specify --remote.")
        remote = remotes[0]
    if not remote or remote.startswith("-") or remote not in remotes:
        raise ValueError("Select a configured Git remote with --remote.")
    return remote


def discover_default_branch(remote):
    advertised = run("git", "ls-remote", "--symref", "--", remote, "HEAD")
    targets = []
    for line in advertised.splitlines():
        target, separator, ref = line.partition("\t")
        if separator and ref == "HEAD" and target.startswith("ref: refs/heads/"):
            targets.append(target.removeprefix("ref: refs/heads/"))
    if len(targets) != 1:
        raise ValueError(
            "Remote does not advertise a default branch; specify --base-branch."
        )
    return targets[0]


def select_base(remote, base_branch):
    if base_branch is None:
        base_branch = discover_default_branch(remote)
    run("git", "check-ref-format", f"refs/heads/{base_branch}")
    return base_branch


def require_plain_git():
    mode = run(str(DETECTOR))
    if mode == "gitbutler":
        raise ValueError(
            "GitButler workspace: use its base-update workflow; "
            "raw Git rebase is disabled."
        )
    if mode != "plain-git":
        raise ValueError("Unable to determine repository mode.")


def require_clean_worktree(message):
    if run("git", "status", "--porcelain", "--untracked-files=all"):
        raise ValueError(message)


def require_no_pending_operation():
    operations = (
        "rebase-merge",
        "rebase-apply",
        "MERGE_HEAD",
        "CHERRY_PICK_HEAD",
        "REVERT_HEAD",
        "sequencer",
        "BISECT_LOG",
    )
    for operation in operations:
        path = Path(run("git", "rev-parse", "--git-path", operation))
        if path.exists():
            raise ValueError(
                "An unfinished Git operation exists; finish it before rebasing."
            )


def validate_starting_state(branch):
    require_plain_git()
    run("git", "check-ref-format", "--branch", branch)
    if run("git", "branch", "--show-current") != branch:
        raise ValueError(
            "The requested PR branch must already be checked out; "
            "detached HEAD is unsupported."
        )
    require_no_pending_operation()
    require_clean_worktree(
        "Working tree must be clean, including untracked files; "
        "no automatic stash is performed."
    )


def fetch_base(remote, base_branch):
    base_ref = f"refs/remotes/{remote}/{base_branch}"
    run("git", "check-ref-format", base_ref)
    run(
        "git",
        "fetch",
        "--no-tags",
        "--",
        remote,
        f"refs/heads/{base_branch}:{base_ref}",
    )
    return run("git", "rev-parse", "--verify", f"{base_ref}^{{commit}}")


def validate_state_after_fetch(branch):
    mode = run(str(DETECTOR))
    current_branch = run("git", "branch", "--show-current")
    if mode != "plain-git" or current_branch != branch:
        raise ValueError(
            "Repository mode or branch changed during fetch; rebase stopped."
        )
    require_clean_worktree("Working tree changed during fetch; rebase stopped.")


def perform_rebase(base):
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_EDITOR="true")
    result = subprocess.run(
        [
            "git",
            "-c",
            "rebase.autoStash=false",
            "-c",
            "rebase.updateRefs=false",
            "rebase",
            "--merge",
            "--no-autosquash",
            "--no-rebase-merges",
            "--no-autostash",
            "--no-fork-point",
            base,
        ],
        check=False,
        text=True,
        capture_output=True,
        env=env,
    )
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise ValueError(
            f"{detail}\nRebase failed. Preserve the state, resolve conflicts "
            "and continue the rebase, or explicitly abort it. Do not push."
        )


def verify_rebase(branch, base):
    if run("git", "branch", "--show-current") != branch:
        raise ValueError("Branch changed during rebase; do not push.")
    run("git", "merge-base", "--is-ancestor", base, "HEAD")
    require_clean_worktree(
        "Working tree is dirty after rebase; inspect the changes before pushing."
    )
    return run("git", "rev-parse", "HEAD")


def rebase(branch, remote=None, base_branch=None):
    validate_starting_state(branch)
    remote = select_remote(branch, remote)
    base_branch = select_base(remote, base_branch)
    if branch in (base_branch, "gitbutler/workspace"):
        raise ValueError("Select a PR branch, not the base or workspace branch.")
    base = fetch_base(remote, base_branch)
    validate_state_after_fetch(branch)
    perform_rebase(base)
    head = verify_rebase(branch, base)
    return {
        "branch": branch,
        "base": base,
        "head": head,
        "remote": remote,
        "base_branch": base_branch,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--branch",
        required=True,
        help="Exact checked-out PR branch name",
    )
    parser.add_argument(
        "--remote",
        help="Override the branch remote or sole configured remote",
    )
    parser.add_argument(
        "--base-branch",
        help="Override the remote's advertised default branch",
    )
    args = parser.parse_args()
    print(json.dumps(rebase(args.branch, args.remote, args.base_branch)))


if __name__ == "__main__":
    try:
        main()
    except (subprocess.CalledProcessError, ValueError, OSError) as error:
        print(getattr(error, "stderr", None) or str(error), file=sys.stderr)
        sys.exit(1)
