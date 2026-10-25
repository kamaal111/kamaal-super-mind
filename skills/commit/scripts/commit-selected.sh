#!/usr/bin/env bash

set -euo pipefail

if [[ $# -lt 3 ]]; then
  echo "Usage: $0 <branch> <message-file> <change-id>..." >&2
  exit 2
fi

branch=$1
message_file=$2
shift 2

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
detector=$script_dir/../../gitbutler-cli/scripts/detect-workspace-mode.sh

if ! mode=$($detector); then
  echo "Unable to determine whether GitButler manages this repository." >&2
  exit 2
fi

if [[ $mode != gitbutler ]]; then
  echo "GitButler workspace marker is absent; use the plain Git workflow." >&2
  exit 2
fi

message_validator=$script_dir/../../git-commit-message/scripts/validate-message.sh

if ! "$message_validator" "$message_file"; then
  exit 1
fi

exec python3 "$script_dir/guarded_commit.py" "$branch" "$message_file" "$@"
