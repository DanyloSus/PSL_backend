---
id: lint-scope
tier: 1
tooling: [ruff, convention]
enforcement: convention
paths:
  - "app/**/*.py"
---

# Lint Scope

Enforces changed-file-only linting inside a task; repo-wide lint/format is owned by CI and the final verification, not intermediate task phases.

## Rules

### LS1. Lint the file you just edited, not the whole repo

**Tooling:** `ruff`, `convention`

After editing a file, the `ruff_fix` hook auto-lints and formats that file. Do not manually run repo-wide `ruff check .` / `ruff format .` between edits inside a task phase — it churns unrelated files and noises up the diff.

```bash
# ❌ AVOID during a task phase — touches files you didn't change
uv run ruff format .

# ✅ scope to the file you edited (the ruff_fix hook does this automatically)
uv run ruff check --fix app/services/activity_service.py
```

**Why:** Repo-wide format runs mid-task blur your diff with drive-by reformatting of untouched files, making review harder and commits less granular.

### LS2. CI and final verification own hard, repo-wide enforcement

**Tooling:** `ruff`, `convention`

Repo-wide `uv run ruff check .` is the hard gate — run it as the final verification before finishing, and CI runs it on every push. It is the authority, not intermediate per-file checks.

```bash
# ✅ final verification, once, before handing off
uv run ruff check . && uv run ruff format --check . && uv run mypy app && uv run pytest -q
```

**Why:** One authoritative repo-wide check at the end catches everything without polluting intermediate diffs. CI mirrors it so nothing slips through.

## Verification

```bash
uv run ruff check .
```
