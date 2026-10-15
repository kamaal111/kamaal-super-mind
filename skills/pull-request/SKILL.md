---
name: pull-request
description: Create or update single-commit PRs whose title and description match the commit message, excluding sign-off trailers.
---

# Pull Request

- Keep one commit per PR. Use [git-commit-message](../git-commit-message/SKILL.md)
  for its Conventional Commit message and [commit](../commit/SKILL.md) for
  the initial commit. Keep the conventional prefix in the PR title.
- Amend fixes into that commit and update its message from the complete diff.
  Use the repository's Git or GitButler workflow; preserve unrelated work.
- Before every requested PR push, including after an amend or reword, run
  `python3 scripts/rebase-before-push.py --branch <branch>`
  from the target repository, resolving the script relative to this skill.
  The script selects the branch's configured remote, or the sole remote when
  the branch has none, and queries that remote's advertised default branch.
  Use `--remote <remote>` or `--base-branch <base>` when discovery is ambiguous
  or the PR targets a different repository or branch. It never guesses names.
  The script requires a clean, checked-out PR branch, fetches the base branch,
  rebases onto its exact fetched SHA, and verifies ancestry. It prints the
  new head SHA and never pushes, stashes, or switches branches. On conflicts,
  preserve the state, resolve them, continue the rebase, then rerun the script.
  In GitButler, the script stops before mutation: use
  [gitbutler-cli](../gitbutler-cli/SKILL.md)'s base-update workflow and verify
  the virtual branch includes the latest remote default branch (or explicit
  PR base). Rerun relevant checks
  after updating. If the update fails, report the blocker and do not push.
- Push and open the requested PR. After every amend or reword, publish the
  updated commit (with lease protection when replacing published history).
- Run `python3 scripts/sync-pr.py <pr> --commit <commit>` from the target
  repository, resolving the script relative to this skill. It verifies one
  published commit, copies its subject/body to the PR, removes sign-off
  trailers, and checks the result. In GitButler, pass the virtual branch's
  commit, not the workspace HEAD.
- Use `--preview --commit <commit>` without a PR to print the derived title
  and body for creation or drafting. Draft-only requests do not publish.
