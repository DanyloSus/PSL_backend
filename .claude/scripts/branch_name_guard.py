#!/usr/bin/env python3
"""PreToolUse(Bash) guard — enforce branch naming convention (skill: git-branch).

PSL uses Conventional-Commit-style branch prefixes, matching the stacked-PR
workflow in CLAUDE.md §9 (feat/db-core, chore/scaffold, fix/db-core, ...).
Allowed prefixes: feat | feature | fix | bugfix | chore | refactor | test |
docs | ci | build | perf | hotfix | revert. Format:
    <type>/<kebab-desc>            e.g. feat/activities-engine
    <type>/<TICKET-123>/<kebab>    optional ticket segment

Fires only when a command CREATES or RENAMES a branch with an explicit name
(checkout -b, switch -c/--create, branch -m/-M). Blocks via stderr + exit 2.
Exits 0 on anything it does not recognise.
"""

from __future__ import annotations

import re
import sys

from _hook_input import bash_command, read_hook_input, segments

ALLOWED = [
    "feat",
    "feature",
    "fix",
    "bugfix",
    "chore",
    "refactor",
    "test",
    "docs",
    "ci",
    "build",
    "perf",
    "hotfix",
    "revert",
]
VALID = re.compile(rf"^({'|'.join(ALLOWED)})/([A-Za-z]+-\d+/)?[a-z0-9]+(-[a-z0-9]+)*$")
PROTECTED_BASES = {"main", "develop", "staging"}


def block(name: str) -> None:
    sys.stderr.write(
        f'BLOCKED: branch "{name}" violates naming convention.\n'
        f"Prefix MUST be one of: {' | '.join(ALLOWED)}.\n"
        f"Format: <type>/<kebab-desc>  or  <type>/<TICKET-123>/<kebab-desc>.\n"
        f"Example: feat/activities-engine  ·  fix/refresh-rotation\n"
    )
    sys.exit(2)


def candidate_branch_name(seg: str) -> str | None:
    if not re.match(r"^git\b", seg):
        return None

    tokens = seg.split()

    def flagless(token: str | None) -> bool:
        return bool(token) and not token.startswith("-")

    for flag in ("-b", "-B", "-c", "-C", "--create"):
        if flag in tokens:
            i = tokens.index(flag)
            if i + 1 < len(tokens) and flagless(tokens[i + 1]):
                return tokens[i + 1]

    if len(tokens) > 1 and tokens[1] == "branch" and ("-m" in tokens or "-M" in tokens):
        positionals = [t for t in tokens[2:] if flagless(t)]
        return positionals[-1] if positionals else None

    return None


def main() -> int:
    payload = read_hook_input()
    cmd = bash_command(payload)

    if not cmd:
        return 0

    for seg in segments(cmd):
        name = candidate_branch_name(seg)

        if not name:
            continue
        if "/" not in name and name in PROTECTED_BASES:
            continue
        if name.startswith(("origin/", "upstream/")):
            continue
        if not VALID.match(name):
            block(name)

    return 0


if __name__ == "__main__":
    sys.exit(main())
