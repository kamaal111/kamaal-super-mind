# Repository Guidelines

## Documentation Synchronization

When a skill is added, renamed, or removed, update `README.md`'s **Included
Skills** list in the same change. Do not leave the published catalog stale.

The `Use Specialized Skills` list in
`plugins/kamaal-super-mind/skills/production-engineering/SKILL.md` documents
the plugin's specialized skills. When a skill is added, removed, renamed, or
materially changes purpose, update that list and its routing guidance in the
same change. Do not leave it stale.

## Plugin Version Refresh

When changing any plugin content, refresh the plugin manifest's Codex
cache-buster version before committing so installed local copies recognize the
update:

```bash
python3 ~/.codex/skills/.system/plugin-creator/scripts/update_plugin_cachebuster.py \
  plugins/kamaal-super-mind
```

The helper preserves the base version and replaces only the `+codex.` suffix.

## Just Recipes

Use `just` from the repository root for repeatable contributor commands:

```bash
just check                # Check installer syntax and its dry-run behavior
just validate-marketplace # Register this checkout for manual Codex testing
```

`just check` is the required lightweight verification for installer changes
and is safe to run repeatedly. `just validate-marketplace` changes local Codex
marketplace registration; run it only when testing skill discovery in a new
Codex task. Run `just` with no recipe to list available commands.

## Security and Configuration

Never add credentials, personal paths, tokens, or customer data. The installer
accepts `KAMAAL_SUPER_MIND_DIR` to override its destination; preserve its safe
failure behavior when that path already exists outside a Git checkout.
