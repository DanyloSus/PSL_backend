# ADR 0004 — XP / level invariants

- **Status:** Accepted
- **Date:** 2026-05-24

## Context

The PRD allows negative-XP activities and originally says "if XP decreases enough, level may decrease in MVP." Two questions need single answers before code:

1. Can stat XP go below 0?
2. Can a level decrease once reached?
3. How should `BINARY` (e.g. "Had breakfast") templates handle a quantity that the client sends anyway?

Implementation paths considered:

- **Allow negative XP, allow level drop** — matches PRD literally but feels punishing and creates a moving baseline for "progress over time". Hostile for a self-improvement product.
- **Floor XP at 0, allow level drop** — softer but still introduces level oscillation around thresholds.
- **Floor XP at 0, level never drops** *(chosen)* — visible progress is monotonic. Negative actions still cost progress (xp toward the next level shrinks) without erasing past achievement.

For BINARY, accepting client-supplied quantity is exploitable (one POST claims 99× the action) without observable benefit.

## Decision

- **Stat XP floor at 0.** Each effect's raw delta is `effect.xp_change * effective_quantity`; the new XP is `max(0, current + raw_delta)`. The *applied* delta (what gets recorded in `ActivityLogEffect`) is `new_xp - old_xp`.
- **Stat level ≥ 1, never decreases.** `LevelingService.level_from_xp(xp)` computes the cumulative level a user would reach with that XP total. The persisted level is `max(persisted_level, computed_level)`.
- **`User.global_xp` and `User.global_level`** follow the same floor / monotonic rules.
- **Level formula:** cumulative XP to reach level L is `floor(100 * (L-1)**1.5)`. Level 1 starts at xp=0; level 2 at xp=100; level 3 at xp≈283. Fast early progression, slower late. Provided by `LevelingService.threshold_for(L)`, `level_from_xp(xp)`, and `progress(xp)`.
- **`BINARY` templates force `quantity = 1` server-side** in `ActivityService.log_activity`. The client value is ignored.

## Consequences

**Positive**
- A user's level chart is monotonically non-decreasing. Visible regression cannot happen, which matches the "I am evolving" emotional promise from PRD §5.
- Negative effects still cost ground (they consume buffer XP toward the next level) so logging them is not free.
- The formula is closed-form, fast to evaluate, and deterministic — no caching needed.
- BINARY enforcement closes a trivial cheat vector.

**Negative**
- Diverges from PRD §9.4 literal text ("level may decrease in MVP"). We preserve product intent by keeping negative effects meaningful (xp does decrease toward 0) while honoring "I am evolving" — explicitly waived in design review.
- Eternal-monotonic level means a balancing mistake (template with huge `xp_change`) is hard to undo from the user's side. Admin can correct via direct DB update if needed.

## Compliance

- Never bypass `LevelingService` for level math. If a future feature needs a different curve, add a new method, do not edit existing constants.
- `log_activity` is the only place that mutates `UserStat.xp` / `UserStat.level` / `User.global_xp` / `User.global_level` in the API path. Admin tools must keep the same invariants.
