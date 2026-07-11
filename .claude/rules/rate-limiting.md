---
id: rate-limiting
tier: 1
tooling: [convention]
enforcement: strict
paths:
  - "app/routers/**/*.py"
  - "pyproject.toml"
---

# Rate Limiting (fastapi-limiter)

Enforces the pinned limiter version and the per-endpoint limits.

## Rules

### RL1. Pin `fastapi-limiter==0.1.6`

**Tooling:** `convention`

The dependency is pinned to `0.1.6`. Version `0.2.x` dropped the `times`/`seconds` kwargs and breaks every `RateLimiter(...)` call.

```toml
# ✅ pyproject.toml
"fastapi-limiter==0.1.6",
```

```python
# ❌ FAILS on 0.2.x — kwargs removed
RateLimiter(times=60, seconds=60)  # TypeError under 0.2.x
```

**Why:** Upgrading silently changes the constructor signature, so an unpinned bump takes down every rate-limited endpoint.

### RL2. Apply limits as route dependencies

**Tooling:** `convention`

Attach limits via `dependencies=[Depends(RateLimiter(...))]`. Auth endpoints: 10 requests / 60s. `POST /api/v1/activities/log`: 60 requests / 60s.

```python
# ✅ CORRECT — activity log limiter
@router.post(
    "/log",
    response_model=LogActivityResponse,
    dependencies=[Depends(RateLimiter(times=60, seconds=60))],
)
async def log_activity(...) -> LogActivityResponse:
    return await service.log_activity(current, payload)

# ✅ CORRECT — auth endpoint limiter
dependencies=[Depends(RateLimiter(times=10, seconds=60))]
```

**Why:** Auth endpoints are brute-force targets (tight 10/60s); the activity-log limit (60/60s) protects the write-heavy XP transaction while allowing normal logging bursts.

## Verification

```bash
uv run pytest -q app/tests -k "rate" && grep -q 'fastapi-limiter==0.1.6' pyproject.toml
```
