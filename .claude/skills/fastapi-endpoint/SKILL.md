---
name: fastapi-endpoint
description: Thin FastAPI routers behind /api/v1. Endpoints are one-line delegations to a service; wiring via app/core/dependencies.py; errors via the global DomainError handler.
metadata:
  version: "1.0"
  stack: python-fastapi
  related-skills:
    - sqlalchemy-repository
    - pydantic-schemas
    - auth-security
tier: 1
triggers:
  - endpoint
  - router
  - route
  - api
  - FastAPI
  - Depends
summary: |
  Routers are THIN: every endpoint body is `return await service.<method>(...)`.
  Mounted under `/api/v1` (`/healthz` unversioned). Inject via typed aliases in
  app/core/dependencies.py — SessionDep, RedisDep, CurrentUser, AdminUser,
  <X>ServiceDep, CSRFGuard. Never put SQL, business logic, or response building
  in a router. Services raise DomainError subclasses; the global handler in
  main.py maps them to JSON. Route paths are kebab-case, functions snake_case.
---

# FastAPI Endpoints

## Overview

| Aspect       | Details                                                          |
| ------------ | ---------------------------------------------------------------- |
| Goal         | Add HTTP routes that delegate straight to a service              |
| When         | Any new/edited endpoint under `app/routers/`                     |
| Verification | `uv run ruff check . && uv run mypy app && uv run pytest -q`     |

## Critical rules

**Every endpoint body is a single `return await service.<method>(...)`. No SQL, no business logic, no cookie/response building, no `try/except` for domain errors in the router.**

## Concepts

### Thin router delegation

A router module owns an `APIRouter(prefix=..., tags=[...])`, declares `response_model`, injects a service, and returns the awaited call. Everything else lives in the service.

```python
from fastapi import APIRouter

from app.core.dependencies import ActivityServiceDep, CurrentUser
from app.schemas.activity import ActivityTemplateOut

router = APIRouter(prefix="/activities", tags=["activities"])


@router.get("", response_model=list[ActivityTemplateOut])
async def list_activities(
    service: ActivityServiceDep,
    _: CurrentUser,
) -> list[ActivityTemplateOut]:
    return await service.list_templates()
```

Routers are mounted under `/api/v1` in `app/main.py`; `/healthz` is the only unversioned route.

### Dependency injection (`app/core/dependencies.py`)

All wiring is centralized as `Annotated[..., Depends(...)]` aliases. Use them; never construct a service or repository inside a router.

| Alias | Injects | Use for |
| ----- | ------- | ------- |
| `SessionDep` | `AsyncSession` | raw session (rarely in routers) |
| `RedisDep` | `Redis` | Redis client |
| `CurrentUser` | `User` | authenticated user (raises 401) |
| `AdminUser` | `User` | admin-only (raises 403) |
| `AuthServiceDep` / `UserServiceDep` / `ActivityServiceDep` | service instance | delegate business logic |
| `CSRFGuard` | `None` | CSRF double-submit check on state-changing routes |

A new service gets a factory + alias:

```python
def get_activity_service(session: SessionDep, redis: RedisDep) -> ActivityService:
    return ActivityService(session, redis)


ActivityServiceDep = Annotated[ActivityService, Depends(get_activity_service)]
```

### Auth, admin, CSRF

`CurrentUser` decodes the `access_token` cookie (HS256 JWT), checks `type == "access"` and `is_active`, and raises raw `HTTPException` — the one place raw HTTP errors are allowed (a FastAPI dependency, not a service). `AdminUser` layers a `role == ADMIN` check. `CSRFGuard` compares the `csrf_token` cookie with the `X-CSRF-Token` header for POST/PUT/PATCH/DELETE, bypassing `/auth/login`, `/auth/register`, `/auth/refresh`.

### Rate limiting

Attach `fastapi-limiter` as a route dependency (pinned `0.1.6`, which still accepts `times`/`seconds`):

```python
from fastapi import Depends
from fastapi_limiter.depends import RateLimiter

@router.post("/log", dependencies=[Depends(RateLimiter(times=60, seconds=60))])
```

Auth endpoints use `times=10, seconds=60`; `POST /activities/log` uses `times=60, seconds=60`.

### Errors: DomainError, not HTTPException

Services raise `DomainError` subclasses carrying `status_code` + `detail` (`app/core/exceptions.py`). A single `@app.exception_handler(DomainError)` in `main.py` maps them to JSON. Routers never catch them.

```python
if template is None:
    raise TemplateNotFoundError  # -> 404 {"detail": "activity not found"}
```

## Patterns

### Add an endpoint

1. Confirm/create the `*Out` (and `*Request`) schema in `app/schemas/`.
2. Add the method to the service (business logic + repo calls).
3. Add the route: declare `response_model`, inject `<X>ServiceDep` + `CurrentUser`/`AdminUser`, `return await service.<method>(...)`.
4. Use kebab-case path segments (`/users/me/activity-history`), snake_case function names.
5. If it mutates state, it is covered by `CSRFGuard`; add a `RateLimiter` dependency if it is a hot/abusable path.

## Common mistakes

| Mistake | Fix |
| ------- | --- |
| `select(...)`/`session.get(...)` in a router | Move query to a repository, call it from the service |
| Building cookies/`Response` in a router | Pass `Response` to the service (auth) or use the global handler |
| `raise HTTPException(404, ...)` in a router/service | Raise a `DomainError` subclass; the handler maps it |
| Instantiating `ActivityService(...)` inline | Inject `ActivityServiceDep` |
| camelCase or snake_case path segment | Use kebab-case (`/activity-history`) |
| Forgetting `response_model` | Always declare it so the ORM never leaks |

## Checklist

- [ ] Endpoint body is one `return await service.<method>(...)`
- [ ] Mounted under `/api/v1`; path is kebab-case
- [ ] Dependencies injected via aliases from `app/core/dependencies.py`
- [ ] `response_model` set to a pydantic `*Out`
- [ ] No SQL, no domain logic, no `try/except` in the router
- [ ] `RateLimiter` added on hot/abusable POSTs
