---
id: decision-records
tier: 1
tooling: [convention]
enforcement: convention
paths:
  - "docs/adrs/**/*.md"
---

# Decision Records (ADRs)

Guides when to record an architecture decision and when to skip it. The `adr_reminder` hook nudges when a change looks architecture-shaping.

## Rules

### DR1. Record architecture-shaping, hard-to-reverse decisions

**Tooling:** `convention` (use `/adr`)

Write an ADR in `docs/adrs/` when a decision shapes the architecture and would be costly to reverse:

- Auth scheme changes (token model, cookie/CSRF strategy, session handling)
- Layer boundary changes (what routers/services/repositories may do)
- Cross-cutting patterns (error handling, caching strategy, logging contract)
- Core dependency choices (swapping the ORM, the limiter, the cache)
- Schema/migration decisions with lasting consequences (PK strategy, denormalization, XP/level storage model)

```
✅ ADR: "Refresh tokens stored as sha256 hashes, rotated on every refresh"
✅ ADR: "activities:templates cached in Redis, invalidated via ORM event hooks"
✅ ADR: "global_xp is a stored running sum; global_level is recomputed, never dropped"
```

**Why:** These decisions constrain future work and are expensive to undo. A short record captures the WHY so the next contributor doesn't relitigate or accidentally reverse it.

### DR2. Skip reversible implementation detail

**Tooling:** `convention`

Do not write an ADR for local, easily-changed choices. Code and commit messages already cover them.

```
❌ ADR: "renamed a local variable to user_stat"
❌ ADR: "added a min_length=3 constraint to the username field"
❌ ADR: "extracted a helper function in activity_service.py"
```

**Why:** ADRs are for durable direction, not diffs. Recording trivia buries the decisions that matter and turns the log into noise.

## Verification

```bash
ls docs/adrs/ && echo "run /adr to add a new decision record"
```
