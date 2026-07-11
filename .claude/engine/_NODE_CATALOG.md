# Node Catalog

> Atomic, reusable nodes that compose into DAG scenarios for the PSL backend AI knowledge system. Each node has a declared cost, cacheability, and I/O contract.

## Nodes (11)

| Node                                | Type    | Cost | Cacheable | Purpose                                          |
| ----------------------------------- | ------- | ---: | :-------: | ------------------------------------------------ |
| [discover](nodes/discover.md)       | input   |   80 |     ✓     | Read `app/` files / search workspace             |
| [extract](nodes/extract.md)         | process |   60 |     ✓     | Pull structured data (routes/services/models)    |
| [skill-load](nodes/skill-load.md)   | input   |  100 |     ✓     | Load a `.claude/skills/**/SKILL.md` or section   |
| [partition](nodes/partition.md)     | process |   40 |           | Split work into N groups                         |
| [spawn](nodes/spawn.md)             | process |  120 |           | Launch a sub-agent (`test-writer`, `code-reviewer`) |
| [verify](nodes/verify.md)           | process |   80 |           | Run `ruff` / `mypy` / `pytest`                   |
| [fix](nodes/fix.md)                 | process |  100 |           | Apply guided fixes to verify failures            |
| [gate](nodes/gate.md)               | gate    |   20 |           | User-approval checkpoint                         |
| [merge](nodes/merge.md)             | output  |   40 |           | Combine parallel branch results                  |
| [transform](nodes/transform.md)     | process |   60 |     ✓     | Apply a template (e.g. router→service→repo slice) |
| [session-log](nodes/session-log.md) | process |   10 |           | Append to session tracker                        |

## Composition rules

1. Every scenario MUST start with `session-log(start)` and end with `session-log(end)`.
2. Every scenario MUST include a `gate` before any write or spawn.
3. Reuse nodes — do NOT create inline operations.
4. Parallel spawns go through `partition` first, then rejoin with `merge`.
5. After a `spawn`/`merge`, run `verify`; on failure route to `fix` and re-`verify`.

## How nodes compose into scenarios

Nodes chain into a DAG (see `_SCENARIO_TEMPLATE.md`). Typical flow:

```
session-log(start)
  → skill-load / discover        # gather knowledge + code (cacheable, cheap on re-run)
  → extract / transform          # structure it, render a scaffold
  → gate                         # MANDATORY approval before touching the tree
  → partition → spawn (×N) → merge   # parallel work, then rejoin
  → verify                       # ruff + mypy + pytest
  → fix → verify                 # loop until green (bounded by max_rounds)
  → session-log(end)
```

- **Read-heavy nodes lead** (`discover`, `extract`, `skill-load`) — all cacheable, so repeat runs of the same scenario stay cheap.
- **`gate` is the pivot** between read/plan and write/spawn; nothing mutates the tree or launches an agent before it.
- **Fan-out pattern**: `partition` splits items → parallel `spawn` → `merge` recombines before a single `verify`.
- **Quality loop**: `verify` → `fix` → `verify` repeats until `passed: true` or `fix` escalates `remaining` errors to a new `gate`.
- **Budget** = sum of node costs on the critical path; declare it in the scenario metadata and record actuals via `session-log(end)`.
