# Scenario: code-review

> Rule-driven review of the current diff via a code-reviewer and an architecture-auditor in parallel. Triggers: "review", "code review", "audit".

## Metadata

```yaml
id: code-review
budget: 7000
sub_agents: 2
verified: false
```

## DAG

```
session-log(start)
  → discover ──→ extract ──┬─→ spawn(code-reviewer)        # read-only
                           └─→ spawn(architecture-auditor)  # read-only, parallel
                                        │
                                        ▼
                                      merge
                                        → transform         # findings → markdown report
                                        → session-log(end)
```

## Nodes

| Step | Node          | Inputs                                                                                                                       | Outputs          |
| ---- | ------------- | ---------------------------------------------------------------------------------------------------------------------------- | ---------------- |
| 1    | `session-log` | `event: start`, `summary: "code-review: current diff"`, `mode: review`, `scenario_id: code-review`                           | `session_name`   |
| 2    | `discover`    | `query: "git diff --name-only main"`                                                                                         | `changed_files`  |
| 3    | `extract`     | `source: $changed_files`, `schema: services`                                                                                | `change_metadata`|
| 4    | `spawn`       | `agent: code-reviewer`, `task: "Review changed files against .claude/rules/ (layer-architecture, code-style, imports, typing, naming, schemas, testing, domain-xp, security-cookies-csrf). Run ruff + mypy on the diff. Return File/Rule/Issue/Line/Severity/Fix table."`, `context: [$changed_files]`, `scope: read-only` | `code_findings`  |
| 5    | `spawn`       | `agent: architecture-auditor`, `parallel: true`, `task: "Audit layer boundaries (router→service→repo→SQLAlchemy), no SQL outside repos, DomainError over HTTPException, schema/model separation, cache-invalidation-via-ORM."`, `context: [$change_metadata]`, `scope: read-only` | `arch_findings`  |
| 6    | `merge`       | `branches: [$code_findings, $arch_findings]`, `strategy: concat`                                                            | `all_findings`   |
| 7    | `transform`   | `input: $all_findings`, `operation: to-markdown`, `params.template: "## Code Review Report\n{findings}\n### Summary\n{summary}"` | `review_report`  |
| 8    | `session-log` | `event: end`, `session_name: $session_name`, `mode: review`, `summary: "code-review done — {count} findings"`               | —                |

## Composition rules (enforced)

1. `session-log` is the FIRST and LAST node.
2. A `gate` precedes any write or state-mutating spawn. Both spawns here are `scope: read-only` and no node writes to the tree, so the gate requirement is satisfied vacuously — no gate node.
3. Only nodes from `engine/nodes/` — no inline operations.
4. Budget declared above (`7000`, `sub_agents: 2` — exactly one code-reviewer + one architecture-auditor, run in parallel).
5. `verified: false` until this scenario runs successfully once.

## Verification

```bash
uv run ruff check . && uv run mypy app && uv run pytest -q
```

_(Read-only scenario: verification confirms the diff still passes; the scenario itself produces a report, not edits.)_
