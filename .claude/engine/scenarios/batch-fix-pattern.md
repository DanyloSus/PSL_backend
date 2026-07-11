# Scenario: batch-fix-pattern

> Apply one consistent fix across every occurrence of a pattern in the codebase. Triggers: "fix pattern", "replace across", "batch fix", "fix all".

## Metadata

```yaml
id: batch-fix-pattern
budget: 800
sub_agents: 0
verified: false
```

## DAG

```
session-log(start)
  → discover              # grep every match of the pattern
  → extract               # normalize match sites (file + line + context)
  → gate                  # MANDATORY: approve the transformation before editing
  → partition             # group matches (by layer / file) for orderly application
  → fix                   # apply the same edit to each group
  → merge                 # collect all edited files
  → verify                # ruff + mypy + pytest
  → session-log(end)
```

## Nodes

| Step | Node          | Inputs                                                                                                                                       | Outputs         |
| ---- | ------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 1    | `session-log` | `event: start`, `summary: "batch-fix-pattern: {pattern}"`, `mode: edit`, `scenario_id: batch-fix-pattern`                                    | `session_name`  |
| 2    | `discover`    | `query: "{pattern}"` (e.g. `raise HTTPException` outside routers, bare `s = get_settings()`)                                                  | `match_files`   |
| 3    | `extract`     | `source: $match_files`, `schema: services`, `filter: "{pattern}"`                                                                            | `match_sites`   |
| 4    | `gate`        | `message: "Apply fix '{fix_desc}' to {count} sites across {n} files. Approve?"`, `options: ["Approve", "Show diff sample", "Cancel"]`         | `user_decision` |
| 5    | `partition`   | `items: $match_sites`, `strategy: by-layer`, `condition: $user_decision.approved`                                                            | `fix_groups`    |
| 6    | `fix`         | `input: $fix_groups`, `for_each: $fix_groups`, `params.instruction: "{fix_desc}"`, `scope: matched-sites-only`                               | `edited_files`  |
| 7    | `merge`       | `branches: [$edited_files]`, `strategy: concat`                                                                                             | `all_edited`    |
| 8    | `verify`      | `check_type: full`                                                                                                                          | `verification`  |
| 9    | `session-log` | `event: end`, `session_name: $session_name`, `files_modified: $all_edited`, `summary: "batch-fix-pattern done — {verification.status}"`      | —               |

## Composition rules (enforced)

1. `session-log` is the FIRST and LAST node.
2. A `gate` node precedes `partition` + `fix` (no edits before approval).
3. Only nodes from `engine/nodes/` — no inline operations.
4. Budget declared above (`800`, `sub_agents: 0` — `fix` runs the groups sequentially in-process).
5. `verified: false` until this scenario runs successfully once.
6. `fix` scope is `matched-sites-only`: edits only the discovered occurrences, no drive-by changes.

## Verification

```bash
uv run ruff check . && uv run mypy app && uv run pytest -q
```
