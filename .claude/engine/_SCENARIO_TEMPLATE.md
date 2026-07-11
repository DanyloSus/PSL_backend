# Scenario: <scenario-id>

> One-line purpose. Triggers: "<kw1>", "<kw2>".

## Metadata

```yaml
id: <scenario-id>
budget: <total token estimate>
sub_agents: <count>
verified: false
```

## DAG

```
session-log(start)
  → discover
  → <process nodes…>
  → gate                # MANDATORY before any write or spawn
  → <write / spawn / verify / fix>
  → merge
  → session-log(end)
```

## Nodes

| Step | Node          | Inputs                       | Outputs             |
| ---- | ------------- | ---------------------------- | ------------------- |
| 1    | `session-log` | `event: start`               | —                   |
| …    | …             | …                            | …                   |
| N    | `session-log` | `event: end`                 | —                   |

## Composition rules (enforced)

1. `session-log` is the FIRST and LAST node.
2. A `gate` node precedes any write or spawn operation.
3. Only nodes from `engine/nodes/` — no inline operations.
4. Budget declared above.
5. `verified: false` until this scenario runs successfully once.

## Verification

```bash
uv run ruff check . && uv run mypy app && uv run pytest -q
```
