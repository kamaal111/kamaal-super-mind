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

# Open project in zed
zed:
    zed .
