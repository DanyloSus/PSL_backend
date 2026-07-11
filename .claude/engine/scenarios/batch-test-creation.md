# Scenario: batch-test-creation

> Generate pytest coverage across many modules in parallel via test-writer sub-agents. Triggers: "batch test", "tests for", "coverage for".

## Metadata

```yaml
id: batch-test-creation
budget: 13000
sub_agents: 4
verified: false
```

## DAG

```
session-log(start)
  → discover              # find target modules (services / repositories / routers)
  → extract               # pull public methods + routes worth covering
  → partition             # split into ≤4 balanced groups
  → gate                  # MANDATORY before spawning writers
  → spawn(test-writer ×N) # parallel, one per group, writes into app/tests/
  → merge                 # collect written test files
  → verify                # pytest -q
  → fix                   # repair failures / lint until green
  → session-log(end)
```

## Nodes

| Step | Node          | Inputs                                                                                                                            | Outputs           |
| ---- | ------------- | -------------------------------------------------------------------------------------------------------------------------------- | ----------------- |
| 1    | `session-log` | `event: start`, `summary: "batch-test-creation: {target}"`, `scenario_id: batch-test-creation`                                   | `session_name`    |
| 2    | `discover`    | `file_pattern: "app/{services,repositories,routers}/**/*.py"` (or `query` from the request)                                      | `target_files`    |
| 3    | `extract`     | `source: $target_files`, `schema: services`                                                                                      | `testable_units`  |
| 4    | `partition`   | `items: $testable_units`, `strategy: by-module`, `max_groups: 4`                                                                 | `test_groups`     |
| 5    | `gate`        | `message: "Write pytest coverage for {count} units across {n} groups into app/tests/ using auth_client/admin_client fixtures. Approve?"`, `options: ["Approve", "Adjust groups", "Cancel"]` | `user_decision`   |
| 6    | `spawn`       | `agent: test-writer`, `parallel: true`, `for_each: $test_groups`, `condition: $user_decision.approved`, `task: "Write pytest tests for {group}: httpx.AsyncClient over ASGITransport, 3+ char usernames, cover XP/level floors + DomainError paths. Files under app/tests/."`, `scope: write` | `written_tests`   |
| 7    | `merge`       | `branches: [$written_tests]`, `strategy: concat`                                                                                 | `all_test_files`  |
| 8    | `verify`      | `check_type: tests`                                                                                                              | `verification`    |
| 9    | `fix`         | `input: $verification`, `condition: "$verification.status != 'pass'"`, `scope: tests-only`                                       | `fixed_files`     |
| 10   | `session-log` | `event: end`, `session_name: $session_name`, `files_modified: $all_test_files`, `summary: "batch-test-creation done — {verification.status}"` | —                 |

## Composition rules (enforced)

1. `session-log` is the FIRST and LAST node.
2. A `gate` node precedes the `spawn` (writers never run before approval).
3. Only nodes from `engine/nodes/` — no inline operations.
4. Budget declared above (`13000`, `sub_agents: 4` max — `partition` caps groups at 4).
5. `verified: false` until this scenario runs successfully once.
6. Writers stay inside `app/tests/`; `fix` scope is `tests-only` — never touches product code.

## Verification

```bash
uv run ruff check . && uv run mypy app && uv run pytest -q
```
