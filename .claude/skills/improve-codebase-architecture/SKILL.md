---
name: improve-codebase-architecture
description: Surface architectural friction in the PSL backend and propose deepening opportunities — refactors that turn shallow modules into deep ones. Informed by docs/PRD.md, docs/TDD.md, docs/adrs/, and CLAUDE.md. Use when asked to improve architecture, find refactoring opportunities, consolidate coupled modules, or make the codebase more testable.
---

# Improve Codebase Architecture (PSL backend)

Surface architectural friction and propose **deepening opportunities** — refactors that turn shallow modules into deep ones. The aim is testability and AI-navigability.

## Glossary

Use these terms exactly in every suggestion. Consistent language is the point.

- **Module** — anything with an interface and an implementation (function, class, package, layer). In PSL: a service, repository, router, or helper.
- **Interface** — everything a caller must know to use the module: types, invariants, error modes, ordering, config. Not just the signature.
- **Implementation** — the code inside.
- **Depth** — leverage at the interface: a lot of behaviour behind a small interface. **Deep** = high leverage. **Shallow** = interface nearly as complex as the implementation.
- **Seam** — where an interface lives; a place behaviour can be altered without editing in place.
- **Adapter** — a concrete thing satisfying an interface at a seam.
- **Leverage** — what callers get from depth. **Locality** — what maintainers get: change, bugs, knowledge concentrated in one place.

Key principles:

- **Deletion test**: imagine deleting the module. If complexity vanishes, it was a pass-through. If complexity reappears across N callers, it was earning its keep.
- **The interface is the test surface.**
- **One adapter = hypothetical seam. Two adapters = real seam.**

## Project mapping (read first)

This skill is *informed* by the project's recorded decisions — don't re-litigate them.

- **Domain + requirements** → `docs/PRD.md`, `docs/TDD.md`.
- **Architectural decisions** → `docs/adrs/` (0001 layered architecture, 0002 auth/cookies/CSRF, 0003 domain errors, 0004 XP/level invariants, 0005 stats seeding, 0006 activity-log per-stat effects, 0007 redis template cache, 0008 tests with fallback, 0009 stacked PR workflow, 0010 fastapi-limiter pin).
- **Layer rules + invariants** → `CLAUDE.md` §4 (layer rules), §5 (XP/level domain rules), §6 (cookies/CSRF/JWT), §7 (cache), §15 (naming/style).
- **Protected boundaries** → auth/security (`app/core/security.py`, `cookies.py`), the `DomainError` hierarchy, existing migrations (never edit), the leveling formula. Propose changes here only with a flagged warning.

If a candidate contradicts a rule in `CLAUDE.md` or an ADR, treat it as a decision conflict — surface it explicitly, don't silently violate.

## Process

### 1. Explore

Read the recorded decisions above for the area you're touching. Then use the `Agent` tool with `subagent_type=Explore` to walk `app/**` (routers, services, repositories, models, schemas). Explore organically; note friction:

- Where does understanding one concept require bouncing between many small modules?
- Where are modules **shallow** — a repository or service whose interface is nearly as complex as its body (pure pass-through to SQLAlchemy / to another service)?
- Where have functions been extracted only for testability, but the real bugs hide in how they're called (no **locality**)?
- Where do layers leak — SQL drifting into a service, HTTP/response shaping drifting into a repository, business logic sitting in a router instead of a 1-line wrapper?
- Which paths are untested or hard to test through their current interface (e.g. logic tangled with the request/session lifecycle)?

Apply the **deletion test** to anything you suspect is shallow.

### 2. Present candidates as an HTML report

Write a self-contained HTML file to the OS temp dir (`$TMPDIR`, fallback `/tmp`) as `architecture-review-<timestamp>.html` so nothing lands in the repo. Open it (`open <path>` on macOS) and give the user the absolute path.

Use Tailwind via CDN for layout and Mermaid via CDN for graph-shaped relationships (call graphs, layer dependencies, transaction sequences). Each candidate is a card:

- **Files** — which modules are involved (`app/services/...`, `app/repositories/...`).
- **Problem** — why the current architecture causes friction.
- **Solution** — plain English of what changes.
- **Benefits** — in terms of locality and leverage, and how tests improve.
- **Before / After diagram** — side-by-side, illustrating the shallowness and the deepening.
- **Recommendation strength** — `Strong` / `Worth exploring` / `Speculative` badge.

End with a **Top recommendation**: which to tackle first and why.

Use the project's domain vocabulary (`ActivityService`, `LevelingService`, `UserStat`, `ActivityLog`, stats/XP/levels) for the domain, and the glossary above for architecture.

**Rule / ADR conflicts**: only surface when the friction is real enough to warrant revisiting the decision. Mark it clearly (warning callout: *"contradicts CLAUDE.md §4 layer rules — worth reopening because…"*). Don't list every theoretical refactor a rule forbids.

Do NOT propose interfaces yet. After writing the file, ask: "Which of these would you like to explore?"

### 3. Grilling loop

Once the user picks a candidate, drop into a one-question-at-a-time grilling conversation (composes with the `grill-me` skill). Walk the design tree — constraints, dependencies, the shape of the deepened module, what sits behind the seam, which tests survive. Provide a recommended answer for each.

Side effects as decisions crystallize:

- **A load-bearing rejection reason a future explorer would need?** Offer to record it as a new ADR under `docs/adrs/` (next zero-padded number), framed as: *"Want me to record this as an ADR so future reviews don't re-suggest it?"* Skip ephemeral or self-evident reasons.
- **Sketching alternative interfaces?** For each option, state the signature, invariants, error modes (which `DomainError` subclasses), and the test surface. Pick the one that maximises depth.

## Project constraints to respect

- **Layering** (CLAUDE.md §4, ADR 0001): routers → services → repositories → SQLAlchemy. No SQL in routers/services. No HTTP in repositories. Routers stay 1-line wrappers.
- **Domain invariants** (CLAUDE.md §5, ADR 0004): XP ≥ 0, level ≥ 1, levels never decrease, BINARY → quantity 1, single transaction per log.
- **Error model** (ADR 0003): domain errors subclass `DomainError`, mapped by one global handler.
- **Cache** (ADR 0007): template-cache invalidation rides ORM events — don't route changes around the ORM.
- **Migrations**: never edit a merged migration; add a new one. New aggregate → import in `app/models/__init__.py`.

A deepening proposal that requires breaking one of these MUST surface the conflict in the candidate card, not silently violate it.
