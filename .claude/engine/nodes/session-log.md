# Node: session-log

> Append a structured entry to the session tracker.

## Spec

```yaml
id: session-log
type: process
token_cost: 10
cacheable: false
```

## Inputs

| Name      | Type   | Required | Description                                    |
| --------- | ------ | -------- | ---------------------------------------------- |
| `event`   | enum   | yes      | `start` / `end` / `checkpoint`                 |
| `summary` | string | no       | Short note about the step                      |
| `data`    | map    | no       | Metrics to record (tokens, files, pass/fail)   |

## Outputs

| Name     | Type   | Description               |
| -------- | ------ | ------------------------- |
| `logged` | bool   | Confirmation of append    |

## Behavior

1. Append an entry to the session tracker with a timestamp
2. On `start` — record scenario id and declared budget
3. On `checkpoint` — record `summary` + `data`
4. On `end` — record actual token spend and verification result
5. Never blocks the pipeline

## MANDATORY usage

**Every scenario MUST begin with `session-log(start)` and end with `session-log(end)`.**

## Example

```yaml
- node: session-log
  inputs:
    event: end
    summary: "Scaffolded achievements slice; full verify green"
    data: { files: 5, verify: pass }
  outputs: [logged]
```
