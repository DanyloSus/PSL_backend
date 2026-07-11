---
name: redis-caching
description: Redis template cache (activities:templates, 5-min TTL) owned by ActivityService, invalidated via ORM event hooks; mutate templates through the ORM. Plus rate limiting (fastapi-limiter 0.1.6).
metadata:
  version: "1.0"
  stack: python-fastapi
  related-skills:
    - sqlalchemy-repository
    - fastapi-endpoint
tier: 1
triggers:
  - cache
  - redis
  - invalidate
  - template cache
  - rate limit
summary: |
  The activity-templates list is cached in Redis under key `activities:templates`
  with a 5-minute TTL, owned by ActivityService.list_templates (caches template
  IDs, revalidates against the DB). Invalidation is automatic: ORM event hooks in
  app/admin/hooks.py delete the key on insert/update/delete of ActivityTemplate or
  ActivityEffect. Raw SQL bypasses hooks — mutate templates through the ORM
  (SQLAdmin does). Redis also backs rate limiting via fastapi-limiter==0.1.6
  (pinned; 0.2.x dropped times/seconds): auth 10/60s, POST /activities/log 60/60s.
---

# Redis: Template Cache & Rate Limiting

## Overview

| Aspect       | Details                                                       |
| ------------ | ------------------------------------------------------------ |
| Goal         | Cache the templates list correctly; keep it fresh via ORM hooks |
| When         | Template read path, cache changes, rate-limit tuning          |
| Verification | `uv run pytest -q` (`test_activities.py`, `test_admin.py`)    |

## Critical rules

**Mutate `ActivityTemplate`/`ActivityEffect` through the ORM, never raw SQL — invalidation rides on ORM events. Key `activities:templates`, TTL 300s, owned by `ActivityService.list_templates`. `fastapi-limiter` is pinned to `0.1.6`.**

## Concepts

### The cache (`ActivityService.list_templates`)

Stores the ordered list of template IDs (not full rows). On read: fetch cached IDs, reload those rows via the repo, and only trust the cache if the row count still matches (guards against deleted rows); otherwise rebuild from `list_enabled()` and re-set with a TTL.

```python
TEMPLATES_CACHE_KEY = "activities:templates"
TEMPLATES_CACHE_TTL = 300  # 5 minutes

async def list_templates(self) -> list[ActivityTemplateOut]:
    cached = await self.redis.get(TEMPLATES_CACHE_KEY)
    if cached:
        ids = json.loads(cached)
        rows = await self.templates.list_by_ids(ids)
        if len(rows) == len(ids):
            return [self._template_out(t) for t in rows]

    templates = await self.templates.list_enabled()
    await self.redis.set(
        TEMPLATES_CACHE_KEY, json.dumps([str(t.id) for t in templates]), ex=TEMPLATES_CACHE_TTL
    )
    return [self._template_out(t) for t in templates]
```

### Invalidation via ORM event hooks (`app/admin/hooks.py`)

`register_cache_hooks()` listens for `after_insert`/`after_update`/`after_delete` on `ActivityTemplate` and `ActivityEffect`, plus an `after_commit` safety net, and schedules a `redis.delete(TEMPLATES_CACHE_KEY)` on the running event loop.

```python
def register_cache_hooks() -> None:
    for model in (ActivityTemplate, ActivityEffect):
        event.listen(model, "after_insert", _on_change)
        event.listen(model, "after_update", _on_change)
        event.listen(model, "after_delete", _on_change)
    event.listen(Session, "after_commit", after_commit)  # safety net
```

Because it's an ORM event, **raw SQL bypasses it**. SQLAdmin mutates via the ORM, so admin edits invalidate correctly. If you ever write templates in a migration or raw statement, delete the key yourself (`ActivityService.invalidate_templates_cache`).

### Rate limiting (`fastapi-limiter==0.1.6`)

Backed by Redis, attached as a route dependency. The pin matters: `0.2.x` dropped the `times`/`seconds` kwargs.

```python
from fastapi_limiter.depends import RateLimiter

# auth endpoints
dependencies=[Depends(RateLimiter(times=10, seconds=60))]
# POST /api/v1/activities/log
dependencies=[Depends(RateLimiter(times=60, seconds=60))]
```

Rate-limit state is per-Redis; tests FLUSHDB between cases so limits don't bleed across tests.

## Patterns

### Add a cached read

1. Pick a stable key + TTL; own the read in one service method.
2. Cache minimal data (IDs) and revalidate against the DB on hit.
3. If the data has ORM mutations, register an event hook to invalidate; otherwise call an explicit `invalidate_*` after writes.

### Change a rate limit

1. Adjust `RateLimiter(times=..., seconds=...)` on the route.
2. Keep `fastapi-limiter` pinned to `0.1.6`.

## Common mistakes

| Mistake | Fix |
| ------- | --- |
| Mutating templates via raw SQL | Use the ORM so hooks fire (or call `invalidate_templates_cache`) |
| Caching full ORM rows | Cache IDs; reload + revalidate on hit |
| No TTL on the key | Always set `ex=TEMPLATES_CACHE_TTL` |
| Upgrading `fastapi-limiter` | Stay on `0.1.6` (`times`/`seconds` kwargs) |
| Relying on rate-limit state across tests | Redis is FLUSHed per test |

## Checklist

- [ ] Reads owned by one service method with a stable key + TTL
- [ ] Template writes go through the ORM (hooks invalidate)
- [ ] Cache stores IDs and revalidates against the DB
- [ ] `fastapi-limiter` pinned `0.1.6`; limits set on hot routes
