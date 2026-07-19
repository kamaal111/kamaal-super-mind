alias z := zed

# List available contributor recipes.
default:
    @just --list

# Check the installer without changing a Codex installation.
check:
    bash -n install.sh
    bash install.sh --dry-run

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
    ln -sfn "$(pwd)/plugins/kamaal-super-mind" ~/.cursor/plugins/local/kamaal-super-mind

# Open project in zed
zed:
    zed .
