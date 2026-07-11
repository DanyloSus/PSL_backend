---
name: pipeline-orchestration
description: Compose multi-step work from the .claude/engine DAG — nodes + scenarios. session-log first/last, a gate before any write or spawn, sub-agents for parallel work. For batch/multi-file tasks.
metadata:
  version: "1.0"
  stack: python-fastapi
  related-skills:
    - self-expansion
    - code-quality
tier: 2
triggers:
  - pipeline
  - scenario
  - engine
  - DAG
  - batch
  - orchestrate
summary: |
  For complex/multi-file/batch work, use the engine at .claude/engine: reusable
  nodes in engine/nodes/ (session-log, discover, extract, transform, partition,
  spawn, gate, verify, fix, merge) composed into scenarios (engine/scenarios/,
  indexed in engine/registry.json). Composition invariants: session-log(start)
  is FIRST and session-log(end) is LAST; a gate node precedes ANY write or spawn;
  only real nodes, no inline ops; declare a token budget; verified:false until it
  runs once. Check registry.json for an existing scenario before composing a new
  one; parallelize independent work via spawn sub-agents; end on the verify gate.
---

# Pipeline Orchestration (Engine)

## Overview

| Aspect       | Details                                                          |
| ------------ | --------------------------------------------------------------- |
| Goal         | Run multi-step / batch / multi-file tasks as a composable DAG    |
| When         | Task spans many files or repeats a pattern (batch tests, scaffold, batch-fix) |
| Verification | Scenario ends with `uv run ruff check . && uv run mypy app && uv run pytest -q` |

## Critical rules

**`session-log(start)` is the first node and `session-log(end)` the last. A `gate` (user approval) node MUST precede any write or spawn. Compose only from `engine/nodes/` — no inline operations.**

## Concepts

### Nodes (`.claude/engine/nodes/`)

Reusable, single-purpose steps with declared inputs/outputs and a token cost:

| Node | Role |
| ---- | ---- |
| `session-log` | append start/checkpoint/end to the session tracker (mandatory bookends) |
| `discover` | locate relevant files/symbols |
| `extract` / `transform` | pull out / reshape data |
| `partition` | split work into parallelizable chunks |
| `spawn` | launch a scoped sub-agent (agent, task, context, scope) |
| `gate` | 🔒 user approval checkpoint before writes/spawns |
| `verify` | run the quality gate |
| `fix` | apply corrections from a failed verify |
| `merge` | recombine sub-agent / partition results |

### Scenarios (`.claude/engine/scenarios/`, indexed in `registry.json`)

A scenario is a named DAG wired from nodes, with metadata (`id`, `budget`, `sub_agents`, `verified`). Known scenarios (see FACADE §G / `registry.json`): `feature-scaffold`, `batch-test-creation`, `code-review`, `refactor-extract`, `batch-fix-pattern`.

```
session-log(start)
  → discover
  → <process nodes…>
  → gate                # MANDATORY before any write or spawn
  → <write / spawn / verify / fix>
  → merge
  → session-log(end)
```

### Composition invariants (enforced)

1. `session-log` first and last.
2. A `gate` before the first write/spawn.
3. Only nodes from `engine/nodes/`.
4. Declare a token `budget`.
5. `verified: false` until the scenario runs green once.

### Node examples

```yaml
- node: gate
  inputs:
    message: "Scaffold router→service→repository slice for '{resource}' plus a migration?"
    options: ["Approve", "Modify scope", "Cancel"]
    show_diff: true
  outputs: [user_decision]

- node: spawn
  inputs:
    agent: test-writer
    task: "Write pytest + httpx.AsyncClient tests for {service} using the auth_client fixture"
    context: [$testing_conventions, $service_metadata]
    scope: read-src-write-test
  outputs: [test_result]
```

`spawn` passes layer discipline (router → service → repository → SQLAlchemy) and a `scope` constraint into the sub-agent prompt.

## Patterns

### Handle a complex task

1. Check `engine/registry.json` for a matching scenario — reuse it if found.
2. No match? Compose from `engine/nodes/`: `session-log(start)` → discover/extract → **gate** → write/spawn → verify → (fix) → merge → `session-log(end)`.
3. For repeated independent work (e.g. many test files), `partition` then `spawn` parallel sub-agents, then `merge`.
4. Always end on `verify` (the full quality gate) before `session-log(end)`.
5. New reusable scenario? Author it from `_SCENARIO_TEMPLATE.md` and register it (see `self-expansion`).

## Common mistakes

| Mistake | Fix |
| ------- | --- |
| Writing files with no approval gate | Insert a `gate` node before the first write/spawn |
| Missing session-log bookends | `session-log(start)` first, `session-log(end)` last |
| Inline ad-hoc steps | Compose from `engine/nodes/` only |
| Reinventing an existing flow | Check `registry.json` first |
| Skipping final verification | End on `verify` (ruff + mypy + pytest) |

## Checklist

- [ ] Checked `registry.json` for an existing scenario
- [ ] `session-log` first and last
- [ ] `gate` before any write/spawn
- [ ] Only `engine/nodes/`; budget declared
- [ ] Ends on `verify`; sub-agents scoped
