---
name: commit
description: Inspect and commit pending repository work, including changes made by another agent, using a precise message derived from the final diff and the user's intent. Use when the user says commit, `$commit`, `/commit`, asks to commit uncommitted changes, or provides commit-message guidance; detect GitButler workspaces and route changes to the correct virtual branch, asking for clarification when branch ownership is ambiguous.
---

# Commit Pending Work

Commit the requested work after inspecting the actual diff. Do not push,
publish, or include unrelated changes.

## Workflow

1. Read repository instructions. Inspect:
   `git status --short --branch`, `git diff`, `git diff --cached`, recent
   commits, and untracked files.

2. Detect GitButler without invoking `but`: run
   `../gitbutler-cli/scripts/detect-workspace-mode.sh` from this skill's
   directory. It returns exactly `gitbutler` or `plain-git`, and fails for an
   indeterminate repository state. Do not substitute a compound shell command
   or infer this result from another command's exit status:

   ```bash
   ../gitbutler-cli/scripts/detect-workspace-mode.sh
   ```

   A failed repository inspection, missing helper, or permission error is
   indeterminate—not evidence that GitButler is absent. Stop and resolve it
   before any `git add` or `git commit`.

   If it is absent, use plain Git. Do not run `but status`, `but setup`, or
   another setup-triggering command just to detect GitButler.

   - **Plain Git:** commit all pending work by default. If the user names
     files or a subset, commit only that scope. Stop if the scope contains
     credentials, private keys, generated secrets, or unrelated work.
   - **GitButler:** after the marker check succeeds, load `gitbutler-cli` and
     `gitbutler-session-commit`. If `but status` cannot open its database,
     request permission to write `.git` and retry before considering setup.
     Use `but branch list` to resolve the target.
     Follow an explicitly named branch or commit. Otherwise, use the latest
     real commit on the only applied branch. If multiple branches or possible
     targets remain, ask the user which one to use. Keep unassigned changes
     out unless the user clearly includes them.

3. Understand the resolved final diff. Check that it is one coherent change
   and that the tests or checks relevant to it are known. Do not rewrite or
   discard unrelated work to make a commit possible.

4. Load `git-commit-message`. Give it the final diff, the user's intent, and
   any requested wording. Use its resulting title, body, trailer, and line
   length rules.

5. Write the complete proposed message to a temporary file and run
   `git-commit-message/scripts/validate-message.sh <message-file>` before
   applying it. Every physical line must be at most 72 characters unless the
   repository documents a stricter limit. Do not assume `git commit -m` wraps
   paragraphs. Run the narrowest relevant checks when practical.

6. Commit through the repository's mode:

   - Plain Git: invoke `scripts/commit-plain-git.sh <message-file> <path>...`.
     It checks for GitButler both before staging and immediately before the
     commit. Do not call `git add` or `git commit` directly from this workflow.
   - GitButler: check `but commit --help`, then use the installed selection
     interface. With positional `CHANGES`, invoke
     `gitbutler-session-commit/scripts/commit-selected.sh <branch>
     <message-file> <change-id>...` so only the resolved IDs are committed.

   In GitButler, never use plain-Git commit, rebase, checkout, reset, or
   history-rewrite commands.

7. Verify the created commit and confirm no requested changes remain. Report
   the commit, branch, scope, message summary, and checks performed.

## Boundaries

- A commit request authorizes creating the commit only. Do not push, open a
  pull request, land a branch, delete work, or rewrite other history.
- Preserve changes you did not make unless the user explicitly includes them.
- If the target, scope, ownership, or repository state is ambiguous, ask
  before mutating anything.
- If a commit fails or conflicts, preserve the state and report the exact
  condition; do not improvise a reset.
- After an explicitly requested commit succeeds, the final response must
  contain only the exact commit title and description used.
