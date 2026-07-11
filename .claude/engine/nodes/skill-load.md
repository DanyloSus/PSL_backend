# Node: skill-load

> Load a `.claude/skills/**/SKILL.md` (or a named section) into working context.

## Spec

```yaml
id: skill-load
type: input
token_cost: 100
cacheable: true
cache_key: "skill-load:{skill}:{section}"
```

## Inputs

| Name      | Type   | Required | Description                                             |
| --------- | ------ | -------- | ------------------------------------------------------- |
| `skill`   | string | yes      | Skill name (e.g., `git-commit`, `pull-request-description`) |
| `section` | string | no       | Load only a named heading instead of the whole file     |

## Outputs

| Name      | Type   | Description                       |
| --------- | ------ | --------------------------------- |
| `content` | string | Skill body (or requested section) |
| `path`    | string | Resolved `SKILL.md` path          |

## Behavior

1. Resolve `.claude/skills/{skill}/SKILL.md`
2. If `section`, slice to that heading only
3. Return content for downstream nodes to consume
4. Cache keyed by `(skill, section)`

## Example

```yaml
- node: skill-load
  inputs:
    skill: git-commit
  outputs: [commit_conventions]
```
