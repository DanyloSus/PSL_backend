---
name: pytest-testcontainers
description: Async API tests with httpx.AsyncClient over ASGITransport. client/auth_client/admin_client fixtures, per-test TRUNCATE + Redis FLUSHDB, testcontainers or TEST_DATABASE_URL override.
metadata:
  version: "1.0"
  stack: python-fastapi
  related-skills:
    - fastapi-endpoint
    - domain-leveling
tier: 1
triggers:
  - test
  - pytest
  - testcontainers
  - fixture
  - coverage
  - async test
summary: |
  Tests live in app/tests/ (auto-collected). Drive the app with httpx.AsyncClient
  over ASGITransport inside the lifespan. Fixtures: `client` (bare), `auth_client`
  (registered user + X-CSRF-Token preset), `admin_client` (promoted to ADMIN,
  re-logged-in). Isolation is per-test TRUNCATE of user tables + Redis FLUSHDB
  (autouse). Default backend = testcontainers Postgres+Redis; override with
  TEST_DATABASE_URL + TEST_REDIS_URL against compose. Usernames must be >=3 chars.
---

# Pytest + Testcontainers

## Overview

| Aspect       | Details                                                       |
| ------------ | ------------------------------------------------------------ |
| Goal         | Fast, isolated async tests exercising real HTTP + Postgres    |
| When         | Any new endpoint, service, or domain-rule behavior            |
| Verification | `uv run pytest -q`                                            |

## Critical rules

**Use the shared fixtures — never spin up your own client or DB. Every test is isolated by an autouse per-test TRUNCATE + Redis FLUSHDB. Usernames in payloads must be ≥3 chars (pattern `[a-zA-Z0-9_.-]+`).**

## Concepts

### Running

```bash
# Default: testcontainers spins disposable Postgres + Redis (needs a docker socket)
uv run pytest -q

# Override: reuse the compose stack (faster locally, matches CI)
docker compose exec postgres psql -U psl -d psl -c "CREATE DATABASE psl_test;"
TEST_DATABASE_URL="postgresql+asyncpg://psl:psl@localhost:5432/psl_test" \
TEST_REDIS_URL="redis://localhost:6379/1" \
  uv run pytest -q
```

`conftest.py` runs Alembic `upgrade head` once per session, then isolates each test.

### Fixtures

| Fixture | Gives you |
| ------- | --------- |
| `client` | bare `AsyncClient` over `ASGITransport` inside the app lifespan |
| `auth_client` | `client` with a registered user and `X-CSRF-Token` header preset |
| `admin_client` | a user promoted to `ADMIN`, re-logged-in for a fresh admin token |

```python
async def test_list_activities_includes_seeded(auth_client: AsyncClient) -> None:
    resp = await auth_client.get("/api/v1/activities")
    assert resp.status_code == 200
    titles = [t["title"] for t in resp.json()]
    assert "Workout (gym)" in titles
```

### State-changing requests need CSRF

`auth_client`/`admin_client` preset `X-CSRF-Token` from the registration/login cookie, so POST/PUT/PATCH/DELETE pass the CSRF guard automatically. With a bare `client`, you must set the header yourself.

```python
resp = await auth_client.post(
    "/api/v1/activities/log",
    json={"activityTemplateId": workout["id"], "quantity": 2},
)
assert resp.status_code == 200, resp.text
```

### Isolation (autouse)

`clean_user_data` truncates `refresh_tokens`, `activity_log_effects`, `activity_logs`, `user_stats`, `users` (RESTART IDENTITY CASCADE), resets seeded template bounds, and FLUSHes Redis (rate-limit + template cache) between tests. Do not rely on state from a previous test.

### Reaching into the DB from a test

For setup that has no endpoint (e.g. promote to admin, tweak seed bounds), use the sessionmaker directly with `update(...)`:

```python
from sqlalchemy import update

from app.core.db import get_sessionmaker
from app.models.activity import ActivityTemplate

sm = get_sessionmaker()
async with sm() as session:
    await session.execute(
        update(ActivityTemplate).where(ActivityTemplate.title == title)
        .values(min_quantity=1, max_quantity=100)
    )
    await session.commit()
```

## Patterns

### Add a test

1. Drop a `test_*.py` into `app/tests/` (auto-collected via `pytest.ini_options.testpaths`).
2. Choose a fixture: reads → `auth_client`; admin routes → `admin_client`; unauth paths → `client`.
3. `await` the request, assert `status_code` (include `resp.text` in the message) and JSON body.
4. Use ≥3-char usernames and valid emails in payloads.
5. For non-HTTP setup, use `get_sessionmaker()` + `commit`.

## Common mistakes

| Mistake | Fix |
| ------- | --- |
| Building your own `AsyncClient` | Use `client`/`auth_client`/`admin_client` |
| POST fails with 403 on bare `client` | Set `X-CSRF-Token`, or use `auth_client` |
| 2-char username in payload | Use ≥3 chars matching `[a-zA-Z0-9_.-]+` |
| Assuming leftover rows from another test | Every test starts truncated + Redis flushed |
| `database "psl_test" does not exist` | `CREATE DATABASE psl_test;` before the override run |
| Docker socket denied for testcontainers | Use the `TEST_DATABASE_URL`/`TEST_REDIS_URL` override |

## Checklist

- [ ] Test file in `app/tests/`, named `test_*.py`
- [ ] Uses a shared fixture, not a hand-rolled client
- [ ] Asserts status + body; includes `resp.text` on failure
- [ ] Usernames ≥3 chars; valid emails
- [ ] No cross-test state assumptions
