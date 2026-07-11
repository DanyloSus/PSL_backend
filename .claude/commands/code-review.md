---
name: "Code Review"
description: Review the current diff against PSL rules — runs the code-review engine scenario (parallel code-reviewer + architecture-auditor).
category: Quality
---

Review the current working diff (or a named branch/file) against PSL rules.

**Input**: optional target after `/code-review` — a branch name, path, or nothing (defaults to the uncommitted diff vs `main`).

**Steps**

1. Determine the diff scope:
   - No arg → `git diff main...HEAD` plus unstaged changes.
   - A path → limit to that path.
   - A branch → `git diff <branch>...HEAD`.
2. Run the `code-review` engine scenario (`.claude/engine/scenarios/code-review.md`): spawn `code-reviewer` and `architecture-auditor` in parallel (read-only), then merge findings.
   - `code-reviewer` → rule compliance (layer-architecture, code-style, imports, typing, naming, schemas, testing, domain-xp, security).
   - `architecture-auditor` → layer-boundary + coupling audit.
3. Each agent runs `uv run ruff check` and `uv run mypy app` on the diff to ground findings.
4. Report a single merged table, most-severe first:

```
| File:Line | Rule | Severity | Problem | Suggested fix |
|-----------|------|----------|---------|---------------|
```

**Rules**

- Read-only. Never edit code, never run git write operations.
- No praise, no scope creep — one line per finding.
- Skip pure formatting nits (the `ruff_fix` hook already handles those) unless they change meaning.
- If nothing is wrong, say so in one line.
