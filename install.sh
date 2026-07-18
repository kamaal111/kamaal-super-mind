#!/usr/bin/env bash

set -euo pipefail

REPOSITORY_URL="https://github.com/kamaal111/kamaal-super-mind.git"
INSTALL_DIRECTORY="${KAMAAL_SUPER_MIND_DIR:-$HOME/.kamaal-super-mind}"
PLUGIN_NAME="kamaal-super-mind"
MARKETPLACE_NAME="kamaal-super-mind"

# Dry runs print the actions without requiring Git, Codex, or changing any files.
if [[ "${1:-}" == "--dry-run" ]]; then
  printf 'Would clone or update %s at %s.\n' "$REPOSITORY_URL" "$INSTALL_DIRECTORY"
  printf 'Would register marketplace %s and install %s@%s.\n' \
    "$MARKETPLACE_NAME" "$PLUGIN_NAME" "$MARKETPLACE_NAME"
  exit 0
fi

# The rest of the script needs Git to download the plugin and Codex to install it.
for command in git codex; do
  if ! command -v "$command" >/dev/null 2>&1; then
    printf 'Error: %s must be installed before installing Kamaal Super Mind.\n' "$command" >&2
    exit 1
  fi
done

if [[ -d "$INSTALL_DIRECTORY/.git" ]]; then
  printf 'Updating Kamaal Super Mind...\n'

  # Remember the last remote revision before fetching. This lets us distinguish
  # a normal upstream history rewrite from commits someone made in this checkout.
  previous_upstream="$(git -C "$INSTALL_DIRECTORY" rev-parse --verify refs/remotes/origin/main 2>/dev/null || true)"
  git -C "$INSTALL_DIRECTORY" fetch origin main

  # Do not overwrite edits that have not been committed, whether or not they
  # have been staged for a Git commit.
  if ! git -C "$INSTALL_DIRECTORY" diff --quiet || \
    ! git -C "$INSTALL_DIRECTORY" diff --cached --quiet; then
    printf 'Error: %s has local changes; update it manually before rerunning the installer.\n' \
      "$INSTALL_DIRECTORY" >&2
    exit 1
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

printf '\nKamaal Super Mind is installed. Start a new Codex task to use it.\n'
