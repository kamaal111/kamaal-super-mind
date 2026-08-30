#!/usr/bin/env bash

set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <message-file>" >&2
  exit 2
fi

message_file=$1

if [[ ! -f $message_file ]]; then
  echo "Commit message file not found: $message_file" >&2
  exit 2
fi

status=0
line_number=0

while IFS= read -r line || [[ -n $line ]]; do
  ((line_number += 1))
  line_length=${#line}

  if ((line_length > 72)); then
    printf 'Line %d is %d characters (maximum 72): %s\n' \
      "$line_number" "$line_length" "$line" >&2
    status=1
  fi
done < "$message_file"

exit "$status"
