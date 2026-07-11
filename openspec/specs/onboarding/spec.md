# Onboarding

## Purpose

Track whether a user has completed the first-run onboarding flow, expose that state on the authenticated user representation, and let the user mark onboarding complete via an authenticated, CSRF-guarded, idempotent endpoint.

## Requirements

### Requirement: FR-ONBOARD-1 — User carries an onboarding-completed flag

The system SHALL persist a per-user `onboarding_completed` boolean, defaulting to `false` at registration, and SHALL expose it on the authenticated user representation returned by `GET /auth/me` and `GET /users/me`.

Verification: local-verifiable

#### Scenario: New user starts un-onboarded
- **WHEN** a user registers and calls `GET /users/me`
- **THEN** the response includes `onboarding_completed` equal to `false`

#### Scenario: Flag surfaces after completion
- **WHEN** a user who has completed onboarding calls `GET /auth/me`
- **THEN** the response includes `onboarding_completed` equal to `true`

### Requirement: FR-ONBOARD-2 — User can mark onboarding complete

The system SHALL provide `POST /users/me/complete-onboarding` that sets the authenticated user's `onboarding_completed` to `true` and returns the updated user representation. The operation SHALL be idempotent — calling it when already complete leaves the flag `true` and still returns success.

Verification: local-verifiable

#### Scenario: First completion
- **WHEN** an un-onboarded authenticated user calls `POST /users/me/complete-onboarding`
- **THEN** the flag becomes `true` and the returned user shows `onboarding_completed` `true`

#### Scenario: Idempotent repeat
- **WHEN** an already-onboarded user calls `POST /users/me/complete-onboarding` again
- **THEN** the request succeeds and the flag remains `true`

### Requirement: NFR-ONBOARD-1 — Completion is an authenticated, CSRF-guarded mutation

`POST /users/me/complete-onboarding` SHALL require a valid access token and SHALL be subject to the CSRF double-submit guard like any other state-changing endpoint.

Verification: local-verifiable

#### Scenario: Unauthenticated call rejected
- **WHEN** an unauthenticated client calls `POST /users/me/complete-onboarding`
- **THEN** the system responds `401`

#### Scenario: Missing CSRF header rejected
- **WHEN** an authenticated client omits the `X-CSRF-Token` header
- **THEN** the system responds `403`

### Requirement: BC-ONBOARD-1 — Backward-compatible column migration

The `onboarding_completed` column SHALL be added via an Alembic migration with a server-side default of `false`, so pre-existing users are treated as un-onboarded, and the migration SHALL be reversible.

Verification: migration

#### Scenario: Existing rows backfilled
- **WHEN** the migration runs against a database with existing users
- **THEN** every existing user has `onboarding_completed` `false`

#### Scenario: Reversible
- **WHEN** the migration is upgraded then downgraded
- **THEN** both directions complete without error
