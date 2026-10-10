---
name: monitor-pr
description: Monitor a GitHub PR's checks, fix failures, and push again until checks pass. Use only when the user explicitly asks to monitor a PR; never automatically after creating or updating one.
---

# Monitor PR

- Start only on an explicit monitoring request. Identify the requested PR,
  its repository, head branch, and full published head SHA using `gh pr view`.
  Confirm the local Git or GitButler branch owns that PR before editing.
- Run `python3 scripts/pr-status.py <pr> --commit <sha>` from the target
  repository, resolving the script relative to this skill. It prints JSON
  containing the PR URL, head SHA, check names, states, links, and aggregate
  `status`. It requires Python 3 and an authenticated GitHub CLI (`gh`).
- On `pending`, wait 30 seconds and poll again, keeping the user informed.
  No checks yet means pending, not success. On `passed`, report the PR URL
  and verified SHA, then stop monitoring. On `closed`, stop and report it.
- On `failed`, read the failed check logs (for Actions, use
  `gh run view <run-id> --log-failed`). Fix the cause within the PR's scope,
  run relevant local checks, then commit and push using the repository's
  Git or GitButler workflow. Preserve unrelated work; use
  [pull-request](../pull-request/SKILL.md) to keep single-commit PRs and their
  messages synchronized. Recheck the remote head before publishing; use
  lease protection when replacing published history. Poll the newly published
  SHA after every push; a previous commit's pass does not finish monitoring.
- Unless the user specifies limits, allow three repair-and-push attempts and
  at most 60 minutes waiting per published SHA. Stop and report the remaining
  failure or pending checks at the limit, or when permissions, external
  infrastructure, or an unexpected head change prevent progress. Do not
  weaken checks, blindly rerun failures, or overwrite another contributor's
  changes to get a pass. Monitoring does not authorize merging or closing.
