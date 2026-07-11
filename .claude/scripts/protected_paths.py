#!/usr/bin/env python3
"""PreToolUse(Edit|Write) guard for PSL protected areas (AGENTS.md §4a).

Auth, security, cookies, config, DB engine, app wiring, and migration
infrastructure have app-wide blast radius, so the FIRST edit to one must be a
deliberate, confirmed choice.

Behaviour:
  - Protected files → ask ONCE per file per session via a permissionDecision
    "ask". After the first prompt for a given path, later edits pass through.
  - .env secret files → hard "deny" (use .env.example templates instead).
  - Anything else → allow (exit 0).
"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile

from _hook_input import emit_decision, is_env_secret, read_hook_input, target_path

PROTECTED = [
    re.compile(r"/app/core/security\.py$"),
    re.compile(r"/app/core/cookies\.py$"),
    re.compile(r"/app/core/config\.py$"),
    re.compile(r"/app/core/db\.py$"),
    re.compile(r"/app/core/dependencies\.py$"),
    re.compile(r"/app/main\.py$"),
    re.compile(r"/app/migrations/env\.py$"),
    re.compile(r"/app/migrations/versions/.+\.py$"),
    re.compile(r"/alembic\.ini$"),
    re.compile(r"/pyproject\.toml$"),
    re.compile(r"/\.pre-commit-config\.yaml$"),
    re.compile(r"/\.github/workflows/.+\.ya?ml$"),
]


def marker_file(session_id: str | None) -> str:
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", session_id or "default")

    return os.path.join(tempfile.gettempdir(), f"claude-protected-asked-{safe}.json")


def already_asked(path_file: str, path: str) -> bool:
    try:
        with open(path_file, encoding="utf8") as handle:
            asked = json.load(handle)
        return isinstance(asked, list) and path in asked
    except Exception:
        return False


def record_asked(path_file: str, path: str) -> None:
    try:
        asked: list[str] = []
        try:
            with open(path_file, encoding="utf8") as handle:
                parsed = json.load(handle)
            asked = parsed if isinstance(parsed, list) else []
        except Exception:
            asked = []
        asked.append(path)
        with open(path_file, "w", encoding="utf8") as handle:
            json.dump(asked, handle)
    except Exception:
        pass  # best-effort; worst case we ask again next time


def main() -> int:
    payload = read_hook_input()
    raw = target_path(payload)

    if not raw:
        return 0

    path = raw.replace("\\", "/")
    base = path.split("/")[-1]

    if is_env_secret(base):
        emit_decision("deny", "Cannot edit .env files (use .env.example templates only).")

    if any(pattern.search(path) for pattern in PROTECTED):
        path_file = marker_file(payload.get("session_id"))
        if already_asked(path_file, path):
            return 0
        record_asked(path_file, path)
        emit_decision("ask", f"{base} is a protected file (AGENTS.md §4a). Can I change it?")

    return 0


if __name__ == "__main__":
    sys.exit(main())
