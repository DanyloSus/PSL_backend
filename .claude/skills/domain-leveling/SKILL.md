---
name: domain-leveling
description: XP/level engine invariants. LevelingService threshold/level formulas, stat XP>=0 & level>=1 & never-decrease, log delta = xp_change * effective_quantity floored at 0, BINARY forces quantity=1, single transaction per log.
metadata:
  version: "1.0"
  stack: python-fastapi
  related-skills:
    - sqlalchemy-repository
    - pydantic-schemas
    - fastapi-endpoint
tier: 1
triggers:
  - xp
  - level
  - leveling
  - stat
  - activity log
  - quantity
summary: |
  XP/level rules (app/services/leveling.py + activity_service.py):
  threshold_for(L)=floor(100*(L-1)**1.5) (L<=1 -> 0); level_from_xp(xp) = highest L
  whose threshold <= xp, min 1. Invariants: stat XP >= 0 floor, level >= 1, levels
  NEVER decrease (max(old, computed)). Per-effect delta = effect.xp_change *
  effective_quantity, applied then floored at 0. BINARY templates force
  effective_quantity=1 (client value ignored); QUANTITY validates against the
  template's min/max bounds. One DB transaction per log: load template+effects →
  lock+update each UserStat → update User.global_xp/level → write ActivityLog +
  per-stat ActivityLogEffect → commit once.
---

# Domain: XP / Leveling Engine

## Overview

| Aspect       | Details                                                        |
| ------------ | ------------------------------------------------------------- |
| Goal         | Apply activity logs to stats/global XP with correct invariants |
| When         | Any change to XP math, quantity handling, or the log txn       |
| Verification | `uv run pytest -q` (`test_leveling.py`, `test_activities.py`)  |

## Critical rules

**Stat XP ≥ 0 (floored), level ≥ 1, levels NEVER decrease (`max(old, computed)`). BINARY → `effective_quantity = 1` server-side; the client value is ignored. One transaction per log.**

## Concepts

### Level formulas (`LevelingService`, `app/services/leveling.py`)

Pure static methods. Threshold to *reach* level L is `floor(100 * (L-1)**1.5)`; level 1 starts at xp 0.

```python
class LevelingService:
    @staticmethod
    def threshold_for(level: int) -> int:
        if level <= 1:
            return 0
        return int(100 * (level - 1) ** 1.5)

    @staticmethod
    def level_from_xp(xp: int) -> int:
        if xp <= 0:
            return 1
        level = 1
        while LevelingService.threshold_for(level + 1) <= xp:
            level += 1
        return level
```

`progress(xp)` returns `LevelProgress(level, xp_into_level, xp_for_next, xp_total)` for the stats view.

### Quantity resolution

```python
if template.input_type is ActivityInputType.BINARY:
    effective_qty = 1
else:
    if not template.min_quantity <= payload.quantity <= template.max_quantity:
        raise QuantityOutOfRangeError(
            f"quantity must be between {template.min_quantity} and {template.max_quantity}"
        )
    effective_qty = payload.quantity
```

BINARY ignores the client quantity entirely. QUANTITY validates against the template's data-dependent bounds and raises `QuantityOutOfRangeError` (422) — a `DomainError`, not a schema error.

### Applying an effect (floors + never-decrease)

Delta per stat is `effect.xp_change * effective_qty`. XP is floored at 0; the *actual* applied delta (post-floor) is what gets summed and logged. Level is recomputed but clamped so it never drops.

```python
raw_delta = effect.xp_change * effective_qty
old_xp = user_stat.xp
new_xp = max(0, old_xp + raw_delta)
actual_delta = new_xp - old_xp
user_stat.xp = new_xp

old_level = user_stat.level
new_level = max(old_level, LevelingService.level_from_xp(new_xp))
user_stat.level = new_level
```

Global XP mirrors this: `User.global_xp` accumulates the summed `actual_delta`, floored at 0; `global_level = max(old, level_from_xp(new_global_xp))`.

### One transaction per log

`ActivityService.log_activity` does the whole thing in a single session transaction:

1. `templates.get_with_effects(id)` — 404 `TemplateNotFoundError` if missing, 409 `TemplateDisabledError` if `not is_enabled`.
2. Resolve `effective_qty` (BINARY/QUANTITY as above).
3. For each effect: `user_stats.get_for_update(...)` (row lock; create at xp=0/level=1 if absent), apply delta + floor + level clamp.
4. Update `User.global_xp` / `global_level`.
5. `logs.create(...)` writes the `ActivityLog` + one `ActivityLogEffect` per stat (actual deltas).
6. `await self.session.commit()` — once, at the end.

Locking each `UserStat` with `with_for_update()` serializes concurrent logs so XP can't be lost to a race.

## Patterns

### Change XP math

1. Edit `LevelingService` (formulas) or the apply loop in `activity_service.log_activity`.
2. Preserve invariants: floor XP at 0, clamp level with `max(old, computed)`.
3. Keep it one transaction — no partial commits.
4. Update `test_leveling.py` (formula) and `test_activities.py` (end-to-end deltas).

## Common mistakes

| Mistake | Fix |
| ------- | --- |
| Trusting client quantity for BINARY | Force `effective_qty = 1` |
| Letting XP go negative | `new_xp = max(0, old_xp + raw_delta)` |
| Letting level drop | `new_level = max(old_level, computed)` |
| Logging `raw_delta` after flooring | Log `actual_delta = new_xp - old_xp` |
| Committing per effect | One `commit()` after all effects + log rows |
| Updating `UserStat` without a lock | `user_stats.get_for_update(...)` |
| Quantity bound as a schema `Field` | Data-dependent → `QuantityOutOfRangeError` in the service |

## Checklist

- [ ] BINARY forces quantity 1; QUANTITY validated against template bounds
- [ ] Stat/global XP floored at 0; levels use `max(old, computed)`
- [ ] Summed/logged value is the post-floor `actual_delta`
- [ ] `UserStat` locked with `with_for_update` before mutation
- [ ] Single `commit()` per log; ActivityLog + per-stat effects written
