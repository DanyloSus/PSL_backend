# Node: discover

> Read files or search the `app/` tree to gather raw content.

## Spec

```yaml
id: discover
type: input
token_cost: 80
cacheable: true
cache_key: "discover:{file_pattern}:{query}"
```

## Inputs

| Name           | Type   | Required | Description                                          |
| -------------- | ------ | -------- | ---------------------------------------------------- |
| `file_pattern` | glob   | yes\*    | Files to read (e.g., `app/services/**/*.py`)         |
| `query`        | string | yes\*    | Search query if pattern insufficient                 |
| `max_files`    | int    | no       | Limit results (default: 20)                          |

\*At least one of `file_pattern` or `query` required.

## Outputs

| Name    | Type                  | Description             |
| ------- | --------------------- | ----------------------- |
| `files` | list[{path, content}] | File paths with content |
| `count` | int                   | Number of files found   |

## Behavior

1. If `file_pattern` — use Glob + Read
2. If `query` — use Grep
3. Deduplicate results
4. Truncate files >300 lines to first 300 (log warning)
5. Cache result keyed by `(file_pattern, query)`

## Example

```yaml
- node: discover
  inputs:
    file_pattern: "app/{routers,services,repositories}/activity*.py"
  outputs: [activity_layer_files]
```
