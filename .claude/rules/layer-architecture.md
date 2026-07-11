---
id: layer-architecture
tier: 0
tooling: [convention]
enforcement: strict
paths:
  - "app/routers/**/*.py"
  - "app/services/**/*.py"
  - "app/repositories/**/*.py"
  - "app/core/exceptions.py"
  - "app/main.py"
---

# Layer Architecture

Enforces the one-directional layered flow: HTTP router → service → repository → SQLAlchemy. Each layer owns exactly one concern and never reaches past its neighbor.

## Rules

### L1. Routers are thin one-line wrappers

**Tooling:** `convention` (`pattern: def .*\n.*(async with|select\(|\.execute\()` inside `app/routers/`)

Every endpoint body is a single `return await service.<method>(...)`. No business logic, no SQL, no cookie/response building in the router — that lives in the service or a global exception handler.

```python
# ❌ FORBIDDEN — logic and SQL leaking into the router
@router.post("/log")
async def log_activity(payload: LogActivityRequest, session: SessionDep, current: CurrentUser):
    template = await session.get(ActivityTemplate, payload.activity_template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="not found")
    ...

# ✅ CORRECT — one line, delegates to the service
@router.post("/log", response_model=LogActivityResponse)
async def log_activity(
    payload: LogActivityRequest,
    current: CurrentUser,
    service: ActivityServiceDep,
) -> LogActivityResponse:
    return await service.log_activity(current, payload)
```

**Why:** Thin routers keep HTTP concerns (routing, status codes, response models) separate from domain logic, so services stay independently testable and endpoints stay uniform.

### L2. No SQL outside repositories

**Tooling:** `convention` (`pattern: select\(|\.execute\(|session\.(get|add|scalar)` outside `app/repositories/`)

Only repositories import SQLAlchemy query constructs (`select`, `.execute`, `session.get`). Services and routers call repository methods; they never build queries.

```python
# ❌ FORBIDDEN — service issuing SQL directly
class UserService:
    async def get_profile(self, user_id: uuid.UUID) -> UserOut:
        result = await self.session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

# ✅ CORRECT — service asks the repository
class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.users = UserRepository(session)

    async def get_profile(self, user_id: uuid.UUID) -> UserOut:
        user = await self.users.get_by_id(user_id)
```

**Why:** Confining SQL to one layer means query changes, eager-loading, and locking live in a single place — and services can be reasoned about without database knowledge.

### L3. Fixed constructor signatures per layer

**Tooling:** `convention`

Repositories: `__init__(self, session: AsyncSession)`. Services: `__init__(self, session[, redis])` and instantiate the repos they need. Dependencies wire them in `app/core/dependencies.py`.

```python
# ✅ repository
class ActivityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

# ✅ service — takes session (+ redis when it caches), builds its repos
class ActivityService:
    def __init__(self, session: AsyncSession, redis: Redis) -> None:
        self.session = session
        self.redis = redis
        self.templates = ActivityRepository(session)
        self.logs = ActivityLogRepository(session)
```

**Why:** A uniform wiring contract lets `dependencies.py` construct every layer the same way and keeps ownership of repos inside the service that uses them.

### L4. Raise DomainError subclasses, not raw HTTPException, in services

**Tooling:** `convention` (`pattern: raise HTTPException` inside `app/services/`)

Services and repositories raise subclasses of `DomainError` (`app/core/exceptions.py`) carrying `status_code` + `detail`. The single `@app.exception_handler(DomainError)` in `main.py` maps them to JSON. Raw `HTTPException` belongs only in FastAPI dependencies (e.g. auth in `dependencies.py`).

```python
# ❌ FORBIDDEN in a service
raise HTTPException(status_code=404, detail="activity not found")

# ✅ CORRECT — domain error, mapped centrally
class TemplateNotFoundError(DomainError):
    status_code = 404
    detail = "activity not found"

# in the service
if template is None:
    raise TemplateNotFoundError()
```

**Why:** Centralized error mapping keeps HTTP status logic out of the domain layer and guarantees consistent error payloads. Routers never need `try/except`.

## Verification

```bash
uv run ruff check . && uv run mypy app && uv run pytest -q
```
