# ADR 0007 — Redis cache for activity templates with ORM-event invalidation

- **Status:** Accepted
- **Date:** 2026-05-24

## Context

`GET /api/v1/activities` is on the dashboard hot path: every page load lists available templates with their per-stat effects. Templates change only when an admin edits them — orders of magnitude less often than reads.

Options:

1. **No cache.** Two queries (templates + their effects) per request. Cheap today, expensive once we have hundreds of templates and thousands of concurrent users.
2. **In-process LRU cache.** Simple but does not survive worker restarts and is per-process — multiple uvicorn workers each cache their own copy and miss each other's invalidations.
3. **Redis cache with TTL + active invalidation on admin write** *(chosen)* — survives restarts, shared across workers, bounded staleness via TTL.

How to invalidate: cron / sidecar / explicit call from admin endpoints / **SQLAlchemy ORM event listeners on the Template + Effect models** (chosen).

## Decision

- Key: `activities:templates`. Value: JSON array of template UUIDs (as strings).
- TTL: 300 seconds (5 minutes). Bounded staleness if invalidation ever misses.
- Read path (`ActivityService.list_templates`):
  1. `redis.get("activities:templates")`. If present, look up templates by id, return them if the count matches.
  2. Otherwise read enabled templates from Postgres, write the id list to Redis with TTL, return.
- Write path (`app/admin/hooks.py`):
  - SQLAlchemy `event.listen` for `after_insert`, `after_update`, `after_delete` on `ActivityTemplate` and `ActivityEffect` — schedule `redis.delete("activities:templates")` via `asyncio.get_running_loop().create_task(...)`.
  - Belt-and-braces: a `Session` `after_commit` listener also flushes the key if any `ActivityTemplate` / `ActivityEffect` was added, dirtied, or deleted in the transaction.

## Consequences

**Positive**
- Reads are a single Redis GET + a primary-key fetch in the warm case.
- Bounded staleness: a missed invalidation will self-heal within 5 minutes.
- SQLAdmin uses the ORM, so admin mutations always fire the events.
- Belt-and-braces `after_commit` listener catches mutations done outside the per-model events (bulk operations, cascade deletes).

**Negative**
- Raw SQL writes bypass ORM events. If an operator runs `UPDATE activity_templates ... ` directly in psql, the cache will be up to 5 minutes stale. Documented in `CLAUDE.md` and `psl-admin` skill: changes must go through the ORM, or call `ActivityService.invalidate_templates_cache()` manually.
- Cache key is intentionally coarse — any change blows the whole list. Acceptable: the list is bounded and the rebuild is cheap.
- A scheduled task created with `create_task` is fire-and-forget; if Redis is unavailable the deletion is logged-and-dropped. Acceptable: the TTL is the safety net.

## Compliance

- New admin paths that mutate templates / effects must go through the ORM.
- New caching needs should follow the same pattern: explicit key, explicit TTL, explicit invalidation hooks. Do not introduce ad-hoc caches in routers or repositories.
