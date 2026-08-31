#!/usr/bin/env bash

set -euo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
validator=$repo_root/skills/git-commit-message/scripts/validate-message.sh
commit_selected=$repo_root/skills/gitbutler-session-commit/scripts/commit-selected.sh
commit_plain_git=$repo_root/skills/commit/scripts/commit-plain-git.sh
detector=$repo_root/skills/gitbutler-cli/scripts/detect-workspace-mode.sh
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

(
  cd "$test_root"
  [[ $($detector) == gitbutler ]]
)

mock_bin=$test_root/mock-bin
mkdir "$mock_bin"
cp "$repo_root/tests/mocks/but-gitbutler" "$mock_bin/but"
chmod +x "$mock_bin/but"

(
  cd "$test_root"
  PATH="$mock_bin:$PATH" "$commit_selected" test-branch \
    "$fixtures/git-commit-message-valid.txt" change-one
)

if (
  cd "$test_root"
  "$commit_plain_git" "$fixtures/git-commit-message-valid.txt" .
); then
  echo "Expected the plain-Git helper to reject a GitButler workspace." >&2
  exit 1
fi

race_root=$(mktemp -d)
trap 'rm -rf "$test_root" "$race_root"' EXIT

git -C "$race_root" init --quiet
git -C "$race_root" -c user.name='Test User' \
  -c user.email='test@example.com' commit --allow-empty --quiet -m test
touch "$race_root/changes.txt"

real_git=$(command -v git)
cp "$repo_root/tests/mocks/git-creates-gitbutler-marker" "$mock_bin/git"
chmod +x "$mock_bin/git"

if (
  cd "$race_root"
  PATH="$mock_bin:$PATH" REAL_GIT="$real_git" \
    "$commit_plain_git" "$fixtures/git-commit-message-valid.txt" changes.txt
); then
  echo "Expected the plain-Git helper to reject a marker created while staging." >&2
  exit 1
fi

(
  cd "$race_root"
  [[ $($detector) == gitbutler ]]
)

plain_root=$(mktemp -d)
trap 'rm -rf "$test_root" "$race_root" "$plain_root"' EXIT

git -C "$plain_root" init --quiet
git -C "$plain_root" config user.name 'Test User'
git -C "$plain_root" config user.email 'test@example.com'
git -C "$plain_root" commit --allow-empty --quiet -m test
touch "$plain_root/changes.txt"

(
  cd "$plain_root"
  [[ $($detector) == plain-git ]]
  "$commit_plain_git" "$fixtures/git-commit-message-valid.txt" changes.txt
)

[[ $(git -C "$plain_root" log -1 --format=%s) == 'Keep GitButler commits deterministic' ]]
