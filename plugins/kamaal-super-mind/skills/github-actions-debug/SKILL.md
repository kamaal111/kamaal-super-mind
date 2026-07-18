---
name: github-actions-debug
description: Diagnose and fix failing GitHub Actions checks with GitHub CLI and workflow logs. Use when a pull request or branch has failing Actions checks and the task includes root-cause analysis or a corrective change.
---

# GitHub Actions Log Debug

## Start

- Verify `gh` is installed and authenticated with the scopes needed to read checks and logs.
- Resolve the current branch's pull request, or use the explicitly provided pull request.
- Inspect failed checks for the pull request head SHA and fetch failed-step logs before editing code.

## Workflow

1. Identify the failed job, run URL, and smallest useful log excerpt.
2. Summarize the root cause before changing code. State ambiguity or incomplete logs explicitly.
3. Make the smallest local fix that addresses that cause and follows repository patterns.
4. Run the most relevant local command, then the repository's aggregate verification command.

## History Safety

Only amend a commit, force-push, or otherwise rewrite history when the user explicitly asks. If a single-commit branch is requested, stage only the intended files, amend intentionally, rerun affected checks if hooks changed files, and force-push with lease protection.
