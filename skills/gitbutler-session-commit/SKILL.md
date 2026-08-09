---
name: gitbutler-session-commit
description: Commit intentional changes from the current work session into a GitButler virtual branch. Use when the user asks to commit session work, create a GitButler branch, assign changes, or prepare a reviewable GitButler commit.
---

# GitButler Session Commit

Apply `gitbutler-cli`, `git-commit-message`, and relevant testing guidance.

1. Confirm the GitButler marker first with
   `git show-ref --verify --quiet refs/heads/gitbutler/workspace`. Do not run
   `but` or `but setup` when the marker is absent. When it is present, inspect
   `but status`, `but diff`, and the Git diff to identify only the intentional
   session changes.
2. Do not stage unrelated user work. If scope is ambiguous, stop and ask which files belong in the commit.
3. Reuse an applied branch that clearly matches the work, or create a concise task-specific virtual branch.
4. Stage only intended file or hunk IDs with `but stage <id> <branch>`, inspect the staged diff, and write commit text from that final diff.
5. Commit the staged changes with `but commit <branch> --only -m "..."` rather than plain Git. Push or open a PR only when requested.
6. Do not claim code ready to commit until relevant verification has passed, unless the user explicitly accepts an unverified commit.
