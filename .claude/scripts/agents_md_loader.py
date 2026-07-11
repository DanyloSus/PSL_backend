#!/usr/bin/env python3
"""PreToolUse(Read|Edit|Write|Glob|Grep|NotebookEdit) — auto-load the nearest
subdirectory AGENTS.md when Claude touches a file in that subtree.

For each tool call: resolve the target path, walk up to the repo root collecting
every AGENTS.md (nearest-first), skip the root one (CLAUDE.md already loads it),
and inject each not-yet-seen AGENTS.md into context. Per-session dedup lives in
~/.cache/claude/agents-loaded/<session_id>.txt so a file is injected at most
once per session. Never blocks — every error path exits 0.
"""

from __future__ import annotations

import os
import sys

from _hook_input import emit_context, read_hook_input, target_path

CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "claude", "agents-loaded")


def repo_root(start: str) -> str | None:
    cur = start if os.path.isdir(start) else os.path.dirname(start)
    while True:
        if os.path.exists(os.path.join(cur, ".git")) or os.path.exists(
            os.path.join(cur, ".claude")
        ):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            return None
        cur = parent


def walk_agents_md(start: str, root: str) -> list[str]:
    out: list[str] = []
    cur = start if os.path.isdir(start) else os.path.dirname(start)

    rel = os.path.relpath(cur, root)
    if rel != "." and rel.startswith(".."):
        return out

    while True:
        candidate = os.path.join(cur, "AGENTS.md")
        if cur != root and os.path.exists(candidate):
            out.append(candidate)
        if cur == root or os.path.dirname(cur) == cur:
            break
        cur = os.path.dirname(cur)

    return out


def load_seen(state_file: str) -> set[str]:
    try:
        with open(state_file, encoding="utf8") as handle:
            return {line.strip() for line in handle if line.strip()}
    except Exception:
        return set()


def mark_seen(state_file: str, paths: list[str]) -> None:
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(state_file, "a", encoding="utf8") as handle:
            handle.write("".join(f"{p}\n" for p in paths))
    except Exception:
        pass


def format_block(file_path: str, root: str, content: str) -> str:
    rel = os.path.relpath(file_path, root)
    return (
        f"# Auto-loaded subdirectory AGENTS.md\n"
        f"# Path: {rel}\n"
        f"# (injected because this tool call touches the {os.path.dirname(rel)} "
        f"subtree; shown at most once per session)\n\n"
        f"{content.rstrip()}\n"
    )


def main() -> int:
    payload = read_hook_input()
    session_id = payload.get("session_id") or payload.get("sessionId")
    if not session_id:
        return 0

    cwd = payload.get("cwd") or os.getcwd()
    raw = target_path(payload)
    if not raw:
        return 0

    target = raw if os.path.isabs(raw) else os.path.abspath(os.path.join(cwd, raw))
    root = repo_root(target) or repo_root(cwd)
    if not root:
        return 0

    candidates = walk_agents_md(target, root)
    if not candidates:
        return 0

    state_file = os.path.join(CACHE_DIR, f"{session_id}.txt")
    seen = load_seen(state_file)
    fresh = [c for c in candidates if c not in seen]
    if not fresh:
        return 0

    blocks: list[str] = []
    loaded: list[str] = []
    for candidate in fresh:
        try:
            with open(candidate, encoding="utf8") as handle:
                content = handle.read()
            if content.strip():
                blocks.append(format_block(candidate, root, content))
                loaded.append(candidate)
        except Exception:
            continue

    if not blocks:
        return 0

    mark_seen(state_file, loaded)
    emit_context("\n\n---\n\n".join(blocks))

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
