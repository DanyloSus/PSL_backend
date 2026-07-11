# Node: gate

> 🔒 User approval checkpoint — pauses execution until user confirms.

## Spec

```yaml
id: gate
type: gate
token_cost: 20
cacheable: false
```

## Inputs

| Name        | Type         | Required | Description                                      |
| ----------- | ------------ | -------- | ------------------------------------------------ |
| `message`   | string       | yes      | What to ask the user                             |
| `options`   | list[string] | no       | Predefined choices (default: approve / reject)   |
| `context`   | string       | no       | Summary of what was done so far                  |
| `show_diff` | bool         | no       | Show file changes before asking (default: false) |

## Outputs

| Name       | Type   | Description            |
| ---------- | ------ | ---------------------- |
| `approved` | bool   | User's decision        |
| `feedback` | string | Optional user feedback |

## Behavior

1. Present `message` to user
2. If `show_diff`, display summary of pending changes
3. Include `context` as supporting info
4. Wait for user response
5. If rejected, pipeline branches to rollback or alternative path

## MANDATORY usage

**Every scenario that writes files or spawns a sub-agent MUST include a gate node before the first write/spawn.**

## Example

```yaml
- node: gate
  inputs:
    message: "Scaffold router→service→repository slice for '{resource}' plus an Alembic migration?"
    options: ["Approve", "Modify scope", "Cancel"]
    show_diff: true
  outputs: [user_decision]
```
