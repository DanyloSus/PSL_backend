---
id: testing
tier: 1
tooling: [pytest, convention]
enforcement: strict
paths:
  - "app/tests/**/*.py"
---

# Testing (pytest + testcontainers)

Enforces async HTTP-level tests over `ASGITransport`, shared fixtures, and per-test isolation.

## Rules

### TE1. Async tests via `httpx.AsyncClient` over `ASGITransport`

**Tooling:** `pytest` (`pytest-asyncio`), `convention`

Exercise the app through HTTP using the `client` fixture (`httpx.AsyncClient` over `ASGITransport` + lifespan), not by calling services directly. Tests live in `app/tests/` and are auto-collected.

```python
# ✅ CORRECT — HTTP-level async test
async def test_list_activities(auth_client: AsyncClient) -> None:
    response = await auth_client.get("/api/v1/activities")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

**Why:** Testing through the real ASGI transport covers routing, dependencies, serialization, and error mapping — the whole stack, not an isolated function.

### TE2. Use the shared auth fixtures

**Tooling:** `convention`

Use `client` (anonymous), `auth_client` (registered user with `X-CSRF-Token` preset), and `admin_client` (promoted to ADMIN, re-logged-in). Don't hand-roll login flows per test.

```python
# ❌ FORBIDDEN — re-registering and juggling CSRF by hand
async def test_thing(client):
    await client.post("/api/v1/auth/register", json={...})
    ...

# ✅ CORRECT — reuse the fixture that already handles auth + CSRF
async def test_log_activity(auth_client: AsyncClient) -> None:
    response = await auth_client.post("/api/v1/activities/log", json={"activityTemplateId": ..., "quantity": 1})
    assert response.status_code == 200
```

**Why:** The fixtures encapsulate registration, cookie handling, and CSRF double-submit, so tests stay focused on behavior.

### TE3. Per-test isolation: TRUNCATE + Redis FLUSHDB

**Tooling:** `pytest`, `convention`

Each test starts clean — user data is TRUNCATEd and Redis is FLUSHDBed by fixtures. Do not leak state or depend on ordering between tests.

**Why:** Isolation makes tests deterministic and parallel-safe; a leaked cache entry or row otherwise causes flakes that are painful to debug.

### TE4. Valid usernames are 3+ chars

**Tooling:** `convention`

Username constraints: `min_length=3`, pattern `[a-zA-Z0-9_.-]+`. Test payloads must use 3+ char usernames or registration 422s.

```python
# ❌ FORBIDDEN — 2 chars, fails validation
{"username": "ab", ...}

# ✅ CORRECT
{"username": "tester", ...}
```

**Why:** Short-username payloads fail at schema validation, producing confusing 422s unrelated to what the test is checking.

### TE5. Two ways to run: testcontainers or env-var override

**Tooling:** `pytest`

Default uses testcontainers (needs a docker socket). On CI or hosts without one, reuse the compose stack via `TEST_DATABASE_URL` / `TEST_REDIS_URL`.

```bash
# testcontainers (disposable Postgres + Redis)
uv run pytest -q

# override against running compose stack
TEST_DATABASE_URL="postgresql+asyncpg://psl:psl@localhost:5432/psl_test" \
TEST_REDIS_URL="redis://localhost:6379/1" uv run pytest -q
```

**Why:** The override keeps tests runnable where the docker socket is unavailable (CI, restricted hosts) while matching production Postgres.

## Verification

```bash
uv run pytest -q
```
