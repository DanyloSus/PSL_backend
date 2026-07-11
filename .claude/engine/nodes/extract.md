# Node: extract

> Pull structured data out of raw file content (symbols, signatures, routes).

## Spec

```yaml
id: extract
type: process
token_cost: 60
cacheable: true
cache_key: "extract:{schema}:{source_hash}"
```

## Inputs

| Name     | Type                  | Required | Description                                            |
| -------- | --------------------- | -------- | ------------------------------------------------------ |
| `source` | list[{path, content}] | yes      | Raw content (usually a `discover` output)              |
| `schema` | enum                  | yes      | `routes` / `services` / `models` / `schemas` / `deps`  |
| `filter` | string                | no       | Optional name/path filter                              |

## Outputs

| Name      | Type   | Description                          |
| --------- | ------ | ------------------------------------ |
| `records` | list   | Structured rows matching `schema`    |
| `count`   | int    | Number of records extracted          |

## Behavior

1. Parse each `source` file according to `schema`:
   - `routes` — `@router.<verb>(path)` + handler + `service.<method>` call
   - `services` — class + public methods + repos instantiated
   - `models` — SQLAlchemy class, table, columns, PK/FK
   - `schemas` — pydantic `*Create/*Update/*Out` fields
   - `deps` — `Depends(...)` factories from `app/core/dependencies.py`
2. Apply `filter` if present
3. Emit normalized records (no raw file bodies)
4. Cache keyed by `(schema, source_hash)`

## Example

```yaml
- node: extract
  inputs:
    source: $activity_layer_files
    schema: routes
  outputs: [activity_routes]
```
