# Kamaal Super Mind

A personal armory of battle-tested skills for Codex, Claude Code, and Cursor,
sharpened through real Swift, TypeScript, testing, dependency-upgrade, and
GitButler work, so every agent shows up already knowing how you like things
done.

## Install

Copy and paste this single command into Terminal:

```bash
curl -fsSL https://raw.githubusercontent.com/kamaal111/kamaal-super-mind/main/install.sh | bash
```

The installer downloads or updates the plugin in `~/.kamaal-super-mind`, then
installs it in whichever of Codex, Claude Code, and Cursor are present on the
machine (at least one is required): it registers the marketplace for Codex and
Claude Code, and symlinks the plugin into Cursor's local plugin directory.
Then start a new Codex task, Claude Code session, or Cursor Agent chat. The
skills are available in every project on that Mac. Invoke one explicitly when
useful, for example:

```text
Use $swift-testing to add tests for this change.
```

In Claude Code, plugin skills are namespaced, so invoke them as
`/kamaal-super-mind:swift-testing` or ask Claude to use the skill by name.

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
python3 ~/.codex/skills/.system/plugin-creator/scripts/update_plugin_cachebuster.py \
  ~/.kamaal-super-mind
```

Claude Code needs no equivalent step: its `plugin.json` omits `version`, so it
tracks the git commit SHA and treats every commit as a new version.

## Included Skills

- `production-engineering` — shared implementation, verification, and safety guidance
- `git-commit-message` — commit and pull-request writing
- `dependency-upgrades` — safe dependency upgrades
- `api-integration-tests` — real endpoint and persistence coverage
- `gitbutler-cli` and `gitbutler-session-commit` — GitButler virtual branches and session commits
- `gitbutler-multi-agent` — GitButler coordination for parallel agent work
- `swift-best-practices` and `swift-testing` — Swift implementation and tests
- `software-testing` — cross-project testing discipline
- `typescript-backend` — secure TypeScript server changes
