# ADR 0005 — Stats as seeded DB rows

- **Status:** Accepted
- **Date:** 2026-05-24

## Context

The PRD lists seven stats: Strength, Health, Intelligence, Mental State, Endurance, Finance, Social Skills. In MVP they are fixed. Two storage models:

1. **Python `enum` (no `stats` table)** — `UserStat.stat` is the enum string; `ActivityEffect.stat` likewise. Fewer joins, no seed migration, simpler schema.
2. **`stats` table seeded via Alembic** *(chosen)* — every other table references `stats.id` (UUID). Slightly more joins, additional seed migration.

## Decision

- `Stat` is an ORM model with `id: UUID`, `key: str (unique)`, `display_name: str`, `icon: str`.
- The seven defaults are inserted by Alembic `0003_seed_stats.py` (idempotent — `downgrade()` deletes by `key`).
- All foreign keys (`UserStat.stat_id`, `ActivityEffect.stat_id`, `ActivityLogEffect.stat_id`) reference `stats.id`.

## Consequences

**Positive**
- Display name and icon can change without a code deploy (admin or migration).
- A future "introduce a new stat" feature is straightforward: a single migration plus a backfill of `user_stats`.
- Referential integrity at the database level — no orphan stat keys.

**Negative**
- Every join through `stats` is an extra index lookup. Acceptable: stats are tiny (7 rows) and fully cacheable.
- Code that needs the canonical key (e.g. `LevelingService` rules per stat — not present today) has to look up by `key`. We accept the indirection.
- New environments require the seed migration to run before any user can be registered (the registration flow calls `UserService.initialize_user_stats`, which depends on `Stat` rows existing).

## Compliance

- Never hardcode stat names or UUIDs in application code. Look up `Stat` rows by `key` if you need to reference one.
- The seven stat keys (`strength`, `health`, `intelligence`, `mental_state`, `endurance`, `finance`, `social_skills`) are part of the seed migration; tests assume they exist.
