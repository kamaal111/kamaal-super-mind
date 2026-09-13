#!/usr/bin/env bash
set -euo pipefail

payload="$(cat)"
command="$(printf '%s' "$payload" | jq -r '.command // empty')"

if printf '%s' "$command" | grep -qEi '(^|[;&|`(]|\bsudo[[:space:]]+)[[:space:]]*find[[:space:]]+(/|~)([[:space:]/]|$)'; then
  printf '%s\n' '{"permission":"deny","user_message":"Blocked: filesystem-wide find (root or home directory) is not allowed. See production-engineering skill.","agent_message":"This command scans the entire filesystem or home directory, which is forbidden. Scope find to the repository or task-relevant directory instead."}'
  exit 0
fi

printf '%s\n' '{"permission":"allow"}'
