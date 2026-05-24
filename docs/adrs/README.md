# Architecture Decision Records

Each ADR captures a single, non-trivial technical decision: the context that forced it, the option we picked, and the consequences we accept. They live forever — never edit a merged ADR; if it changes, write a new one that supersedes it.

## Format

Lightweight [Michael Nygård](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) template:

- **Status** — `Proposed` / `Accepted` / `Superseded by ADR-NNNN`
- **Context** — what makes the decision necessary
- **Decision** — what we picked
- **Consequences** — trade-offs we accept

## Index

| #    | Title                                                                 | Status   |
|------|-----------------------------------------------------------------------|----------|
| 0001 | [Layered architecture with classes](0001-layered-architecture-with-classes.md) | Accepted |
| 0002 | [Auth: JWT access + DB-tracked opaque refresh in httpOnly cookies](0002-auth-cookies-csrf.md) | Accepted |
| 0003 | [Domain errors mapped via global exception handlers](0003-domain-errors-global-handlers.md) | Accepted |
| 0004 | [XP / level invariants](0004-xp-and-level-invariants.md) | Accepted |
| 0005 | [Stats as seeded DB rows](0005-stats-as-seeded-rows.md) | Accepted |
| 0006 | [Activity log per-stat effect rows + total sum](0006-activity-log-per-stat-effects.md) | Accepted |
| 0007 | [Redis cache for activity templates + ORM-event invalidation](0007-redis-template-cache.md) | Accepted |
| 0008 | [Tests: testcontainers with env-var override fallback](0008-tests-with-fallback.md) | Accepted |
| 0009 | [Stacked PR workflow with ≤500 LOC limit and no force-push](0009-stacked-pr-workflow.md) | Accepted |
| 0010 | [Pinned `fastapi-limiter==0.1.6`](0010-fastapi-limiter-pin.md) | Accepted |
