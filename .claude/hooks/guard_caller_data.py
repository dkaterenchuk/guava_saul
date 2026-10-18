#!/usr/bin/env python3
"""PreToolUse hook: block Claude from writing caller-data locations or audio files.

Enforces principle D2 / CLAUDE.md "Never commit real caller data".
Exit code 2 blocks the tool call and shows stderr to Claude.
"""
import json
import sys
from pathlib import PurePath

BLOCKED_DIRS = ("data/raw", "data/calls", "transcripts")
BLOCKED_SUFFIXES = {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm"}


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    path = (payload.get("tool_input") or {}).get("file_path", "")
    if not path:
        return 0
    p = PurePath(path)
    posix = p.as_posix()
    if p.suffix.lower() in BLOCKED_SUFFIXES or any(f"/{d}/" in f"/{posix}" for d in BLOCKED_DIRS):
        print(
            f"Blocked write to {path}: caller data and audio must never be created by Claude "
            "(see docs/compliance/data-handling.md). Use synthetic scenarios in evals/scenarios/.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
