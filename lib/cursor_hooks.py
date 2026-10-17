#!/usr/bin/env python3
"""Merge native user hooks for Cursor desktop and CLI without replacing user hooks."""

import argparse
import json
import os
import shlex
import sys
import tempfile
from pathlib import Path


def configure(action, plugin):
    config = Path.home() / ".cursor/hooks.json"
    if config.is_symlink():
        raise ValueError("symlinked configuration must be managed manually")
    if action == "uninstall" and not config.exists():
        return
    document = json.loads(config.read_text()) if config.exists() else {"version": 1}
    if not isinstance(document, dict) or document.get("version", 1) != 1:
        raise ValueError("expected a version 1 JSON object")
    if action == "uninstall" and "hooks" not in document:
        return
    hooks = document.get("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError("hooks must be an object")
    for event, entries in hooks.items():
        if not isinstance(entries, list) or not all(
            isinstance(entry, dict) for entry in entries
        ):
            raise ValueError(f"{event} hooks must be an array of objects")
    command = (
        f"python3 {shlex.quote(str(plugin / 'hooks/duplication_review.py'))} cursor"
    )
    original = json.dumps(document, sort_keys=True)
    for event in ("beforeSubmitPrompt", "stop"):
        entries = [
            entry for entry in hooks.get(event, []) if entry.get("command") != command
        ]
        if action == "install":
            entry = {"command": command, "timeout": 30}
            if event == "stop":
                entry["loop_limit"] = None
            entries.append(entry)
        if entries:
            hooks[event] = entries
        else:
            hooks.pop(event, None)
    document["hooks"] = hooks
    if action == "install":
        document["version"] = 1
    if json.dumps(document, sort_keys=True) == original:
        return
    config.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".hooks-", dir=config.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            json.dump(document, output, indent=2)
            output.write("\n")
        if config.exists():
            os.chmod(temporary, config.stat().st_mode & 0o777)
        os.replace(temporary, config)
    finally:
        Path(temporary).unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("install", "uninstall"))
    parser.add_argument("plugin", type=Path)
    arguments = parser.parse_args()
    try:
        configure(arguments.action, arguments.plugin.absolute())
    except (OSError, ValueError, TypeError) as error:
        print(
            f"Error: Cursor hooks configuration was not changed: {error}",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
