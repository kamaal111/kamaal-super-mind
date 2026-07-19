# Repository Guidelines

## Documentation Synchronization

When a skill is added, renamed, or removed, update `README.md`'s **Included
Skills** list in the same change. Do not leave the published catalog stale.

The `Use Specialized Skills` list in
`skills/production-engineering/SKILL.md` documents the plugin's specialized
skills. When a skill is added, removed, renamed, or materially changes
purpose, update that list and its routing guidance in the same change. Do not
leave it stale.

## Plugin Version Refresh

When changing any plugin content, refresh the Codex plugin manifest's
cache-buster version before committing so installed local copies recognize the
update:

```bash
python3 ~/.codex/skills/.system/plugin-creator/scripts/update_plugin_cachebuster.py \
  .
```

The helper preserves the base version and replaces only the `+codex.` suffix.
This only applies to `.codex-plugin/plugin.json`. The Claude Code manifest,
`.claude-plugin/plugin.json`, and the Cursor manifest,
`.cursor-plugin/plugin.json`, omit `version` on purpose: Claude Code tracks
the git commit SHA instead, and Cursor discovers this plugin through the
installer's symlink into `~/.cursor/plugins/local`, not a versioned
marketplace listing. Leave both without a `version` field.

## Just Recipes

Use `just` from the repository root for repeatable contributor commands:

```bash
just check                # Check installer syntax and its dry-run behavior
just test                 # Run install.sh's automated test suite
just validate-marketplace # Register this checkout for manual Codex testing
```

`just check` is the required lightweight verification for installer changes
and is safe to run repeatedly. `just validate-marketplace` changes local Codex
marketplace registration; run it only when testing skill discovery in a new
Codex task. Run `just` with no recipe to list available commands.

Agents must run `just test` before claiming any task touching `install.sh`
is done, and must not report success if it fails. It runs
`tests/test_install.sh`, which drives `install.sh` against mocked
`git`/`codex`/`claude`/`cursor` binaries (see `tests/mocks/`) in a scratch
`$HOME` and `KAMAAL_SUPER_MIND_DIR`, so it exercises fresh installs, updates,
dirty/diverged checkouts, and per-harness failure fallbacks without touching
this machine's real installs or the network. Add a new `test_*` function to
`tests/test_install.sh` for any new install.sh behavior.

## Security and Configuration

Never add credentials, personal paths, tokens, or customer data. The installer
accepts `KAMAAL_SUPER_MIND_DIR` to override its destination; preserve its safe
failure behavior when that path already exists outside a Git checkout.
