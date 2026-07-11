# Thermo-Nuclear Review — Standards catalog (PSL backend)

Detailed standards loaded on demand by the `pr-review` skill — per-rule standards, review questions, flag list, preferred remedies, and tone. Grounded in `.claude/rules/`, `docs/adrs/`, and `AGENTS.md`.

## Non-Negotiable Standards (project-tuned)

### 0. Be ambitious about structural simplification

- Look for reframings that make whole branches, helpers, modes, or layers **disappear**.
- Prefer "the solution that feels inevitable in hindsight."
- If the change can be deleted rather than moved, push for deletion.

### 1. Layering is sacred (`layer-architecture`, ADR-0001)

Order: HTTP → service → repository → SQLAlchemy. A diff that crosses a boundary is a presumptive blocker.

- **Routers are 1-line wrappers** — every endpoint is `return await service.<method>(...)`. Cookie-setting, response building, and error mapping live in the service or a global handler, not the router. A router with an `if`, a `try`, a `select()`, or a `Response` construction is a blocker.
- **No SQL outside `app/repositories/`** — `select()`, `session.execute`, `session.scalars`, `with_for_update` in a service or router = blocker. Extract a repository method.
- **No HTTP in repositories** — no `HTTPException`, no `Response`, no `Request` in `app/repositories/`.
- **Services raise `DomainError` subclasses**, never bare `HTTPException` (ADR-0003). One global `@app.exception_handler(DomainError)` maps them. A service raising `HTTPException` is a blocker.

### 2. No spaghetti growth — push logic into typed models / dedicated collaborators

- New ad-hoc `if` / ternary branches inserted into a busy service flow = design problem, not style nit.
- Prefer: a discriminated shape, a dedicated method, an extracted collaborator service (e.g. `LevelingService` split from `ActivityService`).
- Repeated conditionals across files signal a missing model.
- Replace nested ternaries with early returns or extracted locals.

### 3. Clean the design — don't rubber-stamp "it works"

- If behavior can stay the same while structure becomes meaningfully cleaner, push for the cleaner version.
- Reject refactors that merely spread the same complexity around.
- Green tests are not approval — the bar is structural.

### 4. Direct & boring beats hacky & magical

- Thin wrappers / identity abstractions / pass-through service methods that only forward to one repository call = remove or inline.
- Generic mechanisms hiding a single concrete data shape = remove.

### 5. Type & boundary cleanliness (`typing`, `schemas`)

- `Any` is avoided; unjustified casts / `# type: ignore` / optionality → push for the explicit shape (`typing`; `uv run mypy app` is the gate).
- Full type hints on every def; SQLAlchemy 2.0 `Mapped[]` columns.
- **Never reuse an ORM model as an API DTO.** Request/response bodies are pydantic v2 `*Create` / `*Update` / `*Out` schemas; `Out` uses `from_attributes`. Validation and bounds live in the schema `Field(...)`, not scattered in the service (`schemas`).

### 6. Canonical layer & reuse — call out architectural drift (`imports`, `file-health`)

- **No cross-layer imports** — repositories must not import services or routers; services must not import routers; models must not import services (`imports`, A-rules of `layer-architecture`).
- Absolute `app.*` imports, ruff-ordered — no deep reach-arounds.
- **Reuse the canonical collaborator** — before adding logic, check whether an existing service/repository method, `LevelingService`, a `app/core/dependencies.py` factory, or a `DomainError` subclass already covers it. Copy-pasted query logic instead of a shared repository method is a finding.
- **New aggregate?** It MUST be imported in `app/models/__init__.py` so Alembic autogenerate sees it via `Base.metadata` (`migrations`).

### 7. Domain XP / leveling invariants (`domain-xp`, ADR-0004)

Any change touching stats/XP/levels is checked against the invariants — a violation is a blocker:

- Stat XP ≥ 0 floor; stat level ≥ 1; levels **never decrease**.
- BINARY templates force `quantity = 1` server-side; the client value is ignored.
- Log delta per stat = `effect.xp_change * effective_quantity`, then floored at 0.
- `User.global_xp` is the running sum of applied deltas; `global_level` is recomputed and never drops.
- Level formula: `LevelingService.threshold_for(L) = floor(100 * (L-1)**1.5)`; `level_from_xp` returns the highest L whose threshold ≤ xp, min 1.
- **Single transaction per log**: template load → per effect lock+update `UserStat` → write `ActivityLog` + per-stat `ActivityLogEffect`. Splitting this across transactions, or dropping the row-level lock, is a blocker.

### 8. Cache & rate limiting (`caching`, ADR-0007; `rate-limiting`)

- Template mutations (`ActivityTemplate` / `ActivityEffect`) go **through the ORM** so the `activities:templates` invalidation hook (`app/admin/hooks.py`) fires. Raw SQL / bulk ops that bypass the ORM without a manual invalidate = blocker.
- `activities:templates` cache is owned by `ActivityService.list_templates`, 5-min TTL — no second writer.
- Rate limits intact: auth 10 req/60s, `POST /api/v1/activities/log` 60 req/60s. `fastapi-limiter` stays pinned `0.1.6` (0.2.x drops the `times`/`seconds` kwargs).

### 9. Migrations (`migrations`)

- **Never edit an already-merged migration** — add a new one. Proposing an edit to an existing `app/migrations/versions/*` file is a blocker.
- Zero-padded `0NNN_<slug>.py`; `revision` matches the filename; `down_revision` points to the prior migration.
- Data seeds via `op.bulk_insert(...)`. Postgres-only — no SQLite-specific behavior.

### 10. Style & comments (`code-style`, `naming`)

- Python snake_case; route paths kebab-case; classes PascalCase.
- All IO async — `async with` for sessions and Redis.
- Spell out locals (`settings`, `user_stat`, `progress`) — never single letters when context isn't obvious.
- **No code comments unless the WHY is genuinely non-obvious.** A diff that adds comments restating the code is a finding — flag for removal.
- UUID PKs (`default=uuid.uuid4`); `created_at` / `updated_at` on mutable entities.

### 11. Granular-commit hygiene (`granular-commits`)

If the branch bundles refactor + feature + migration + style into one commit, the reframing **is** the split:

- Pure refactor commit, then behavior commit.
- Migration commit separate from the code that uses it where practical.
- Style/format commit separate from logic.

This is a review finding too, not just a commit-lint concern. No `Co-Authored-By` / "Generated with…" / 🤖 / Claude / Anthropic references (the commit-msg hook blocks them).

## Primary Review Questions

For every meaningful change:

- Is there a **code-judo** move that makes this dramatically simpler?
- Can the change be reframed so fewer concepts, branches, or helper layers exist?
- Did a `select()` / `session.execute` land outside `app/repositories/`? (`layer-architecture`)
- Is the router still a 1-line delegation, or did logic / error handling leak into it?
- Does a service raise `HTTPException` instead of a `DomainError` subclass? (ADR-0003)
- Was an ORM model reused as a request/response body instead of a `*Create/*Update/*Out` schema? (`schemas`)
- Does a change to stats/XP/levels preserve every invariant in §7? (`domain-xp`)
- Is the activity-log flow still a single transaction with per-stat row locks? (`domain-xp`)
- Do template mutations still ride the ORM so the cache hook fires? (`caching`)
- Did a cross-layer import sneak in — repo→service, service→router, model→service? (`imports`)
- Did a new aggregate get imported in `app/models/__init__.py`? (`migrations`)
- Did an already-merged migration get edited instead of a new one added? (`migrations`)
- Did an abstraction earn its keep, or is it a pass-through wrapper?
- Did a service/repository grow past a cohesive single purpose, or a model file gain a second aggregate? (`file-health`)
- Did `Any` / an unjustified cast / `# type: ignore` appear? (`typing`)
- Did code comments appear that merely restate the code? (`code-style`)
- Did a protected `§4a` file get edited? (refuse to redesign — flag for sign-off)

## Flag Aggressively

Escalate when you see:

- `select()` / `session.execute` / `with_for_update` in a service or router.
- A router with an `if` / `try` / response construction / error mapping instead of a 1-line `return await service.…`.
- A service raising bare `HTTPException` where a `DomainError` subclass belongs.
- An ORM model passed straight to/from an endpoint as the request/response body.
- XP change that can drive a stat XP below 0, a level below 1, or a level decrease.
- Activity-log write split across multiple transactions, or missing the per-stat row lock.
- BINARY template path that honors a client `quantity` instead of forcing 1.
- Template mutation via raw SQL / bulk op that skips the ORM cache-invalidation hook.
- Cross-layer import (`from app.services…` inside a repository, `from app.routers…` inside a service).
- New aggregate model not imported in `app/models/__init__.py`.
- Edit to an already-merged `app/migrations/versions/*` file.
- Service/repository ballooning into a god-class; two aggregates in one model file.
- `Any` / unjustified `unknown`-style cast / `# type: ignore` without a reason.
- Copy-pasted query logic instead of a shared repository method.
- Bespoke leveling math inline instead of `LevelingService`.
- Code comments restating the code (no explicit user request for them).
- Magic numbers in the XP/level path instead of `LevelingService` constants/formulas.
- Sequential `await`s where independent IO could run under `asyncio.gather`.
- Commit bundling refactor + feature + migration + style.

## Preferred Remedies

When you identify a problem, prefer:

- **Delete** a wrapper / mode / branch — not polish it.
- **Reframe** state so conditionals vanish — not centralize them.
- **Move ownership** so the feature becomes a natural extension of an existing service/repository.
- SQL in a service → extract a method on the owning repository (`__init__(self, session)`).
- Router doing work → push it into the service; leave `return await service.<method>(...)`.
- `HTTPException` in a service → a `DomainError` subclass with `status_code` + `detail`.
- ORM model as DTO → a pydantic `*Out` schema with `from_attributes` (and `*Create/*Update` for input).
- Inline validation/bounds → `Field(...)` constraints on the schema.
- Bespoke leveling math → `LevelingService.threshold_for` / `level_from_xp`.
- God-service → extract a focused collaborator (mirror `LevelingService` split from `ActivityService`).
- Two aggregates in one model file → split into one file per aggregate; re-import both in `__init__.py`.
- Cache bypass → mutate via the ORM so `app/admin/hooks.py` invalidates; or add an explicit invalidate with a WHY comment.
- Repeated condition chain → a typed discriminated shape + explicit dispatch.
- Mixed-concern commit → split refactor / behavior / migration / style into separate commits.

## Tone

Direct, serious, demanding about quality. Never rude. Do not soften major maintainability issues into mild suggestions. If the diff makes the codebase messier, say so clearly. If a dramatic simplification was missed, say so clearly.

Sample phrasing:

- `select() in app/services/activity_service.py — that query belongs on ActivityRepository. Extract get_template_with_effects(template_id) and call it.`
- `this router builds the response and maps the error itself. push both into the service; the endpoint should be one line: return await service.log_activity(...).`
- `service raises HTTPException(409). use a DomainError subclass — the global handler already maps status_code + detail (ADR-0003).`
- `ActivityLogOut is the ORM model. add a pydantic *Out schema with from_attributes; never serialize the model directly (schemas rule).`
- `this XP path can floor a stat below 0 — the delta must be floored at 0 after applying (domain-xp / ADR-0004).`
- `template updated via raw UPDATE — the activities:templates cache won't invalidate. route it through the ORM so the hook fires, or invalidate explicitly.`
- `feels like a code-judo move here: <reframing>. that deletes <N> branches and the extra service layer.`
- `this refactor moves complexity around — it doesn't delete it. is there a simpler model?`
- `app/core/security.py is a §4a protected area — flagging, not proposing a redesign. needs explicit sign-off.`
