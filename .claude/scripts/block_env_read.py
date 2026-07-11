#!/usr/bin/env python3
"""PreToolUse(Read|Grep) guard — blocks reading secrets out of .env files.

.env.example templates are allowed. Blocks via stderr + exit 2; exits 0
otherwise.
"""

from __future__ import annotations

import sys

from _hook_input import is_env_secret, read_hook_input, target_path


def main() -> int:
    payload = read_hook_input()
    raw = target_path(payload)

    if not raw:
        return 0

    base = raw.replace("\\", "/").split("/")[-1]

    if is_env_secret(base):
        sys.stderr.write("BLOCKED: Cannot read .env files (use .env.example templates only).\n")
        sys.exit(2)

    return 0


if __name__ == "__main__":
    sys.exit(main())
