# Scenario: feature-scaffold

> Scaffold a complete vertical slice for a new aggregate across every layer. Triggers: "new aggregate", "scaffold module", "new feature".

## Metadata

```yaml
id: feature-scaffold
budget: 700
sub_agents: 0
verified: false
```

## DAG

```
session-log(start)
  → discover              # read an existing aggregate as the pattern reference
  → extract               # pull its layer structure (model/repo/service/schema/router)
  → gate                  # MANDATORY: approve the slice + migration before writing
  → transform             # generate the vertical slice files
  → verify                # ruff + mypy + pytest (includes new migration + tests)
  → session-log(end)
```

## Nodes

| Step | Node          | Inputs                                                                                                                                                    | Outputs                |
| ---- | ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------- |
| 1    | `session-log` | `event: start`, `summary: "feature-scaffold: {aggregate}"`, `scenario_id: feature-scaffold`                                                                | `session_name`         |
| 2    | `discover`    | `file_pattern: "app/{models,repositories,services,schemas,routers}/activity*.py"`                                                                          | `reference_files`      |
| 3    | `extract`     | `source: $reference_files`, `schema: models`                                                                                                               | `reference_structure`  |
| 4    | `gate`        | `message: "Scaffold aggregate '{aggregate}': model + models/__init__ import + Alembic migration + repository + service + schema (Create/Update/Out) + router under /api/v1 + tests. Approve?"`, `options: ["Approve", "Modify scope", "Cancel"]` | `user_decision`        |
| 5    | `transform`   | `input: [$reference_structure]`, `operation: to-code`, `condition: $user_decision.approved`, `params.template: "Generate vertical slice per BOOTSTRAP layer rules: UUID PK + created_at/updated_at; import model in app/models/__init__.py; new zero-padded migration in app/migrations/versions/; repo __init__(session); service __init__(session[, redis]); pydantic *Create/*Update/*Out; thin router mounted under /api/v1; pytest tests in app/tests/. No code comments."` | `slice_files`          |
| 6    | `verify`      | `check_type: full`                                                                                                                                        | `verification`         |
| 7    | `session-log` | `event: end`, `session_name: $session_name`, `files_modified: $slice_files`, `summary: "feature-scaffold done: {aggregate} — {verification.status}"`       | —                      |

### Files created

```
app/models/{aggregate}.py               # SQLAlchemy ORM, UUID PK, created_at/updated_at
app/models/__init__.py                   # add import so Alembic autogenerate sees it
app/migrations/versions/00NN_{slug}.py   # new zero-padded migration (revision matches filename)
app/repositories/{aggregate}.py          # class, __init__(self, session: AsyncSession), SQL only
app/services/{aggregate}.py              # class, __init__(self, session[, redis]); DomainError subclasses
app/schemas/{aggregate}.py               # {Aggregate}Create / {Aggregate}Update / {Aggregate}Out
app/routers/{aggregate}.py               # thin router, mounted under /api/v1 in app/main.py
app/tests/test_{aggregate}.py            # httpx.AsyncClient + auth_client patterns
```

## Composition rules (enforced)

1. `session-log` is the FIRST and LAST node.
2. A `gate` node precedes the `transform` write step (nothing is written before approval).
3. Only nodes from `engine/nodes/` — no inline operations.
4. Budget declared above (`700`, `sub_agents: 0`).
5. `verified: false` until this scenario runs successfully once.
6. Migration is additive: new zero-padded file, `revision` matches filename, `down_revision` points at current head. Never edit a merged migration.

## Verification

```bash
uv run ruff check . && uv run mypy app && uv run pytest -q
```
