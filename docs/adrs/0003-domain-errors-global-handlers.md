# ADR 0003 — Domain errors mapped via global exception handlers

- **Status:** Accepted
- **Date:** 2026-05-24

## Context

The codebase has business-level failure cases (`EmailTakenError`, `InvalidCredentialsError`, `TemplateNotFoundError`, …). Where should they be translated into HTTP status codes?

1. **Inside routers via `try`/`except` + `HTTPException`** — keeps the service layer free of FastAPI imports but forces every endpoint to repeat the same translation table. Routers stop being thin.
2. **Inside services via `HTTPException`** — services depend on FastAPI. Violates the "no HTTP in services" rule from ADR 0001.
3. **Domain errors raised in services, mapped by a single global handler in `main.py`** *(chosen)* — services know nothing about HTTP, routers stay thin, and every error has exactly one canonical status code.

## Decision

- `app/core/exceptions.py` defines a `DomainError` base with class-level `status_code: int` and `detail: str`. Subclasses override the defaults. Adding `detail=...` to a constructor call overrides at the instance level.
- Services raise these errors. They never raise `HTTPException`. They never reach for `fastapi.status` constants.
- `app/main.py` registers exactly one handler:

  ```python
  @app.exception_handler(DomainError)
  async def _domain_error_handler(_: Request, exc: DomainError) -> JSONResponse:
      return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
  ```

- Routers do not catch `DomainError`. They simply `return await service.<method>(...)`.

Current set of domain errors (and the status code each maps to):

| Error                       | Status |
|-----------------------------|--------|
| `EmailTakenError`           | 409    |
| `UsernameTakenError`        | 409    |
| `InvalidCredentialsError`   | 401    |
| `MissingRefreshError`       | 401    |
| `InvalidRefreshError`       | 401    |
| `TemplateNotFoundError`     | 404    |
| `TemplateDisabledError`     | 409    |

## Consequences

**Positive**
- New endpoints inherit existing error mappings for free.
- Routers stay 1-line wrappers (ADR 0001).
- Status codes for each error are reviewable in one file (`app/core/exceptions.py`).
- Easy to add structured error responses later (error codes, i18n keys) without touching routers.

**Negative**
- `fastapi`-native validation errors and `HTTPException` from outside the service layer (e.g. auth dependencies that reject missing cookies) still follow the default FastAPI path. Two error-shaping paths coexist. We document this in `CLAUDE.md` and live with it.
- Services can no longer set a one-off status code per call site without defining a new error class. This is by design: status codes belong to the error type, not the call site.

## Compliance

- A new service-level failure → add a new `DomainError` subclass in `app/core/exceptions.py` with the appropriate `status_code` and `detail`. Never raise `HTTPException` from a service.
- A new HTTP error type that doesn't fit `DomainError` (e.g. authentication) belongs in `app/core/dependencies.py` near the dependency that surfaces it.
