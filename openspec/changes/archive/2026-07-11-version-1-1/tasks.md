## 1. Schema & Migration

- [x] 1.1 Add `onboarding_completed: Mapped[bool]` (`server_default="false"`, `default=False`) to `app/models/user.py` (BC-ONBOARD-1)
- [x] 1.2 Autogenerate the Alembic migration, rename to next zero-padded `NNNN_add_onboarding_completed.py`, fix `revision`/`down_revision`, verify `upgrade head` then `downgrade -1` (BC-ONBOARD-1)
- [x] 1.3 Add `LogNotFoundError(DomainError)` (`status_code = 404`) to `app/core/exceptions.py` (FR-HISTORY-5)

## 2. Schemas

- [x] 2.1 Add `onboarding_completed: bool` to `UserPublic` (`app/schemas/auth.py`) and any `/users/me` output schema (FR-ONBOARD-1)
- [x] 2.2 Extend `AppliedEffect` with `xp_into_level`, `xp_for_next`, `previous_level`, `levels_gained`; extend `LogActivityResponse` with global `xp_into_level`, `xp_for_next`, `previous_global_level`, `global_levels_gained` (FR-LEVELUP-1, FR-LEVELUP-2)
- [x] 2.3 Enrich `ActivityHistoryEntry` (template `title`/`description`/`input_type`) and `ActivityHistoryEffect` (stat `key`/`display_name`/`icon`); add `ActivityHistoryPage { items, total, has_more, next_before }` (FR-HISTORY-1, FR-HISTORY-3)

## 3. Failing Tests (red)

- [x] 3.1 `app/tests/test_onboarding.py` — flag defaults false on `/users/me`, surfaces on `/auth/me`, `POST /users/me/complete-onboarding` sets true and is idempotent, 401 unauthenticated, 403 without CSRF `# @trace FR-ONBOARD-1 FR-ONBOARD-2 NFR-ONBOARD-1`
- [x] 3.2 `app/tests/test_levelup_feedback.py` — per-stat and global progress fields present, `levels_gained` on a multi-level jump, `0` on no-op, non-negative on floored negative log `# @trace FR-LEVELUP-1 FR-LEVELUP-2 FR-LEVELUP-3`
- [x] 3.3 `app/tests/test_activity_history_enrich.py` — entries carry template + stat detail `# @trace FR-HISTORY-1`
- [x] 3.4 `app/tests/test_activity_history_filter.py` — filter by `template_id`, by `from`/`to`, and composed with `limit` `# @trace FR-HISTORY-2`
- [x] 3.5 `app/tests/test_activity_history_pagination.py` — `total`/`has_more`/`next_before` correct across a full page and the last page `# @trace FR-HISTORY-3`
- [x] 3.6 `app/tests/test_activity_history_delete.py` — delete reverses XP floored at 0, level not lowered, 204 on own log, 404 on foreign/unknown, 401/403 auth+CSRF `# @trace FR-HISTORY-4 FR-HISTORY-5 NFR-HISTORY-1`

## 4. Repositories (green)

- [x] 4.1 `UserRepository.set_onboarding_completed(user_id)` — ORM update, no raw SQL (FR-ONBOARD-2)
- [x] 4.2 `ActivityLogRepository`: add optional `template_id`/`from`/`to` to `list_for_user`, fetch `limit + 1` for `has_more`, eager-load `template` and each effect's `stat` (FR-HISTORY-1, FR-HISTORY-2, FR-HISTORY-3, D4, D5)
- [x] 4.3 `ActivityLogRepository.count_for_user(user_id, *, template_id, from_, to)` for `total` (FR-HISTORY-3)
- [x] 4.4 `ActivityLogRepository.get_owned(user_id, log_id)` and `delete(log)` (with `UserStat` row lock reuse) (FR-HISTORY-4, FR-HISTORY-5)

## 5. Services (green)

- [x] 5.1 `UserService.complete_onboarding(user)` — set flag, return updated user representation, idempotent (FR-ONBOARD-2)
- [x] 5.2 `ActivityService.log_activity` — populate the new per-stat and global progress fields from tracked old/new levels + `LevelingService.progress`, never negative (FR-LEVELUP-1, FR-LEVELUP-2, FR-LEVELUP-3)
- [x] 5.3 `ActivityService.get_history` — accept filters, build `ActivityHistoryPage` (items/total/has_more/next_before), map enriched template + stat fields (FR-HISTORY-1, FR-HISTORY-2, FR-HISTORY-3)
- [x] 5.4 `ActivityService.delete_log(user_id, log_id)` — load owned-or-404, reverse per-stat + global XP floored at 0, recompute level without lowering, single transaction (FR-HISTORY-4, FR-HISTORY-5)

## 6. Routers (thin, green)

- [x] 6.1 `POST /users/me/complete-onboarding` → `return await service.complete_onboarding(current)` (FR-ONBOARD-2, NFR-ONBOARD-1)
- [x] 6.2 `GET /users/me/activity-history` — add `template_id`/`from`/`to` query params, return `ActivityHistoryPage` (FR-HISTORY-2, FR-HISTORY-3)
- [x] 6.3 `DELETE /users/me/activity-history/{log_id}` → `await service.delete_log(current.id, log_id)`, 204 (FR-HISTORY-4, NFR-HISTORY-1)

## 7. Validate & Archive

- [x] 7.1 Confirm every requirement id is traced by a `# @trace`-tagged test; fill any gap
- [x] 7.2 Run `uv run ruff check . && uv run ruff format --check . && uv run mypy app && uv run pytest -q` — all green
- [x] 7.3 `openspec validate --change version-1-1`, then archive with `/opsx:archive`
