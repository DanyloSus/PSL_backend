# AI Knowledge System — Bootstrap

> **Single source of truth** for Claude Code working on this project. Root `CLAUDE.md` and `AGENTS.md` reference this directory; the harness loads it natively. Keep <200 lines.

## Stack

Python 3.12 + uv | FastAPI behind `/api/v1` (`/healthz` unversioned) | SQLAlchemy 2.0 async + Alembic + asyncpg + Postgres 16
Redis 7 (rate limit `fastapi-limiter==0.1.6` + template cache) | argon2 (passlib) + JWT HS256 access (15m) + opaque DB refresh (7d) + CSRF double-submit
SQLAdmin at `/admin` | structlog (JSON non-local, console local) | pytest + pytest-asyncio + httpx.AsyncClient + testcontainers-postgres
Architecture: **Layered** — HTTP router → service → repository → SQLAlchemy.

## Architecture

```
app/
  main.py                # FastAPI app, lifespan, CORS, sessions, exception handlers, router mount
  core/
    config.py            # pydantic-settings Settings singleton (get_settings, lru-cached)
    db.py                # async engine, sessionmaker, DeclarativeBase
    redis.py             # async Redis client + lifecycle
    logging.py           # structlog config
    security.py          # argon2 hash/verify, JWT encode/decode, refresh + CSRF helpers
    cookies.py           # set/clear auth cookies
    dependencies.py      # Depends factories: SessionDep, RedisDep, *ServiceDep, CSRF guard, CurrentUser, AdminUser
    exceptions.py        # DomainError hierarchy → HTTP responses
  routers/               # HTTP routes, THIN: every endpoint `return await service.<method>(...)`
  services/              # business logic classes: AuthService, UserService, ActivityService, LevelingService
  repositories/          # data access classes; SQLAlchemy queries only
  models/                # SQLAlchemy ORM, one file per aggregate; import all in __init__ for Alembic
  schemas/               # pydantic v2 *Create/*Update/*Out; never reuse ORM models for API IO
  migrations/            # alembic env.py + versions/ (0001_… zero-padded)
  admin/                 # SQLAdmin AuthBackend, ModelViews, cache invalidation hooks
  cli.py                 # Typer CLI (psl create-admin)
  tests/                 # pytest + testcontainers conftest
```

### Boundary rules

- Routers call services. Services call repositories. Repositories own SQL.
- No SQL in routers/services. No HTTP/Response objects in services (except setting auth cookies). No HTTP in repositories.
- All IO async — `async with` for sessions and Redis.
- Repos: `__init__(self, session: AsyncSession)`. Services: `__init__(self, session[, redis])`, instantiate the repos they need.
- Routers are 1-line wrappers. Cookie setting / response building / error mapping live in the service or global exception handlers.
- Domain errors subclass `DomainError` (`app/core/exceptions.py`) with `status_code` + `detail`; one `@app.exception_handler(DomainError)` in `main.py` maps them. Routers never catch domain errors.

## Critical Rules (Tier 0 — always enforced)

| #   | Rule                          | Details                                                                                     |
| --- | ----------------------------- | ------------------------------------------------------------------------------------------- |
| 1   | Layer discipline              | router → service → repository → SQLAlchemy. No SQL outside repositories.                     |
| 2   | Thin routers                  | Every endpoint body is `return await service.<method>(...)`.                                 |
| 3   | All IO async                  | `async with` sessions/Redis; never block the event loop.                                    |
| 4   | Schema/model separation       | pydantic `*Create/*Update/*Out` for API IO; never expose ORM models.                        |
| 5   | Domain errors                 | Subclass `DomainError`; never raise raw `HTTPException` in services.                         |
| 6   | UUID PKs + timestamps         | `default=uuid.uuid4`; `created_at`/`updated_at` with `server_default=func.now()`.           |
| 7   | Settings via `get_settings()` | lru-cached; never re-read in a hot path. Local var name `settings`, not `s`.                 |
| 8   | Migrations are additive       | Never edit a merged migration; add a new zero-padded one. Postgres-only.                     |
| 9   | Cache invalidation            | `activities:templates` (5-min TTL) invalidated via ORM event hooks; changes go through ORM. |
| 10  | XP/level floors               | Stat XP ≥ 0, level ≥ 1, levels never decrease; BINARY templates force quantity=1 server-side. |
| 11  | Spell out locals              | `user_stat`, `progress`, `cookie_kwargs` — never single letters when context isn't obvious. |
| 12  | No unsolicited comments       | Zero code comments unless the user asks or a non-obvious WHY needs recording.                |
| 13  | snake_case / kebab paths      | Python snake_case; route paths kebab-case (`/users/me/stats`, `/activity-history`).          |
| 14  | Conventional commits          | `feat\|fix\|refactor\|chore\|style\|docs\|test\|ci\|build\|perf`, with scope. Granular.      |
| 15  | Record decisions              | Architecture-shaping, hard-to-reverse change → `/adr`. Skip reversible detail. Hook reminds. |
| 16  | Spec-driven on new features   | Non-trivial feature/fix → OpenSpec change first (`/opsx:propose`); tests `# @trace <req-id>`.|

## Navigation

```
.claude/
├── FACADE.md          # Task router — START HERE for any task
├── BOOTSTRAP.md       # This file — full reference (<200 lines)
├── README.md          # System docs (hooks, engine, onboarding)
├── manifest.json      # Registry of all artifacts
├── context-tiers.json # Token optimization: what loads when
├── settings.json      # Hooks + permissions
├── rules/             # Enforcement rules (ruff / mypy / conventions)
├── skills/            # Knowledge modules (loaded by trigger keywords)
├── agents/            # Sub-agent personas with scope constraints
├── protocols/         # Cross-cutting workflows
├── templates/         # Self-expansion templates
├── scripts/           # Python hook scripts
├── commands/          # /adr /code-review /sprint /opsx:*
└── engine/            # DAG pipeline engine (nodes + scenarios)

CLAUDE.md              # Pointer to this system
AGENTS.md              # How-we-work source of truth (all AI tools)
docs/PRD.md docs/TDD.md# Source of truth — do not edit unless asked
docs/adrs/             # Architecture Decision Records (why). Add via /adr
openspec/              # Spec-driven workflow (config.yaml + specs/ + changes/)
```

### Loading protocol

1. **Always loaded**: this file.
2. **On trigger**: match task keywords → `manifest.json` `triggers` → load matching skill.
3. **On demand**: full protocols, agent personas — only when needed.

## Rules (mapped to tooling)

| Rule file | Area | Tier |
| --------- | ---- | ---- |
| `layer-architecture.md` | router/service/repo boundaries | 0 |
| `code-style.md` | ruff lint/format, snake_case, no comments | 0 |
| `imports.md` | import order, no cross-layer leaks | 0 |
| `typing.md` | mypy strictness, type hints | 0 |
| `naming.md` | files, routes, vars, classes | 0 |
| `schemas.md` | pydantic Create/Update/Out separation | 1 |
| `migrations.md` | alembic conventions | 1 |
| `testing.md` | pytest + testcontainers patterns | 1 |
| `domain-xp.md` | XP/level/quantity invariants | 1 |
| `security-cookies-csrf.md` | JWT/refresh/CSRF/cookies | 1 |
| `caching.md` | Redis template cache + invalidation | 1 |
| `rate-limiting.md` | fastapi-limiter usage | 1 |
| `file-health.md` | max size, SRP | 1 |
| `decision-records.md` | when to write an ADR | 1 |
| `granular-commits.md` | one logical change per commit | 1 |
| `lint-scope.md` | changed-file-only lint | 1 |
| `spec-driven.md` | OpenSpec requirement grammar + traceability | 1 |

## Commands

```bash
uv run uvicorn app.main:app --reload   # dev server
uv run alembic revision --autogenerate -m "msg" && uv run alembic upgrade head
uv run ruff check .    && uv run ruff format .
uv run mypy app        && uv run pytest -q
uv run pre-commit run --all-files
uv run psl create-admin --email a@b.com --username admin --password "..."
```

## Verification

After completing any code task:

```bash
uv run ruff check . && uv run mypy app && uv run pytest -q
```
