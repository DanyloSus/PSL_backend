## ADDED Requirements

### Requirement: FR-HISTORY-1 — History entries are enriched

Each entry returned by `GET /users/me/activity-history` SHALL include the source template's `title`, `description`, and `input_type`, and each per-effect item SHALL include the stat's `key`, `display_name`, and `icon` — so the client renders history without a second lookup.

Verification: local-verifiable

#### Scenario: Entry carries template and stat detail
- **WHEN** a user with logged activities requests their history
- **THEN** each entry includes the template `title`/`description`/`input_type` and each effect includes the stat `key`/`display_name`/`icon`

### Requirement: FR-HISTORY-2 — History supports filtering

`GET /users/me/activity-history` SHALL accept optional `template_id`, `from`, and `to` query parameters. `template_id` restricts results to that template; `from`/`to` restrict to logs whose `created_at` falls in the inclusive range. Filters compose with each other and with the existing `before` cursor and `limit`.

Verification: local-verifiable

#### Scenario: Filter by template
- **WHEN** a user requests history with `template_id` set to one of their logged templates
- **THEN** only logs for that template are returned

#### Scenario: Filter by date range
- **WHEN** a user requests history with `from` and `to` bounding a window
- **THEN** only logs created within that window are returned

#### Scenario: Filters compose with pagination
- **WHEN** a user combines `template_id`, a date range, and `limit`
- **THEN** the result honors all constraints together

### Requirement: FR-HISTORY-3 — History returns pagination metadata

`GET /users/me/activity-history` SHALL return an object containing `items` (the page), `total` (count of logs matching the active filter, ignoring `limit`/`before`), `has_more` (whether more pages exist beyond this one), and `next_before` (the cursor to fetch the next page, or `null` when none). This replaces the previous bare-list response.

Verification: local-verifiable

#### Scenario: Metadata reflects the filtered set
- **WHEN** a user has 30 logs and requests `limit=10`
- **THEN** `items` has 10 entries, `total` is 30, `has_more` is `true`, and `next_before` is set

#### Scenario: Last page
- **WHEN** the returned page exhausts the matching logs
- **THEN** `has_more` is `false` and `next_before` is `null`

### Requirement: FR-HISTORY-4 — User can delete a log, reversing its XP

`DELETE /users/me/activity-history/{log_id}` SHALL delete the authenticated user's own log and, in a single transaction, reverse the XP that log applied to each affected stat and to the global total. Reversal SHALL floor stat and global XP at 0, and SHALL recompute levels without ever lowering a stored level (levels-never-decrease is preserved).

Verification: local-verifiable

#### Scenario: XP reversed on delete
- **WHEN** a user deletes a log that had applied +50 total XP
- **THEN** the log is removed and the corresponding stat and global XP are reduced by the amount that log applied, floored at 0

#### Scenario: Level not lowered by reversal
- **WHEN** deleting a log would mathematically drop a stat below its current level
- **THEN** the stored level is left unchanged (never decreased)

#### Scenario: Successful delete status
- **WHEN** a user deletes one of their own logs
- **THEN** the system responds `204`

### Requirement: FR-HISTORY-5 — Deleting a missing or foreign log is rejected

Deleting a log id that does not exist, or that belongs to another user, SHALL raise `LogNotFoundError` mapped to HTTP `404`, and SHALL NOT alter any XP or level.

Verification: local-verifiable

#### Scenario: Foreign log rejected
- **WHEN** user A attempts to delete a log owned by user B
- **THEN** the system responds `404` and user B's log and XP are unchanged

#### Scenario: Unknown id rejected
- **WHEN** a user deletes a non-existent log id
- **THEN** the system responds `404`

### Requirement: NFR-HISTORY-1 — History read and delete are authenticated; delete is CSRF-guarded

`GET` and `DELETE` on activity history SHALL require a valid access token, and the `DELETE` SHALL be subject to the CSRF double-submit guard.

Verification: local-verifiable

#### Scenario: Unauthenticated delete rejected
- **WHEN** an unauthenticated client calls `DELETE /users/me/activity-history/{log_id}`
- **THEN** the system responds `401`

#### Scenario: Delete without CSRF rejected
- **WHEN** an authenticated client calls the delete without the `X-CSRF-Token` header
- **THEN** the system responds `403`
