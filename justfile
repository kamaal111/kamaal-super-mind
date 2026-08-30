alias z := zed

# List available contributor recipes.
default:
    @just --list

# Check the installer and uninstaller without changing a Codex installation.
check:
    bash -n install.sh
    bash install.sh --dry-run
    bash -n uninstall.sh
    bash uninstall.sh --dry-run

# Run install.sh's and uninstall.sh's automated test suites against mocked
# git/codex/claude/cursor.
test:
    bash tests/test_install.sh
    bash tests/test_uninstall.sh
    bash tests/test_gitbutler_helpers.sh

# Verify deterministic GitButler commit helpers against a mocked GitButler CLI.
test-gitbutler-helpers:
    bash tests/test_gitbutler_helpers.sh

# Refresh the Codex plugin manifest cache-buster after changing plugin content.
update-cachebuster:
    python3 ~/.codex/skills/.system/plugin-creator/scripts/update_plugin_cachebuster.py .

# Register this checkout as a local Codex marketplace for manual discovery testing.
validate-marketplace:
    codex plugin marketplace add .

# Register this checkout as a local Claude Code marketplace for manual discovery testing.
validate-claude-marketplace:
    claude plugin marketplace add ./
    claude plugin validate .

# Symlink this checkout into Cursor's local plugin directory for manual discovery testing.
validate-cursor-plugin:
    mkdir -p ~/.cursor/plugins/local
    ln -sfn "$(pwd)" ~/.cursor/plugins/local/kamaal-super-mind

# Open project in zed
zed:
    zed .
