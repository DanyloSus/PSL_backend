# Node: partition

> Split a list of work items into N groups for parallel processing.

## Spec

```yaml
id: partition
type: process
token_cost: 40
cacheable: false
```

## Inputs

| Name       | Type   | Required | Description                                       |
| ---------- | ------ | -------- | ------------------------------------------------- |
| `items`    | list   | yes      | Work items to split (files, records, tasks)       |
| `groups`   | int    | no       | Number of groups (default: min(items, 4))         |
| `strategy` | enum   | no       | `even` / `by-layer` / `by-file` (default: `even`) |

## Outputs

| Name          | Type       | Description                       |
| ------------- | ---------- | --------------------------------- |
| `partitions`  | list[list] | The grouped items                 |
| `group_count` | int        | Actual number of groups produced  |

## Behavior

1. If fewer `items` than `groups`, reduce `groups` to `len(items)`
2. `even` — round-robin distribute
3. `by-layer` — group by router/service/repository/model bucket
4. `by-file` — one item per group
5. Emit `partitions` for downstream parallel `spawn` fan-out

## Example

```yaml
- node: partition
  inputs:
    items: $changed_service_files
    strategy: by-file
  outputs: [service_batches]
```
