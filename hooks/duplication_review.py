#!/usr/bin/env python3
"""Request one in-context duplication review per user request on local hosts."""

import argparse
import fcntl
import hashlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

MARKER = "[kamaal-super-mind:duplication-review:v1]"
SKILL = Path(__file__).resolve().parents[1] / "skills/refactor-pr-duplication/SKILL.md"


def git(directory, *arguments, check=True):
    return subprocess.run(
        ["git", "-C", str(directory), *arguments],
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
        capture_output=True,
        check=check,
        timeout=5,
    )


def repositories(payload, host):
    directories = payload.get("workspace_roots", [])
    if host != "cursor":
        directories = [payload.get("cwd")]
    if not isinstance(directories, list):
        raise ValueError("workspace_roots must be an array")
    roots = set()
    for directory in directories:
        if not isinstance(directory, str) or not directory:
            continue
        result = git(directory, "rev-parse", "--show-toplevel", check=False)
        if result.returncode == 0:
            roots.add(os.fsdecode(result.stdout.strip()))
        elif not Path(directory).is_dir():
            raise ValueError("workspace directory is unavailable")
    return sorted(roots)


def paths(output):
    return [os.fsdecode(path) for path in output.split(b"\0") if path]


def snapshot(root):
    head_result = git(root, "rev-parse", "--verify", "HEAD", check=False)
    head = head_result.stdout.decode().strip() if head_result.returncode == 0 else None
    digest = hashlib.sha256()
    digest.update(json.dumps(head).encode())
    dirty_paths = set()
    for options in ([], ["--cached"]):
        diff = git(root, "diff", *options, "--no-ext-diff", "--no-textconv", "--binary")
        digest.update(len(diff.stdout).to_bytes(8, "big"))
        digest.update(diff.stdout)
        dirty_paths.update(
            paths(git(root, "diff", *options, "--name-only", "-z").stdout)
        )
    untracked = paths(
        git(root, "ls-files", "--others", "--exclude-standard", "-z").stdout
    )
    for name in sorted(untracked):
        path = Path(root) / name
        metadata = path.lstat()
        file_digest = hashlib.sha256()
        file_digest.update(
            str(stat.S_IFMT(metadata.st_mode) | (metadata.st_mode & 0o111)).encode()
        )
        if stat.S_ISLNK(metadata.st_mode):
            file_digest.update(os.fsencode(os.readlink(path)))
        elif stat.S_ISREG(metadata.st_mode):
            with path.open("rb") as source:
                for chunk in iter(lambda: source.read(65536), b""):
                    file_digest.update(chunk)
        else:
            continue
        digest.update(os.fsencode(name) + b"\0" + file_digest.digest())
        dirty_paths.add(name)
    return {
        "head": head,
        "fingerprint": digest.hexdigest(),
        "dirty_paths": sorted(dirty_paths),
    }


def review_prompt(changed):
    baselines = {
        root: {
            "head": baseline["head"],
            "preexisting_dirty_paths": baseline["dirty_paths"],
        }
        for root, baseline in changed.items()
    }
    return (
        f"{MARKER}\n"
        "Check whether the implementation requested by the user is completed. "
        "If this turn is planning, answering a question, awaiting user input or approval, "
        "blocked, or has no task-owned code changes, stop without refactoring. "
        "Otherwise read and follow the duplication skill at "
        f"{json.dumps(str(SKILL))}. "
        "Review this task's code changes, including local commits and uncommitted files. "
        "If the final changes were already reviewed with this skill, do not repeat the review. "
        "Search the codebase for equivalent logic, reuse or extract shared implementations "
        "where worthwhile, preserve behavior, and run the affected checks and the "
        "repository-required final verification. "
        "Use the conversation and the repository's Git/GitButler workflow to establish "
        "task and branch ownership; do not modify unrelated or pre-existing work. "
        "Do not assume HEAD is the task's virtual branch in GitButler. "
        "Do not commit, push, or publish unless the user's request already authorizes it. "
        "Report what was reused or extracted and the verification result, or that no "
        "duplication warranted a refactor. This is the single automatic review for this "
        "request; finish after the review and verification. "
        "The following request-start metadata identifies candidate scope, not ownership: "
        f"{json.dumps(baselines, ensure_ascii=True)}."
    )


def allow_response(payload, host):
    if (
        host == "cursor"
        and isinstance(payload, dict)
        and payload.get("hook_event_name") == "beforeSubmitPrompt"
    ):
        return {"continue": True}
    return {}


def handle(payload, host):
    if not isinstance(payload, dict):
        raise ValueError("hook input must be a JSON object")
    event = payload.get("hook_event_name")
    prompt_event = "beforeSubmitPrompt" if host == "cursor" else "UserPromptSubmit"
    stop_event = "stop" if host == "cursor" else "Stop"
    allowed = allow_response(payload, host)
    if os.environ.get("KAMAAL_SUPER_MIND_DUPLICATION_REVIEW") == "0":
        return allowed
    if event not in (prompt_event, stop_event):
        return allowed
    prompt = payload.get("prompt", "")
    if event == prompt_event and isinstance(prompt, str) and prompt.startswith(MARKER):
        return allowed
    if event == stop_event and (
        payload.get("status") in ("aborted", "error")
        or payload.get("permission_mode") == "plan"
    ):
        return allowed
    session = (
        payload.get("conversation_id")
        if host == "cursor"
        else payload.get("session_id")
    )
    if not isinstance(session, str) or not session:
        raise ValueError("hook input is missing a conversation/session id")
    roots = repositories(payload, host)
    if not roots:
        return allowed
    cache = Path(os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache")))
    if not cache.is_absolute():
        cache = Path.home() / ".cache"
    directory = cache / "kamaal-super-mind/hooks"
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    identity = hashlib.sha256(f"{host}\0{session}".encode()).hexdigest()
    state_path = directory / f"{identity}.json"
    descriptor = os.open(state_path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "r+", encoding="utf-8") as state_file:
        fcntl.flock(state_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if event == prompt_event:
            state_file.truncate(0)
            state_file.flush()
            state = {
                "requested": False,
                "repositories": {root: snapshot(root) for root in roots},
            }
            result = allowed
        else:
            contents = state_file.read()
            state = json.loads(contents) if contents else {}
            if state.get("requested") or not state.get("repositories"):
                return allowed
            changed = {
                root: baseline
                for root, baseline in state["repositories"].items()
                if root in roots
                and snapshot(root)["fingerprint"] != baseline["fingerprint"]
            }
            if not changed:
                return allowed
            state["requested"] = True
            prompt = review_prompt(changed)
            result = (
                {"followup_message": prompt}
                if host == "cursor"
                else {
                    "decision": "block",
                    "reason": prompt,
                }
            )
        state_file.seek(0)
        json.dump(state, state_file)
        state_file.truncate()
        state_file.flush()
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("host", choices=("codex", "claude", "cursor"))
    arguments = parser.parse_args()
    result = {}
    try:
        payload = json.load(sys.stdin)
        result = allow_response(payload, arguments.host)
        result = handle(payload, arguments.host)
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        AttributeError,
        subprocess.SubprocessError,
    ) as error:
        print(
            f"Kamaal Super Mind duplication review hook skipped: {error}",
            file=sys.stderr,
        )
    print(json.dumps(result))


if __name__ == "__main__":
    main()
