---
name: "Sprint"
description: Walk a feature or fix through Think → Plan → Build → Review → Test → Ship → Reflect with an approval gate between phases.
category: Workflow
---

Drive a feature or fix through the full lifecycle, pausing for approval between phases. Skip this for trivial one-line fixes — use the §A–§M skills directly. Everything runs inside Claude Code; no external CLI or model vendor.

**Input**: a short description of the feature/fix after `/sprint`. If none, ask.

**Phases** (gate = pause for user approval before continuing)

| Phase   | Do                                                                                          | Gate |
| ------- | ------------------------------------------------------------------------------------------- | ---- |
| Think   | `grill-me` skill — interrogate the plan/design one question at a time until shared understanding | ✓ |
| Plan    | `Plan` agent; for non-trivial features open an OpenSpec change (`/opsx:propose`); pick an engine scenario if multi-file | ✓ |
| Build   | Implement per `.claude/rules/*`; changed-file lint only (`ruff_fix` hook handles it)         | ✓    |
| Review  | `code-review` engine scenario (or `code-reviewer` agent) on the diff                        | ✓    |
| Test    | `pytest-testcontainers`; run `uv run pytest -q`; add `# @trace <req-id>` where a spec exists | ✓   |
| Ship    | `git-commit` (granular, Conventional) → `pull-request-description`; never auto-push          | ✓    |
| Reflect | `learn` — capture durable lessons (CLAUDE.md/AGENTS.md/ADR/rule); skip if nothing durable    | —    |

**Rules**

- One gate between each phase — present a short summary and wait.
- No repo-wide lint/build/test inside a phase (rule `lint-scope`); scope to changed files until the Test phase.
- Never push automatically — the PR is the user's call at the Ship gate.
- Respect the stacked-PR workflow (CLAUDE.md §9): base may be a parent branch, not `main`.
- Full verification before the Ship gate: `uv run ruff check . && uv run mypy app && uv run pytest -q`.
