"""Shared stdin reader for Claude Code hook scripts.

Claude Code pipes a JSON payload to each hook on stdin. These helpers read it
and degrade gracefully — a parse error must never block the tool, so every
failure path returns an empty payload instead of raising.
"""

from __future__ import annotations

import json
import re
import sys


def read_hook_input() -> dict:
    """Parse the JSON payload piped on stdin. Returns {} on any failure."""
    try:
        raw = sys.stdin.read().strip()
    except Exception:
        return {}

    if not raw:
        return {}

    try:
        parsed = json.loads(raw)
    except Exception:
        return {}

    return parsed if isinstance(parsed, dict) else {}


def target_path(payload: dict) -> str | None:
    """The file path a tool is touching, regardless of which field carries it."""
    tool_input = payload.get("tool_input") or {}
    raw = tool_input.get("file_path") or tool_input.get("notebook_path") or tool_input.get("path")

    return raw if isinstance(raw, str) and raw else None


def bash_command(payload: dict) -> str:
    """The Bash command string a tool is about to run."""
    raw = (payload.get("tool_input") or {}).get("command")

    return raw if isinstance(raw, str) else ""


_ENV_SECRET = re.compile(r"^\.env(\..+)?$")


def is_env_secret(base: str) -> bool:
    """True for a real .env secret file, but not the committable .env.example."""
    return bool(_ENV_SECRET.match(base)) and base != ".env.example"


def emit_context(additional_context: str) -> None:
    """Inject non-blocking context for the agent (PreToolUse additionalContext)."""
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "additionalContext": additional_context,
            }
        },
        sys.stdout,
    )


def emit_decision(decision: str, reason: str) -> None:
    """Emit a PreToolUse permission decision (allow / ask / deny) and exit."""
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": decision,
                "permissionDecisionReason": reason,
            }
        },
        sys.stdout,
    )
    sys.exit(0)


def segments(cmd: str) -> list[str]:
    """Split a shell command into segments at command-position separators."""
    parts = re.split(r"\n|;|&&|\|\||[|&]", cmd)

    return [seg.strip() for seg in parts if seg.strip()]
