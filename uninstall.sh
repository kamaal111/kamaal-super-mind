#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

if [[ "${1:-}" == "--dry-run" ]]; then
  printf 'Would remove the %s marketplace and plugin from Codex and/or Claude Code.\n' "$MARKETPLACE_NAME"
  printf 'Would remove %s from Cursor'\''s local plugin directory.\n' "$PLUGIN_NAME"
  printf 'Would remove each skill symlink from ~/.agents/skills.\n'
  printf 'Would delete %s.\n' "$INSTALL_DIRECTORY"
  exit 0
fi

# Safe to rerun even if some or all of this was already removed.
detect_harnesses

if [[ "$have_codex" -eq 1 ]]; then
  codex plugin remove "$PLUGIN_NAME@$MARKETPLACE_NAME" || \
    printf 'Notice: Codex plugin %s was already not installed.\n' "$PLUGIN_NAME" >&2
  codex plugin marketplace remove "$MARKETPLACE_NAME" || \
    printf 'Notice: Codex marketplace %s was already not registered.\n' "$MARKETPLACE_NAME" >&2

  printf 'Kamaal Super Mind is uninstalled from Codex.\n'
fi

if [[ "$have_claude" -eq 1 ]]; then
  claude plugin uninstall "$PLUGIN_NAME@$MARKETPLACE_NAME" || \
    printf 'Notice: Claude Code plugin %s was already not installed.\n' "$PLUGIN_NAME" >&2
  claude plugin marketplace remove "$MARKETPLACE_NAME" || \
    printf 'Notice: Claude Code marketplace %s was already not registered.\n' "$MARKETPLACE_NAME" >&2

  printf 'Kamaal Super Mind is uninstalled from Claude Code.\n'
fi

if [[ "$have_cursor" -eq 1 ]]; then
  remove_symlink_if_present "$HOME/.cursor/plugins/local/$PLUGIN_NAME"

  # Matched by target path, so this works even if the checkout is already gone.
  agents_skills_dir="$HOME/.agents/skills"
  if [[ -d "$agents_skills_dir" ]]; then
    for skill_link in "$agents_skills_dir"/*; do
      [[ -L "$skill_link" ]] || continue
      case "$(readlink "$skill_link")" in
      "$INSTALL_DIRECTORY/skills/"*) rm "$skill_link" ;;
      esac
    done
  fi

  printf 'Kamaal Super Mind is uninstalled from Cursor.\n'
fi

if is_managed_checkout; then
  rm -rf "$INSTALL_DIRECTORY"
  printf 'Removed %s.\n' "$INSTALL_DIRECTORY"
elif [[ -e "$INSTALL_DIRECTORY" ]]; then
  error_not_managed "$INSTALL_DIRECTORY" "checkout"
fi
