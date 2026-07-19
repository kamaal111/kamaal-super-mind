#!/usr/bin/env bash
# Automated test suite for install.sh. Invoke via `just test`.
#
# Each test runs install.sh in an isolated sandbox: a scratch $HOME, a
# scratch KAMAAL_SUPER_MIND_DIR, and a PATH pointing at the fake `git`,
# `codex`, `claude`, and `cursor` binaries under tests/mocks/. Those mocks
# log every invocation to $MOCK_LOG and their behavior is driven by
# MOCK_*_EXIT / MOCK_*_OUTPUT environment variables, so scenarios that are
# hard to reach for real (a force-pushed remote, an already-registered
# marketplace, a failed plugin install) can be exercised deterministically
# without network access or mutating the real Codex/Claude Code/Cursor
# installs on this machine.
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_SCRIPT="$ROOT_DIR/install.sh"
MOCKS_DIR="$ROOT_DIR/tests/mocks"

TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/kamaal-super-mind-tests.XXXXXX")"
trap 'rm -rf "$TMP_ROOT"' EXIT

pass_count=0
fail_count=0
current_test=""
test_failed=0

fail() {
  printf 'FAIL: %s: %s\n' "$current_test" "$1" >&2
  test_failed=1
  fail_count=$((fail_count + 1))
}

assert_exit_code() {
  local expected="$1"
  [[ "$EXIT_CODE" == "$expected" ]] || fail "expected exit code $expected, got $EXIT_CODE (output: $OUTPUT)"
}

assert_contains() {
  local haystack="$1" needle="$2"
  case "$haystack" in
  *"$needle"*) ;;
  *) fail "expected to find '$needle' in: $haystack" ;;
  esac
}

assert_not_contains() {
  local haystack="$1" needle="$2"
  case "$haystack" in
  *"$needle"*) fail "expected NOT to find '$needle' in: $haystack" ;;
  esac
}

log_contains() {
  grep -Fq -- "$1" "$MOCK_LOG"
}

assert_log_contains() {
  log_contains "$1" || fail "expected mock log to contain: $1 (log: $(cat "$MOCK_LOG"))"
}

assert_log_not_contains() {
  log_contains "$1" && fail "expected mock log NOT to contain: $1 (log: $(cat "$MOCK_LOG"))"
  return 0
}

# Resets sandbox directories and every MOCK_* control variable so tests
# never leak state into one another regardless of run order.
setup_test() {
  local case_dir
  case_dir="$(mktemp -d "$TMP_ROOT/case.XXXXXX")"
  FAKE_HOME="$case_dir/home"
  INSTALL_DIR="$FAKE_HOME/.kamaal-super-mind"
  MOCK_BIN="$case_dir/bin"
  MOCK_LOG="$case_dir/mock.log"
  mkdir -p "$FAKE_HOME" "$MOCK_BIN"
  : >"$MOCK_LOG"
  export MOCK_LOG
  TEST_PATH="$MOCK_BIN:/usr/bin:/bin"

  unset MOCK_GIT_PREV_UPSTREAM MOCK_GIT_HEAD MOCK_GIT_FETCH_EXIT \
    MOCK_GIT_DIFF_EXIT MOCK_GIT_DIFF_CACHED_EXIT MOCK_GIT_STASH_EXIT \
    MOCK_GIT_MERGE_BASE_EXIT MOCK_GIT_RESET_EXIT MOCK_GIT_CLONE_EXIT \
    MOCK_CODEX_MARKETPLACE_ADD_EXIT MOCK_CODEX_PLUGIN_LIST_OUTPUT MOCK_CODEX_PLUGIN_ADD_EXIT \
    MOCK_CLAUDE_MARKETPLACE_ADD_EXIT MOCK_CLAUDE_MARKETPLACE_LIST_JSON \
    MOCK_CLAUDE_MARKETPLACE_UPDATE_EXIT MOCK_CLAUDE_PLUGIN_INSTALL_EXIT MOCK_CLAUDE_PLUGIN_UPDATE_EXIT
}

link_mock() {
  ln -s "$MOCKS_DIR/$1" "$MOCK_BIN/$1"
}

run_install() {
  OUTPUT="$(PATH="$TEST_PATH" HOME="$FAKE_HOME" KAMAAL_SUPER_MIND_DIR="$INSTALL_DIR" bash "$INSTALL_SCRIPT" "$@" 2>&1)"
  EXIT_CODE=$?
}

test_dry_run_needs_no_dependencies() {
  TEST_PATH="/bin"
  run_install --dry-run

  assert_exit_code 0
  assert_contains "$OUTPUT" "Would clone or update"
  assert_contains "$OUTPUT" "Would register marketplace"
  assert_contains "$OUTPUT" "Would link"
  [[ ! -e "$INSTALL_DIR" ]] || fail "dry run must not create $INSTALL_DIR"
}

test_missing_git_fails() {
  TEST_PATH="$MOCK_BIN:/bin"
  link_mock codex
  run_install

  assert_exit_code 1
  assert_contains "$OUTPUT" "git must be installed"
}

test_no_harness_detected_fails() {
  link_mock git
  run_install

  assert_exit_code 1
  assert_contains "$OUTPUT" "install Codex, Claude Code, or Cursor"
}

test_fresh_install_clones_and_installs_codex() {
  link_mock git
  link_mock codex
  run_install

  assert_exit_code 0
  [[ -d "$INSTALL_DIR/.git" ]] || fail "expected $INSTALL_DIR to be cloned"
  assert_log_contains "git clone https://github.com/kamaal111/kamaal-super-mind.git $INSTALL_DIR"
  assert_log_contains "codex plugin marketplace add $INSTALL_DIR"
  assert_log_contains "codex plugin add kamaal-super-mind@kamaal-super-mind"
  assert_contains "$OUTPUT" "installed for Codex"
  assert_not_contains "$OUTPUT" "installed for Claude Code"
  assert_not_contains "$OUTPUT" "installed for Cursor"
}

test_existing_non_checkout_directory_errors() {
  link_mock git
  link_mock codex
  : >"$INSTALL_DIR"
  run_install

  assert_exit_code 1
  assert_contains "$OUTPUT" "exists but is not a Kamaal Super Mind checkout"
  assert_log_not_contains "git clone"
}

test_update_with_clean_history_resets_hard() {
  link_mock git
  link_mock codex
  mkdir -p "$INSTALL_DIR/.git"
  export MOCK_GIT_PREV_UPSTREAM="sha1"
  export MOCK_GIT_HEAD="sha1"
  run_install

  assert_exit_code 0
  assert_contains "$OUTPUT" "Updating Kamaal Super Mind"
  assert_not_contains "$OUTPUT" "Stashing local changes"
  assert_log_contains "git -C $INSTALL_DIR fetch origin main"
  assert_log_contains "git -C $INSTALL_DIR reset --hard FETCH_HEAD"
  assert_log_not_contains "merge-base"
}

test_update_stashes_dirty_worktree() {
  link_mock git
  link_mock codex
  mkdir -p "$INSTALL_DIR/.git"
  export MOCK_GIT_DIFF_EXIT=1
  run_install

  assert_exit_code 0
  assert_contains "$OUTPUT" "Stashing local changes"
  assert_log_contains "stash push -m"
}

test_update_detects_local_commits_and_errors() {
  link_mock git
  link_mock codex
  mkdir -p "$INSTALL_DIR/.git"
  export MOCK_GIT_PREV_UPSTREAM="old_sha"
  export MOCK_GIT_HEAD="new_sha"
  export MOCK_GIT_MERGE_BASE_EXIT=0
  run_install

  assert_exit_code 1
  assert_contains "$OUTPUT" "has local commits"
  assert_log_not_contains "reset --hard"
}

test_update_allows_force_pushed_history() {
  link_mock git
  link_mock codex
  mkdir -p "$INSTALL_DIR/.git"
  export MOCK_GIT_PREV_UPSTREAM="old_sha"
  export MOCK_GIT_HEAD="new_sha"
  export MOCK_GIT_MERGE_BASE_EXIT=1
  run_install

  assert_exit_code 0
  assert_not_contains "$OUTPUT" "has local commits"
  assert_log_contains "git -C $INSTALL_DIR reset --hard FETCH_HEAD"
}

test_codex_marketplace_add_fails_but_already_registered() {
  link_mock git
  link_mock codex
  export MOCK_CODEX_MARKETPLACE_ADD_EXIT=1
  export MOCK_CODEX_PLUGIN_LIST_OUTPUT='Marketplace `kamaal-super-mind` (local)'
  run_install

  assert_exit_code 0
  assert_log_contains "codex plugin add kamaal-super-mind@kamaal-super-mind"
}

test_codex_marketplace_add_fails_and_not_registered_errors() {
  link_mock git
  link_mock codex
  export MOCK_CODEX_MARKETPLACE_ADD_EXIT=1
  export MOCK_CODEX_PLUGIN_LIST_OUTPUT=''
  run_install

  assert_exit_code 1
  assert_contains "$OUTPUT" "Codex could not register the marketplace"
}

test_claude_marketplace_add_fails_but_already_registered_updates_it() {
  link_mock git
  link_mock claude
  export MOCK_CLAUDE_MARKETPLACE_ADD_EXIT=1
  export MOCK_CLAUDE_MARKETPLACE_LIST_JSON='[{"name":"kamaal-super-mind"}]'
  run_install

  assert_exit_code 0
  assert_log_contains "claude plugin marketplace update kamaal-super-mind"
  assert_contains "$OUTPUT" "installed for Claude Code"
}

test_claude_marketplace_add_fails_and_not_registered_errors() {
  link_mock git
  link_mock claude
  export MOCK_CLAUDE_MARKETPLACE_ADD_EXIT=1
  export MOCK_CLAUDE_MARKETPLACE_LIST_JSON='[]'
  run_install

  assert_exit_code 1
  assert_contains "$OUTPUT" "Claude Code could not register the marketplace"
}

test_claude_install_falls_back_to_update() {
  link_mock git
  link_mock claude
  export MOCK_CLAUDE_PLUGIN_INSTALL_EXIT=1
  run_install

  assert_exit_code 0
  assert_log_contains "claude plugin update kamaal-super-mind@kamaal-super-mind"
  assert_contains "$OUTPUT" "installed for Claude Code"
}

test_cursor_creates_fresh_symlink() {
  link_mock git
  link_mock cursor
  run_install

  assert_exit_code 0
  local link="$FAKE_HOME/.cursor/plugins/local/kamaal-super-mind"
  [[ -L "$link" ]] || fail "expected $link to be a symlink"
  [[ "$(readlink "$link")" == "$INSTALL_DIR" ]] || fail "expected $link to point at $INSTALL_DIR"
  assert_contains "$OUTPUT" "installed for Cursor"
}

test_cursor_replaces_existing_symlink() {
  link_mock git
  link_mock cursor
  mkdir -p "$FAKE_HOME/.cursor/plugins/local"
  ln -s "/tmp/stale-target" "$FAKE_HOME/.cursor/plugins/local/kamaal-super-mind"
  run_install

  assert_exit_code 0
  local link="$FAKE_HOME/.cursor/plugins/local/kamaal-super-mind"
  [[ "$(readlink "$link")" == "$INSTALL_DIR" ]] || fail "expected stale symlink to be replaced"
}

test_cursor_existing_non_symlink_errors() {
  link_mock git
  link_mock cursor
  mkdir -p "$FAKE_HOME/.cursor/plugins/local/kamaal-super-mind"
  run_install

  assert_exit_code 1
  assert_contains "$OUTPUT" "exists but is not a Kamaal Super Mind symlink"
}

test_all_harnesses_installed_together() {
  link_mock git
  link_mock codex
  link_mock claude
  link_mock cursor
  run_install

  assert_exit_code 0
  assert_contains "$OUTPUT" "installed for Codex"
  assert_contains "$OUTPUT" "installed for Claude Code"
  assert_contains "$OUTPUT" "installed for Cursor"
}

main() {
  local test_names
  test_names="$(declare -F | awk '{print $3}' | grep '^test_')"

  local t
  while IFS= read -r t; do
    [[ -n "$t" ]] || continue
    current_test="$t"
    test_failed=0
    setup_test
    "$t"
    if [[ "$test_failed" -eq 0 ]]; then
      pass_count=$((pass_count + 1))
      printf 'PASS: %s\n' "$t"
    fi
  done <<<"$test_names"

  printf '\n%d passed, %d failed\n' "$pass_count" "$fail_count"
  [[ "$fail_count" -eq 0 ]]
}

main
