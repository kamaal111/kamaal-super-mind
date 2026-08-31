---
name: gitbutler-session-commit
description: Commit intentional changes from the current work session into a GitButler virtual branch. Use when the user asks to commit session work, create a GitButler branch, assign changes, or prepare a reviewable GitButler commit.
---

# GitButler Session Commit

Apply `gitbutler-cli`, `git-commit-message`, and relevant testing guidance.

1. Confirm the workspace mode first with
   `../gitbutler-cli/scripts/detect-workspace-mode.sh` from this skill's
   directory. Do not run `but` or `but setup` unless it returns `gitbutler`.
   When it does, inspect
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
