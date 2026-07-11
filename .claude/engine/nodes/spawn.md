# Node: spawn

> Launch a sub-agent with scoped context and a defined task.

## Spec

```yaml
id: spawn
type: process
token_cost: 120
cacheable: false
```

## Inputs

| Name      | Type   | Required | Description                                                     |
| --------- | ------ | -------- | --------------------------------------------------------------- |
| `agent`   | string | no       | Agent name from manifest (e.g., `test-writer`, `code-reviewer`) |
| `task`    | string | yes      | Task description for the sub-agent                              |
| `context` | list   | no       | Pre-loaded data to pass (avoids re-read)                        |
| `scope`   | enum   | no       | `read-only` / `read-src-write-test` / `write-ai`                |

## Outputs

| Name             | Type         | Description                 |
| ---------------- | ------------ | --------------------------- |
| `result`         | string       | Sub-agent's final report    |
| `files_modified` | list[string] | Files the sub-agent changed |

## Behavior

1. Build prompt from `task` + `context`
2. If `agent` specified, select that persona from `.claude/agents/`
3. Pass `scope` constraints in the prompt (layer discipline: router → service → repository → SQLAlchemy)
4. Collect and validate result
5. Log token estimate: base 3,000 + context size

## Example

```yaml
- node: spawn
  inputs:
    agent: test-writer
    task: "Write pytest + httpx.AsyncClient tests for {service_name} using the auth_client fixture"
    context: [$testing_conventions, $service_metadata]
    scope: read-src-write-test
  outputs: [test_result]
```
