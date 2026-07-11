#!/usr/bin/env python3
"""PreToolUse(Bash) advisory — remind about ADRs on architecture-shaping commits.

NON-BLOCKING. Fires only when a command runs `git commit`. Inspects the staged
file set; if it touches architecture-shaping surfaces (auth/security/deps,
app wiring, a new model, a migration, or a new .claude rule) WITHOUT also
staging a docs/adrs or CLAUDE.md change, it injects a reminder to consider
`/adr`. It never blocks the commit (exit 0 always) — see decision-records rule.

Suppress for a single commit with ADR_SKIP=1 in the environment.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys

from _hook_input import bash_command, emit_context, read_hook_input, segments

SHAPING = [
    re.compile(r"^app/core/security\.py$"),
    re.compile(r"^app/core/dependencies\.py$"),
    re.compile(r"^app/core/cookies\.py$"),
    re.compile(r"^app/main\.py$"),
    re.compile(r"^app/models/.+\.py$"),
    re.compile(r"^app/migrations/versions/.+\.py$"),
    re.compile(r"^\.claude/rules/.+\.md$"),
]
RECORDS = [re.compile(r"^docs/adrs?/"), re.compile(r"^CLAUDE\.md$")]


def is_commit(cmd: str) -> bool:
    return any(re.match(r"^git\b", seg) and re.search(r"\bcommit\b", seg) for seg in segments(cmd))


def staged_files() -> list[str]:
    try:
        out = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout
        return [line.strip() for line in out.splitlines() if line.strip()]
    except Exception:
        return []


def dependency_changed() -> bool:
    try:
        diff = subprocess.run(
            ["git", "diff", "--cached", "--", "pyproject.toml"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout
        return any(
            re.match(r'^[+-]\s*"?[\w.-]+"?\s*[>=<~]', line) and line[0] in "+-"
            for line in diff.splitlines()
            if not line.startswith(("+++", "---"))
        )
    except Exception:
        return False


def main() -> int:
    payload = read_hook_input()
    cmd = bash_command(payload)

    if not cmd or not is_commit(cmd) or os.environ.get("ADR_SKIP") == "1":
        return 0

    staged = staged_files()
    if not staged:
        return 0
    if any(rec.search(f) for f in staged for rec in RECORDS):
        return 0

    hits = [f for f in staged if any(pat.match(f) for pat in SHAPING)]
    if dependency_changed():
        hits.append("pyproject.toml (dependency change)")
    if not hits:
        return 0

    listing = "\n".join(f"  - {f}" for f in hits)
    message = (
        f"This commit stages architecture-shaping changes with no ADR/CLAUDE.md update:\n"
        f"{listing}\n"
        f"If this reflects a decision (auth, layer boundaries, a cross-cutting pattern, "
        f'a core dependency, a schema/migration), record it: run /adr "<title>". '
        f"Skip if it's reversible implementation detail. "
        f"Suppress this reminder for one commit with ADR_SKIP=1."
    )

    sys.stderr.write(f"ADR reminder:\n{message}\n")
    emit_context(message)

    return 0


if __name__ == "__main__":
    sys.exit(main())
