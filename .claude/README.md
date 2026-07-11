# AI Knowledge System — PSL Backend

> Knowledge base under `.claude/` that instructs Claude Code on how to work inside this project. Read natively by the harness — no build/sync step.

## 1. Why this exists

A monolithic `CLAUDE.md` gets dumped into the agent's context for every task — whether it's relevant or not. That wastes tokens and dilutes attention.

This system uses the **Facade pattern**: a single small router (`FACADE.md`) decides which knowledge to load based on what the user asked for. Skills, rules, and agents live in their own files and load on-demand, keyed by trigger words registered in `manifest.json`.

## 2. Layout

```
.claude/
├── FACADE.md              # Task router (read first)
├── BOOTSTRAP.md           # Always-loaded compact reference
├── README.md              # This file
├── manifest.json          # Registry: rules, skills, agents, protocols, templates
├── context-tiers.json     # Token-budget rules per task type
├── settings.json          # Hooks + permissions wiring
├── rules/                 # Enforceable rules (mapped to ruff / mypy / conventions)
├── skills/                # Domain knowledge modules
├── agents/                # Sub-agent personas with explicit scopes
├── protocols/             # Cross-cutting workflows
├── templates/             # Scaffolds for adding new artifacts
├── scripts/               # PreToolUse / PostToolUse hook scripts (Python)
├── commands/              # Slash commands (/adr, /code-review, /sprint, /opsx:*)
└── engine/                # DAG pipeline engine
    ├── registry.json
    ├── nodes/             # 11 atomic reusable nodes
    └── scenarios/         # Composed multi-step workflows
```

Root `CLAUDE.md` and `AGENTS.md` point here; the harness loads `.claude/skills/`, `.claude/rules/`, and `.claude/agents/` natively.

## 3. Loading protocol

```
1. Always loaded   →  .claude/BOOTSTRAP.md  (tier 0)
2. Pick budget     →  simple | feature | audit  (see context-tiers.json)
3. Match keywords  →  manifest.json triggers field
4. Read summary    →  manifest summary (≤5 lines)
5. Load full skill →  only if summary insufficient
6. Load tier-1     →  rules touched by the task
7. Protocols       →  only when orchestrating sub-agents or expanding knowledge
```

This caps context overhead at <1k tokens for simple tasks and ~3k tokens for full module work.

## 4. Hooks (`scripts/`)

Wired in `settings.json`. All hooks are Python (project language); they degrade gracefully — a parse error never blocks a tool.

| Hook | Event | Purpose |
| ---- | ----- | ------- |
| `ci_guard.py` | PreToolUse(Bash) | Block force-push + direct push to `main` + ruleset/`gh repo edit` mutations |
| `branch_name_guard.py` | PreToolUse(Bash) | Enforce branch prefix (feat/fix/chore/refactor/test/docs/…) |
| `adr_reminder.py` | PreToolUse(Bash) | Advisory: remind about `/adr` on architecture-shaping commits |
| `protected_paths.py` | PreToolUse(Edit\|Write) | Ask once before editing security/config/migration files; deny `.env` |
| `block_env_read.py` | PreToolUse(Read\|Grep) | Block reading `.env` secrets (`.env.example` allowed) |
| `agents_md_loader.py` | PreToolUse(Read\|Edit\|Write\|Glob\|Grep) | Auto-load nearest subdirectory `AGENTS.md` |
| `ruff_fix.py` | PostToolUse(Edit\|Write) | `ruff check --fix` + `ruff format` the single changed `.py` file |

## 5. The DAG Pipeline Engine

For tasks that span >3 files or run sub-agents in parallel, the engine composes 11 atomic **nodes** into named **scenarios** stored in `engine/scenarios/`. See `engine/_NODE_CATALOG.md`.

### Scenarios (`engine/scenarios/`)

| Scenario              | Triggers                                   | Sub-agents | Use case                                            |
| --------------------- | ------------------------------------------ | :--------: | --------------------------------------------------- |
| `feature-scaffold`    | "new aggregate", "scaffold module"         |     0      | Create a full router→service→repo→model+migration slice |
| `batch-test-creation` | "batch test", "tests for", "coverage for"  |  up to 4   | Write pytest tests for many modules in parallel     |
| `code-review`         | "review", "audit", "code review"           |     2      | Parallel review against rules + layer-boundary audit |
| `refactor-extract`    | "refactor", "extract", "split file", "SRP" |     0      | Split oversized services/repos into smaller units   |
| `batch-fix-pattern`   | "fix pattern", "replace across", "fix all" |     0      | Bulk codemod / lint-fix sweep                       |

### Composition rules (self-expansion)

Any new scenario MUST:

1. Include `session-log` as the **first and last** node.
2. Include a `gate` node before any write or spawn operations.
3. Reuse existing nodes — no inline operations.
4. Declare its budget in metadata.
5. Start with `verified: false` until the scenario successfully runs once.

## 6. Spec-driven development (OpenSpec)

`openspec/` holds the spec-driven workflow (`config.yaml` context + `specs/` + `changes/`). Drive it with `/opsx:propose`, `/opsx:apply`, `/opsx:archive`, `/opsx:explore`, `/opsx:sync`. Requirement-ID grammar and verification vocab live in `openspec/config.yaml` and `.claude/rules/spec-driven.md`.

## 7. Adding new knowledge

1. **New rule** → copy `templates/_RULE_TEMPLATE.md` → `rules/<id>.md` → register in `manifest.json`.
2. **New skill** → copy `templates/_SKILL_TEMPLATE.md` → `skills/<id>/SKILL.md` → register with `triggers`.
3. **New agent** → copy `templates/_AGENT_TEMPLATE.md` → `agents/<id>.md` → register with `scope`.
4. **New scenario** → copy `engine/_SCENARIO_TEMPLATE.md` → `engine/scenarios/<id>.md` → register in `engine/registry.json` with `verified: false`.

Always check for an existing artifact first — duplicates waste context and create conflicting guidance.

## 8. Verification

After any code change:

```bash
uv run ruff check . && uv run mypy app && uv run pytest -q
```

For a deeper audit, use the `code-review` engine scenario or `/code-review`.
