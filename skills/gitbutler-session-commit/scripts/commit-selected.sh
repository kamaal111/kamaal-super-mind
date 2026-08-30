#!/usr/bin/env bash

set -euo pipefail

if [[ $# -lt 3 ]]; then
  echo "Usage: $0 <branch> <message-file> <change-id>..." >&2
  exit 2
fi

branch=$1
message_file=$2
shift 2

if ! git show-ref --verify --quiet refs/heads/gitbutler/workspace; then
  echo "GitButler workspace marker is absent; use the plain Git workflow." >&2
  exit 2
fi

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
message_validator=$script_dir/../../git-commit-message/scripts/validate-message.sh

if ! "$message_validator" "$message_file"; then
  exit 1
fi

if ! but status --json >/dev/null; then
  echo "GitButler workspace access failed." >&2
  echo "If this is a sandboxed agent, request permission to write .git and retry." >&2
  echo "Do not run 'but setup' solely because this check failed." >&2
  exit 1
fi

if ! but commit --help | grep -Fq '[CHANGES]...'; then
  echo "Installed GitButler does not expose positional CHANGES." >&2
  echo "Read 'but commit --help' and use its supported selection interface." >&2
  exit 1
fi

exec but commit --branch "$branch" --message "$(<"$message_file")" "$@"
