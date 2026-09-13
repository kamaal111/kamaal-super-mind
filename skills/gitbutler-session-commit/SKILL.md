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
4. Reuse an applied branch that clearly matches the work, or create a concise
   task-specific virtual branch. If a matching unapplied branch cannot be
   applied without overwriting working files, create a separate branch unless
   the user authorizes a history operation.
5. Write the proposed message to a temporary file and validate it with
   the `git-commit-message` skill's `validate-message.sh` helper before any
   commit mutation.
6. With the positional-`CHANGES` interface, commit only the intended IDs using
   `scripts/commit-selected.sh <branch> <message-file> <change-id>...`. If the
   installed help shows a different interface, follow that help and preserve
   the same explicit file-or-hunk scope.
7. Inspect `but status -fv`, the stored commit message, and the resulting diff.
   Do not claim code ready to commit until relevant verification has passed,
   unless the user explicitly accepts an unverified commit.
