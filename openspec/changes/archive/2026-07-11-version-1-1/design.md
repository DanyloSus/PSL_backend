## Context

PSL is a layered async FastAPI backend (router → service → repository → SQLAlchemy). Version 1.1 touches three areas — onboarding, level-up feedback, and activity history — across the `User` and activity aggregates. `LevelingService.progress` already computes `xp_into_level`/`xp_for_next`; the leveling work is exposure, not new math. Activity history already has a service (`ActivityService.get_history`) and repo (`ActivityLogRepository.list_for_user`) using a `before`/`limit` cursor. Log categories from PRD §18 are out of scope.

## Goals / Non-Goals

**Goals:**
- Persist and expose an onboarding-completed flag with a completion endpoint.
- Add progress-to-next-level and levels-gained data to activity-log responses (per stat + global).
- Enrich, filter, and paginate activity history; allow deleting a log with correct XP reversal.
- Keep all layer rules intact: thin routers, no SQL outside repos, `DomainError` subclasses, all-async, typed schemas.

**Non-Goals:**
- Log categories (dropped).
- Changing the level formula or the levels-never-decrease invariant.
- Any streak/quest/achievement work (later versions).
- New rate-limit surfaces or cache keys.

## Decisions

### D1. Onboarding: single boolean column, not a state machine
Add `User.onboarding_completed: Mapped[bool]` with `server_default="false"`, `default=False`. A dedicated `POST /users/me/complete-onboarding` sets it via `UserRepository.set_onboarding_completed`. **Why not** an onboarding-steps table: the PRD asks only for "simple onboarding"; the frontend owns the flow, the backend only needs a done/not-done bit. Idempotency falls out for free (set-to-true is a no-op when already true).

### D2. Level-up feedback: reuse `LevelingService.progress`, enrich schemas
Extend `AppliedEffect` with `xp_into_level`, `xp_for_next`, `previous_level`, `levels_gained`, and `LogActivityResponse` with global `xp_into_level`, `xp_for_next`, `previous_global_level`, `global_levels_gained`. The service already tracks `old_level`/`new_level` per stat and `old_global_level`/`new_global_level`; `levels_gained = new_level - old_level` (≥0 by the ratchet). Progress fields come from `LevelingService.progress(new_xp)`. **Why not** a new endpoint: the data is already produced inside `log_activity`; surfacing it costs no extra query.

### D3. History response becomes an object (BREAKING)
Introduce `ActivityHistoryPage { items, total, has_more, next_before }`. `has_more` is derived by fetching `limit + 1` rows (repo returns up to `limit+1`; service trims and sets the flag) plus a separate `count` query for `total`. `next_before` is the `created_at` of the last returned item, or `null`. **Why not** keep a bare list with headers: an explicit wrapper is self-documenting, typed, and testable, and matches how the client will drive infinite scroll. The break is acceptable pre-launch (no external consumers).

### D4. History enrichment via eager-loaded relationships
`ActivityLog` → `template` and `ActivityLogEffect` → `stat` are loaded so the service can populate titles and stat display fields. The log repo already returns logs with `effects_applied` (selectin). Add a join/`selectinload` for `template` and each effect's `stat` in `ActivityLogRepository.list_for_user`. Titles reflect the template's **current** value (denormalization of the historical title is out of scope).

### D5. Filtering pushed into the repository
`template_id`, `from`, `to` become optional args on `ActivityLogRepository.list_for_user` and a parallel `count_for_user`, added to the `WHERE` clause alongside the existing `before`/`user_id`. Services pass query params straight through; no SQL leaves the repo (L2).

### D6. Delete-log: reverse within one transaction, honor floors and ratchet
New `DELETE /users/me/activity-history/{log_id}`. Service loads the log **scoped to the user** (`get_owned(user_id, log_id)`); missing/foreign → `LogNotFoundError` (404). For each `ActivityLogEffect`, lock the `UserStat` and subtract `xp_applied` floored at 0; subtract `total_xp_applied` from `user.global_xp` floored at 0; recompute levels via `level_from_xp` but **never lower** the stored level (`max(stored, recomputed)` — same ratchet as logging). Delete the log (cascades `ActivityLogEffect`). Single commit. **Why floor-and-recompute-without-lowering**: matches DX1; a user who deletes a mistaken log should not be demoted, only lose the XP.

### D7. New error + no new cross-layer surface
`LogNotFoundError(DomainError)` with `status_code = 404` in `app/core/exceptions.py`, mapped by the existing global handler. Routers stay one-liners; delete route is CSRF-guarded like any mutation.

## Risks / Trade-offs

- [History response shape break] → Pre-launch, no external clients; the frontend for 1.1 is built against the new shape. Documented as BREAKING in the proposal.
- [`total` count adds a second query per history call] → Acceptable at MVP scale; the query is indexed on `user_id`/`created_at`. Can be cached later if it shows up in profiling.
- [Reversal-without-level-drop can leave `level` higher than `level_from_xp(xp)`] → Intentional (ratchet, DX1). Stat XP and level can be temporarily "out of sync" downward, exactly as after a negative log today.
- [Enriched titles reflect current template, not the title at log time] → Accepted; historical denormalization is out of scope and templates rarely rename.
- [Concurrent delete + log on the same stat] → `UserStat` row lock (`get_for_update`, already used by logging) serializes them.

## Migration Plan

1. Alembic migration adds `users.onboarding_completed BOOLEAN NOT NULL DEFAULT false` (zero-padded next revision; reversible via `op.drop_column`). No data backfill needed — the server default covers existing rows.
2. Deploy is additive except the history response shape; ship backend and the 1.1 frontend together.
3. Rollback: `alembic downgrade -1` drops the column; the new endpoints simply 404 if the older router is restored. No destructive data change.

## Open Questions

- None blocking. (If a GitHub issue is later opened for Version 1.1, add `Parent: #<n>` to the specs.)
