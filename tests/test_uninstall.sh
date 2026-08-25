#!/usr/bin/env bash
# Automated test suite for uninstall.sh. Invoke via `just test-uninstall`.
#
# Each test runs uninstall.sh in an isolated sandbox: a scratch $HOME, a
# scratch KAMAAL_SUPER_MIND_DIR, and a PATH pointing at the fake `codex`,
# `claude`, and `cursor` binaries under tests/mocks/. Those mocks log every
# invocation to $MOCK_LOG and their behavior is driven by MOCK_*_EXIT
# environment variables, so scenarios that are hard to reach for real (a
# missing plugin, an unregistered marketplace) can be exercised
# deterministically without mutating the real Codex/Claude Code/Cursor
# installs on this machine.
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UNINSTALL_SCRIPT="$ROOT_DIR/uninstall.sh"
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

log_contains() {
  grep -Fq -- "$1" "$MOCK_LOG"
}

assert_log_contains() {
  log_contains "$1" || fail "expected mock log to contain: $1 (log: $(cat "$MOCK_LOG"))"
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

  unset MOCK_CODEX_PLUGIN_REMOVE_EXIT MOCK_CODEX_MARKETPLACE_REMOVE_EXIT \
    MOCK_CLAUDE_PLUGIN_UNINSTALL_EXIT MOCK_CLAUDE_MARKETPLACE_REMOVE_EXIT
}

link_mock() {
  ln -s "$MOCKS_DIR/$1" "$MOCK_BIN/$1"
}

run_uninstall() {
  OUTPUT="$(PATH="$TEST_PATH" HOME="$FAKE_HOME" KAMAAL_SUPER_MIND_DIR="$INSTALL_DIR" bash "$UNINSTALL_SCRIPT" "$@" 2>&1)"
  EXIT_CODE=$?
}

run_uninstall_from_stdin() {
  OUTPUT="$(PATH="$TEST_PATH" HOME="$FAKE_HOME" KAMAAL_SUPER_MIND_DIR="$INSTALL_DIR" \
    MOCK_CURL_COMMON="$ROOT_DIR/lib/common.sh" bash -s -- "$@" <"$UNINSTALL_SCRIPT" 2>&1)"
  EXIT_CODE=$?
}

# Populates a fake skill directory under INSTALL_DIR/skills, mimicking what a
# real clone provides, and links it into ~/.cursor/skills the way install.sh
# would have.
seed_installed_skill() {
  local skill_dir="$INSTALL_DIR/skills/$1"
  mkdir -p "$skill_dir"
  printf -- '---\nname: %s\ndescription: fake skill for tests\n---\n' "$1" >"$skill_dir/SKILL.md"
  mkdir -p "$FAKE_HOME/.cursor/skills"
  ln -s "$skill_dir" "$FAKE_HOME/.cursor/skills/$1"
}

test_dry_run_needs_no_dependencies() {
  TEST_PATH="/bin"
  mkdir -p "$INSTALL_DIR/.git"
  run_uninstall --dry-run

  assert_exit_code 0
  assert_contains "$OUTPUT" "Would remove"
  assert_contains "$OUTPUT" "Would delete"
  [[ -d "$INSTALL_DIR/.git" ]] || fail "dry run must not delete $INSTALL_DIR"
}

test_dry_run_from_stdin_loads_the_shared_library() {
  TEST_PATH="$MOCK_BIN:/usr/bin:/bin"
  link_mock curl
  run_uninstall_from_stdin --dry-run

  assert_exit_code 0
  assert_contains "$OUTPUT" "Would remove"
  [[ ! -e "$INSTALL_DIR" ]] || fail "dry run must not create $INSTALL_DIR"
}

test_no_harness_present_only_removes_checkout() {
  mkdir -p "$INSTALL_DIR/.git"
  run_uninstall

  assert_exit_code 0
  [[ ! -e "$INSTALL_DIR" ]] || fail "expected $INSTALL_DIR to be removed"
}

test_missing_checkout_is_a_no_op() {
  run_uninstall

  assert_exit_code 0
  [[ ! -e "$INSTALL_DIR" ]] || fail "expected no directory to be created"
}

test_existing_non_checkout_directory_errors() {
  : >"$INSTALL_DIR"
  run_uninstall

  assert_exit_code 1
  assert_contains "$OUTPUT" "exists but is not a Kamaal Super Mind checkout"
}

test_codex_uninstall_removes_plugin_and_marketplace() {
  link_mock codex
  mkdir -p "$INSTALL_DIR/.git"
  run_uninstall

  assert_exit_code 0
  assert_log_contains "codex plugin remove kamaal-super-mind@kamaal-super-mind"
  assert_log_contains "codex plugin marketplace remove kamaal-super-mind"
  assert_contains "$OUTPUT" "uninstalled from Codex"
}

test_codex_uninstall_tolerates_already_absent() {
  link_mock codex
  export MOCK_CODEX_PLUGIN_REMOVE_EXIT=1
  export MOCK_CODEX_MARKETPLACE_REMOVE_EXIT=1
  mkdir -p "$INSTALL_DIR/.git"
  run_uninstall

  assert_exit_code 0
  assert_contains "$OUTPUT" "already not installed"
  assert_contains "$OUTPUT" "already not registered"
  assert_contains "$OUTPUT" "uninstalled from Codex"
}

test_claude_uninstall_removes_plugin_and_marketplace() {
  link_mock claude
  mkdir -p "$INSTALL_DIR/.git"
  run_uninstall

  assert_exit_code 0
  assert_log_contains "claude plugin uninstall kamaal-super-mind@kamaal-super-mind"
  assert_log_contains "claude plugin marketplace remove kamaal-super-mind"
  assert_contains "$OUTPUT" "uninstalled from Claude Code"
}

test_claude_uninstall_tolerates_already_absent() {
  link_mock claude
  export MOCK_CLAUDE_PLUGIN_UNINSTALL_EXIT=1
  export MOCK_CLAUDE_MARKETPLACE_REMOVE_EXIT=1
  mkdir -p "$INSTALL_DIR/.git"
  run_uninstall

  assert_exit_code 0
  assert_contains "$OUTPUT" "already not installed"
  assert_contains "$OUTPUT" "already not registered"
  assert_contains "$OUTPUT" "uninstalled from Claude Code"
}

test_cursor_removes_plugin_symlink() {
  link_mock cursor
  mkdir -p "$FAKE_HOME/.cursor/plugins/local"
  ln -s "$INSTALL_DIR" "$FAKE_HOME/.cursor/plugins/local/kamaal-super-mind"
  mkdir -p "$INSTALL_DIR/.git"
  run_uninstall

  assert_exit_code 0
  [[ ! -e "$FAKE_HOME/.cursor/plugins/local/kamaal-super-mind" ]] \
    || fail "expected the Cursor plugin symlink to be removed"
  assert_contains "$OUTPUT" "uninstalled from Cursor"
}

test_cursor_missing_plugin_symlink_is_a_no_op() {
  link_mock cursor
  mkdir -p "$INSTALL_DIR/.git"
  run_uninstall

  assert_exit_code 0
  assert_contains "$OUTPUT" "uninstalled from Cursor"
}

test_cursor_existing_non_symlink_errors() {
  link_mock cursor
  mkdir -p "$FAKE_HOME/.cursor/plugins/local/kamaal-super-mind"
  mkdir -p "$INSTALL_DIR/.git"
  run_uninstall

  assert_exit_code 1
  assert_contains "$OUTPUT" "exists but is not a Kamaal Super Mind symlink"
}

test_cursor_removes_skill_symlinks() {
  link_mock cursor
  mkdir -p "$INSTALL_DIR/.git"
  seed_installed_skill commit
  seed_installed_skill backend
  run_uninstall

  assert_exit_code 0
  [[ ! -e "$FAKE_HOME/.cursor/skills/commit" ]] || fail "expected commit skill symlink to be removed"
  [[ ! -e "$FAKE_HOME/.cursor/skills/backend" ]] || fail "expected backend skill symlink to be removed"
}

test_cursor_leaves_unrelated_cursor_skills_entries() {
  link_mock cursor
  mkdir -p "$INSTALL_DIR/.git"
  mkdir -p "$FAKE_HOME/.cursor/skills"
  ln -s "/tmp/unrelated-skill" "$FAKE_HOME/.cursor/skills/unrelated"
  run_uninstall

  assert_exit_code 0
  [[ -L "$FAKE_HOME/.cursor/skills/unrelated" ]] \
    || fail "expected unrelated symlink to be left alone"
}

test_cursor_skill_symlinks_removed_even_if_checkout_already_gone() {
  link_mock cursor
  # Seed the skill and its symlink, then delete the checkout by hand before
  # uninstalling, simulating a user who already removed it manually.
  seed_installed_skill commit
  rm -rf "$INSTALL_DIR"
  run_uninstall

  assert_exit_code 0
  [[ ! -e "$FAKE_HOME/.cursor/skills/commit" ]] \
    || fail "expected commit skill symlink to be removed even without a checkout"
}

test_cursor_removes_legacy_agents_skills_symlinks() {
  link_mock cursor
  mkdir -p "$INSTALL_DIR/.git" "$FAKE_HOME/.agents/skills"
  local skill_dir="$INSTALL_DIR/skills/commit"
  mkdir -p "$skill_dir"
  ln -s "$skill_dir" "$FAKE_HOME/.agents/skills/commit"
  run_uninstall

  assert_exit_code 0
  [[ ! -e "$FAKE_HOME/.agents/skills/commit" ]] \
    || fail "expected legacy agent skill symlink to be removed"
}

test_removes_checkout_directory() {
  link_mock codex
  mkdir -p "$INSTALL_DIR/.git"
  run_uninstall

  assert_exit_code 0
  [[ ! -e "$INSTALL_DIR" ]] || fail "expected $INSTALL_DIR to be deleted"
  assert_contains "$OUTPUT" "Removed $INSTALL_DIR"
}

test_all_harnesses_uninstalled_together() {
  link_mock codex
  link_mock claude
  link_mock cursor
  mkdir -p "$INSTALL_DIR/.git"
  run_uninstall

  assert_exit_code 0
  assert_contains "$OUTPUT" "uninstalled from Codex"
  assert_contains "$OUTPUT" "uninstalled from Claude Code"
  assert_contains "$OUTPUT" "uninstalled from Cursor"
  [[ ! -e "$INSTALL_DIR" ]] || fail "expected $INSTALL_DIR to be deleted"
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
