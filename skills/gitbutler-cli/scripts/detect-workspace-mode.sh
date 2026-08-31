#!/usr/bin/env bash

set -euo pipefail

if git show-ref --verify --quiet refs/heads/gitbutler/workspace; then
  marker_present=true
else
  marker_status=$?
  if [[ $marker_status -ne 1 ]]; then
    echo "Unable to inspect the GitButler workspace marker." >&2
    exit 2
  fi
  marker_present=false
fi

if ! current_branch=$(git branch --show-current); then
  echo "Unable to determine the current Git branch." >&2
  exit 2
fi

if [[ $marker_present == true || $current_branch == gitbutler/workspace ]]; then
  echo gitbutler
else
  echo plain-git
fi
