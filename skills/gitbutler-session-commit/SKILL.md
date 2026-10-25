---
name: gitbutler-session-commit
description: Commit intentional changes into a GitButler virtual branch only after the mode detector returns `gitbutler`. Use for explicit GitButler branch or `but` requests, or when a parent workflow has confirmed GitButler; never for generic Git commits in an ordinary worktree.
---

# GitButler Session Commit

## Mode Gate

This skill is inapplicable until the repository is confirmed as GitButler.
Run `../gitbutler-cli/scripts/detect-workspace-mode.sh` first unless a parent
workflow has just reported `gitbutler`. Run it from inside the target
repository, resolving the path relative to this skill's own installed
directory — never `cd` into this skill's directory to run it, since the
script checks whatever directory it is run from and will silently report on
the wrong repository otherwise. If it returns `plain-git`, stop: do
not run `but`, do not create a virtual branch, and do not apply this skill's
remaining workflow. Use the ordinary Git commit workflow instead.

Apply `gitbutler-cli`, `git-commit-message`, and relevant testing guidance.

1. Confirm the workspace mode first by running
   `../gitbutler-cli/scripts/detect-workspace-mode.sh` from inside the
   target repository as described above. Do not run `but` or `but setup`
   unless it returns `gitbutler`. When it does, inspect
   `but status -fv`, `but diff`, and the Git diff to identify only the
   intentional session changes. If `but status` cannot open its database,
   request `.git` write permission and retry; do not treat that error as an
   instruction to run `but setup`.
2. Read `but commit --help` before selecting changes. Use the installed CLI's
   current interface rather than assuming `but stage` or `--only` exists.
3. Do not include unrelated user work. If scope is ambiguous, stop and ask
   which files belong in the commit.
4. Reuse an applied branch that clearly matches the work, or choose a concise
   task-specific virtual branch name. The commit helper creates a missing
   branch through `but commit --branch`; no separate branch mutation is needed.
   If a matching unapplied branch cannot be
   applied without overwriting working files, create a separate branch unless
   the user authorizes a history operation.
5. Draft a Conventional Commit message through `git-commit-message`, reviewing
   its type, scope, and breaking-change markers against the selected diff.
   Write the proposed message to a temporary file and validate it with
   the `git-commit-message` skill's `validate-message.sh` helper before any
   commit mutation.
6. With the positional-`CHANGES` interface, commit only the intended IDs using
   `scripts/commit-selected.sh <branch> <message-file> <change-id>...`. If the
   installed help shows a different interface, follow that help and preserve
   the same explicit file-or-hunk scope. Do not bypass the helper for the
   positional interface: it provides workspace backups and commit coordination.
7. Inspect `but status -fv`, the stored commit message, and the resulting diff.
   Do not claim code ready to commit until relevant verification has passed,
   unless the user explicitly accepts an unverified commit.

## Failed Commit Recovery

The helper requires Python 3. It takes a nonblocking, repository-wide lock
shared by cooperating helper invocations and refuses an existing Git index
lock before calling GitButler. It never removes an index lock. This does not
lock out GitButler's GUI or agents bypassing the helper.

Before any GitButler call, it saves dirty tracked and untracked file content,
symlink targets, file modes, and deletion state in a private directory under
`<git-common-dir>/kamaal-super-mind/recovery-*/workspace.json`. The backup path
is printed and retained on success and failure; do not commit these backups.
They may contain private working files, so keep the directory private.

On failure, if HEAD is unchanged, it restores previously present files that
are missing or whose regular-file bytes exactly match the captured HEAD
version. It preserves differing content, changed parent symlinks, and changed
HEAD states for manual recovery from the printed backup. A newer edit equal
to HEAD cannot be distinguished from a revert; inspect the recovery report.
The manifest stores regular-file bytes as hex, alongside the original path,
mode, or symlink target. Resolve remaining recovery gaps before stopping.
Never reset, discard, run setup, delete a lock, or retry a mutation blindly.

A user request to commit authorizes committing its resolved scope and creating
a missing task branch. Do not ask again merely because no branch is applied.
After a failure, report the exact error and recovery result. Investigate lock
ownership and retry only after the blocking condition is resolved.
