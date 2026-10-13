#!/usr/bin/env python3
"""Inspect merge conflicts for an agent; never touches the index or HEAD.

The only writes are backup copies placed inside the repository's git dir.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

SIDES = {
    "merge": (
        "current branch (HEAD)",
        "incoming branch (MERGE_HEAD)",
        "MERGE_HEAD",
    ),
    "rebase": (
        "upstream being rebased onto (HEAD)",
        "your commit being replayed (REBASE_HEAD)",
        "REBASE_HEAD",
    ),
    "cherry-pick": (
        "current branch (HEAD)",
        "commit being picked (CHERRY_PICK_HEAD)",
        "CHERRY_PICK_HEAD",
    ),
    "revert": (
        "current branch (HEAD)",
        "inverse of the commit being reverted (REVERT_HEAD)",
        "REVERT_HEAD",
    ),
    None: ("current branch (HEAD)", "stash or other incoming change", None),
}
STAGE_KINDS = {
    frozenset({1, 2, 3}): "both-modified",
    frozenset({2, 3}): "both-added",
    frozenset({1, 3}): "deleted-by-us",
    frozenset({1, 2}): "deleted-by-them",
    frozenset({2}): "added-by-us",
    frozenset({3}): "added-by-them",
    frozenset({1}): "both-deleted",
}
TEXT_KINDS = {"both-modified", "both-added"}
OPEN = re.compile(r"(<{7,})(?: (.*))?")


class GitError(Exception):
    pass


def run(repo, *args, check=True):
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, check=False
    )
    if check and result.returncode != 0:
        message = result.stderr.decode(errors="replace").strip()
        raise GitError(f"git {' '.join(args)} failed: {message}")
    return result


def out(repo, *args, check=True):
    return run(repo, *args, check=check).stdout.decode(errors="replace").strip()


def toplevel(start):
    return Path(out(start, "rev-parse", "--show-toplevel"))


def gitdir(repo):
    return Path(out(repo, "rev-parse", "--absolute-git-dir"))


def resolve(repo, name):
    result = run(
        repo, "rev-parse", "--verify", "--quiet", f"{name}^{{commit}}", check=False
    )
    return result.stdout.decode().strip() if result.returncode == 0 else None


def describe(repo, sha):
    if sha is None:
        return None
    subject = out(repo, "show", "-s", "--format=%s", sha)
    return {"sha": sha, "short": sha[:10], "subject": subject}


def detect_operation(git_dir):
    if (git_dir / "rebase-merge").is_dir() or (git_dir / "rebase-apply").is_dir():
        return "rebase"
    for marker, operation in (
        ("MERGE_HEAD", "merge"),
        ("CHERRY_PICK_HEAD", "cherry-pick"),
        ("REVERT_HEAD", "revert"),
    ):
        if (git_dir / marker).exists():
            return operation
    return None


def unmerged(repo):
    """Map each unmerged path to its sorted index stages."""
    raw = run(repo, "ls-files", "-u", "-z").stdout.decode(errors="surrogateescape")
    stages = {}
    for entry in filter(None, raw.split("\0")):
        meta, path = entry.split("\t", 1)
        stages.setdefault(path, set()).add(int(meta.split()[2]))
    return {path: sorted(found) for path, found in sorted(stages.items())}


def kind_of(stages):
    return STAGE_KINDS.get(frozenset(stages), "unknown")


def read_worktree(repo, path):
    file = Path(repo) / path
    if not file.is_file():
        return None
    return file.read_bytes()


def decode(data):
    return data.decode("utf-8", errors="surrogateescape")


def hint_for(ours, base, theirs):
    squash = lambda lines: [" ".join(line.split()) for line in lines]  # noqa: E731
    if ours == theirs:
        return "identical"
    if base is not None and ours == base:
        return "take-theirs"
    if base is not None and theirs == base:
        return "take-ours"
    if squash(ours) == squash(theirs):
        return "whitespace-only"
    if not ours or not theirs:
        return "one-side-empty"
    return "both-changed"


def parse_conflicts(text):
    """Parse conflict hunks, honoring marker length, diff3 and zdiff3 styles."""
    hunks, errors = [], []
    current = None
    for number, raw in enumerate(text.split("\n"), 1):
        line = raw.rstrip("\r")
        if current is None:
            match = OPEN.fullmatch(line)
            if match:
                current = {
                    "start_line": number,
                    "size": len(match[1]),
                    "ours_label": match[2] or "",
                    "base_label": "",
                    "theirs_label": "",
                    "section": "ours",
                    "ours": [],
                    "base": None,
                    "theirs": [],
                }
            continue
        size, section = current["size"], current["section"]
        base_marker = re.fullmatch(rf"\|{{{size}}}(?: (.*))?", line)
        close_marker = re.fullmatch(rf">{{{size}}}(?: (.*))?", line)
        if section == "ours" and base_marker:
            current.update(section="base", base=[], base_label=base_marker[1] or "")
        elif section in {"ours", "base"} and line == "=" * size:
            current["section"] = "theirs"
        elif section == "theirs" and close_marker:
            current["theirs_label"] = close_marker[1] or ""
            hunks.append(finish(current, number, len(hunks) + 1))
            current = None
        else:
            current[section].append(raw)
    if current is not None:
        errors.append(f"unterminated conflict starting at line {current['start_line']}")
    return hunks, errors


def finish(current, end_line, index):
    ours, base, theirs = current["ours"], current["base"], current["theirs"]
    return {
        "index": index,
        "start_line": current["start_line"],
        "end_line": end_line,
        "ours_label": current["ours_label"],
        "base_label": current["base_label"],
        "theirs_label": current["theirs_label"],
        "ours": ours,
        "base": base,
        "theirs": theirs,
        "hint": hint_for(ours, base, theirs),
    }


def stage_blob(repo, path, stage):
    result = run(repo, "show", f":{stage}:{path}", check=False)
    return result.stdout if result.returncode == 0 else None


def diff3_from_stages(repo, path, stages):
    """Rebuild diff3 markers from index stages without touching the worktree."""
    blobs = {stage: stage_blob(repo, path, stage) for stage in (1, 2, 3)}
    if blobs[2] is None or blobs[3] is None:
        return None
    blobs[1] = blobs[1] if blobs[1] is not None else b""
    with tempfile.TemporaryDirectory() as scratch:
        paths = []
        for name, stage in (("ours", 2), ("base", 1), ("theirs", 3)):
            file = Path(scratch) / name
            file.write_bytes(blobs[stage])
            paths.append(str(file))
        merged = subprocess.run(
            [
                "git",
                "merge-file",
                "-p",
                "--diff3",
                "-L",
                "ours",
                "-L",
                "base",
                "-L",
                "theirs",
                *paths,
            ],
            capture_output=True,
            check=False,
        )
    if merged.returncode < 0 or merged.returncode > 127:
        return None
    return decode(merged.stdout)


def file_hunks(repo, path, stages, source):
    data = read_worktree(repo, path)
    if data is not None and b"\0" in data:
        return {"path": path, "binary": True, "hunks": [], "errors": []}
    kind = kind_of(stages)
    if kind not in TEXT_KINDS:
        return {"path": path, "kind": kind, "hunks": [], "errors": []}
    worktree_text = decode(data) if data is not None else ""
    hunks, errors = parse_conflicts(worktree_text)
    used = "worktree"
    has_base = all(hunk["base"] is not None for hunk in hunks)
    if source == "stages" or (source == "auto" and hunks and not has_base):
        rebuilt = diff3_from_stages(repo, path, stages)
        if rebuilt is not None:
            hunks, errors = parse_conflicts(rebuilt)
            used = "stages"
    return {
        "path": path,
        "kind": kind,
        "source": used,
        "hunks": hunks,
        "errors": errors,
    }


def state_report(repo):
    git_dir = gitdir(repo)
    operation = detect_operation(git_dir)
    ours_label, theirs_label, incoming_ref = SIDES[operation]
    conflicts = []
    for path, stages in unmerged(repo).items():
        data = read_worktree(repo, path)
        entry = {"path": path, "kind": kind_of(stages), "stages": stages}
        if data is not None and b"\0" in data:
            entry.update(binary=True, hunks=None, errors=[])
        else:
            parsed = file_hunks(repo, path, stages, "worktree")
            entry.update(
                binary=False,
                hunks=len(parsed["hunks"]) if entry["kind"] in TEXT_KINDS else None,
                errors=parsed["errors"],
            )
        entry["needs_decision"] = entry["kind"] not in TEXT_KINDS or entry["binary"]
        conflicts.append(entry)
    return {
        "repo": str(repo),
        "operation": operation,
        "head": describe(repo, resolve(repo, "HEAD")),
        "incoming": describe(
            repo, resolve(repo, incoming_ref) if incoming_ref else None
        ),
        "sides": {"ours": ours_label, "theirs": theirs_label},
        "conflicts": conflicts,
    }


def find_commits(repo, subject):
    refs = [
        name
        for name in (
            "HEAD",
            "MERGE_HEAD",
            "REBASE_HEAD",
            "CHERRY_PICK_HEAD",
            "ORIG_HEAD",
        )
        if resolve(repo, name)
    ]
    raw = out(
        repo,
        "log",
        "--all",
        *refs,
        "--fixed-strings",
        f"--grep={subject}",
        "-n",
        "50",
        "--format=%H%x1f%s",
    )
    found = []
    for line in filter(None, raw.splitlines()):
        sha, title = line.split("\x1f", 1)
        found.append((sha, title))
    exact = [item for item in found if item[1].strip() == subject.strip()]
    seen, unique = set(), []
    for sha, title in exact or found:
        if sha not in seen:
            seen.add(sha)
            unique.append((sha, title))
    return unique


def contains(repo, sha, ref):
    if ref is None or resolve(repo, ref) is None:
        return None
    result = run(repo, "merge-base", "--is-ancestor", sha, ref, check=False)
    return result.returncode == 0


def history(repo, spec, path):
    raw = out(
        repo, "log", "-n", "8", "--format=%h %an: %s", spec, "--", path, check=False
    )
    return raw.splitlines()


def intent_report(repo, subject):
    state = state_report(repo)
    conflicted = [entry["path"] for entry in state["conflicts"]]
    _, _, incoming_ref = SIDES[state["operation"]]
    report = {"operation": state["operation"], "sides": state["sides"], "commits": []}
    for sha, title in find_commits(repo, subject) if subject else []:
        files = out(
            repo, "diff-tree", "--no-commit-id", "--name-only", "-r", sha
        ).splitlines()
        report["commits"].append(
            {
                "sha": sha,
                "short": sha[:10],
                "subject": title,
                "body": out(repo, "show", "-s", "--format=%b", sha),
                "on_ours_side": contains(repo, sha, "HEAD"),
                "on_theirs_side": contains(repo, sha, incoming_ref),
                "files": files,
                "touches_conflicts": [path for path in files if path in conflicted],
            }
        )
    base = None
    if incoming_ref and resolve(repo, incoming_ref):
        base = out(repo, "merge-base", "HEAD", incoming_ref, check=False) or None
    per_file = {}
    for path in conflicted:
        if base:
            per_file[path] = {
                "ours_commits": history(repo, f"{base}..HEAD", path),
                "theirs_commits": history(repo, f"{base}..{incoming_ref}", path),
            }
    report["merge_base"] = base
    report["history"] = per_file
    report["found_user_commit"] = bool(report["commits"]) if subject else None
    return report


def backup(repo):
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    target = gitdir(repo) / "conflict-backups" / stamp
    copied = []
    for path in unmerged(repo):
        source = Path(repo) / path
        if not source.is_file():
            continue
        destination = target / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        copied.append(path)
    return {"backup_dir": str(target), "files": copied}


def verify(repo, expected_head):
    problems, remaining, needs_decision, clean = [], [], [], []
    head = resolve(repo, "HEAD")
    if (
        expected_head
        and head
        and not head.startswith(expected_head)
        and not expected_head.startswith(head)
    ):
        problems.append(f"HEAD moved: expected {expected_head}, found {head}")
    for path, stages in unmerged(repo).items():
        kind = kind_of(stages)
        data = read_worktree(repo, path)
        if kind not in TEXT_KINDS or (data is not None and b"\0" in data):
            needs_decision.append({"path": path, "kind": kind})
            continue
        hunks, errors = parse_conflicts(decode(data or b""))
        if hunks or errors:
            remaining.append(
                {
                    "path": path,
                    "hunks": [h["start_line"] for h in hunks],
                    "errors": errors,
                }
            )
        else:
            clean.append(path)
    ok = not problems and not remaining
    return {
        "ok": ok,
        "problems": problems,
        "markers_remaining": remaining,
        "needs_decision": needs_decision,
        "marker_free": clean,
        "head": head,
    }


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="repository path (default: cwd)")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("state", help="operation, sides and conflicted files")
    hunks = sub.add_parser("hunks", help="parsed conflict hunks per file")
    hunks.add_argument("paths", nargs="*", help="default: every unmerged text file")
    hunks.add_argument(
        "--source", choices=("auto", "worktree", "stages"), default="auto"
    )
    intent = sub.add_parser("intent", help="locate the user's commit and side history")
    intent.add_argument("subject", nargs="?", help="exact commit subject")
    sub.add_parser("backup", help="copy conflicted files into the git dir")
    check = sub.add_parser("verify", help="fail if conflict markers remain")
    check.add_argument("--head", help="HEAD sha recorded by `state`; fail if it moved")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        repo = toplevel(args.repo)
        if args.command == "state":
            report = state_report(repo)
        elif args.command == "hunks":
            table = unmerged(repo)
            paths = args.paths or [
                path for path, stages in table.items() if kind_of(stages) in TEXT_KINDS
            ]
            unknown = [path for path in paths if path not in table]
            if unknown:
                raise GitError(f"not unmerged: {', '.join(unknown)}")
            report = [
                file_hunks(repo, path, table[path], args.source) for path in paths
            ]
        elif args.command == "intent":
            report = intent_report(repo, args.subject)
        elif args.command == "backup":
            report = backup(repo)
        else:
            report = verify(repo, args.head)
    except GitError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2))
    if args.command == "verify" and not report["ok"]:
        return 1
    if args.command == "intent" and args.subject and not report["found_user_commit"]:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
