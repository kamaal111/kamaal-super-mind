---
name: git-commit-message
description: Write high-signal Git commit messages and pull-request descriptions that match the final diff. Use when a user asks to write, suggest, improve, or commit with a Git commit message; when preparing commits or squashing history; or when drafting reusable PR descriptions.
---

# Commit Message Best Practices

## Goal

Explain the meaningful product or logic change without narrating routine engineering hygiene.

## Workflow

1. Inspect the final staged and unstaged diff before writing anything.
2. Identify the actual user-facing or logic-facing change.
3. Treat tests, formatting, lockfile churn, and internal tooling as secondary unless the user asks to mention them.
4. If the message will be reused as a PR description, write body prose that stands on its own in Markdown.
5. Before drafting a commit message, read `git config --get user.name` and `git config --get user.email` from the target repository. Append a blank line followed by `Signed-off-by: <name> <email>` using exactly those configured values. Do not infer, reuse, or invent an identity; if either value is unavailable, ask the user to configure it before adding the trailer.

## Title Rules

- Keep the title factual, specific, and within the repository's line limit.
- Describe the behavior or logic changed, not the implementation tools used.
- Avoid vague titles such as `fix stuff`, `refactor code`, or `update tests`.

## Line Length

- Limit every line in the title, body, and trailers to 72 characters or fewer,
  unless the repository has a stricter documented limit.
- Before creating or rewording a commit, verify the exact proposed message with
  a line-length check. Do not rely on a commit tool to wrap it implicitly.
- After the commit is created or reworded, inspect the stored message and
  confirm no line exceeds 72 characters.

## Body Rules

- Always use a `**Summary**` section followed by a `**Solution**` section for a commit body.
- In `**Summary**`, state the task or problem being solved in concise user-facing terms.
- In `**Solution**`, explain how the commit achieves that task, focusing on the core implementation choices.
- Keep the sections concise; do not spend body space on routine test, formatting, or lint work unless it is itself the change.

Example:

```text
Retry transient upstream import failures

**Summary**
Imports no longer fail immediately when the upstream service times out.

**Solution**
The importer retries transient fetch failures with a short backoff and marks
the job failed only after the final attempt.

Signed-off-by: Humpty Dumpty <humpty.dumpty@example.com>
```

## Scope Discipline

- Match the final commit, not an earlier partial diff or intended design.
- Omit helper artifacts from the narrative unless they matter to reviewers.
- When the worktree mixes unrelated changes, separate the intended commit before drafting text.
