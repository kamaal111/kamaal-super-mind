#!/usr/bin/env bash

set -euo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
validator=$repo_root/skills/git-commit-message/scripts/validate-message.sh
commit_selected=$repo_root/skills/gitbutler-session-commit/scripts/commit-selected.sh
fixtures=$repo_root/tests/fixtures

"$validator" "$fixtures/git-commit-message-valid.txt"

if "$validator" "$fixtures/git-commit-message-overlong.txt" 2>/dev/null; then
  echo "Expected the validator to reject an overlong message." >&2
  exit 1
fi

test_root=$(mktemp -d)
trap 'rm -rf "$test_root"' EXIT

git -C "$test_root" init --quiet
git -C "$test_root" -c user.name='Test User' \
  -c user.email='test@example.com' commit --allow-empty --quiet -m test
git -C "$test_root" update-ref refs/heads/gitbutler/workspace HEAD

mock_bin=$test_root/mock-bin
mkdir "$mock_bin"
cp "$repo_root/tests/mocks/but-gitbutler" "$mock_bin/but"
chmod +x "$mock_bin/but"

(
  cd "$test_root"
  PATH="$mock_bin:$PATH" "$commit_selected" test-branch \
    "$fixtures/git-commit-message-valid.txt" change-one
)
