# GitButler Commit Recovery


The helper requires Python 3. It takes a nonblocking, repository-wide lock
shared by cooperating helper invocations and refuses an existing Git index
lock before calling GitButler. It never removes an index lock. This does not
lock out GitButler's GUI or agents bypassing the helper.

Before any GitButler call, it saves dirty tracked and untracked file content,
symlink targets, file modes, and deletion state in a private directory under
`<git-common-dir>/kamaal-super-mind/recovery-*/workspace.json`. The backup path
is printed and retained on success and failure; do not commit these backups.
They may contain private working files, so keep the directory private.

On failure, if HEAD is unchanged, it restores previously present files that
are missing or whose regular-file bytes exactly match the captured HEAD
version. It preserves differing content, changed parent symlinks, and changed
HEAD states for manual recovery from the printed backup. A newer edit equal
to HEAD cannot be distinguished from a revert; inspect the recovery report.
The manifest stores regular-file bytes as hex, alongside the original path,
mode, or symlink target. Resolve remaining recovery gaps before stopping.
Never reset, discard, run setup, delete a lock, or retry a mutation blindly.

A user request to commit authorizes committing its resolved scope and creating
a missing task branch. Do not ask again merely because no branch is applied.
After a failure, report the exact error and recovery result. Investigate lock
ownership and retry only after the blocking condition is resolved.
