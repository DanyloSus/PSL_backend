## ADDED Requirements

### Requirement: FR-LEVELUP-1 — Per-stat log response carries progress-to-next-level

Each per-stat entry in the `POST /activities/log` response SHALL include, in addition to the existing `xp`, `level`, and `leveled_up` fields: `xp_into_level`, `xp_for_next`, `previous_level`, and `levels_gained`. These values SHALL be derived from `LevelingService.progress` for the stat's post-log XP.

Verification: local-verifiable

#### Scenario: Progress fields present after a log
- **WHEN** a user logs an activity affecting a stat
- **THEN** that stat's applied-effect entry includes `xp_into_level`, `xp_for_next`, `previous_level`, and `levels_gained`

#### Scenario: Levels gained on a level-up
- **WHEN** a log raises a stat from level 2 to level 4
- **THEN** the entry shows `previous_level` 2, `level` 4, `levels_gained` 2, and `leveled_up` `true`

#### Scenario: No level change
- **WHEN** a log adds XP without crossing a threshold
- **THEN** `levels_gained` is `0` and `leveled_up` is `false`

### Requirement: FR-LEVELUP-2 — Global log response carries progress-to-next-level

The top-level `POST /activities/log` response SHALL include global `xp_into_level`, `xp_for_next`, `previous_global_level`, and `global_levels_gained`, alongside the existing `global_xp`, `global_level`, and `global_leveled_up`.

Verification: local-verifiable

#### Scenario: Global progress present
- **WHEN** a user logs any activity
- **THEN** the response includes global `xp_into_level`, `xp_for_next`, `previous_global_level`, and `global_levels_gained`

#### Scenario: Global level-up reported
- **WHEN** a log raises the global level
- **THEN** `global_levels_gained` equals `global_level - previous_global_level` and `global_leveled_up` is `true`

### Requirement: FR-LEVELUP-3 — Progress values obey the level invariants

Reported `levels_gained` and `global_levels_gained` SHALL never be negative, and `previous_level`/`previous_global_level` SHALL reflect the value before the log was applied. The underlying level formula is unchanged.

Verification: local-verifiable

#### Scenario: Non-negative on a negative-XP log
- **WHEN** a negative-effect activity is logged and XP floors at 0
- **THEN** `levels_gained` is `0` and the reported level is not below the previous level
