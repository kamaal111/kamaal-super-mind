#!/usr/bin/env bash
# Shared by install.sh and uninstall.sh.

REPOSITORY_URL="https://github.com/kamaal111/kamaal-super-mind.git"
INSTALL_DIRECTORY="${KAMAAL_SUPER_MIND_DIR:-$HOME/.kamaal-super-mind}"
PLUGIN_NAME="kamaal-super-mind"
MARKETPLACE_NAME="kamaal-super-mind"

# Sets have_codex/have_claude/have_cursor (0 or 1). Cursor also checks its
# config dir, since cursor-agent isn't always on PATH even when installed.
detect_harnesses() {
  have_codex=0
  have_claude=0
  have_cursor=0
  command -v codex >/dev/null 2>&1 && have_codex=1
  command -v claude >/dev/null 2>&1 && have_claude=1
  { command -v cursor >/dev/null 2>&1 || [[ -d "$HOME/.cursor" ]]; } && have_cursor=1
  return 0
}

is_managed_checkout() {
  [[ -d "$INSTALL_DIRECTORY/.git" ]]
}

# Prints "$1 exists but is not a Kamaal Super Mind $2" (e.g. "checkout",
# "symlink") and exits.
error_not_managed() {
  printf 'Error: %s exists but is not a Kamaal Super Mind %s.\n' "$1" "$2" >&2
  exit 1
}

# Removes $1 if it is a symlink; errors if something else is there instead;
# does nothing if nothing is there.
remove_symlink_if_present() {
  local path="$1"
  if [[ -L "$path" ]]; then
    rm "$path"
  elif [[ -e "$path" ]]; then
    error_not_managed "$path" "symlink"
  fi
  return 0
}
