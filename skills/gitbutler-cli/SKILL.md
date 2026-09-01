---
name: gitbutler-cli
description: Use GitButler's `but` CLI to work in a GitButler-managed repository. Use when inspecting or setting up a GitButler workspace; creating, applying, or stacking virtual branches; assigning changes; committing or reorganizing history; resolving conflicts; recovering with the oplog; pushing, creating pull requests, or landing a branch. Also use when the user says GitButler, virtual branch, virtual branch stack, or `but`.
---

# GitButler CLI

GitButler keeps all applied virtual branches in one working directory. Do not
check out between feature branches. Put each intentional change on the virtual
branch (also called a stack) that owns it.

## Start With The Workspace

Resolve which repository you are operating on before anything else. A
"workspace" directory that bundles several independent Git checkouts (as
submodules or sibling clones) is not itself the repository the user means —
it is a different Git repository with its own, unrelated GitButler state, if
it has one at all. If the user names a project, path, or submodule, `cd` into
that exact repository (or pass `-C <path>` to every `git`/`but` command)
before running the detector or anything else. Never run `but setup` or
diagnose `but` failures from the outer workspace root as a stand-in for the
inner repository the user actually asked about — a "no GitButler project
found" or "uncommitted files would be overwritten" error from the wrong
directory tells you nothing about the repository you were asked to change.

Do not use `but status` to detect GitButler. GitButler may prompt to set up an
ordinary Git repository. First check for its workspace marker without invoking
`but`. Run `scripts/detect-workspace-mode.sh` instead of reimplementing the
check. It returns `gitbutler` or `plain-git` and fails closed when it cannot
inspect the repository. Do not append a marker check after a possibly failing
command or infer its result from a compound command:

```bash
scripts/detect-workspace-mode.sh
```

Only if that check succeeds should you run `but status`, `but diff`, or other
GitButler commands. If it fails, use plain Git and do not run `but setup`.
Ask the user to set up GitButler separately if they want that workflow.

A failed inspection, missing helper, permission error, or interrupted command
is not a negative marker result. Resolve the failure before choosing a
workflow. Both commit helpers call this detector immediately before mutating
the index or history.

No matter how many `but` commands fail, do not substitute raw `git` mutation
commands (`checkout`, `rebase`, `commit --amend`, `reset`, `clean`, `stash`)
to route around the failure — even though raw Git is the right tool in this
workspace's other, non-GitButler projects. A `but` error is information about
that one command, not license to drop out of GitButler's history model for
a repository this detector confirmed is GitButler-managed. If every `but`
avenue is exhausted, stop and report the exact error to the user instead of
improvising with plain Git.

If the marker exists but `but status` fails with `unable to open database file`
or `Setup required`, do not run `but setup` reflexively. In sandboxed agent
environments, GitButler needs write access to `.git/gitbutler/but.sqlite` even
for workspace inspection. Request permission to write the repository's `.git`
directory, then retry `but status`. Run `but setup` only when the user asks to
initialize or repair GitButler after the access issue has been ruled out.

If `but setup` reports `Uncommitted files would be overwritten by checkout:
<paths>`, stop. This means those paths differ from what GitButler's managed
branch expects to check out — it does not mean GitButler is broken, and it is
not authorization to clear the way. Do not run `git stash`, `git clean`,
`git checkout -- .`, or a submodule-wide checkout to force the setup past
this error: that discards state you have not inspected, and the listed paths
may belong to sibling submodules that are not even part of the repository you
are trying to manage. First re-confirm you are inside the exact repository
the user named (see the repository-resolution note above). If you are, list
the affected paths for the user and ask before discarding anything in them.

If a GitButler command reports `GitButler mode exit required`, normal
GitButler operations are unavailable until the workspace is migrated out of
that mode. Do not retry the blocked command or use plain-Git history edits.
Inspect `but teardown --help`, `git status`, and `git branch` first. Explain
that `but teardown` creates an oplog snapshot, checks out a local branch, and
preserves dangling workspace commits. Run
`but teardown --checkout-to <matching-local-branch>` only after the user
explicitly authorizes leaving GitButler mode. Then verify the checked-out
branch and workspace status. Resume using plain Git; do not run `but setup`
unless the user asks to return to GitButler mode.

1. Read repository instructions and inspect the state before changing it:

   ```bash
   but status
   but diff
   but branch list
   ```

2. Treat unassigned changes and changes assigned to another branch as someone
   else's work until the user confirms otherwise. Never silently discard them.
3. Prefer `but status --json` when structured output helps. Use
   `but <command> --help` when flags or behavior are uncertain—the installed
   GitButler version is authoritative.

4. Check `but commit --help` before the first commit in a workspace. The CLI
   changes quickly: do not assume `but stage`, `--only`, `--changes`, or branch
   flags exist. In versions where `but commit` accepts positional `CHANGES`,
   pass the exact file or hunk IDs from `but status -fv` to make the commit
   scope deterministic. Use
   `scripts/commit-selected.sh <branch> <message-file> <change-id>...` when
   this plugin's helper is available.

## Core Loop: Create, Assign, Commit

Treat `but commit` and `git stash` as destructive operations. Run either only
in an isolated worktree or when the user explicitly authorizes that exact
operation.

Create a focused virtual branch, then route only its changes to that branch:

```bash
but branch new feature-short-description
but status -fv
scripts/commit-selected.sh feature-short-description message.txt <change-id>...
```

- `but status -fv` exposes short IDs for files or hunks. Pass only those IDs
  to the installed CLI's supported selection interface; never guess paths or
  rely on a stale staging command from another GitButler version.
- The included `commit-selected.sh` validates the message and uses the current
  positional-`CHANGES` interface. If `but commit --help` differs from that
  interface, stop and follow the installed help instead of adapting the helper
  by guesswork.
- Inspect `but show <branch>` and `but diff` before committing. Run the
  relevant checks before saying the branch is ready.

If an identically named but unapplied branch is a possible target, inspect it
with `but show <branch>` first. If applying it fails because uncommitted files
would be overwritten, do not force, discard, or rewrite it. Create a new,
task-specific branch unless the user directs a different history operation.

## Keep Related Work Separate

- Create one virtual branch per independently reviewable concern. Several
  branches can remain applied at once; never switch branches just to work on a
  different concern.
- Build a stack only when one branch truly depends on another:

  ```bash
  but branch new feature-foundation
  but branch new feature-api --above feature-foundation
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
| Add selected changes to an existing commit | `but amend --target <commit> <file-or-hunk>...` |
| Let GitButler place fitting edits into prior commits | `but absorb --dry-run`, then `but absorb` |
| Move a committed item to a branch | `but move --branch <branch> <source>...` |
| Rename a branch or reword a commit | `but reword <target>` |
| Return a commit's changes to the workspace | `but uncommit <target>` |
| Combine commits | `but squash <commits>` |
| Move a commit or branch in a stack | `but move <commit-or-branch> <target>` |

Inspect `but move --help`, `but amend --help`, and `but squash --help` before a
history mutation; their source and target flags are version-sensitive. Ask
before rewording, rebasing/moving, squashing, uncommitting, deleting, or
force-pushing user-owned history.

## Update And Resolve

Before publishing, update applied branches and deal with conflicts through
GitButler:

```bash
but pull --check
but pull
but status
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
