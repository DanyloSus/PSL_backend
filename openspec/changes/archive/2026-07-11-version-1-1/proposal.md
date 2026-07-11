## Why

PRD §18 Version 1.1 asks for a friendlier first-run and clearer progression. Today the backend has no way to know whether a user finished onboarding, log responses expose only bare `leveled_up` booleans (no progress-to-next data), and activity history returns raw IDs with no titles, no filtering, no page metadata, and no way to remove a mistaken log. This change closes those gaps so the client can build simple onboarding, richer level-up feedback, and a usable history view.

Parent issue: none yet (PRD §18 Version 1.1). This change owns requirement IDs in areas `ONBOARD`, `LEVELUP`, and `HISTORY`.

## What Changes

- **Onboarding flag**: add `onboarding_completed` boolean to `User` (default `false`), expose it on the `/auth/me` and `/users/me` responses, and add `POST /users/me/complete-onboarding` to mark it done (idempotent).
- **Level-up feedback**: enrich `LogActivityResponse` and its per-stat `AppliedEffect` with progress fields — `xp_into_level`, `xp_for_next`, `previous_level`, and `levels_gained` — for each stat and for the global level. Reuses the existing `LevelingService.progress`; no formula change.
- **Activity history — enrich**: each history entry gains the template `title`/`description`/`input_type` and each effect gains the stat `key`/`display_name`/`icon`, so the client no longer joins client-side.
- **Activity history — filter**: `GET /users/me/activity-history` accepts optional `template_id`, `from`, and `to` (created-at range) filters, composable with the existing `before` cursor and `limit`.
- **Activity history — pagination metadata**: the endpoint returns a wrapper carrying the page `items`, `total` count (for the active filter), and `has_more` / `next_before` cursor. **BREAKING**: response shape changes from a bare list to an object.
- **Activity history — delete a log**: `DELETE /users/me/activity-history/{log_id}` removes a user's own log and reverses its applied XP within a single transaction, honoring the XP≥0 floor and the levels-never-decrease invariant (level is recomputed but never lowered).
- Log categories from PRD §18 are **out of scope** (dropped for this change).

## Capabilities

### New Capabilities
- `onboarding`: tracking and completion of first-run onboarding state per user.
- `activity-history`: retrieval, filtering, pagination, enrichment, and deletion of a user's activity logs.
- `leveling-feedback`: progress-to-next-level data returned on stat views and activity-log responses.

### Modified Capabilities
<!-- none: baseline specs are empty; these areas are captured as new retro-specs -->

## Impact

- **Models**: `app/models/user.py` (+`onboarding_completed`). New Alembic migration for the column.
- **Schemas**: `app/schemas/user.py`, `app/schemas/auth.py` (`UserPublic` +flag), `app/schemas/activity.py` (enriched history entry/effect, new history-page wrapper, enriched `AppliedEffect`/`LogActivityResponse`).
- **Services**: `app/services/user_service.py` (complete-onboarding), `app/services/activity_service.py` (enriched/filtered/paginated history, delete-log, progress in log response).
- **Repositories**: `app/repositories/activity_log_repo.py` (filtered list + count + get-owned + delete), `app/repositories/user_repo.py` (set onboarding flag).
- **Routers**: `app/routers/users.py` (complete-onboarding, history query params + delete route), `app/routers/auth.py` (flag surfaces via schema only).
- **Errors**: new `LogNotFoundError` (404) in `app/core/exceptions.py` for delete of a missing/foreign log.
- **APIs**: `/auth/me`, `/users/me`, `/users/me/stats` unchanged shape except added fields; `/activities/log` response gains fields; `/users/me/activity-history` response shape changes (BREAKING) and gains filter params; new `POST /users/me/complete-onboarding` and `DELETE /users/me/activity-history/{log_id}`.
- **Cache / rate-limit**: no change to the template cache; delete-log is a standard authenticated mutation (CSRF-guarded).
