# Kamaal Super Mind

Personal Codex marketplace with reusable software-engineering skills for Swift,
TypeScript services, testing, dependency upgrades, GitHub Actions, GitButler,
and commit messages.

## Install

Copy and paste this single command into Terminal:

```bash
curl -fsSL https://raw.githubusercontent.com/kamaal111/kamaal-super-mind/main/install.sh | bash
```

The installer downloads or updates the plugin in `~/.kamaal-super-mind`,
registers its marketplace, and installs it in Codex. Then start a new Codex
task. The skills are available in every project on that Mac. Invoke one
explicitly when useful, for example:

```text
Use $swift-testing to add tests for this change.
```

## Update

To receive changes pushed to GitHub, run the same command again:

```bash
curl -fsSL https://raw.githubusercontent.com/kamaal111/kamaal-super-mind/main/install.sh | bash
```

Start a new Codex task after updating.

When changing a skill yourself, refresh the plugin version before committing so
Codex recognizes the update:

```bash
python3 ~/.codex/skills/.system/plugin-creator/scripts/update_plugin_cachebuster.py \
  ~/.kamaal-super-mind/plugins/kamaal-super-mind
```

## Included Skills

- `production-engineering` — shared implementation, verification, and safety guidance
- `git-commit-message` — commit and pull-request writing
- `dependency-upgrades` — safe dependency upgrades
- `api-integration-tests` — real endpoint and persistence coverage
- `github-actions-debug` — GitHub Actions failure diagnosis
- `gitbutler-cli` and `gitbutler-session-commit` — GitButler virtual branches and session commits
- `gitbutler-multi-agent` — GitButler coordination for parallel agent work
- `swift-best-practices` and `swift-testing` — Swift implementation and tests
- `software-testing` — cross-project testing discipline
- `typescript-backend` — secure TypeScript server changes
