---
name: gitbutler-cli
description: Use GitButler's `but` CLI to work in a GitButler-managed repository. Use when inspecting or setting up a GitButler workspace; creating, applying, or stacking virtual branches; assigning changes; committing or reorganizing history; resolving conflicts; recovering with the oplog; pushing, creating pull requests, or landing a branch. Also use when the user says GitButler, virtual branch, virtual branch stack, or `but`.
---

# GitButler CLI

GitButler keeps all applied virtual branches in one working directory. Do not
check out between feature branches. Put each intentional change on the virtual
branch (also called a stack) that owns it.

## Start With The Workspace

1. Read repository instructions and inspect the state before changing it:

   ```bash
   but status --format=agent
   but diff
   but branch list
   ```

2. Treat unassigned changes and changes assigned to another branch as someone
   else's work until the user confirms otherwise. Never silently discard them.
3. Prefer `but ... --format=agent` for detailed inspection and `--format=json`
   when structured output helps. Use `but <command> --help` when flags or
   behavior are uncertain—the installed GitButler version is authoritative.

## Core Loop: Create, Assign, Commit

Create a focused virtual branch, then route only its changes to that branch:

```bash
but branch new feature-short-description
but status --format=agent
but stage <file-or-hunk-id> feature-short-description
but commit feature-short-description --only -m "feat: explain the change"
```

- `but status` exposes short IDs for files or hunks. Use those IDs with
  `but stage`; do not guess path syntax when a hunk needs to be separated.
- `but stage` without arguments opens an interactive picker. Use
  `but stage --branch <branch>` for the same picker scoped to one branch.
- `but commit` normally includes all uncommitted changes not staged to another
  branch. Use `--only` after staging to make a narrow, reviewable commit.
- Use `--changes <id[,id]>` when committing exactly the listed uncommitted
  files or hunks is clearer than staging first.
- Inspect `but show <branch>` and `but diff` before committing. Run the
  relevant checks before saying the branch is ready.

## Keep Related Work Separate

- Create one virtual branch per independently reviewable concern. Several
  branches can remain applied at once; never switch branches just to work on a
  different concern.
- Build a stack only when one branch truly depends on another:

  ```bash
  but branch new feature-foundation
  but branch new feature-api --anchor feature-foundation
  ```

- Name branches for their task, not the tool or the agent, unless the user
  needs explicit ownership in a shared workspace.
- Before reorganizing a stack or moving commits, create a named restore point:

  ```bash
  but oplog snapshot --message "Before reorganizing feature stack"
  ```

## Edit Existing History Deliberately

Use GitButler commands rather than stock Git history editing while the
repository is in GitButler mode.

| Intent | Command |
| --- | --- |
| Add selected changes to an existing commit | `but amend <commit> --changes <file-or-hunk>` |
| Let GitButler place fitting edits into prior commits | `but absorb --dry-run`, then `but absorb` |
| Move or combine entities | `but rub <source> <target>` |
| Rename a branch or reword a commit | `but reword <target>` |
| Return a commit's changes to the workspace | `but uncommit <target>` |
| Combine commits | `but squash <commits>` |
| Move a commit or branch in a stack | `but move <commit-or-branch> <target>` |

`but rub` is context-sensitive: file/hunk → branch stages work, file/hunk →
commit amends it, commit → branch moves it, and commit → commit combines it.
Inspect the before and after state. Ask before rewording, rebasing/moving,
squashing, uncommitting, deleting, or force-pushing user-owned history.

## Update And Resolve

Before publishing, update applied branches and deal with conflicts through
GitButler:

```bash
but pull --check
but pull
but status --format=agent
but resolve <conflicted-commit>
# edit the conflict markers
but resolve status
but resolve finish
```

Do not use `git checkout`, `git rebase`, `git reset`, or `git commit` to work
around a GitButler workspace problem. Read the relevant `but --help` output,
make a snapshot, and preserve the state instead.

## Publish Or Land

Publishing is explicit user authorization. Confirm the target branch and review
route, then inspect and test first:

```bash
but push --dry-run feature-short-description
but push feature-short-description
but pr new feature-short-description
```

Use `but land <branch>` only when the user explicitly requests direct landing;
it bypasses the pull-request review route. Do not add `--yes` to `but land`,
`--with-force` to `but push`, or `--skip-force-push-protection` without clear
authorization.

For a stack, publish and merge in dependency order: foundation first, then each
dependent branch after its base is incorporated. Refresh with `but pull` between
landings or merged pull requests.

## Recover Safely

GitButler records workspace operations—including uncommitted work—in its oplog.
Use it before reaching for destructive Git commands:

```bash
but oplog list
but undo
but oplog restore <snapshot>
```

Take a snapshot before a complex reorganization, conflict-resolution session,
or direct landing. If state still looks wrong, stop after preserving evidence
with `but status`, `but oplog list`, and `git status`; report the condition
instead of running setup, teardown, deletion, or reset speculatively.

## Plain Git Boundaries

GitButler remains Git-compatible, so read-only commands such as `git diff`,
`git log`, `git show`, and `git status` are fine for diagnosis. In an active
GitButler workspace, use `but` for mutations that create or rewrite commits,
move branches, assign changes, resolve conflicts, push GitButler branches, or
restore state. Use ordinary Git mutation commands only when the user explicitly
asks to leave GitButler mode or a documented recovery procedure requires it.
