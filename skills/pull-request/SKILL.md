---
name: pull-request
description: Create or update single-commit PRs whose title and description match the commit message, excluding sign-off trailers.
---

# Pull Request

- Keep one commit per PR. Use [git-commit-message](../git-commit-message/SKILL.md)
  for its message and [commit](../commit/SKILL.md) for the initial commit.
- Amend fixes into that commit and update its message from the complete diff.
  Use the repository's Git or GitButler workflow; preserve unrelated work.
- Push and open the requested PR. After every amend or reword, publish the
  updated commit (with lease protection when replacing published history).
- Run `python3 scripts/sync-pr.py <pr> --commit <commit>` from the target
  repository, resolving the script relative to this skill. It verifies one
  published commit, copies its subject/body to the PR, removes sign-off
  trailers, and checks the result. In GitButler, pass the virtual branch's
  commit, not the workspace HEAD.
- Use `--preview --commit <commit>` without a PR to print the derived title
  and body for creation or drafting. Draft-only requests do not publish.
