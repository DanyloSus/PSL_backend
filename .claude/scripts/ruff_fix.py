#!/usr/bin/env python3
"""PostToolUse(Edit|Write) — auto-fix the single file just edited.

Mechanises lint-scope LS1: ruff runs on the changed file only, never the whole
repo. Only .py files inside the project (not .venv) are touched. Always exits 0
— a lint failure must never block the tool; the user's own `uv run ruff check`
/ CI owns hard enforcement.
"""

from __future__ import annotations

import contextlib
import os
import subprocess
import sys

from _hook_input import read_hook_input, target_path


def main() -> int:
    payload = read_hook_input()
    raw = target_path(payload)

    if not raw:
        return 0

    file = raw.replace("\\", "/")
    if not file.endswith(".py") or "/.venv/" in file:
        return 0

    cwd = payload.get("cwd") or os.getcwd()
    path = file if os.path.isabs(file) else os.path.join(cwd, file)

    for args in (
        ["uv", "run", "ruff", "check", "--fix", path],
        ["uv", "run", "ruff", "format", path],
    ):
        with contextlib.suppress(Exception):
            subprocess.run(
                args,
                cwd=cwd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=13,
                check=False,
            )

    return 0


if __name__ == "__main__":
    sys.exit(main())
