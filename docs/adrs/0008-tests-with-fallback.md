# ADR 0008 — Tests: testcontainers with env-var override fallback

- **Status:** Accepted
- **Date:** 2026-05-24

## Context

Backend tests must hit a real Postgres (asyncpg-specific behavior, JSONB, enums, FK cascades). SQLite is not an option. Three ways to procure a database for the suite:

1. **Run against a long-lived shared database.** Tests pollute each other; isolation requires fragile per-test resets.
2. **Spin up a fresh Postgres + Redis per test session via testcontainers.** Self-contained, no external state. Requires an accessible Docker socket.
3. **Use whatever Postgres + Redis the dev has running, via env vars.** Fast, depends on user-supplied infra.

Dev environments differ: CI has a privileged Docker socket; some local setups (Docker Desktop on Linux with rootless config) do not. We want one suite that works in both worlds.

## Decision

- **Default path:** `app/tests/conftest.py` spins up `PostgresContainer("postgres:16-alpine")` and `RedisContainer("redis:7-alpine")` at session scope. Alembic upgrades head against the container, then the suite runs.
- **Override path:** if both `TEST_DATABASE_URL` and `TEST_REDIS_URL` are set, the conftest yields those URLs and skips testcontainers entirely. The CI workflow uses this path against service containers; local devs without docker-socket access use it against the compose stack.
- **Per-test isolation:** an autouse fixture `TRUNCATE`s user data (`refresh_tokens`, `activity_log_effects`, `activity_logs`, `user_stats`, `users`) and `FLUSHDB`s Redis between tests. Seeded `stats` and `activity_templates` are left intact.
- **Lifespan:** the `client` fixture wraps `httpx.AsyncClient` with `ASGITransport(app=app)` and enters `app.router.lifespan_context(app)` so `FastAPILimiter.init` and other startup hooks run.

## Consequences

**Positive**
- One `uv run pytest -q` works for every dev with Docker access. Anyone without it sets two env vars and is unblocked.
- CI uses the same env-var path as compose-using devs, so CI behavior is reproducible locally.
- Per-test truncate is cheap (small tables) and avoids transactional-rollback complications with the FastAPI lifespan.

**Negative**
- Two paths to support. Mitigated by keeping the conditional in one place (`conftest.py`).
- `TEST_*_URL` paths assume the target database already exists (`CREATE DATABASE psl_test;`). Documented in `CLAUDE.md` §11.
- Rate-limit state lives in Redis. `FLUSHDB` between tests prevents leakage but also wipes the template cache — a measurable test should call `ActivityService.list_templates` once after a flush before asserting on the cache.

## Compliance

- New tests assume the conftest fixtures and do not stand up their own DB / Redis.
- New env vars consumed by tests go through `configure_env`.
- New service modules used by the suite get a corresponding fixture in `conftest.py` (e.g. `admin_client` was added when admin auth needed to be exercised end-to-end).
