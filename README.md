# Kamaal Super Mind

A personal armory of battle-tested skills for Codex, Claude Code, and Cursor,
sharpened through real Swift, TypeScript, testing, dependency-upgrade, and
GitButler work, so every agent shows up already knowing how you like things
done.

## Install

Local hooks require Git and Python 3.9 or newer on macOS or Linux. Runtime
scripts use only the Python standard library; uv is for development checks.

Copy and paste this single command into Terminal:

```bash
curl -fsSL https://raw.githubusercontent.com/kamaal111/kamaal-super-mind/main/install.sh | bash
```

The installer downloads or updates the plugin in `~/.kamaal-super-mind`, then
installs it in whichever of Codex, Claude Code, and Cursor are present on the
machine (at least one is required): it registers the marketplace for Codex and
Claude Code, and symlinks the plugin into Cursor's local plugin directory. It
also symlinks each skill into `~/.cursor/skills`, working around a
[known parity gap](https://forum.cursor.com/t/cursor-agent-cli-does-not-register-skills-from-plugins-ide-does-parity-gap/158947)
where the `cursor-agent` CLI never registers skills bundled inside a plugin,
even though the Cursor desktop app does.
Then start a new Codex task, Claude Code session, or Cursor Agent chat. The
skills are available in every project on that Mac. Invoke one explicitly when
useful, for example:

```text
Use $software-testing to add tests for this change.
```

In Claude Code, plugin skills are namespaced, so invoke them as
`/kamaal-super-mind:software-testing` or ask Claude to use the skill by name.

## Automatic Duplication Review

The plugin includes a completion hook that asks the current agent to use
`refactor-pr-duplication` after implementing your request. A skill describes
how to do the review; a hook decides when to request it. No separate reviewer
agent is created.

The review is a checkpoint within your request. After reviewing or skipping,
the agent continues remaining authorized work, including PR monitoring and
fixing checks when requested. Review limitations are reported without halting
unaffected work. Completing the review does not complete the whole request.

The hook runs when the agent finishes a response cycle, which may include
many edits, commands, and tests. It compares repository state with a baseline
captured when you submitted your request. Changed code gets one review that
searches the codebase for equivalent logic, reuses or extracts shared code
where worthwhile, and runs the required checks. Local changes work without
a PR; PR reviews retain their existing workflow. The agent skips the review
when implementation is incomplete, blocked, awaiting input, or already
reviewed. Unchanged repositories do not trigger a follow-up. You may see an
automatic follow-up message before the agent reports its review results.

In Codex, this follow-up may appear under **Blocked by hook**, followed by
“Checking whether an automatic duplication review is needed.” The label
means the hook is asking the agent to continue before finishing; it does
not mean a command was denied or user approval is needed. Codex controls
that label. The agent can still skip the review when no code changed.

The hook uses `Stop` in Codex and Claude Code and native `stop` in Cursor.
These are end-of-turn events; closing an app is not a reliable way to start
a code review. The review's own changes cannot trigger another review for
the same request. A new user request starts a new cycle. Automatic review
does not authorize commits, pushes, or publication.

- **Codex:** hooks are bundled with the plugin. Review and trust their
  definitions before use (`/hooks` in the CLI); installation alone does not
  trust them. Changed hook definitions may require another trust review.
- **Claude Code:** hooks are bundled with the plugin. Start a new session
  after installing or updating.
- **Cursor desktop and `cursor-agent`:** the installer merges native entries
  into `~/.cursor/hooks.json`, preserving other hooks and settings. It does
  not also register plugin hooks, avoiding duplicate registration and the
  CLI's plugin discovery gap. Invalid or symlinked hook configuration is
  preserved and reported as an error for manual management.

Hooks are enabled by default in local sessions. To disable this review,
launch your tool with `KAMAAL_SUPER_MIND_DUPLICATION_REVIEW=0` in its
environment, or disable its entries through the tool's hook controls.
Start a new request after enabling hooks so a baseline can be captured.
Missing baselines, hook errors, and interruptions do not force a review.
Local state stores hashes, commit IDs, and path names under
`${XDG_CACHE_HOME:-~/.cache}/kamaal-super-mind/hooks`; it stores no file
contents and can be deleted when the tools are closed.

This integration targets local desktop and CLI sessions. Hosted agents are
not covered. Codex currently requires manual/local distribution for plugins
with lifecycle hooks; they are not eligible for its public plugin directory.
See the official [Codex hooks](https://learn.chatgpt.com/docs/hooks),
[Codex plugin packaging](https://developers.openai.com/plugins/build/plugins),
[Claude Code hooks](https://code.claude.com/docs/en/hooks), and
[Cursor hooks](https://cursor.com/docs/hooks) documentation.

## Update

To receive changes pushed to GitHub, run the same command again:

```bash
curl -fsSL https://raw.githubusercontent.com/kamaal111/kamaal-super-mind/main/install.sh | bash
```

Start a new Codex task, Claude Code session, or Cursor Agent chat after
updating.

When changing a skill yourself, refresh the Codex plugin version before
committing so Codex recognizes the update:

```bash
just update-cachebuster
```

Claude Code needs no equivalent step: its `plugin.json` omits `version`, so it
tracks the git commit SHA and treats every commit as a new version.

## Uninstall

To cleanly remove Kamaal Super Mind, run:

```bash
curl -fsSL https://raw.githubusercontent.com/kamaal111/kamaal-super-mind/main/uninstall.sh | bash
```

This removes the marketplace registration and installed plugin from Codex and
Claude Code, the Cursor symlink and the `~/.cursor/skills` skill symlinks, and
the native Cursor hook entries owned by this installation, then deletes the
`~/.kamaal-super-mind` checkout. Other Cursor hooks are preserved. It is safe
to run even if only some of Codex, Claude Code, or Cursor were ever installed.

## Development

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and
[just](https://just.systems/man/en/), then run from the repository root:

```bash
uv sync --locked
just verify
```

uv creates `.venv` using the Python version in `.python-version` and the
development tools in `uv.lock`. Standalone plugin scripts and installation
do not require uv or Ruff.

`just lint` checks all Python files with Ruff, including import ordering,
explicit subprocess checks, and formatting. Use `just format` to format
Python files. `just test` runs the shell suites and discovers Python tests
with pytest. To run only the Python tests, use `uv run --locked pytest tests`.
`just check` checks installer and uninstaller syntax and dry-run behavior.
`just verify` runs
all three checks and is the same command used by CI on pushes and pull
requests. Agents must follow the verification requirements in `AGENTS.md`.

For release smoke tests, use a scratch repository and a new conversation in
Codex desktop and CLI, Claude Code, Cursor desktop, and `cursor-agent`.
Record each tested version. Request an implementation that duplicates an
existing helper: expect one review follow-up, consolidation, and verification.
Ask a question afterward: expect no review follow-up. Request another code
change: expect one new review. Trust Codex hooks before testing and confirm
the review's own edits do not produce another follow-up. Automated tests
exercise the hook commands and JSON protocols without opening live chats.

## Included Skills

- `production-engineering` — shared implementation, pure-function and immutability preferences, verification, and safety guidance
- `plan-mode` — concise, implementation-ready planning and agent handoffs
- `git-commit-message` — Conventional Commit and pull-request writing
- `reword-git-commit` — safely rewrite a commit message as a Conventional Commit from its diff
- `commit` — inspect and commit pending work with Git and GitButler routing
- `resolve-merge-conflicts` — resolve merge/rebase conflicts in place, non-destructively, for user review
- `pull-request` — single-commit PRs with titles and descriptions kept in sync
- `refactor-pr-duplication` — review completed local task changes or PR logic and consolidate duplicates into shared implementations
- `monitor-pr` — explicitly requested PR monitoring, failure fixes, and pushes until checks pass
- `dependency-upgrades` — safe dependency upgrades
- `api-integration-tests` — real endpoint and persistence coverage
- `swift-snapshot-tests` — SwiftUI snapshot test coverage for a given screen
- `gitbutler-cli` and `gitbutler-session-commit` — GitButler virtual branches and session commits
- `gitbutler-multi-agent` — GitButler coordination for parallel agent work
- `swift-best-practices` — Swift implementation
- `typescript-best-practices` — clear, type-safe TypeScript implementation
- `java-best-practices` — Java immutable data, pure transformations, optional values, sealed hierarchies, and exhaustive switches
- `software-testing` — cross-project testing discipline, including Java, Swift, and TypeScript guidance
- `backend` — secure backend-service changes in any language or framework
- `database` — secure, efficient data access and user-resource ownership scoping
- `logging` — successes, failures, and workflow milestones, with structured backend logging guidance
