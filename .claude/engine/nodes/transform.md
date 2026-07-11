# Node: transform

> Apply a prompt template or formatter to input data.

## Spec

```yaml
id: transform
type: process
token_cost: 60
cacheable: true
cache_key: "transform:{template}:{input_hash}"
```

## Inputs

| Name       | Type   | Required | Description                                             |
| ---------- | ------ | -------- | ------------------------------------------------------- |
| `template` | string | yes      | Template name (e.g., `router-service-repo-slice`)       |
| `data`     | any    | yes      | Input to render through the template                    |
| `vars`     | map    | no       | Extra substitution variables                            |

## Outputs

| Name       | Type   | Description                     |
| ---------- | ------ | ------------------------------- |
| `rendered` | string | Templated output                |
| `artifact` | any    | Structured result if applicable |

## Behavior

1. Load `template` from `.claude/templates/`
2. Substitute `data` + `vars`
3. Enforce PSL conventions in the output (thin routers, `*Create/*Update/*Out` schemas, snake_case, UUID PKs + timestamps)
4. Emit `rendered` text and/or a structured `artifact`
5. Cache keyed by `(template, input_hash)`

## Example

```yaml
- node: transform
  inputs:
    template: router-service-repo-slice
    data: $resource_spec
    vars: { resource: "achievement", route_prefix: "/achievements" }
  outputs: [slice_scaffold]
```
