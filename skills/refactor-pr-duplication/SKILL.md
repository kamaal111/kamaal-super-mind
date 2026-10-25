---
name: refactor-pr-duplication
description: Review completed task changes or a specified PR for duplicated logic across the codebase and refactor it into existing or newly extracted shared implementations.
---

# Refactor Duplication

## Continue The User's Task

An automatic review is a checkpoint within the existing request. After reviewing
or skipping, continue remaining authorized work, including PR monitoring and
fixing checks when requested. Do not finish the user's task merely because the
review is complete or ask again for permission already granted. If scope, tools,
or verification prevent the review, report the gap and continue unaffected work.
Keep uncertain changes untouched; a review limitation does not cancel the rest
of the request.

## Establish The Scope

- Use a PR the user specifies or the unique PR just created for this task.
  Otherwise review the completed task's local changes; a PR and GitHub
  authentication are not required for local review. If an explicit PR
  request is ambiguous, ask which PR rather than guessing.
- For an automatic completion review, first confirm implementation is
  complete. Skip planning, questions, approval waits, blocked work, and
  turns without task-owned code changes. If this skill already reviewed
  the final task changes, do not repeat the review.
- For local review, use the conversation and request-start baseline when
  supplied by the hook to identify this task's commits, staged and unstaged
  changes, and new files. Read their full diffs and context. A baseline
  lists candidate changes and pre-existing dirty paths; it does not prove
  ownership. Preserve unrelated work, including unrelated hunks in a
  task-owned file. Do not treat all dirty files or all branch commits as
  belonging to the task.
- Confirm the owning Git or GitButler branch before editing. In GitButler,
  use the actual task branch's history and workspace changes, not the
  integration branch's `HEAD` as a substitute for the task branch. If
  ownership cannot be established, report the unresolved scope and leave
  the ambiguous work untouched.
- For PR review, read its base, head, and complete diff. Run
  `python3 scripts/pr-context.py <pr> --commit <ref>` from the target
  repository, resolving the script relative to this skill. Use `HEAD` for
  a checked-out PR branch, or the actual virtual branch head in GitButler.
  Add `--repo OWNER/REPO` when needed to select the GitHub repository.
  It requires authenticated `gh` and local PR base/head history; it never
  fetches, switches branches, or edits files. It verifies the selected
  commit matches the published head and prints JSON with base/head SHAs,
  the merge base, changed paths, rename origins, binary flags, and hunk
  ranges on both sides. Ranges use one-based starts and line counts;
  a zero count is an insertion/deletion boundary, not a changed line.
  The scope is the committed merge-base-to-head diff, even in a dirty
  workspace; inspect local changes separately. On missing history, fetch
  through the repository workflow and rerun. Use this scope to read the
  full diff and callers; it does not detect duplication or prove ownership.

## Refactor And Verify

- Inspect the changed logic in context, then search across the codebase
  for equivalent behavior, including unchanged files and existing shared
  utilities or services. Do not limit the review to duplicated lines in
  the diff: logic can be equivalent despite different names or syntax.
- Prefer reusing an existing implementation when its contract fits.
  Otherwise extract the duplicated behavior to a central owner at the
  lowest suitable shared layer, following repository conventions. Update
  the affected callers, including matching copies outside the diff, so
  they use that owner and the redundant implementations are removed.
- Preserve behavior, validation, errors, and side effects at each caller.
  Check apparent duplicates for intentional differences; keep those
  differences explicit instead of forcing unrelated behavior into one
  abstraction. Keep the refactor tied to logic introduced or touched by
  the task or PR rather than expanding into unrelated cleanup.
- Run relevant checks for the shared implementation and affected callers,
  adding or adjusting behavioral tests when needed, then run the
  repository-required verification. Recheck the final diff for remaining
  copies and unintended behavior changes.
- Report what was reused or extracted, which callers changed, and the
  verification results. If no duplication warrants a refactor, say so.
  When committing or publishing is requested, use
  [pull-request](../pull-request/SKILL.md) to keep the PR synchronized.
  An automatic hook does not grant permission to commit, push, or publish.
