---
name: pr-review
description: Extremely strict maintainability review of a branch/PR diff — layer-boundary regressions, fat routers, SQL leaking out of repositories, raw HTTPException over DomainError, ORM models reused as DTOs, spaghetti-condition growth, XP-invariant drift, and missed code-judo simplifications. Tuned to this repo's layered architecture and the rules in .claude/rules/. Every review target is analyzed by two parallel read-only sub-agents — code-reviewer reviews the changed files against the rules in isolation, architecture-auditor reviews how the change integrates with the layers and the wider codebase — then their findings are merged into one ranked list (never a table). Reviews the current branch by default; give it multiple PR numbers to fan out both sub-agents per PR in parallel. Use for a pr-review, thermo-nuclear / thermonuclear review, deep maintainability audit, or harsh code-quality pass.
argument-hint: "[pr-numbers…] [--base <ref>]"
metadata:
  version: "1.0"
  stack: python-fastapi
  related-skills:
    - improve-codebase-architecture
    - code-quality
  related-agents:
    - code-reviewer
    - architecture-auditor
tier: 2
triggers:
  - pr-review
  - review PR
  - review PRs
  - thermo-nuclear code review
  - thermonuclear review
  - harsh code review
  - deep maintainability audit
  - strict quality review
  - aggressive refactor review
  - code judo review
summary: |
  Run unusually strict maintainability review on a branch/PR diff. Push for
  code-judo restructurings that delete complexity rather than rearrange it.
  Anchored to this repo's rules: router→service→repo→SQLAlchemy layering, thin
  1-line routers, no SQL outside repositories, DomainError over HTTPException,
  separate *Create/*Update/*Out schemas (never reuse ORM models for IO), XP
  invariants (≥0 floor, level≥1, never decrease, BINARY→qty 1), template-cache
  mutated via ORM only, single-responsibility files. Refuses to redesign AGENTS
  §4a protected areas (security.py, cookies.py, config.py, db.py,
  dependencies.py, main.py, migrations, alembic.ini, pyproject.toml, CI). Every
  target runs two parallel read-only sub-agents — code-reviewer (changed files
  vs rules, in isolation) + architecture-auditor (integration + whole-codebase
  boundaries) — whose findings the main thread merges into one ranked list
  (never a table) per target. Current branch by default; multiple PR numbers fan
  out both agents per PR (2N sub-agents) and aggregate per PR. Output = ranked
  findings LIST, never a table (each entry: op · file:line · severity · rule ·
  issue · reframing) — few high-conviction comments, not nit floods. Read-only —
  never patches code, never runs git writes.
---

# PR Review (Thermo-Nuclear)

Unusually strict review of a branch/PR diff, focused on implementation quality, layer discipline, and maintainability. **Read-only.** Never patches code, never runs git operations.

Reviews the **current branch** by default, or one/many named PRs. **Every review target is analyzed by two parallel read-only sub-agents** — `code-reviewer` (the changed files judged against `.claude/rules/` in isolation) and `architecture-auditor` (how the change integrates with the layers and the wider codebase) — and the main thread merges their findings into one ranked **list** (never a table) per target (see [The two operations](#the-two-operations-per-target) and [Sub-agent fan-out](#sub-agent-fan-out-mechanics)).

Above all: be **ambitious** about structure. Do not stop at local cleanup. Actively hunt for **code-judo** moves — restructurings that preserve behavior while making the implementation dramatically simpler, smaller, and more direct. Prefer paths that **delete** complexity over paths that rearrange it.

This skill is the strict / "thermonuclear" sibling of the `/code-review` command. `/code-review` runs the same two agents and emits a **table** for a quick rule-compliance pass; `pr-review` demands ambitious simplification and emits a ranked **list**. Same agents, harsher bar.

## Overview

| Aspect       | Details                                                                                                                    |
| ------------ | -------------------------------------------------------------------------------------------------------------------------- |
| Goal         | Surface layer regressions, missed simplifications, spaghetti growth, XP-invariant drift, abstraction smells in a diff      |
| When         | User invokes pr-review / thermonuclear review / harsh review / deep maintainability audit                                  |
| Scope        | Current branch diff vs base by default; or one/many named PRs (default base `main`)                                        |
| Operations   | Every target → 2 parallel read-only agents: **A** = `code-reviewer` (changed files vs rules) + **B** = `architecture-auditor` (integration + whole-codebase boundaries) |
| Fan-out      | 1 target → 2 sub-agents (A+B). N PRs → 2N sub-agents, all spawned in one parallel message, merged per PR                    |
| Output       | Ranked findings **list, never a table** — op · file:line · severity · rule · issue · reframing (one merged list per target)|
| Verification | Scoped ruff + mypy on changed files only (per `lint-scope` rule)                                                           |

## Pre-flight

0. **Determine targets.** No PR number → one target: the current branch. One PR number → one target, materialized via a disposable worktree. Two or more PR numbers → each PR is a target. **Every target is reviewed by the two parallel agents** (Operation A + Operation B — see [The two operations](#the-two-operations-per-target)); the [fan-out](#sub-agent-fan-out-mechanics) spawns them all in one message and each agent runs steps 1–5 for its target.
1. Identify the base branch (default `main`, override via `--base`; for a PR use its own base from `gh pr view <n> --json baseRefName`).
2. Collect changed files: `git diff --name-only --diff-filter=ACMR origin/<base>...HEAD`.
   **rtk guard:** this repo routes Bash `git` through the rtk hook, which can filter/reformat output. If the collected list comes back empty or obviously wrong while `git status` shows changes, re-run the diff via `rtk proxy git diff …` to bypass the filter (see [Verification](#verification)). Never review off a silently-truncated file set — an empty list means "abort and re-fetch", not "nothing to review".
3. Read the `.claude/rules/*.md` cited in findings (rule IDs below). The agents already load their own rule set; the main thread reads them to merge and rank.
4. **Refuse** to propose restructures inside `AGENTS.md §4a` protected areas: `app/core/security.py`, `app/core/cookies.py`, `app/core/config.py`, `app/core/db.py`, `app/core/dependencies.py`, `app/main.py`, `app/migrations/env.py`, `app/migrations/versions/*`, `alembic.ini`, `pyproject.toml`, `.pre-commit-config.yaml`, `.github/workflows/*`. Flag, do not redesign. Never propose editing an already-merged migration (`migrations` rule) — only adding a new one.
5. Scoped lint per `lint-scope`: `uv run ruff check <changed-files>` + `uv run mypy app`. Treat surviving findings as input signal, not the review itself. **Skip this step in CI** where deps/`rtk` are absent — review from the diff + rules only.

## The two operations (per target)

Every review target — the current branch, or one materialized PR — is reviewed by **two agents running in parallel**. They are complementary: **A asks "is this file well-written and rule-compliant?"**, **B asks "does this change belong here, does it cross a layer boundary, and does it duplicate what already exists?"**

### Operation A — `code-reviewer` (changed files vs rules, in isolation)

Judges each changed file on its own merits against `.claude/rules/`. Stays **within the diff and the changed files themselves** — does not fan out across the repo. Covers:

- **Thin routers** — every endpoint is `return await service.<method>(...)`; no business logic, no SQL, no error mapping in routers (`layer-architecture` L1–L2).
- **Layer purity inside the file** — no `select()` / `session.execute` outside `app/repositories/` (`layer-architecture`); no HTTP/`Response` objects in a service except cookie-setting.
- **DomainError over HTTPException** — services raise `DomainError` subclasses, never bare `HTTPException` (`layer-architecture`, ADR-0003).
- **Schema/model separation** — `*Create` / `*Update` / `*Out` DTOs; never an ORM model reused for API IO; bounds/validation in the schema (`schemas`).
- **XP invariants** — stat XP ≥ 0 floor, level ≥ 1, levels never decrease, BINARY forces `quantity=1`, delta = `xp_change * effective_quantity` floored at 0, single transaction per log (`domain-xp`, ADR-0004).
- **Style / typing** — snake_case, all IO `async with`, spelled-out locals, no code comments unless the WHY is non-obvious, no `Any`, full type hints, `Mapped[]` columns (`code-style`, `typing`, `naming`).
- **Spaghetti / branching growth** inside a function; nested conditionals a discriminated union or early return would flatten.
- **Local** code-judo — simplifications visible within the file.

### Operation B — `architecture-auditor` (integration & architecture, across the whole codebase)

Reads **beyond the diff**. Greps the wider repo for existing helpers, canonical patterns, duplicate logic, and the consumers of changed exports, to judge how the change fits the architecture. Covers:

- **Cross-layer imports** — repositories importing services/routers, services importing routers, models importing services (`imports`, `layer-architecture`).
- **SQL leakage across files** — a query that drifted into a service where a repository method should own it; business logic sitting in a router instead of a 1-line wrapper.
- **Canonical-helper duplication** — does an existing service/repository method, `LevelingService`, `app/core/dependencies.py` factory, or the `DomainError` hierarchy already do this? (`file-health` FH2–FH3).
- **Ownership / placement** — should this logic live in a different service/repository, a `core/` helper, or the leveling engine? Is a new aggregate imported in `app/models/__init__.py` so Alembic sees it? (`migrations`).
- **Cache correctness** — template mutations go through the ORM so the `activities:templates` invalidation hook fires; no raw SQL bypassing it (`caching`, ADR-0007).
- **Rate limiting** — auth 10/60s and `POST /activities/log` 60/60s still declared; `fastapi-limiter` still pinned `0.1.6` (`rate-limiting`).
- **File health** — a service/repository grown past a cohesive single purpose; two aggregates crammed in one model file (`file-health` FH1–FH3).
- **Cross-file** code-judo — restructurings that delete whole branches / modes / layers spanning multiple files; moving ownership so the change becomes a natural extension of an existing service.
- **Protected §4a blast radius** — flag, never redesign.

## Sub-agent fan-out (mechanics)

For **every** target, spawn Operation A (`code-reviewer`) and Operation B (`architecture-auditor`) as two parallel sub-agents. Do NOT run either operation inline in the main thread — even a single current-branch review is two sub-agents. Both agents are already read-only and rule-tuned (`.claude/agents/`).

1. **One message, all sub-agents.** Launch every sub-agent for every target in a single response (parallel). 1 target → 2 sub-agents; N PRs → 2N sub-agents, all at once. Never sequential, never one-per-turn.
2. **Isolation.**
   - **Current branch:** both agents read the main working tree directly, read-only — **no worktree** (a worktree would not carry uncommitted changes).
   - **PR target:** each agent materializes the PR in its own disposable worktree — `isolation: "worktree"`, or `git worktree add /tmp/psl-pr-<N>/ <headRef>` cleaned up unconditionally on exit. Two read-only worktrees per PR is fine — no data race.
3. **Each agent runs its operation's scope** (A or B above) plus the shared flow (Pre-flight → Core Prompt → Output Format) against its target, and returns **only** its ranked findings list (never a table) — not file dumps, not raw diffs. Its final message IS the payload the main thread merges. Operation B is explicitly told to grep the wider codebase, not just the diff.
4. **Stable IDs are target- and op-scoped.** Prefix findings so IDs never collide: PR → `#23-file-B1`, `#23-arch-M2`; current branch → `file-B1`, `arch-M2`. The `file` / `arch` tag names the operation; `B/M/N` is severity. The user references findings across turns by that qualified ID.
5. **Merge per target, aggregate across targets.** The main thread merges each target's A + B findings into **one ranked list — never a table** (each finding tags its op `file` / `arch`), with one combined approval verdict. For multiple PRs, print one merged list per PR under a `## PR #<n> — <title>` heading — never fuse findings from different PRs. End with a one-line cross-PR summary (which are clean, which block).
6. **Cap: ≤10 per operation, ≤12 merged per target.** When merging, dedupe A↔B overlaps and keep the highest-conviction findings. Two passes must not double the nit flood.

## Core Prompt

Baseline given to each agent:

> Perform a deep code quality audit of the target's diff against `.claude/rules/`.
> Rethink how to structure / implement the changes to meaningfully improve quality without changing behavior.
> Push for abstractions that **delete** spaghetti, not abstractions that hide it.
> Be ambitious. If there is a clear restructuring path that makes the implementation dramatically simpler, push for it.
> Measure twice, cut once. Ground every finding in a real `app/` file and a rule ID.

**Detailed standards catalog → [reference/STANDARDS.md](reference/STANDARDS.md)** — load before writing findings (per-rule standards, review questions, flag list, preferred remedies, tone).

## Output Format

Per target, the main thread merges Operation A + Operation B into a **single ranked list of findings — never a table**. One finding per list entry. Rank across both operations by this priority order (structural regressions come mostly from Operation B, style/legibility mostly from A — merge and rank across both, do not keep two separate lists):

1. Structural regressions (layer-boundary breaks, SQL outside repositories, `HTTPException` in a service, protected-area edits, XP-invariant violations)
2. Missed code-judo simplifications
3. Spaghetti / branching growth
4. Boundary / type-contract problems (ORM model reused as DTO, `Any`, cross-layer import)
5. File-size / single-responsibility (`file-health`)
6. Modularity / abstraction smells
7. Legibility / maintainability

**Do NOT render findings as a markdown table.** Use a ranked list, each finding a short block. Per-finding shape:

```
### arch-B1 · blocker · layer-architecture · `arch`
`app/services/activity_service.py:120`
Issue — one-sentence problem statement.
Reframe — one-sentence fix (delete / extract / reframe / move ownership), naming the new method, repository, or schema.
```

Every finding carries the same six fields as prose, not columns: **ID · severity · rule · op** on the heading line, then **file:line**, **Issue**, **Reframe**. Keep each block tight — no paragraphs, no praise.

**Stable finding IDs.** Each ID is `<op>-<severity><n>`: the op tag (`file` = Operation A / `code-reviewer`, `arch` = Operation B / `architecture-auditor`) followed by a severity-prefixed number assigned in priority order, so the user can reference findings across turns ("fix arch-B1, skip file-N3") without re-pasting the list:

- `<op>-B1, <op>-B2, …` — **B**locker findings, in priority order.
- `<op>-M1, <op>-M2, …` — **M**ajor findings.
- `<op>-N1, <op>-N2, …` — mi**N**or / nit findings.

For a PR target, prefix the whole ID with the PR number: `#23-arch-B1`. IDs are stable within a single review run. Number Blockers first, then Majors, then miNors within each operation — matching the priority order above.

> **Output is a ranked list, not a table.** No markdown tables anywhere in the review body — findings, summaries, and verdicts are all prose / lists. Tables in this skill file are documentation of the field set, not the output shape.

**Severity:**

- **blocker** (`B*`) — must change before merge (layer-boundary break, SQL outside a repository, `HTTPException` in a service, ORM model reused as DTO, XP-invariant violation, §4a edit, edit to a merged migration, missed dramatic simplification that's clearly available)
- **major** (`M*`) — strongly push to change (spaghetti growth, missed reuse of an existing service/repository method, unjustified abstraction, cache bypassing the ORM hook)
- **minor** (`N*`) — nit, only include if no larger issue exists (drop pure ruff-format nits — the `ruff_fix` hook and CI own those)

**Cap:** ≤10 per operation, ≤12 merged per target. Dedupe A↔B overlaps when merging. Do not flood with cosmetic notes when structural issues dominate. Cluster duplicate findings (e.g. "three services raising `HTTPException` — list once with all sites").

End the report with a one-line **Approval verdict** (see below) and a one-line **Suggested next commit split** when the branch bundles refactor + feature + migration (`granular-commits`).

## Approval Bar

Do not approve merely because behavior looks correct or tests are green.

Approval requires:

- No layer-boundary leak (SQL outside repositories, HTTP/`Response` in a service, business logic in a router — `layer-architecture`)
- No service raising bare `HTTPException` instead of a `DomainError` subclass (ADR-0003)
- No ORM model reused for API IO; `*Create/*Update/*Out` respected (`schemas`)
- No XP-invariant violation (`domain-xp`, ADR-0004)
- No template mutation bypassing the ORM cache-invalidation hook (`caching`, ADR-0007)
- No cross-layer import (`imports`)
- No obvious missed code-judo simplification
- No spaghetti growth from special-case branching
- No god-service / two-aggregate model file added or grown (`file-health`)
- No `Any` / unjustified cast / optionality churn (`typing`)
- No protected `§4a` edit and no edit to a merged migration without explicit sign-off
- No commit bundling distinct concerns (`granular-commits`)

If any of these fail, leave explicit actionable feedback and push for the cleaner decomposition. Do not approve.

## Verification

Scoped ruff + mypy on changed files per `lint-scope` (never repo-wide inside the review):

```bash
BASE=${1:-origin/main}
CHANGED=$(git diff --name-only --diff-filter=ACMR "$BASE"...HEAD -- '*.py' \
        | sort -u | grep -v '^$')

# rtk guard — if the hook filtered the diff to empty while changes exist, bypass it.
if [ -z "$CHANGED" ] && command -v rtk >/dev/null 2>&1; then
  CHANGED=$(rtk proxy git diff --name-only --diff-filter=ACMR "$BASE"...HEAD -- '*.py' \
          | sort -u | grep -v '^$')
fi

[ -n "$CHANGED" ] && uv run ruff check $CHANGED && uv run mypy app
```

Do not run `uv run pytest` repo-wide as part of the review — CI (`.github/workflows/ci.yml`) owns the full gate. In CI where `uv`/`rtk` are absent, skip this step entirely and review from the diff + `.claude/rules/*.md` only.

## Common mistakes

| Mistake                                             | Fix                                                                 |
| --------------------------------------------------- | ------------------------------------------------------------------- |
| Running Operation A or B inline in the main thread  | Always spawn both as parallel sub-agents — even for one target      |
| Emitting a markdown table                           | Ranked **list** only; tables are the `/code-review` command's shape |
| Rubber-stamping because tests pass                  | Approval bar is structural, not behavioral                          |
| Nit flood (ruff-format cosmetics)                   | Drop format nits; cap ≤12 merged; structural findings first         |
| Proposing a redesign of a §4a file / merged migration | Flag only; never redesign protected areas                          |
| Reviewing off a silently-truncated diff             | rtk guard — re-fetch via `rtk proxy git diff` if the list is empty  |

## Checklist

- [ ] Targets determined (current branch / single PR / multiple PRs)
- [ ] Two sub-agents per target (`code-reviewer` A + `architecture-auditor` B), all spawned in parallel in one message (2 for one target, 2N for N PRs)
- [ ] Operation B told to grep the wider codebase, not just the diff
- [ ] Isolation correct: current branch = shared working tree read-only; PR = own disposable worktree per agent
- [ ] Base branch identified (default `main`)
- [ ] Changed-file set collected (rtk guard applied if empty)
- [ ] No proposals inside `§4a` protected areas or merged migrations
- [ ] Scoped ruff + mypy run (skipped in CI where tooling is absent)
- [ ] A + B findings merged per target into one ranked **list (never a table)**, capped ≤10/op, ≤12 merged
- [ ] Each finding has a stable op-scoped ID (`<op>-B*`/`<op>-M*`/`<op>-N*`, PR-prefixed for PRs)
- [ ] Each finding cites op, file:line, severity, rule ID, proposed reframing
- [ ] One combined approval verdict per target (+ cross-PR summary for multi-PR)
- [ ] Suggested commit-split offered if the branch bundles concerns
