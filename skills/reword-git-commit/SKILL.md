---
name: reword-git-commit
description: Reword an existing Git commit from its actual diff, using the repository's commit-message conventions and safely routing plain Git or GitButler history edits. Use when the user asks to reword, rename, improve, or rewrite a commit message, optionally naming a commit or branch.
---

# Reword Git Commit

Rewrite only the selected commit's message; do not change its tree, reorder
history, push, or amend unrelated work. Construct the replacement with the
`git-commit-message` skill after inspecting the target commit and context.

## Resolve the target

1. Read repository instructions and inspect the repository root with read-only
   commands: `git status --short --branch`, `git log --oneline --decorate -n
   10`, and the relevant diff. Preserve all pre-existing uncommitted changes.
2. Parse the request for an explicit commit identifier, commit range, or
   branch. An explicit commit target takes precedence over the default. An
   explicit branch means the last commit on that branch unless the user also
   names a commit.
3. Detect GitButler without invoking `but`: check for the local branch
   `gitbutler/workspace` with
   `git show-ref --verify --quiet refs/heads/gitbutler/workspace`. If it is
   absent, use plain Git. Do not run `but status` or `but setup` just to detect
   GitButler. If the marker is present, inspect `but status` and
   `but branch list`, then use GitButler commands for every history mutation.
4. When the user supplies no extra message, default to the last commit of the
   resolved branch/current branch. In a GitButler workspace, count the virtual
   branches before choosing that default. If more than one branch exists and
   the user did not name a branch, stop and ask which branch to reword.
5. If a commit is named, use exactly that commit even when it is not the last
   commit. Verify that it resolves to the intended branch or virtual branch.
   If the target cannot be resolved unambiguously, ask for clarification.

## Construct the replacement message

1. Inspect the complete target commit, not just its old message:
   - Plain Git: `git show --stat --summary <target>` and
     `git diff <target>^ <target>`.
   - GitButler: use the corresponding `but show`/`but diff` inspection, and
     follow the installed GitButler skill if command syntax is uncertain.
2. Load and follow `git-commit-message`. Give it the target diff, relevant
   user intent, and any message supplied by the user. Preserve the repository's
   title/body format, 72-character line limit, and configured Signed-off-by
   trailer requirements. A supplied message is input to that skill, not a
   reason to skip diff analysis or validation.
3. Check the proposed message line by line before applying it. Do not alter
   author, committer, files, parents, or other commit metadata unless the
   selected tool necessarily does so and the user explicitly requested it.

## Apply the reword

### Plain Git

For `HEAD`, use an explicit message with `git commit --amend --only -m ...`
only after confirming the staged tree is exactly the target tree; avoid
including staged user work accidentally. For a non-`HEAD` commit, use an
interactive rebase scoped to that commit's parent and mark only the target as
`reword`. Preserve existing working changes by stopping if the chosen rebase
workflow requires a clean worktree and cannot safely autostash without user
direction.

Afterward, inspect `git show --format=fuller --stat <target>` (or the new
commit identifier if history was rewritten) and verify the tree and parent
relationships are unchanged. Confirm the stored message has no line over 72
characters.

### GitButler

Use `but reword <target>` for the resolved commit/branch target, following
`gitbutler-cli` for GitButler safety and the installed command's `--help` when
needed. Do not use `git commit --amend`, `git rebase`, checkout, reset, or
other plain-Git history mutations in an active GitButler workspace. Inspect
`but status`, `but show <branch-or-commit>`, and the resulting
commit message after the operation.

If GitButler reports multiple branches and no branch was named for a default
request, ask the user which branch to reword before making any change. Do not
reword every branch or choose based only on which branch appears first.

## Verify and report

- Verify the commit's tree, parent(s), and metadata that should remain stable;
  only the message should differ.
- Report the selected branch/commit, the new title, and verification result.
- Never push, open a pull request, or rewrite another commit unless the user
  explicitly names that target. If the operation fails or encounters conflicts,
  preserve the state, report the exact condition, and do not improvise a reset.
