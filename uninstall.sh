#!/usr/bin/env bash

set -euo pipefail

SCRIPT_SOURCE="${BASH_SOURCE[0]:-}"
if [[ "$SCRIPT_SOURCE" == */* ]]; then
  SCRIPT_DIR="${SCRIPT_SOURCE%/*}"
else
  SCRIPT_DIR="."
fi
if [[ -n "$SCRIPT_SOURCE" ]] && [[ -f "$SCRIPT_DIR/lib/common.sh" ]]; then
  # shellcheck source=lib/common.sh
  source "$SCRIPT_DIR/lib/common.sh"
else
  # `curl ... | bash` has no script path, so fetch the shared library
  # explicitly instead of relying on BASH_SOURCE being set by the caller.
  BOOTSTRAP_LIBRARY="$(mktemp "${TMPDIR:-/tmp}/kamaal-super-mind-common.XXXXXX")"
  trap 'rm -f "$BOOTSTRAP_LIBRARY"' EXIT
  curl --fail --silent --show-error --location \
    "https://raw.githubusercontent.com/kamaal111/kamaal-super-mind/main/lib/common.sh" >"$BOOTSTRAP_LIBRARY"
  # shellcheck source=/dev/null
  source "$BOOTSTRAP_LIBRARY"
fi

if [[ "${1:-}" == "--dry-run" ]]; then
  printf 'Would remove the %s marketplace and plugin from Codex and/or Claude Code.\n' "$MARKETPLACE_NAME"
  printf 'Would remove %s from Cursor'\''s local plugin directory.\n' "$PLUGIN_NAME"
  printf 'Would remove each skill symlink from ~/.cursor/skills.\n'
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
  # ~/.agents/skills is retained here solely to remove legacy links created
  # before the workaround moved to Cursor's dedicated skill directory.
  for skills_dir in "$HOME/.cursor/skills" "$HOME/.agents/skills"; do
    if [[ -d "$skills_dir" ]]; then
      for skill_link in "$skills_dir"/*; do
        [[ -L "$skill_link" ]] || continue
        case "$(readlink "$skill_link")" in
        "$INSTALL_DIRECTORY/skills/"*) rm "$skill_link" ;;
        esac
      done
    fi
  done

  printf 'Kamaal Super Mind is uninstalled from Cursor.\n'
fi

if is_managed_checkout; then
  rm -rf "$INSTALL_DIRECTORY"
  printf 'Removed %s.\n' "$INSTALL_DIRECTORY"
elif [[ -e "$INSTALL_DIRECTORY" ]]; then
  error_not_managed "$INSTALL_DIRECTORY" "checkout"
fi
