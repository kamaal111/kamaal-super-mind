#!/usr/bin/env bash

set -euo pipefail

REPOSITORY_URL="https://github.com/kamaal111/kamaal-super-mind.git"
INSTALL_DIRECTORY="${KAMAAL_SUPER_MIND_DIR:-$HOME/.kamaal-super-mind}"
PLUGIN_NAME="kamaal-super-mind"
MARKETPLACE_NAME="kamaal-super-mind"

# Dry runs print the actions without requiring Git, Codex, Claude Code,
# Cursor, or changing any files.
if [[ "${1:-}" == "--dry-run" ]]; then
  printf 'Would clone or update %s at %s.\n' "$REPOSITORY_URL" "$INSTALL_DIRECTORY"
  printf 'Would register marketplace %s and install %s@%s in Codex and/or Claude Code.\n' \
    "$MARKETPLACE_NAME" "$PLUGIN_NAME" "$MARKETPLACE_NAME"
  printf 'Would link %s into Cursor'\''s local plugin directory.\n' "$PLUGIN_NAME"
  exit 0
fi

# The rest of the script needs Git to download the plugin, plus at least one
# of Codex, Claude Code, or Cursor to install it into.
if ! command -v git >/dev/null 2>&1; then
  printf 'Error: git must be installed before installing Kamaal Super Mind.\n' >&2
  exit 1
fi

have_codex=0
have_claude=0
have_cursor=0
command -v codex >/dev/null 2>&1 && have_codex=1
command -v claude >/dev/null 2>&1 && have_claude=1
{ command -v cursor >/dev/null 2>&1 || [[ -d "$HOME/.cursor" ]]; } && have_cursor=1

if [[ "$have_codex" -eq 0 && "$have_claude" -eq 0 && "$have_cursor" -eq 0 ]]; then
  printf 'Error: install Codex, Claude Code, or Cursor before installing Kamaal Super Mind.\n' >&2
  exit 1
fi

if [[ -d "$INSTALL_DIRECTORY/.git" ]]; then
  printf 'Updating Kamaal Super Mind...\n'

  # Remember the last remote revision before fetching. This lets us distinguish
  # a normal upstream history rewrite from commits someone made in this checkout.
  previous_upstream="$(git -C "$INSTALL_DIRECTORY" rev-parse --verify refs/remotes/origin/main 2>/dev/null || true)"
  git -C "$INSTALL_DIRECTORY" fetch origin main

  # This checkout is installer-managed only; nobody should hand-edit it, but
  # tooling (for example a Codex cache-buster bump) can leave uncommitted
  # changes to tracked files behind. Stash those so they are recoverable via
  # `git stash list` instead of blocking every future update or being
  # silently discarded by the reset below.
  if ! git -C "$INSTALL_DIRECTORY" diff --quiet || \
    ! git -C "$INSTALL_DIRECTORY" diff --cached --quiet; then
    printf 'Stashing local changes in %s before updating...\n' "$INSTALL_DIRECTORY"
    git -C "$INSTALL_DIRECTORY" stash push \
      -m "kamaal-super-mind installer: auto-stashed before update $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  fi

  # Do not discard commits created locally. An older remote revision that merely
  # became obsolete after a force-push is safe to replace; a newer local commit
  # is not.
  if [[ -n "$previous_upstream" ]] && \
    [[ "$previous_upstream" != "$(git -C "$INSTALL_DIRECTORY" rev-parse HEAD)" ]] && \
    git -C "$INSTALL_DIRECTORY" merge-base --is-ancestor "$previous_upstream" HEAD; then
    printf 'Error: %s has local commits; update it manually before rerunning the installer.\n' \
      "$INSTALL_DIRECTORY" >&2
    exit 1
  fi

  # Make this managed checkout exactly match the newly fetched main branch.
  # Unlike `git pull --ff-only`, this also succeeds when upstream was force-pushed.
  git -C "$INSTALL_DIRECTORY" reset --hard FETCH_HEAD
elif [[ -e "$INSTALL_DIRECTORY" ]]; then
  # Avoid treating an unrelated directory as a plugin checkout.
  printf 'Error: %s exists but is not a Kamaal Super Mind checkout.\n' \
    "$INSTALL_DIRECTORY" >&2
  exit 1
else
  # This is the first installation, so create the checkout from scratch.
  printf 'Downloading Kamaal Super Mind...\n'
  git clone "$REPOSITORY_URL" "$INSTALL_DIRECTORY"
fi

if [[ "$have_codex" -eq 1 ]]; then
  # Register the checkout as a Codex marketplace. Re-registering an existing
  # marketplace may report an error, so confirm it is already present before
  # treating that result as a real failure.
  if ! codex plugin marketplace add "$INSTALL_DIRECTORY"; then
    if ! codex plugin list | grep -Fq "Marketplace \`$MARKETPLACE_NAME\`"; then
      printf 'Error: Codex could not register the marketplace.\n' >&2
      exit 1
    fi
  fi

  # Install or update the plugin from the marketplace we just registered.
  codex plugin add "$PLUGIN_NAME@$MARKETPLACE_NAME"

  printf 'Kamaal Super Mind is installed for Codex. Start a new Codex task to use it.\n'
fi

if [[ "$have_claude" -eq 1 ]]; then
  # Register the checkout as a Claude Code marketplace. Re-registering an
  # existing marketplace may report an error, so confirm it is already
  # present before treating that result as a real failure.
  if ! claude plugin marketplace add "$INSTALL_DIRECTORY"; then
    if ! claude plugin marketplace list --json | grep -Eq "\"name\"[[:space:]]*:[[:space:]]*\"$MARKETPLACE_NAME\""; then
      printf 'Error: Claude Code could not register the marketplace.\n' >&2
      exit 1
    fi
    claude plugin marketplace update "$MARKETPLACE_NAME"
  fi

  # Install the plugin from the marketplace we just registered. If it is
  # already installed, update it to the checkout's latest commit instead.
  if ! claude plugin install "$PLUGIN_NAME@$MARKETPLACE_NAME"; then
    claude plugin update "$PLUGIN_NAME@$MARKETPLACE_NAME"
  fi

  printf 'Kamaal Super Mind is installed for Claude Code. Start a new Claude Code session to use it.\n'
fi

if [[ "$have_cursor" -eq 1 ]]; then
  # Cursor discovers plugins placed under ~/.cursor/plugins/local without any
  # marketplace registration or install command, so a symlink to the checkout
  # is enough and stays current whenever the checkout is updated.
  cursor_plugin_link="$HOME/.cursor/plugins/local/$PLUGIN_NAME"
  mkdir -p "$HOME/.cursor/plugins/local"

  if [[ -L "$cursor_plugin_link" ]]; then
    rm "$cursor_plugin_link"
  elif [[ -e "$cursor_plugin_link" ]]; then
    printf 'Error: %s exists but is not a Kamaal Super Mind symlink.\n' "$cursor_plugin_link" >&2
    exit 1
  fi

  ln -s "$INSTALL_DIRECTORY" "$cursor_plugin_link"

  printf 'Kamaal Super Mind is installed for Cursor. Start a new Cursor Agent chat to use it.\n'
fi
