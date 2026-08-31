#!/usr/bin/env bash

set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <message-file> <path>..." >&2
  exit 2
fi

message_file=$1
shift

require_plain_git_workspace() {
  script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
  detector=$script_dir/../../gitbutler-cli/scripts/detect-workspace-mode.sh

  if ! mode=$($detector); then
    echo "Unable to determine whether GitButler manages this repository." >&2
    exit 2
  fi

  if [[ $mode != plain-git ]]; then
    echo "GitButler manages this repository; use GitButler to commit." >&2
    exit 2
  fi
}

require_plain_git_workspace
git add -- "$@"
require_plain_git_workspace
git commit -F "$message_file"
