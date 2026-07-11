#!/usr/bin/env python3
"""PreToolUse(Bash) guard — defense-in-depth for git/gh operations.

permissions.deny in settings.json catches the common glob forms; this guard
catches the refspec / flag variants globs cannot express (HEAD:main,
--force-with-lease=<x>, etc.). Blocks by writing to stderr and exiting 2 (the
canonical PreToolUse block signal). Exits 0 on anything it does not recognise.
"""

from __future__ import annotations

import re
import sys

from _hook_input import bash_command, read_hook_input, segments


def block(message: str) -> None:
    sys.stderr.write(f"BLOCKED: {message}\n")
    sys.exit(2)


def main() -> int:
    payload = read_hook_input()
    cmd = bash_command(payload)

    if not cmd:
        return 0

    for seg in segments(cmd):
        # Block all force-pushes on every branch.
        if re.match(r"^git\s+push\b", seg) and re.search(
            r"(--force\b|--force-with-lease|\s-f\b)", seg
        ):
            block("Force push is prohibited on all branches.")

        # Block direct pushes to the protected deploy branch — catches
        # `HEAD:main`, `origin main`, and refspec variants the deny globs miss.
        if re.match(r"^git\s+push\b", seg) and re.search(r"[\s:]main(\s|:|$)", seg):
            block("Direct push to main is prohibited. Open a PR: gh pr create")

        # Block GitHub ruleset mutations — prevents removing repo protections.
        if (
            re.match(r"^gh\s+api\b", seg)
            and "rulesets" in seg
            and re.search(r"--method\s+(PUT|DELETE|PATCH)", seg)
        ):
            block("Mutating GitHub rulesets is prohibited.")

        # Block gh repo edit — modifies repository-level settings.
        if re.match(r"^gh\s+repo\s+edit\b", seg):
            block("gh repo edit modifies repository settings and is prohibited.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
