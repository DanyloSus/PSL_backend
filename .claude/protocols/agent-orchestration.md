# Protocol: Agent Orchestration

> When to delegate to the sub-agents in `.claude/agents/`, how to run them (parallel vs
> sequential), and how the engine `spawn` node formalizes it.

## The agents

| Agent                     | Mode       | Use for                                                          |
| ------------------------- | ---------- | ---------------------------------------------------------------- |
| `code-reviewer`           | read-only  | Review a diff/branch against rules; correctness + layer bugs     |
| `architecture-auditor`    | read-only  | Audit router→service→repo boundaries, SQL leaks, file health/SRP |
| `spec-compliance-auditor` | read-only  | Check code against `docs/PRD.md` / `docs/TDD.md` / OpenSpec specs |
| `test-writer`             | write      | Author pytest + testcontainers tests for one or more modules     |
| `docs-keeper`             | write      | Update `CLAUDE.md` / `AGENTS.md` / `BOOTSTRAP.md` / ADRs after a change |
| `migration-writer`        | write      | Generate an additive, zero-padded Alembic migration + model wiring |
| `ai-skill-creator`        | write      | Create a new rule/skill/agent/scenario (drives `self-expansion`) |

Read-only agents may Read/Grep/Glob/Bash but never edit. Write agents edit only files in
their declared scope — pass the scope in the prompt and they enforce it.

## When to spawn

- The work would crowd core context out of the main thread (large research/exploration).
- A specialized agent's scope matches better than doing it inline.
- Independent units of work can run at once (e.g. tests for 4 unrelated modules).

## When NOT to spawn

- One-shot, small, obvious — inline is cheaper than a handoff.
- The task needs information only the main thread holds and can't be handed off cleanly.
- The user has not authorized background/parallel work.
- Never re-delegate your *entire* assignment to a single sub-agent — do the work.

## Parallel vs sequential

| Shape          | Use when                                                                  |
| -------------- | ------------------------------------------------------------------------- |
| **Parallel**   | Units are independent — `batch-test-creation` (up to 4), dual review pass |
| **Sequential** | Later steps consume earlier output — scaffold → test → verify → docs      |

Prefer parallel when independent; send those spawns in one message so they run at once.
A common mixed shape: parallel `code-reviewer` + `architecture-auditor` (independent read
passes), then sequentially feed both reports to a fix step.

## Handoff format

Give every sub-agent:

- **Goal** — one sentence.
- **Context** — what's already loaded/decided (paths, branch, base).
- **Constraints** — scope (which files), read-only vs write, what NOT to touch.
- **Deliverable** — short report vs applied edits; return absolute paths.

## How the engine `spawn` node maps to this

Engine scenarios (`.claude/engine/scenarios/`) are the formalized version of this
protocol. In a scenario DAG:

- A `gate` node (user approval) MUST precede any `spawn`. No spawn without a gate.
- The `spawn` node fans out one or more of the agents above; its `sub_agents` count is
  declared in the scenario metadata and its budget accounted for.
- `session-log` is the first and last node; results converge at a `merge` node.

So: ad-hoc delegation follows this protocol directly; recurring multi-agent flows
(`code-review` scenario = 2 parallel agents, `batch-test-creation` = up to 4) encode the
same rules as a reusable DAG. Check `engine/registry.json` for an existing scenario before
orchestrating by hand.
