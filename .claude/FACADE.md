# AI Facade — Task Router

> **Read this FIRST.** Single entry point for all AI agents working on this project. Routes to the right skill or engine scenario. `BOOTSTRAP.md` is for reference only.
>
> Design pattern: [Facade](https://refactoring.guru/design-patterns/facade) — simplified interface hiding subsystem complexity.

## §A — HTTP / Routers

**Rules:** layer-architecture, naming | **Skills:** `fastapi-endpoint`

| Task            | Load                          | Notes                                                          |
| --------------- | ----------------------------- | -------------------------------------------------------------- |
| New endpoint    | fastapi-endpoint §Routes      | THIN router: `return await service.<method>(...)`; `/api/v1`   |
| Dependency wire | fastapi-endpoint §Depends     | `app/core/dependencies.py`: SessionDep, CurrentUser, *ServiceDep |
| Error mapping   | layer-architecture §Errors    | Raise `DomainError` subclasses; global handler maps to HTTP    |
| Route path      | naming §Paths                 | kebab-case (`/users/me/stats`, `/activity-history`)            |

## §B — Services (business logic)

**Rules:** layer-architecture, domain-xp | **Skills:** `fastapi-endpoint`, `domain-leveling`

| Task              | Load                        | Notes                                                     |
| ----------------- | --------------------------- | --------------------------------------------------------- |
| Service method    | layer-architecture §Service | Class `__init__(self, session[, redis])`; instantiate repos |
| XP / level logic  | domain-leveling §Engine     | Stat XP ≥ 0, level ≥ 1, never decrease; single txn per log |
| Quantity handling | domain-xp §Quantity         | BINARY → quantity forced to 1 server-side                 |

## §C — Repositories & Models

**Rules:** layer-architecture, migrations | **Skills:** `sqlalchemy-repository`, `alembic-migration`

| Task          | Load                          | Notes                                                     |
| ------------- | ----------------------------- | --------------------------------------------------------- |
| Repository    | sqlalchemy-repository §Queries | `__init__(self, session: AsyncSession)`; SQL only here    |
| New model     | sqlalchemy-repository §Models  | UUID PK `default=uuid.uuid4`; timestamps; import in `__init__` |
| Migration     | alembic-migration §Revision    | `0006_<slug>.py`; set revision/down_revision; never edit merged |
| Lock + update | sqlalchemy-repository §Locking | `with_for_update` for per-stat updates inside the log txn |

## §D — Schemas (pydantic)

**Rules:** schemas | **Skills:** `pydantic-schemas`

| Task       | Load                    | Notes                                          |
| ---------- | ----------------------- | ---------------------------------------------- |
| Request IO | pydantic-schemas §Create | `*Create` / `*Update`; validation + bounds     |
| Response   | pydantic-schemas §Out    | `*Out`; never expose ORM models directly       |

## §E — Tests

**Rules:** testing | **Skills:** `pytest-testcontainers`

| Task           | Load                              | Notes                                          |
| -------------- | --------------------------------- | ---------------------------------------------- |
| Unit / route   | pytest-testcontainers §Client     | `client`, `auth_client`, `admin_client` fixtures |
| Batch (>3)     | **Engine:** `batch-test-creation` | Parallel sub-agents                            |
| Isolation      | pytest-testcontainers §Isolation  | Per-test TRUNCATE + Redis FLUSHDB              |

## §F — New Aggregate / Feature

**Skills:** `sqlalchemy-repository` + `fastapi-endpoint` + `alembic-migration`
**Engine:** `feature-scaffold` (full router→service→repo→model+migration slice with approval gate)

Layout: `app/{routers,services,repositories,models,schemas}/<name>.py` + migration + tests.

## §G — Complex / Multi-file

**→ Check `.claude/engine/registry.json` for matching pipeline scenario.**

| Pattern                  | Scenario              |
| ------------------------ | --------------------- |
| Batch tests              | `batch-test-creation` |
| Full aggregate           | `feature-scaffold`    |
| Code review              | `code-review`         |
| Refactor / SRP split     | `refactor-extract`    |
| Pattern fix across files | `batch-fix-pattern`   |

No match? → Compose from nodes (`.claude/engine/nodes/`) with a user approval gate. See skill: `pipeline-orchestration`.

## §H — Git / PR

| Task                                  | Skill                      |
| ------------------------------------- | -------------------------- |
| Branch naming / new branch / stacking | `git-branch`               |
| Conventional commit                   | `git-commit`               |
| Squash branch                         | `git-squash`               |
| PR description                        | `pull-request-description` |

> Branch prefixes: `feat|feature|fix|bugfix|chore|refactor|test|docs|ci|build|perf`. Format `<type>/<kebab-desc>`. Stacked-PR workflow: base = parent branch, not `main` (CLAUDE.md §9). No Claude/Anthropic/`Co-Authored-By` refs — the commit-msg hook blocks them. `gh` authed as `dsu-empat`; SSH push via `github-sus.com` alias.

## §I — Security / Auth

**Rules:** security-cookies-csrf | **Skills:** `auth-security`

`security.py`/`cookies.py`/`dependencies.py` are **protected** (hook asks before first edit). JWT HS256 access (15m) + opaque refresh (7d, sha256 in DB) + CSRF double-submit. Refresh rotates every `/auth/refresh`. CSRF bypassed only for login/register/refresh.

## §J — Quality / Review

| Task        | Skill / Engine            | Command                                       |
| ----------- | ------------------------- | --------------------------------------------- |
| Lint        | `code-quality`            | `uv run ruff check .`                         |
| Type check  | `code-quality`            | `uv run mypy app`                             |
| Tests       | `pytest-testcontainers`   | `uv run pytest -q`                            |
| Code review | **Engine:** `code-review` | `/code-review`                                |

## §K — Lifecycle (sprint)

**Command:** `/sprint` — walks a feature/fix through Think → Plan → Build → Review → Test → Ship → Reflect with an approval gate between phases. Skip for trivial fixes. Everything runs inside Claude Code.

| Phase   | Skill / agent                                | Gate |
| ------- | -------------------------------------------- | ---- |
| Think   | `grill-me`                                   | ✓    |
| Plan    | `Plan` agent (+ engine scenario if multi-file) | ✓  |
| Build   | implement per rules; changed-file lint only  | ✓    |
| Review  | `code-review` engine / `code-reviewer` agent | ✓    |
| Test    | `pytest-testcontainers`; verify              | ✓    |
| Ship    | `git-commit` → `pull-request-description`    | ✓    |
| Reflect | `learn` (skip if nothing durable)            | —    |

## §L — Spec-driven (OpenSpec)

**Rule:** `spec-driven` · **Commands:** `/opsx:propose` `/opsx:apply` `/opsx:archive` `/opsx:explore` `/opsx:sync`

Non-trivial feature/fix → propose an OpenSpec change first. Requirement IDs `FR/NFR/TC/BC-<AREA>-<n>`; every FR/NFR declares `Verification:` from the closed vocab (local-verifiable | migration | manual). Tests carry `# @trace <req-id>`. Grammar in `openspec/config.yaml`. Source-of-truth product/tech specs: `docs/PRD.md`, `docs/TDD.md` (do not edit unless asked).

## §M — Decisions / Domain "why"

**Rule:** `decision-records` · **Command:** `/adr`

Read `docs/adrs/` (accepted decisions) before proposing architecture changes. Record an architecture-shaping, hard-to-reverse decision as an ADR (`/adr "<title>"`); skip reversible detail. The `adr_reminder` hook nudges on shaping commits.

## Critical Rules (always enforced)

```
router → service → repo → SQL      No SQL in routers/services       All IO async (async with)
Thin routers (1-line)              DomainError, not HTTPException    pydantic *Create/*Update/*Out
UUID PK + created/updated_at       get_settings() lru-cached         Stat XP ≥ 0, level ≥ 1, never drop
BINARY → quantity = 1              Migrations additive, never edit   Cache invalidation via ORM hooks
snake_case + kebab routes          Spell out locals (no 1-letter)    No unsolicited comments
Conventional commits + granular    No Claude/Anthropic in commits    Record shaping decisions → /adr
```

## Reference

Full architecture, rules table, hooks, commands → `.claude/BOOTSTRAP.md`
Engine documentation → `.claude/README.md` §5
