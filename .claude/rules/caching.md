---
id: caching
tier: 1
tooling: [convention]
enforcement: strict
paths:
  - "app/services/activity_service.py"
  - "app/admin/hooks.py"
  - "app/models/activity.py"
---

# Caching (Redis template cache)

Enforces the single owner and invalidation path for the activity-template cache.

## Rules

### CA1. `activities:templates` is owned by `ActivityService.list_templates`

**Tooling:** `convention`

The key `activities:templates` (constant `TEMPLATES_CACHE_KEY`) has a 5-minute TTL (`TEMPLATES_CACHE_TTL = 300`) and is read/written only in `ActivityService.list_templates`. No other code path sets this key.

```python
# ✅ CORRECT — read-through with TTL, in the owning method
async def list_templates(self) -> list[ActivityTemplateOut]:
    cached = await self.redis.get(TEMPLATES_CACHE_KEY)
    if cached is not None:
        return [ActivityTemplateOut.model_validate_json(item) for item in json.loads(cached)]
    templates = await self.templates.list_enabled()
    payload = [ActivityTemplateOut.model_validate(t).model_dump() for t in templates]
    await self.redis.set(TEMPLATES_CACHE_KEY, json.dumps(payload), ex=TEMPLATES_CACHE_TTL)
    return [ActivityTemplateOut.model_validate(item) for item in payload]
```

**Why:** A single owner keeps the serialization format and TTL in one place; scattered writers cause format drift and stale reads.

### CA2. Invalidation happens via ORM event hooks — go through the ORM

**Tooling:** `convention`

The cache is invalidated automatically by SQLAlchemy `after_insert`/`after_update`/`after_delete` hooks on `ActivityTemplate` and `ActivityEffect` (`app/admin/hooks.py`), plus an `after_commit` safety net. Any code that mutates templates/effects must go through the ORM (SQLAdmin does). Raw SQL bypasses the hooks and leaves the cache stale.

```python
# ❌ FORBIDDEN — raw SQL update skips the hooks; cache goes stale
await session.execute(
    update(ActivityTemplate).where(ActivityTemplate.id == tid).values(is_enabled=False)
)

# ✅ CORRECT — ORM mutation fires the invalidation hook
template = await session.get(ActivityTemplate, tid)
template.is_enabled = False
await session.commit()
```

**Why:** Invalidation is wired to ORM events, not to SQL statements. Bypassing the ORM serves stale templates for up to the full 5-minute TTL.

## Verification

```bash
uv run pytest -q app/tests -k "cache or template"
```
