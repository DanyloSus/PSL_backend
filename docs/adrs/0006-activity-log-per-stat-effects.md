# ADR 0006 — Activity log keeps per-stat effect rows alongside a total

- **Status:** Accepted
- **Date:** 2026-05-24

## Context

`ActivityLog` records what the user did. A single activity can move several stats with different signs (e.g. Alcohol: +3 social, −10 health, −3 mental). The TDD shows `ActivityLog.totalXpApplied: number` — one scalar. That's ambiguous when multiple stats move.

Options:

1. **Single `total_xp_applied` only** — minimal storage; loses per-stat detail; the activity-history view would have to re-derive deltas from the template definition (which may have changed since the log was written).
2. **Per-stat detail in a JSONB column** — single row per log; queryable in Postgres; less normalized; per-stat reporting needs JSON path queries.
3. **Per-stat rows + total scalar** *(chosen)* — normalized; full audit; total is denormalized for fast aggregation.

## Decision

Two tables:

- `activity_logs` — `id`, `user_id`, `template_id`, `quantity`, `total_xp_applied`, `created_at`. One row per logged activity. `total_xp_applied` is the sum of applied (post-floor) deltas.
- `activity_log_effects` — `id`, `log_id`, `stat_id`, `xp_applied`. One row per stat that the activity affected, with the **actual** post-floor delta written into `xp_applied`.

Both rows are inserted in the same transaction (`ActivityLogRepository.create`).

The activity-history endpoint returns the per-stat breakdown so the frontend can show, for each log entry, which stats moved and by how much without re-reading the (possibly mutated) template.

## Consequences

**Positive**
- Activity history is truthful even if an admin retunes a template later. The applied deltas at the time of the log are preserved.
- Per-stat aggregations ("how much strength did the user gain this week?") are a simple `SUM(xp_applied) WHERE stat_id = ? AND created_at >= ?` against `activity_log_effects`.
- `total_xp_applied` keeps "give me the sum across all stats per log" O(1) without scanning the effects table.

**Negative**
- One extra table and FK to maintain. Inserts cost N+1 rows per log instead of 1.
- `total_xp_applied` can drift from `SUM(activity_log_effects.xp_applied)` if a future code path writes one without the other. Mitigated by keeping `ActivityLogRepository.create` the single insertion point.

## Compliance

- Never mutate `activity_logs` or `activity_log_effects` after insert. They are an audit trail.
- New aggregation queries should prefer `activity_log_effects` over `activity_logs.total_xp_applied` when per-stat breakdown is relevant.
