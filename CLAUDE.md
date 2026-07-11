# CLAUDE.md

## Agent Context

See @AGENTS.md for all project conventions and instructions (stack, layer rules, domain rules, git workflow, migrations, tests, spec-driven development).

When working in any subdirectory, check for a local `AGENTS.md` and read it before making changes. Subdirectory instructions take precedence over root instructions where they conflict.

## Harness

`.claude/` holds the Claude Code AI knowledge system — a Facade-pattern router that loads only the knowledge a task needs.

- **Start at `.claude/FACADE.md`** — the task router. It points to the right rule, skill, or engine scenario.
- `.claude/BOOTSTRAP.md` — always-loaded compact reference.
- `.claude/README.md` — how the system (hooks, engine, tiers) is organised.

Prefer `AGENTS.md` for "how we write code here"; use `.claude/` for "how this harness is configured".
