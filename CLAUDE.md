# CLAUDE.md — PSL Backend

Guidance for Claude Code working in this repo. Keep terse.

## Project

Real-life RPG backend for Project Solo Levelling (PSL). Users log real-life activities → stats gain XP → level up. See `docs/PRD.md` + `docs/TDD.md` for spec.

## Stack

- Python 3.12 + uv (single source of truth for deps + venv)
- FastAPI behind `/api/v1` prefix; `/healthz` unversioned
- SQLAlchemy 2.0 async + Alembic + asyncpg + Postgres
- Redis: rate limit (fastapi-limiter) + activity template cache
- Auth: argon2 (passlib), JWT access(15m) + DB-tracked opaque refresh(7d) in httpOnly cookies, SameSite=None, CSRF double-submit
- Admin: SQLAdmin at `/admin`, AuthBackend against `users` table where `role=ADMIN`
- Logging: structlog (JSON in non-local envs)
- Tests: pytest + pytest-asyncio + httpx.AsyncClient + testcontainers-postgres

## Layout (layered)

```
app/
  main.py
  core/         config, db, redis, security, logging, dependencies
  routers/      one module per resource (auth, users, activities, admin)
  services/     business logic, transactional units
  repositories/ data access; SQLAlchemy queries only
  models/       ORM models, one file per aggregate
  schemas/      pydantic v2 request/response models
  migrations/   alembic
  tests/        pytest
```

Layer rules:
- Routers call services. Services call repositories. Repositories own SQL.
- No SQL in routers/services. No HTTP in services/repositories.
- All IO is async. Use `async with` for sessions/redis.

## Commands

```bash
# Deps
uv sync                                 # install
uv add <pkg>                            # add runtime dep
uv add --group dev <pkg>                # add dev dep

# Run
uv run uvicorn app.main:app --reload    # dev server
docker compose up -d                    # full stack

# DB
uv run alembic revision --autogenerate -m "msg"
uv run alembic upgrade head
uv run alembic downgrade -1

# Quality
uv run ruff check .
uv run ruff format .
uv run mypy app
uv run pytest -q
uv run pre-commit run --all-files

# Tests (testcontainers by default; or set TEST_DATABASE_URL + TEST_REDIS_URL to reuse compose)
uv run pytest -q

# Admin bootstrap
uv run psl create-admin --email a@b.com --username admin --password "..."
```

## Conventions

- **Naming**: snake_case for python, kebab-case for files only when not python module; route paths kebab-case (`/activity-history`).
- **Models**: UUID PKs as `uuid.UUID`, server-side default via SQLA. `created_at`/`updated_at` on all mutable entities.
- **Schemas**: Separate `*Create`, `*Update`, `*Out`. Never reuse models for API IO.
- **Errors**: raise `HTTPException` in routers; raise domain exceptions in services and map in router or via exception handler in `app/main.py`.
- **Tx**: services start/commit transactions. Repositories accept `AsyncSession`.
- **XP rules** (domain invariants):
  - Stat XP ≥ 0 floor. Stat level ≥ 1. Levels never decrease.
  - BINARY templates → quantity forced to 1.
  - Log applies delta = `effect.xp_change * quantity` per stat, floored.
  - User.global_xp = stored sum of all UserStat.xp; recompute global level same formula.
  - Level formula: `xp_for_level(L) = floor(100 * L**1.5)`; `level_from_xp(xp)` returns highest L where threshold ≤ xp, min 1.
- **Cookies**: `access_token`, `refresh_token` HttpOnly + Secure + SameSite=None. `csrf_token` non-HttpOnly. Check `X-CSRF-Token` header == csrf cookie on POST/PUT/PATCH/DELETE.
- **Cache**: list templates cached `activities:templates`, TTL 5m; invalidate on admin template/effect write.
- **Tests**: per-test transaction rollback against testcontainers Postgres. Use `auth_client` fixture for authed reqs.

## Stacked PR workflow

Each feature = branch on top of previous + PR with `base=<previous-branch>`.

Order: `chore/scaffold` → `chore/tooling` → `feat/db-core` → `feat/auth-models` → `feat/auth-endpoints` → `feat/stats` → `feat/activities-models` → `feat/activities-engine` → `feat/admin` → `feat/tests`.

Commit style: Conventional Commits (`feat:`, `chore:`, `fix:`, `refactor:`, `docs:`, `test:`). PRs must use the template in `.github/pull_request_template.md` and stay under 500 LOC (excluding `uv.lock`).

## Files not to touch unless asked

- `docs/PRD.md`, `docs/TDD.md` — source of truth
- `.claude/` — local
