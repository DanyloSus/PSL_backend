---
id: domain-xp
tier: 1
tooling: [convention, pytest]
enforcement: strict
paths:
  - "app/services/activity_service.py"
  - "app/services/leveling.py"
  - "app/repositories/user_stat_repo.py"
---

# Domain Rules — XP / Levels / Quantity

Enforces the XP/level invariants and quantity handling that define PSL's core loop.

## Rules

### DX1. XP floor at 0, level floor at 1, levels never decrease

**Tooling:** `convention`, `pytest`

Stat XP is clamped at `>= 0`. Stat and global level are `>= 1`. A recomputed level never drops below the stored one.

```python
# ❌ FORBIDDEN — lets XP go negative and level fall
user_stat.xp += delta
user_stat.level = LevelingService.level_from_xp(user_stat.xp)

# ✅ CORRECT — floor XP, never lower the level
user_stat.xp = max(0, user_stat.xp + delta)
recomputed = LevelingService.level_from_xp(user_stat.xp)
user_stat.level = max(user_stat.level, recomputed)
```

**Why:** Levels are a one-way ratchet in the MVP — a user must never feel demoted. Negative XP would corrupt the level computation.

### DX2. BINARY templates force quantity = 1 server-side

**Tooling:** `convention`, `pytest`

For a template whose `input_type` is BINARY, the effective quantity is forced to 1 on the server. The client-supplied `quantity` is ignored.

```python
# ✅ CORRECT
if template.input_type is ActivityInputType.BINARY:
    effective_quantity = 1
else:
    effective_quantity = payload.quantity
```

**Why:** A BINARY activity is "done or not" — multiplying its XP by a client-chosen quantity would let clients inflate rewards.

### DX3. Delta = `xp_change * effective_quantity`, floored at 0

**Tooling:** `convention`

Per-stat log delta is `effect.xp_change * effective_quantity`, then floored at 0. `User.global_xp` accumulates the running sum of applied deltas; `global_level` is recomputed (never dropped).

```python
# ✅ CORRECT
delta = max(0, effect.xp_change * effective_quantity)
user_stat.xp = max(0, user_stat.xp + delta)
user.global_xp += delta
user.global_level = max(user.global_level, LevelingService.level_from_xp(user.global_xp))
```

**Why:** A single consistent delta formula keeps per-stat XP, global XP, and levels in agreement across every log.

### DX4. Quantity within the template's bounds

**Tooling:** `convention`, `pytest`

Non-BINARY quantity must fall within the template's `min_quantity`/`max_quantity`. Out-of-range raises `QuantityOutOfRangeError` (422). This is a domain check in the service, in addition to the static `ge/le` bound on the schema.

```python
# ✅ CORRECT
if not (template.min_quantity <= payload.quantity <= template.max_quantity):
    raise QuantityOutOfRangeError()
```

**Why:** Bounds are per-template data, not a static schema constant, so they must be validated where the template is loaded. The schema's `ge/le` only catches absolute limits.

### DX5. One transaction per log

**Tooling:** `convention`

A log is a single transaction: load template → for each effect lock+update `UserStat` → write `ActivityLog` + per-stat `ActivityLogEffect` rows. Use the leveling formula `threshold_for(L) = floor(100 * (L-1)**1.5)`.

**Why:** Atomicity guarantees XP, levels, and log rows never partially apply. Row locking on `UserStat` prevents lost updates under concurrent logs.

## Verification

```bash
uv run pytest -q app/tests -k "xp or level or quantity"
```
