---
name: commit
description: Inspect and commit pending repository work, including changes made by another agent, using a precise message derived from the final diff and the user's intent. Use when the user says commit, `$commit`, `/commit`, asks to commit uncommitted changes, or provides commit-message guidance; detect GitButler workspaces and route changes to the correct virtual branch, asking for clarification when branch ownership is ambiguous.
---

# Commit Pending Work

Commit the repository's pending work after understanding the final diff. This
skill is an execution workflow, not a substitute for implementation: it must
inspect the worktree even when another agent or the user wrote every change.

## 1. Establish scope and repository mode

1. Read repository instructions (`AGENTS.md` and equivalent files) before
   mutating anything.
2. Inspect the current directory and repository state with read-only commands:
   `git status --short --branch`, `git diff`, `git diff --cached`, and the
   relevant recent commit messages. Include untracked files in the review.
3. Detect GitButler before choosing a mutation command. Run
   `but status --format=agent` and, when it succeeds as a GitButler workspace,
   also inspect `but diff` and `but branch list`. Do not use plain Git commit
   mutations in an active GitButler workspace.
4. Treat the user's request as authorization to create a commit, but do not
   infer authorization to push, open a PR, land a branch, rewrite history, or
   delete work. A request to commit never implies a request to push.

## 2. Resolve the commit target

For plain Git:

- By default, commit all pending tracked and untracked work in the repository,
  because “commit” in this skill means the current uncommitted work unless the
  user narrows the scope.
- If the user names files, a feature, or a subset, include only that scope and
  leave the rest untouched.
- Never silently include obvious credentials, private keys, generated secrets,
  or unrelated user data. Stop and report the exact path if such a file is in
  the requested scope.

For GitButler:

- Before taking any GitButler action, load and follow the existing
  `gitbutler-cli` skill. Use `gitbutler-session-commit` for the commit flow
  and its integration with `git-commit-message`. Those skills are the source
  of truth for `but` commands, staging, branch ownership, and recovery. Do not
  recreate or override their procedures here.
- Identify a virtual branch from the user's wording, a clearly matching
  applied branch, or an existing branch whose purpose unambiguously matches
  the diff.
- Treat unassigned changes and changes assigned to another branch as
  user-owned until the target is clear. If more than one branch fits, or no
  branch fits, ask which virtual branch should receive the changes.
- Reuse a clearly matching branch. Otherwise create a concise task-specific
  virtual branch only when the user's intent clearly identifies the task.
- After the target is resolved, hand control to those specialized skills for
  branch creation/reuse, file or hunk staging, staged-diff inspection, and
  committing. Do not switch branches or use plain Git commit mutations in an
  active GitButler workspace.

## 3. Understand the final diff

Read enough source, tests, configuration, and nearby documentation to explain
what the pending code actually does. Do not rely on the conversation or on
which agent authored it. Check for:

- the primary behavior or contract change;
- affected boundaries, error handling, and compatibility impact;
- tests or verification that materially support the change;
- unrelated, partial, or conflicting work mixed into the requested scope.

If the requested scope contains unrelated changes that cannot form one
coherent commit, ask whether to split them or commit them together. Do not
rewrite or discard them to make the commit easier.

## 4. Delegate message construction

Load and follow the existing `git-commit-message` skill. Give it the final
staged diff, the relevant user intent, and any requested wording; use its
result as the commit message. Do not duplicate that skill's title, body,
trailer, identity, or line-length rules here. If the user supplies an exact
message, pass it to `git-commit-message` for handling alongside the final
diff.

## 5. Verify and commit

1. Run the narrowest relevant checks when practical. Do not invent a broad
   test suite for an unfamiliar repository. If checks are unavailable,
   expensive, or the user explicitly asks for an immediate commit, proceed
   and report that verification was skipped.
2. Reinspect the exact staged diff and status immediately before committing.
3. For plain Git, stage the requested scope (use `git add -A` only when the
   resolved scope is the whole worktree), then run `git commit` with the
   constructed message. Include untracked files intentionally; do not use
   `git commit -am` as a substitute.
4. For GitButler, follow `gitbutler-session-commit` and commit through `but`
   using only the resolved branch and selected change IDs.
5. Inspect the created commit (`git show --stat --oneline HEAD` for plain Git,
   or the corresponding `but show` output) and confirm no requested changes
   remain uncommitted. Report the commit identifier, branch, scope, message
   summary, and verification result.

After the user has explicitly requested a commit, do not pause to ask for
approval before completing the authorized commit workflow. Once a commit is
successfully created, the final response must contain only the exact commit
title and description used for that commit. Do not append the commit hash,
branch, verification details, or a request for further approval to that final
response.

Never push or publish automatically. Push only when the user explicitly asks
for a push in the current request, and confirm the intended remote/branch when
the request does not identify them. If there are no eligible pending changes,
report that no commit was created.
