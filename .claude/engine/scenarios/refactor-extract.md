# Scenario: refactor-extract

> Split an oversized service or repository into smaller single-responsibility units. Triggers: "refactor", "extract", "split file", "SRP".

## Metadata

```yaml
id: refactor-extract
budget: 500
sub_agents: 0
verified: false
```

## DAG

```
session-log(start)
  → discover              # locate the oversized service / repository
  → extract               # map its public methods + collaborators
  → gate                  # MANDATORY: approve the extraction plan before rewriting
  → transform             # extract into smaller units, keep public API stable
  → verify                # ruff + mypy + pytest (behavior must be unchanged)
  → session-log(end)
```

## Nodes

| Step | Node          | Inputs                                                                                                                                            | Outputs           |
| ---- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------- |
| 1    | `session-log` | `event: start`, `summary: "refactor-extract: {target}"`, `mode: edit`, `scenario_id: refactor-extract`                                           | `session_name`    |
| 2    | `discover`    | `file_pattern: "app/{services,repositories}/**/*.py"`, `query: "files exceeding file-health max size / mixed responsibilities"`                  | `oversized_files` |
| 3    | `extract`     | `source: $oversized_files`, `schema: services`                                                                                                  | `unit_map`        |
| 4    | `gate`        | `message: "Extract {target} into: {proposed_units}. Public method signatures and layer boundaries stay intact; callers unchanged. Approve?"`, `options: ["Approve", "Modify split", "Cancel"]` | `user_decision`   |
| 5    | `transform`   | `input: [$unit_map]`, `operation: to-code`, `condition: $user_decision.approved`, `params.template: "Extract cohesive units per BOOTSTRAP layer rules. Services keep __init__(self, session[, redis]); repos keep __init__(self, session). No SQL leaks across the split. Preserve public API and import paths (or update all callers). No new comments."` | `refactored_files`|
| 6    | `verify`      | `check_type: full`                                                                                                                              | `verification`    |
| 7    | `session-log` | `event: end`, `session_name: $session_name`, `files_modified: $refactored_files`, `summary: "refactor-extract done — {verification.status}"`     | —                 |

## Composition rules (enforced)

1. `session-log` is the FIRST and LAST node.
2. A `gate` node precedes the `transform` write step.
3. Only nodes from `engine/nodes/` — no inline operations.
4. Budget declared above (`500`, `sub_agents: 0`).
5. `verified: false` until this scenario runs successfully once.
6. Behavior-preserving: no schema/route/response changes; existing tests must pass unmodified.

## Verification

```bash
uv run ruff check . && uv run mypy app && uv run pytest -q
```
