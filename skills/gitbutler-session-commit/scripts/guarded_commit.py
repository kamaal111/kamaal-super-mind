#!/usr/bin/env python3
"""Preserve dirty workspace files around a selected GitButler commit."""

import fcntl
import json
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path


def git(*args):
    return subprocess.check_output(
        ["git", *args], env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"}
    )


def state(path):
    if path.is_symlink():
        return {"kind": "symlink", "target": os.readlink(path)}
    if not path.exists():
        return {"kind": "missing"}
    if not path.is_file():
        raise RuntimeError(f"Cannot protect non-file path: {path}")
    return {
        "kind": "file",
        "data": path.read_bytes().hex(),
        "mode": stat.S_IMODE(path.stat().st_mode),
    }


def snapshot(root, directory):
    paths = set()
    for args in (
        ("diff", "--name-only", "-z", "HEAD", "--"),
        ("ls-files", "--others", "--exclude-standard", "-z"),
    ):
        paths.update(os.fsdecode(p) for p in git(*args).split(b"\0") if p)
    records = {}
    for name in sorted(paths):
        path = root / name
        if not path.parent.resolve().is_relative_to(root):
            raise RuntimeError(f"Cannot protect path outside workspace: {name}")
        before = state(path)
        baseline = subprocess.run(
            ["git", "show", f"HEAD:{name}"], capture_output=True, check=False
        )
        records[name] = {
            "before": before,
            "baseline": baseline.stdout.hex() if baseline.returncode == 0 else None,
        }
    manifest = {
        "root": str(root),
        "head": git("rev-parse", "HEAD").decode().strip(),
        "files": records,
    }
    with (directory / "workspace.json").open("x") as output:
        json.dump(manifest, output)
        output.flush()
        os.fsync(output.fileno())
    return manifest


def recover(root, manifest):
    if git("rev-parse", "HEAD").decode().strip() != manifest["head"]:
        print(
            "HEAD changed; preserve current files and recover from the backup.",
            file=sys.stderr,
        )
        return
    for name, record in manifest["files"].items():
        path = root / name
        if not path.parent.resolve().is_relative_to(root):
            print(f"Preserved changed parent path: {name}", file=sys.stderr)
            continue
        before = record["before"]
        current = state(path)
        if current == before:
            continue
        reverted = (
            current["kind"] == "file"
            and record["baseline"] is not None
            and current["data"] == record["baseline"]
        )
        if before["kind"] == "missing" or not (
            current["kind"] == "missing" or reverted
        ):
            print(
                f"Preserved differing content: {name}; original is in backup.",
                file=sys.stderr,
            )
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        if before["kind"] == "symlink":
            path.unlink(missing_ok=True)
            path.symlink_to(before["target"])
        else:
            descriptor, temporary = tempfile.mkstemp(dir=path.parent)
            try:
                with os.fdopen(descriptor, "wb") as output:
                    output.write(bytes.fromhex(before["data"]))
                os.chmod(temporary, before["mode"])
                os.replace(temporary, path)
            finally:
                Path(temporary).unlink(missing_ok=True)
        print(f"Recovered lost workspace content: {name}", file=sys.stderr)


def commit(branch, message_file, changes):
    root = Path(os.fsdecode(git("rev-parse", "--show-toplevel")).strip()).resolve()
    os.chdir(root)
    common = Path(os.fsdecode(git("rev-parse", "--git-common-dir")).strip()).resolve()
    protection = common / "kamaal-super-mind"
    protection.mkdir(mode=0o700, exist_ok=True)
    with (protection / "commit.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(
                "Another protected GitButler commit is running; retry after it finishes.",
                file=sys.stderr,
            )
            return 1
        index_lock = Path(
            os.fsdecode(git("rev-parse", "--git-path", "index.lock")).strip()
        )
        if index_lock.exists():
            print(
                f"Existing index lock: {index_lock}. No GitButler commands ran. "
                "Do not remove a lock owned by another process.",
                file=sys.stderr,
            )
            return 1
        backup = Path(tempfile.mkdtemp(prefix="recovery-", dir=protection))
        manifest = snapshot(root, backup)
        print(f"Workspace recovery copy: {backup / 'workspace.json'}", file=sys.stderr)
        result = 1
        try:
            if subprocess.run(
                ["but", "status", "--json"], stdout=subprocess.DEVNULL, check=False
            ).returncode:
                print(
                    "GitButler workspace access failed; do not run but setup.",
                    file=sys.stderr,
                )
                return 1
            help_result = subprocess.run(
                ["but", "commit", "--help"], capture_output=True, check=False
            )
            if help_result.returncode or b"[CHANGES]..." not in help_result.stdout:
                print(
                    "Installed GitButler does not expose positional CHANGES.",
                    file=sys.stderr,
                )
                return 1
            result = subprocess.run(
                [
                    "but",
                    "commit",
                    "--branch",
                    branch,
                    "--message",
                    Path(message_file).read_text().rstrip("\n"),
                    *changes,
                ],
                check=False,
            ).returncode
            return result if result >= 0 else 128 - result
        finally:
            if result != 0:
                recover(root, manifest)
                print(
                    f"Commit failed. Recovery copy retained: {backup / 'workspace.json'}",
                    file=sys.stderr,
                )


def main():
    if len(sys.argv) < 4:
        print(
            "Usage: guarded_commit.py <branch> <message-file> <change-id>...",
            file=sys.stderr,
        )
        return 2
    try:
        return commit(sys.argv[1], str(Path(sys.argv[2]).resolve()), sys.argv[3:])
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"Protected GitButler commit failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
