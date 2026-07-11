# Node: merge

> Combine the results of parallel branches into a single artifact.

## Spec

```yaml
id: merge
type: output
token_cost: 40
cacheable: false
```

## Inputs

| Name       | Type   | Required | Description                                          |
| ---------- | ------ | -------- | ---------------------------------------------------- |
| `branches` | list   | yes      | Outputs from parallel `spawn` / `transform` nodes    |
| `strategy` | enum   | no       | `concat` / `dedupe` / `summary` (default: `concat`)  |

## Outputs

| Name       | Type         | Description                            |
| ---------- | ------------ | -------------------------------------- |
| `merged`   | any          | Combined result                        |
| `conflicts`| list[string] | Overlaps needing manual resolution     |

## Behavior

1. Collect all `branches` (wait for every parallel spawn to finish)
2. `concat` — append in partition order
3. `dedupe` — drop duplicate records / file entries
4. `summary` — condense into a single report
5. Flag `conflicts` when two branches modified the same file
6. Feed `merged` into a downstream `verify`

## Example

```yaml
- node: merge
  inputs:
    branches: [$batch_a_result, $batch_b_result]
    strategy: dedupe
  outputs: [combined_changes]
```
