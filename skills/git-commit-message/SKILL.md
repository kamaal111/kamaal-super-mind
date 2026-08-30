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

- The 72-character rule is a hard maximum, not a target: every physical line
  in the title, body, and trailers must contain 72 characters or fewer, unless
  the repository has a stricter documented limit.
- Wrap prose manually before creating or rewording the commit. `git commit -m`
  does not wrap long paragraphs for you.
- Validate the exact proposed message line by line before applying it, then
  inspect the stored message afterward and confirm no line exceeds 72
  characters. Treat any overlong line as a failed check that must be fixed
  before the commit is reported as complete.
- Use `scripts/validate-message.sh <message-file>` for both checks. It reports
  every overlong line and exits nonzero, avoiding manual character counting.

## Body Rules

- Always use a `**Summary**` section followed by a `**Changes**` section for a commit body.
- In `**Summary**`, state the user-facing outcome or motivation in concise terms.
- In `**Changes**`, describe the meaningful behavior, affected boundaries, and
  implementation decisions—not a file-by-file recap.
- Include the details needed to assess correctness: changed contracts,
  validation or error behavior, data flow, compatibility impact, and deliberate
  tradeoffs when relevant.
- Be specific: name the primary component or workflow and explain what it now
  does differently. Aim for one to three concise paragraphs or bullets.
- When a public interface, schema, configuration, or command contract changes,
  include a compact code example when it makes the new behavior clearer. Show
  only the changed shape and state why that shape is needed.
- Do not mention routine tests, formatting, lint work, or lockfile updates
  unless they are the purpose of the commit or reveal an important constraint.

Example:

```text
Retry transient upstream import failures

**Summary**
Imports no longer fail immediately when the upstream service times out.

**Changes**
The importer retries transient fetch failures with a short backoff and marks
the job failed only after the final attempt.

Signed-off-by: Humpty Dumpty <humpty.dumpty@example.com>
```

Interface-change example:

````text
Add a per-request timeout option

**Summary**
Callers can override the client timeout for unusually slow operations.

**Changes**
Accept `timeoutMs` on individual requests, which overrides the client default
without changing existing callers.

```ts
client.request({ path: "/reports", timeoutMs: 30_000 });
```

The per-request option keeps the default conservative while allowing report
generation to wait longer.

Signed-off-by: Humpty Dumpty <humpty.dumpty@example.com>
````

## Scope Discipline

- Match the final commit, not an earlier partial diff or intended design.
- Omit helper artifacts from the narrative unless they matter to reviewers.
- When the worktree mixes unrelated changes, separate the intended commit before drafting text.
