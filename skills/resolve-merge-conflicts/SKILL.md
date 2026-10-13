---
name: resolve-merge-conflicts
description: Resolve rebase conflicts in place without destructive Git commands so the user can review them. Always rebases, never merges. Use when the user asks to resolve or fix merge conflicts, optionally naming their own commit.
---

# Resolve Merge Conflicts

Always rebase, never merge: PRs keep one commit
([pull-request](../pull-request/SKILL.md)). Edit files in place, then stop for
review. Do not stage, commit, continue, abort, skip, or push.

Helper: `python3 scripts/conflicts.py` (resolve relative to this skill, run
inside the target repo). Read-only, prints JSON.

1. Run `../gitbutler-cli/scripts/detect-workspace-mode.sh`. If `gitbutler`,
   use `gitbutler-cli` and never raw Git.
2. Run `state`. If no rebase is in progress, start one with
   `python3 ../pull-request/scripts/rebase-before-push.py --branch <branch>`.
   If a merge is in progress, stop and ask. Record `head.sha`.
3. If the user named their commit, run `intent "<subject>"`. Their commit is
   the change to preserve; the other side is work to integrate. In a rebase,
   `theirs` is the user's commit.
4. Run `backup` before editing.
5. Run `hunks`. Combine both sides' intent; if they contradict, keep the
   user's and flag it. Never drop a side silently.
6. Delete/modify and binary conflicts have no markers: report options, don't
   decide. Lockfiles: flag the regenerate command.
7. Run `verify --head <sha>` (fails while markers remain or HEAD moved), then
   relevant lint/tests.
8. Report per file how it was merged and any doubts. Tell the user to review
   with `git diff`, then `git add` and `git rebase --continue`. Don't run them.

## Never, without approval

`reset`, `restore`, `clean`, `stash`, `checkout --ours|--theirs|--`,
`commit`, `add`, `rm`, `push`, `merge`, any `--abort|--skip|--continue`.

Read a side with `git show :2:<path>` (ours), `:3:` (theirs), `:1:` (base).
On any unexpected state, stop and report.
