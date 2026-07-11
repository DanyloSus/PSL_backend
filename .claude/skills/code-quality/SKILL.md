---
name: code-quality
description: The PSL quality gate — ruff lint + ruff format + mypy + pytest. Full-suite verification command, changed-file-only lint during tasks, pre-commit parity.
metadata:
  version: "1.0"
  stack: python-fastapi
  related-skills:
    - pytest-testcontainers
tier: 1
triggers:
  - quality
  - lint
  - ruff
  - mypy
  - format
  - review
summary: |
  Every code task ends green on: `uv run ruff check . && uv run mypy app &&
  uv run pytest -q` (add `uv run ruff format .` to fix formatting). During a task,
  lint only the files you changed to stay fast; run the full suite before
  declaring done / committing. Do NOT hand-format against ruff. mypy runs strict
  (typed defs, no stray Any); passlib stubs already overridden in pyproject.toml.
  pre-commit mirrors CI — never bypass with --no-verify.
---

# Code Quality Gate

## Overview

| Aspect       | Details                                                        |
| ------------ | ------------------------------------------------------------- |
| Goal         | Keep the tree lint-clean, typed, and green before commit/PR    |
| When         | After any edit; always before committing or reporting done     |
| Verification | `uv run ruff check . && uv run mypy app && uv run pytest -q`   |

## Critical rules

**A task is not done until `uv run ruff check . && uv run mypy app && uv run pytest -q` passes. Never `--no-verify`. Never hand-format against ruff.**

## Concepts

### The full gate

```bash
uv run ruff check .        # lint (incl. import order, I rules)
uv run ruff format .       # auto-format (or --check in CI)
uv run mypy app            # static types over app/
uv run pytest -q           # tests (see pytest-testcontainers)
```

CI (`.github/workflows/ci.yml`) runs ruff lint + format-check + mypy + pytest with Postgres + Redis service containers.

### Changed-file-only lint during a task

To stay fast mid-task, lint just what you touched, then run the full suite before finishing:

```bash
uv run ruff check app/services/activity_service.py app/routers/activities.py
uv run ruff format app/services/activity_service.py
# ...then, before done/commit:
uv run ruff check . && uv run mypy app && uv run pytest -q
```

`mypy` is best run over the whole `app` package (cross-module inference); don't narrow it.

### mypy expectations

Strict-ish: every def typed, no gratuitous `Any`, `X | None` for optionals, SQLAlchemy `Mapped[]` models. Untyped third-party stubs are handled via overrides in `pyproject.toml` (passlib is already there) — add new untyped deps to the same block rather than sprinkling `# type: ignore`.

### pre-commit parity

```bash
uv run pre-commit run --all-files
```

Mirrors the CI checks locally. The commit-msg hook blocks Claude/Anthropic/`Co-Authored-By`/"Generated with"/🤖 references — fix the message, don't bypass. (On very early stacked branches the pre-commit config may be absent; see CLAUDE.md §18 — never use `--no-verify`.)

## Patterns

### Finish a code change

1. Format + lint the changed files.
2. Run the full gate: `ruff check . && mypy app && pytest -q`.
3. Fix real issues (don't `type: ignore` to silence).
4. Only then commit (Conventional Commits, granular) / report done.

## Common mistakes

| Mistake | Fix |
| ------- | --- |
| Committing without running the gate | Run all four before commit |
| Hand-tweaking whitespace | `uv run ruff format .` |
| `# type: ignore` to hush mypy | Fix the type or add a stub override in `pyproject.toml` |
| `git commit --no-verify` | Never; fix the underlying issue (incl. commit-msg refs) |
| Narrowing mypy to one file | Run over the whole `app` package |

## Checklist

- [ ] `uv run ruff check .` clean
- [ ] `uv run ruff format .` applied (no diff)
- [ ] `uv run mypy app` clean
- [ ] `uv run pytest -q` green
- [ ] No `--no-verify`; commit message hook-clean
