alias z := zed

# List available contributor recipes.
default:
    @just --list

# Check the installer without changing a Codex installation.
check:
    bash -n install.sh
    bash install.sh --dry-run

# Register this checkout as a local marketplace for manual discovery testing.
validate-marketplace:
    codex plugin marketplace add .

# Open project in zed
zed:
    zed .
