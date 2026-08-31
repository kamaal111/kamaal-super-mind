#!/usr/bin/env bash

set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <message-file> <path>..." >&2
  exit 2
fi

message_file=$1
shift

require_plain_git_workspace() {
  if git show-ref --verify --quiet refs/heads/gitbutler/workspace; then
    echo "GitButler workspace marker is present; use GitButler to commit." >&2
    exit 2
  fi

  if [[ $(git branch --show-current) == gitbutler/workspace ]]; then
    echo "Checked out gitbutler/workspace; use GitButler to commit." >&2
    exit 2
  fi
}

require_plain_git_workspace
git add -- "$@"
require_plain_git_workspace
git commit -F "$message_file"
