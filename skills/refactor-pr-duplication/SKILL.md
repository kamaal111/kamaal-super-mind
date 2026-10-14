---
name: refactor-pr-duplication
description: Check a just-created or user-specified PR for duplicated logic across the codebase and refactor it to reuse existing or newly extracted shared implementations.
---

# Refactor PR Duplication

- Use the PR the user specifies, or the PR just created in this session.
  If neither identifies a unique PR, ask which one. Read its base, head,
  and complete diff; confirm the local Git or GitButler branch owns the PR
  before editing. Preserve unrelated work.
- Run `python3 scripts/pr-context.py <pr> --commit <ref>` from the target
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
  the PR rather than expanding into unrelated cleanup.
- Run relevant checks for the shared implementation and affected callers,
  adding or adjusting behavioral tests when needed, then run the
  repository-required verification. Recheck the final diff for remaining
  copies and unintended behavior changes.
- Report what was reused or extracted, which callers changed, and the
  verification results. If no duplication warrants a refactor, say so.
  When committing or publishing is requested, use
  [pull-request](../pull-request/SKILL.md) to keep the PR synchronized.
