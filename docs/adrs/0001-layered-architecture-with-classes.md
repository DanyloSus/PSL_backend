# ADR 0001 — Layered architecture with classes

- **Status:** Accepted
- **Date:** 2026-05-24

## Context

We need a structure that survives growth from MVP into achievements, quests, AI insights, and social features (see `docs/PRD.md` §18 Roadmap). The TDD calls for Service-Oriented Architecture but does not prescribe shape. Two real choices:

1. **Module-level async functions** keyed by `AsyncSession` argument. Minimal, easy to start. Becomes hard to track which dependencies a service needs as the surface grows. No constructor seam to swap implementations.
2. **Classes with constructor-injected dependencies.** Slightly more ceremony per file but gives an obvious unit of composition, an obvious surface for testing, and a single place to wire dependencies via FastAPI `Depends`.

Routers also had a real choice between "controllers with try/except + response shaping" and "thin pass-throughs to the service". With domain errors and cookie-setting both happening inside services, the thin variant is reachable.

## Decision

Adopt a strict three-layer pipeline:

```
HTTP route (router)  →  business logic (service class)  →  data access (repository class)
```

- Repositories: `__init__(self, session: AsyncSession)`. Only SQL.
- Services: `__init__(self, session[, redis])`. Instantiate the repos they need inside the constructor. Hold business logic, commit transactions, set auth cookies, raise domain errors.
- Routers: 1-line wrappers — `return await service.<method>(...)`. No try/except for domain errors, no response shaping, no `set_cookie`. The only logic is FastAPI dependency declaration.
- Wiring: `app/core/dependencies.py` exposes `Depends`-factory `get_<thing>_service` and `<Thing>ServiceDep = Annotated[..., Depends(...)]` aliases. Routers consume the aliases.

Domain errors live in `app/core/exceptions.py` as `DomainError` subclasses (status code + detail). `app/main.py` registers a single `@app.exception_handler(DomainError)` that maps them to JSON responses. See ADR 0003 for that decision.

## Consequences

**Positive**
- New endpoints add ~3 lines to a router. The business path is obvious — open the service, find the method.
- Tests touch HTTP via `httpx.AsyncClient`; the service surface remains stable across refactors, and class-based services are also straightforward to instantiate directly with an `AsyncSession` if a test needs to skip the HTTP layer.
- Adding caching or background work doesn't require threading new arguments through router signatures — the service constructor takes the new collaborator.
- Cross-cutting concerns (error mapping, CSRF, rate limiting) live in dependencies / middleware rather than in every endpoint.

**Negative**
- Services that wrap a single repo call look slightly over-engineered. Accepted: even one-line services give a stable public name and a place to grow.
- Constructor-injection isn't FastAPI's most common pattern; new contributors might initially reach for `Depends` parameters inside service methods. The skill `psl-architecture` documents the pattern, and `app/core/dependencies.py` keeps every wiring in one place.

## Compliance

- Routers must not contain `try`/`except` for `DomainError` subclasses, must not call `response.set_cookie`, and must not build pydantic `*Out` models from raw ORM rows.
- New repositories or services that take an `AsyncSession` as a method parameter (rather than via constructor) should be refactored to the class shape.
