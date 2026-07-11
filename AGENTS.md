# AGENTS.md — PSL Backend

> Primary instruction surface for every AI agent working in this repo (Claude Code, Cursor, Copilot, Codex, …). Subdirectory `AGENTS.md` files override this one within their scope. Humans: read this too — it is the source of truth for "how we work here".
>
> Harness config (facade router, hooks, engine, skills) lives under `.claude/` — start at `.claude/FACADE.md`. This file is "how we write code"; `.claude/` is "how the harness is configured".

## 1. Project

Real-life RPG backend for Project Solo Levelling (PSL). Users log real-life activities → stats gain XP → level up.

Source-of-truth specs (do not edit unless explicitly asked):
- `docs/PRD.md` — product requirements
- `docs/TDD.md` — technical description

Spec-driven work lives in `openspec/` (see §19).

## 2. Stack

- Python 3.12 + uv (single source of truth for deps + venv)
- FastAPI behind `/api/v1` prefix; `/healthz` unversioned
- SQLAlchemy 2.0 async + Alembic + asyncpg + Postgres 16
- Redis 7: rate limit (`fastapi-limiter==0.1.6`, pinned) + activity template cache
- Auth: argon2 (passlib), JWT HS256 access (15m) + opaque DB-tracked refresh (7d) in httpOnly cookies, CSRF double-submit
- Admin: SQLAdmin at `/admin`, AuthBackend against `users` table where `role=ADMIN`
- Logging: structlog (JSON in non-local envs, console in `ENV=local`)
- Tests: pytest + pytest-asyncio + httpx.AsyncClient + testcontainers-postgres (with env-var override for CI / hosts without a docker socket)

## 3. Layout

Layered with classes. Order: HTTP → service → repository → SQLAlchemy.

```
app/
  main.py                # FastAPI app, lifespan, CORS, sessions, exception handlers, router mount
  core/
    config.py            # pydantic-settings Settings singleton
    db.py                # async engine, sessionmaker, DeclarativeBase
    redis.py             # async Redis client + lifecycle
    logging.py           # structlog config
    security.py          # argon2 hash/verify, JWT encode/decode, refresh + CSRF helpers
    cookies.py           # set/clear auth cookies
    dependencies.py      # FastAPI Depends factories: SessionDep, RedisDep, *ServiceDep, CSRF guard, CurrentUser, AdminUser
    exceptions.py        # DomainError hierarchy mapped to HTTP responses
  routers/               # HTTP routes (one module per resource). THIN: every endpoint is `return await service.<method>(...)`
  services/              # business logic, classes. AuthService, UserService, ActivityService, LevelingService
  repositories/          # data access, classes. SQLAlchemy queries only
  models/                # SQLAlchemy ORM. One file per aggregate. Import all in __init__ so Alembic sees them
  schemas/               # pydantic v2 request/response models. Never reuse ORM models for API IO
  migrations/            # alembic env.py + versions/
  admin/                 # SQLAdmin AuthBackend, ModelViews, cache invalidation hooks
  cli.py                 # Typer CLI (`psl create-admin`)
  tests/                 # pytest + testcontainers conftest
```

## 4. Layer rules

- Routers call services. Services call repositories. Repositories own SQL.
- No SQL in routers/services. No HTTP/Response objects in services unless setting auth cookies. No HTTP in repositories.
- All IO async. Use `async with` for sessions and Redis.
- Repos are classes: `__init__(self, session: AsyncSession)`. Services are classes: `__init__(self, session[, redis])` and instantiate the repos they need.
- Routers are 1-line wrappers: `return await service.<method>(...)`. Cookie setting, response building, and error mapping live in the service or in global exception handlers.
- Domain errors subclass `DomainError` (`app/core/exceptions.py`) with `status_code` and `detail`. `main.py` registers one `@app.exception_handler(DomainError)` that maps them to JSON responses. Routers do not catch domain errors.

### 4a. Protected areas (deliberate-first-edit)

The `protected_paths` hook (`.claude/scripts/protected_paths.py`) asks once per session before the first edit to any of these app-wide-blast-radius files, because a careless change is hard to reverse:

- `app/core/security.py`, `app/core/cookies.py`, `app/core/config.py`, `app/core/db.py`, `app/core/dependencies.py`
- `app/main.py`
- `app/migrations/env.py`, `app/migrations/versions/*` (also: never edit a merged migration — §10)
- `alembic.ini`, `pyproject.toml`, `.pre-commit-config.yaml`, `.github/workflows/*`

`.env` secret files are hard-denied for both read and edit — use `.env.example` templates.

## 5. Domain rules (XP / levels)

- Stat XP ≥ 0 floor. Stat level ≥ 1. Levels never decrease.
- BINARY templates → quantity forced to 1 server-side; client value ignored.
- Log delta per stat = `effect.xp_change * effective_quantity`, then floored at 0.
- `User.global_xp` stores the running sum of applied deltas. `global_level` recomputed (no drop).
- Level formula: `LevelingService.threshold_for(L) = floor(100 * (L-1)**1.5)`; `LevelingService.level_from_xp(xp)` returns the highest L whose threshold ≤ xp, min 1.
- Single transaction per log: template load → for each effect lock+update UserStat → write `ActivityLog` + per-stat `ActivityLogEffect` rows.

## 6. Cookies, CSRF, JWT

- `access_token` HttpOnly JWT HS256 (15 min) + `refresh_token` HttpOnly opaque (sha256-hashed in DB, 7 days) + `csrf_token` non-HttpOnly (double-submit). See `app/core/cookies.py`.
- `SameSite` defaults to `lax` locally; production must be `none` with `Secure=true` for the Vercel ↔ Render cross-site setup.
- Refresh rotates on every `/auth/refresh`: old token revoked, new pair issued. `clear_auth_cookies` on bad refresh.
- CSRF guard bypassed for `/auth/login`, `/auth/register`, `/auth/refresh` (no session yet). All other POST/PUT/PATCH/DELETE require `X-CSRF-Token` header matching the cookie.

## 7. Cache

- Key `activities:templates`, 5-minute TTL, owned by `ActivityService.list_templates`.
- Invalidated automatically on `ActivityTemplate`/`ActivityEffect` insert/update/delete via SQLAlchemy ORM event hooks (`app/admin/hooks.py`). Raw SQL bypasses this — admin changes must go through ORM (SQLAdmin does).

## 8. Rate limiting

- `fastapi-limiter==0.1.6` (pinned: 0.2.x dropped `times`/`seconds` kwargs).
- Auth endpoints: 10 req / 60s.
- `POST /api/v1/activities/log`: 60 req / 60s.

## 9. Stacked PR workflow

Order: `main` → `chore/scaffold` → `chore/tooling` → `feat/db-core` → `feat/auth-models` → `feat/auth-endpoints` → `feat/stats` → `feat/activities-models` → `feat/activities-engine` → `feat/admin` → `feat/tests`.

Each PR:
- Branched on top of the previous (base = previous branch, not `main`)
- ≤500 LOC of insertions (excluding `uv.lock`). Verify with `git diff <base>..<head> --stat -- . ":(exclude)uv.lock" | tail -1`. Split into multiple PRs if larger.
- Uses `.github/pull_request_template.md` — body must contain the four headings: `## What was done`, `## Related issue`, `## How to test`, `## Additional notes`
- Assigned to `DanyloSus`: `gh pr edit <N> --add-assignee DanyloSus`
- No references to Claude, Anthropic, `Co-Authored-By`, "Generated with ...", or 🤖 in commits or PR bodies. The local commit-msg hook blocks them.

Commit style: Conventional Commits with scope (`feat(auth-endpoints): ...`, `fix(db-core): ...`, `test: ...`, `docs: ...`, `ci: ...`, `refactor(activities): ...`, `chore(tooling): ...`).

Branch naming (enforced by `.claude/scripts/branch_name_guard.py`): prefix ∈ `feat|feature|fix|bugfix|chore|refactor|test|docs|ci|build|perf`; format `<type>/<kebab-desc>`.

Updating the stack without force-push: add new commits at the source branch where the file lives, then cherry-pick onto each downstream branch in order. Resolve conflicts by hand when downstream has touched the same lines.

`gh` is authed as `dsu-empat` (collaborator on `DanyloSus/PSL_backend`). SSH push uses the `github-sus.com` host alias which routes to the `DanyloSus` SSH key. If `gh pr create` returns "must be a collaborator", re-check `gh auth status`.

## 10. Migrations (Alembic)

```bash
uv run alembic revision --autogenerate -m "<short message>"
# 1. rename generated file to 4-digit prefix: 0006_<slug>.py
# 2. set `revision: str = "0006_<slug>"` to match the filename
# 3. confirm `down_revision` points to the previous migration id
uv run alembic upgrade head
uv run alembic downgrade -1
```

- Migrations live in `app/migrations/versions/`. Naming: `0001_*` ... (zero-padded). Each PR adds its own.
- Data seeds use `op.bulk_insert(...)`. See `0003_seed_stats.py`, `0005_seed_activity_templates.py`.
- New aggregates: import the model module in `app/models/__init__.py` so Alembic autogenerate sees it via `Base.metadata`.
- Postgres-only. Do not rely on SQLite-specific behavior.
- Never edit an already-merged migration. Add a new one instead.

## 11. Tests (pytest + testcontainers)

```bash
# Default: testcontainers spins up disposable Postgres + Redis (needs an accessible docker socket)
uv run pytest -q

# Override: reuse running compose Postgres + Redis (faster locally; matches CI)
docker compose exec postgres psql -U psl -d psl -c "CREATE DATABASE psl_test;"
TEST_DATABASE_URL="postgresql+asyncpg://psl:psl@localhost:5432/psl_test" \
TEST_REDIS_URL="redis://localhost:6379/1" \
  uv run pytest -q
```

Patterns:
- `client` fixture — `httpx.AsyncClient` over `ASGITransport` plus lifespan
- `auth_client` — registers a user and presets `X-CSRF-Token`
- `admin_client` — promotes a user to ADMIN and logs in again to refresh the access token
- Per-test `TRUNCATE` of user data + Redis `FLUSHDB` keep tests isolated
- Username constraints: `min_length=3`, pattern `[a-zA-Z0-9_.-]+`. Test payloads must use 3+ char usernames.
- New test files: drop into `app/tests/`. Auto-collected via `pytest.ini_options.testpaths`.

CI (`.github/workflows/ci.yml`) runs ruff lint + format check + mypy + pytest with Postgres + Redis service containers.

## 12. Admin

- SQLAdmin mounted at `/admin`. `AdminAuth` (`app/admin/auth.py`) checks `users.role == ADMIN` and verifies argon2 password. Session via Starlette `SessionMiddleware`.
- ModelViews (`app/admin/views.py`): `User`, `Stat`, `UserStat`, `ActivityTemplate`, `ActivityEffect`, `ActivityLog` (read-only), `ActivityLogEffect` (read-only).
- ORM event hooks (`app/admin/hooks.py`) invalidate the Redis templates cache on insert/update/delete of `ActivityTemplate` or `ActivityEffect`.
- Bootstrap an admin (idempotent — promotes existing users):

```bash
uv run psl create-admin --email admin@psl.io --username admin --password "strong-pw"
```

## 13. Settings

- `pydantic-settings` `Settings` class in `app/core/config.py`, loaded from `.env` or env vars.
- `.env` is gitignored. `.env.example` is the canonical list of expected variables.
- Read settings via `get_settings()` (lru-cached). Never re-read inside a hot path.
- Local variable names: prefer `settings = get_settings()` rather than `s = ...`.

## 14. Logging

- `configure_logging()` runs in the FastAPI lifespan.
- Local: human-readable console renderer. Non-local: JSON renderer.
- Use `structlog.get_logger()`; bind contextvars per request when needed.

## 15. Naming and style

- Python: snake_case. Route paths: kebab-case (`/activity-history`, `/users/me/stats`).
- Models: UUID PKs as `uuid.UUID`, server-side default via `default=uuid.uuid4`. `created_at` / `updated_at` on every mutable entity, `server_default=func.now()` and `onupdate=func.now()` where appropriate.
- Schemas: separate `*Create`, `*Update`, `*Out`. Never reuse models for API IO.
- Local variables: spell things out — `settings`, `user_stat`, `progress`, `cookie_kwargs`, `sessionmaker` — never single letters when the context isn't obvious.
- Comments: do NOT add code comments unless the user explicitly asks. Default to zero comments — write self-explanatory code. Exception: a genuinely non-obvious WHY (subtle invariant, workaround). Never restate the code.

## 16. Common commands

```bash
uv sync                                 # deps
uv add <pkg>                            # add dep
uv run uvicorn app.main:app --reload    # run
docker compose up -d                    # full stack
uv run alembic upgrade head             # migrate
uv run ruff check . && uv run ruff format .
uv run mypy app
uv run pytest -q
uv run pre-commit run --all-files
```

## 17. Files not to touch unless asked

- `docs/PRD.md`, `docs/TDD.md` — source of truth
- Existing migrations in `app/migrations/versions/` — never edit, only add new ones
- `.claude/settings.local.json` — local-only harness config

## 18. Troubleshooting

- `gh pr create: must be a collaborator` — `gh` is authed as `dsu-empat`. Check `gh auth status`. SSH push uses the `github-sus.com` host alias.
- `fastapi-limiter` `RateLimiter(...)` rejects `times`/`seconds` — your install is on 0.2.x. Pin to `0.1.6`.
- `mypy` complains about `passlib` stubs — already overridden in `pyproject.toml`. New untyped dep → add to the same override block.
- Tests fail with `database "psl_test" does not exist` — `CREATE DATABASE psl_test;` on the compose Postgres before running with the env-var override.
- Docker socket permission denied for testcontainers locally — use the `TEST_DATABASE_URL` / `TEST_REDIS_URL` override against the compose stack.
- Commit blocked by the commit-msg hook — remove every Claude / Anthropic / `Co-Authored-By` / "Generated with ..." / 🤖 reference and retry. Do not bypass the hook.

## 19. Spec-driven development (OpenSpec)

Non-trivial features/fixes start as an OpenSpec change before code. Layout: `openspec/config.yaml` (project context + per-artifact rules) + `openspec/specs/` (baseline) + `openspec/changes/` (proposals).

Commands: `/opsx:propose "<idea>"` → `/opsx:apply` → `/opsx:archive`; `/opsx:explore` to think first; `/opsx:sync` to fold delta specs into baseline.

- Requirement IDs: `FR/NFR/TC/BC-<AREA>-<n>` as headings; the traceability spine.
- Every FR/NFR declares `Verification:` from the closed vocab — `local-verifiable` (pytest) | `migration` (alembic up/down) | `manual`.
- Declare `Parent: #<issue>` when a GitHub issue exists.
- Tests written from the spec, red first, annotated `# @trace <req-id>`.
- Retro-spec-on-touch: a change touching an area with no baseline spec reverse-engineers that spec first.

See `.claude/rules/spec-driven.md` and `openspec/config.yaml`.

## 20. The `.claude/` harness system

- `.claude/FACADE.md` — task router; start here.
- `.claude/BOOTSTRAP.md` — always-loaded compact reference.
- `.claude/rules/` — enforceable rules (ruff/mypy/conventions). `.claude/skills/` — knowledge modules. `.claude/agents/` — sub-agent personas. `.claude/protocols/` — cross-cutting workflows. `.claude/engine/` — DAG pipeline for complex multi-file tasks. `.claude/commands/` — `/adr`, `/code-review`, `/sprint`, `/opsx:*`.
- `.claude/scripts/` — PreToolUse/PostToolUse hooks (git guards, protected paths, env-read block, ADR reminder, changed-file ruff fix). Wired in `.claude/settings.json`.
- Add new artifacts via the templates in `.claude/templates/` and register them in `.claude/manifest.json` (see `.claude/README.md` §7).
