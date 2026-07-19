---
name: gitbutler-multi-agent
description: Coordinate multiple agents in a shared GitButler workspace using virtual branches. Use when agents work in parallel, hand work off, transfer commits, review each other's changes, or organize concurrent work with GitButler, virtual branches, or `but`.
---

# GitButler Multi-Agent Coordination

Apply `gitbutler-cli` for all GitButler commands. GitButler can keep multiple
virtual branches applied in one workspace, making ownership and later
reorganization explicit. It does not remove the need to coordinate physical
file edits or serialize conflicting workspace mutations.

## Choose The Right Shape

Use this workflow when work can be divided into independent files or hunks and
each task can become its own reviewable branch. Use one agent or a worktree when
agents must frequently edit the same files, need different dependency states, or
must run disruptive commands concurrently.

Do not ask several agents to test different implementations of the same lines
in one applied GitButler workspace. Use isolated worktrees or clones for that
experiment, then bring the chosen result back deliberately.

## Establish Lanes Before Editing

One coordinator should inspect the workspace, create a recovery point, and
announce ownership before parallel work begins:

```bash
but status --format=agent
but oplog snapshot --message "Before multi-agent work"
but branch new agent-auth-session
but branch new agent-api-endpoints
```

- Name branches `<owner>-<task>` when agent ownership matters; use task-oriented
  names when it does not.
- Give every lane an explicit scope: paths or symbols it owns, its target
  branch, expected output, and any dependencies.
- Treat unassigned changes and changes staged to another branch as reserved.
  Do not modify them without a handoff from the owner.
- Communicate a short handoff/status message through the agent coordination
  channel, not a temporary file: branch, files/hunks, commit IDs, validation,
  and remaining work.

## Parallel Work Protocol

Each agent works only in its lane:

```bash
but status --format=agent
# make changes only in the assigned scope
but stage <file-or-hunk-id> agent-auth-session
but commit agent-auth-session --only -m "feat: add session validation"
but show agent-auth-session
```

Keep `but` mutations serialized when agents share one checkout. Branch creation,
staging, commits, pulls, conflict resolution, history edits, and oplog restores
all change shared GitButler state; announce the operation and wait for it to
finish before another agent runs one. Independent source edits may proceed in
parallel only when their scopes do not overlap.

Before committing, re-run `but status --format=agent`. If another agent's
changes are present, stage only the current lane's IDs and use `--only`.

## Handoffs And Review

For a completed lane, hand off the branch name and commit IDs rather than
copying patches. A receiving agent can continue on the same branch, or move a
commit to its own branch when ownership should change:

```bash
but rub <commit-id> recipient-follow-up
```

For review fixes, keep the fix as a separate, focused commit first. Move or
combine it with the author branch only after the author accepts that scope. Do
not rewrite another agent's commits merely to make the history look tidy.

If work depends on another lane, make that relationship a GitButler stack:

```bash
but branch new foundation
# Commit the shared foundation before starting dependent work.
but branch new api-on-foundation --anchor foundation
```

Finish and publish stack branches from foundation to dependents. Refresh the
workspace with `but pull` after an upstream branch lands.

## Resolve Collisions

When two agents need the same file, stop both from staging that file. Choose one
owner, split non-overlapping hunks with `but stage`, or sequence the work. If
the branches conflict after `but pull`, let the branch owner resolve it using
`but resolve`; do not have multiple agents edit conflict markers at once.

If work lands on the wrong branch, inspect first, snapshot if the move is
non-trivial, then use `but rub <commit> <branch>` or the precise command from
`but --help`. Recover a mistaken operation with `but undo` or a named oplog
snapshot rather than discarding source changes.

## Completion Checklist

Before declaring multi-agent work complete:

- Confirm every intended change is assigned and committed to its owner branch.
- Confirm no lane contains unrelated work from another agent.
- Run the relevant validation for each lane and report it with the handoff.
- Inspect branch relationships before publishing; push or open reviews only
  with user authorization.
- Preserve the snapshot until the work is integrated and the workspace is
  confirmed healthy.
