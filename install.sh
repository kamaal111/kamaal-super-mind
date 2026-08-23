#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

if [[ "${1:-}" == "--dry-run" ]]; then
  printf 'Would clone or update %s at %s.\n' "$REPOSITORY_URL" "$INSTALL_DIRECTORY"
  printf 'Would register marketplace %s and install %s@%s in Codex and/or Claude Code.\n' \
    "$MARKETPLACE_NAME" "$PLUGIN_NAME" "$MARKETPLACE_NAME"
  printf 'Would link %s into Cursor'\''s local plugin directory.\n' "$PLUGIN_NAME"
  printf 'Would link each skill into ~/.agents/skills as a cursor-agent CLI workaround.\n'
  exit 0
fi

if ! command -v git >/dev/null 2>&1; then
  printf 'Error: git must be installed before installing Kamaal Super Mind.\n' >&2
  exit 1
fi

detect_harnesses

if [[ "$have_codex" -eq 0 && "$have_claude" -eq 0 && "$have_cursor" -eq 0 ]]; then
  printf 'Error: install Codex, Claude Code, or Cursor before installing Kamaal Super Mind.\n' >&2
  exit 1
fi

if is_managed_checkout; then
  printf 'Updating Kamaal Super Mind...\n'

  # Distinguishes an upstream force-push (safe to replace) from local commits.
  previous_upstream="$(git -C "$INSTALL_DIRECTORY" rev-parse --verify refs/remotes/origin/main 2>/dev/null || true)"
  git -C "$INSTALL_DIRECTORY" fetch origin main

  # Stash rather than discard, in case tooling left uncommitted changes here.
  if ! git -C "$INSTALL_DIRECTORY" diff --quiet || \
    ! git -C "$INSTALL_DIRECTORY" diff --cached --quiet; then
    printf 'Stashing local changes in %s before updating...\n' "$INSTALL_DIRECTORY"
    git -C "$INSTALL_DIRECTORY" stash push \
      -m "kamaal-super-mind installer: auto-stashed before update $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  fi

  # A newer local commit must not be discarded; an obsolete force-pushed one may be.
  if [[ -n "$previous_upstream" ]] && \
    [[ "$previous_upstream" != "$(git -C "$INSTALL_DIRECTORY" rev-parse HEAD)" ]] && \
    git -C "$INSTALL_DIRECTORY" merge-base --is-ancestor "$previous_upstream" HEAD; then
    printf 'Error: %s has local commits; update it manually before rerunning the installer.\n' \
      "$INSTALL_DIRECTORY" >&2
    exit 1
  fi

  # Unlike `git pull --ff-only`, this also succeeds after an upstream force-push.
  git -C "$INSTALL_DIRECTORY" reset --hard FETCH_HEAD
elif [[ -e "$INSTALL_DIRECTORY" ]]; then
  error_not_managed "$INSTALL_DIRECTORY" "checkout"
else
  printf 'Downloading Kamaal Super Mind...\n'
  git clone "$REPOSITORY_URL" "$INSTALL_DIRECTORY"
fi

if [[ "$have_codex" -eq 1 ]]; then
  # Re-registering an existing marketplace may error, so check plugin list
  # before treating that as a real failure.
  if ! codex plugin marketplace add "$INSTALL_DIRECTORY"; then
    if ! codex plugin list | grep -Fq "Marketplace \`$MARKETPLACE_NAME\`"; then
      printf 'Error: Codex could not register the marketplace.\n' >&2
      exit 1
    fi
  fi

  codex plugin add "$PLUGIN_NAME@$MARKETPLACE_NAME"

  printf 'Kamaal Super Mind is installed for Codex. Start a new Codex task to use it.\n'
fi

if [[ "$have_claude" -eq 1 ]]; then
  # Re-registering an existing marketplace may error, so check marketplace
  # list before treating that as a real failure.
  if ! claude plugin marketplace add "$INSTALL_DIRECTORY"; then
    if ! claude plugin marketplace list --json | grep -Eq "\"name\"[[:space:]]*:[[:space:]]*\"$MARKETPLACE_NAME\""; then
      printf 'Error: Claude Code could not register the marketplace.\n' >&2
      exit 1
    fi
    claude plugin marketplace update "$MARKETPLACE_NAME"
  fi

  if ! claude plugin install "$PLUGIN_NAME@$MARKETPLACE_NAME"; then
    claude plugin update "$PLUGIN_NAME@$MARKETPLACE_NAME"
  fi

  printf 'Kamaal Super Mind is installed for Claude Code. Start a new Claude Code session to use it.\n'
fi

if [[ "$have_cursor" -eq 1 ]]; then
  # Cursor discovers plugins under ~/.cursor/plugins/local with no
  # marketplace/install step, so a symlink to the checkout is enough.
  cursor_plugin_link="$HOME/.cursor/plugins/local/$PLUGIN_NAME"
  mkdir -p "$HOME/.cursor/plugins/local"
  remove_symlink_if_present "$cursor_plugin_link"
  ln -s "$INSTALL_DIRECTORY" "$cursor_plugin_link"

  # Workaround: cursor-agent CLI doesn't register plugin-bundled skills, so
  # also symlink each skill into ~/.agents/skills directly.
  # https://forum.cursor.com/t/cursor-agent-cli-does-not-register-skills-from-plugins-ide-does-parity-gap/158947
  agents_skills_dir="$HOME/.agents/skills"
  mkdir -p "$agents_skills_dir"

  for skill_dir in "$INSTALL_DIRECTORY"/skills/*/; do
    [[ -f "${skill_dir}SKILL.md" ]] || continue

    skill_name="$(basename "$skill_dir")"
    skill_link="$agents_skills_dir/$skill_name"
    remove_symlink_if_present "$skill_link"
    ln -s "${skill_dir%/}" "$skill_link"
  done

  printf 'Kamaal Super Mind is installed for Cursor. Start a new Cursor Agent chat to use it.\n'
fi
