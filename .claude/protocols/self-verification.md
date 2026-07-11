# Protocol: Self-Verification

> Post-task quality check. Three scopes — pick the one that matches how much you touched.
> Verification gates: `ruff` (lint + format) → `mypy app` (types) → `pytest -q` (behavior).

## Scopes

### Quick (simple task, 1-2 files)

```bash
uv run ruff check <file> [<file> ...]
```

Seconds. Catches lint + import-order violations on exactly what you changed. Pair with
`uv run ruff format <file>` if you touched formatting. Use for a rename, a docstring, a
one-line fix.

### Standard (feature task, 3-10 files)

```bash
uv run ruff check . && uv run mypy app
```

Adds full-project lint and static typing. Run after any change that alters signatures,
schemas (`*Create/*Update/*Out`), service/repo methods, or `Depends` wiring — mypy is the
gate that catches broken layer contracts.

### Full (audit, breaking change, pre-PR)

```bash
uv run ruff check . && uv run mypy app && uv run pytest -q
```

Adds the pytest suite (testcontainers Postgres + Redis, or the `TEST_DATABASE_URL` /
`TEST_REDIS_URL` override). Mandatory before opening a PR and after any change to domain
logic (XP/levels), migrations, auth/CSRF, caching, or rate limiting.

## Decision matrix

| Task                                        | Scope    |
| ------------------------------------------- | -------- |
| Rename one local / fix a docstring          | Quick    |
| Edit a single router or schema field        | Quick    |
| Add/alter a service or repository method    | Standard |
| Change `Depends` wiring or schemas          | Standard |
| New aggregate / feature (router→repo slice) | Full     |
| Migration added or edited                   | Full     |
| Touch XP/leveling, auth/CSRF, cache, limits | Full     |
| Refactor shared code (`core/`, `deps`)      | Full     |
| Pre-PR                                       | Full     |

## If a gate fails

1. **Read the error** — ruff prints the rule code, mypy the exact type mismatch, pytest
   the failing assertion. Understand it before touching anything.
2. **Fix at the source.** Never disable the rule (`# noqa`, `# type: ignore`, per-file
   ruff ignores), never `--no-verify`, never delete/weaken the failing test.
3. **If the rule seems genuinely wrong**, do not silence it locally. Propose a change via
   the `self-expansion` protocol (adjust the rule in `.claude/rules/` + register) and ask
   the user before applying. Type-ignore/noqa is a last resort that requires a WHY comment
   and user sign-off.
