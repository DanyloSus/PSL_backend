# Node: fix

> Apply guided fixes to failures reported by a `verify` node.

## Spec

```yaml
id: fix
type: process
token_cost: 100
cacheable: false
```

## Inputs

| Name          | Type                              | Required | Description                              |
| ------------- | --------------------------------- | -------- | ---------------------------------------- |
| `errors`      | list[{file, line, rule, message}] | yes      | Structured errors from `verify`          |
| `max_rounds`  | int                               | no       | Retry attempts before giving up (default: 2) |
| `constraints` | list[string]                      | no       | Rules the fix must respect               |

## Outputs

| Name             | Type         | Description                          |
| ---------------- | ------------ | ------------------------------------ |
| `files_modified` | list[string] | Files edited                         |
| `resolved`       | bool         | True if all input errors cleared     |
| `remaining`      | list         | Errors still unresolved              |

## Behavior

1. Group `errors` by file
2. For each error, apply the minimal edit that satisfies the rule (ruff, mypy, or a failing assertion)
3. Respect `constraints` — never break layer discipline, keep routers thin, no unsolicited comments
4. Re-run the relevant `verify` after edits, up to `max_rounds`
5. Emit `remaining` if not fully resolved (pipeline may escalate to a `gate`)

## Example

```yaml
- node: fix
  inputs:
    errors: $verification.errors
    constraints: ["thin routers", "no SQL outside repositories"]
  outputs: [fix_result]
```
