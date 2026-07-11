# Node: verify

> Run lint / type-check / tests against the working tree.

## Spec

```yaml
id: verify
type: process
token_cost: 80
cacheable: false
```

## Inputs

| Name         | Type         | Required | Description                         |
| ------------ | ------------ | -------- | ----------------------------------- |
| `check_type` | enum         | yes      | `lint` / `types` / `tests` / `full` |
| `targets`    | list[string] | no       | Specific files/paths to check       |

## Outputs

| Name     | Type                              | Description               |
| -------- | --------------------------------- | ------------------------- |
| `passed` | bool                              | True if all checks passed |
| `errors` | list[{file, line, rule, message}] | Structured errors         |

## Behavior

| check_type | Command                                                     |
| ---------- | ----------------------------------------------------------- |
| `lint`     | `uv run ruff check .` (add paths if `targets` given)        |
| `types`    | `uv run mypy app`                                           |
| `tests`    | `uv run pytest -q`                                          |
| `full`     | `uv run ruff check . && uv run mypy app && uv run pytest -q` |

## Example

```yaml
- node: verify
  inputs:
    check_type: full
  outputs: [verification]
```
