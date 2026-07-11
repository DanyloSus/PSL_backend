---
id: naming
tier: 0
tooling: [ruff, convention]
enforcement: strict
paths:
  - "app/**/*.py"
---

# Naming Conventions

Enforces file, route, class, model, and schema naming across the layered codebase.

## Rules

### NM1. Files and modules = snake_case

**Tooling:** `convention`

Module files are snake_case, named after the aggregate or resource they hold.

```
✅ app/services/activity_service.py
✅ app/repositories/user_stat_repo.py
✅ app/models/refresh_token.py
❌ app/services/ActivityService.py
❌ app/repositories/userStatRepo.py
```

**Why:** PEP 8 module naming; consistent with imports like `from app.services.activity_service import ActivityService`.

### NM2. Route paths = kebab-case

**Tooling:** `convention`

URL path segments are kebab-case; Python handler functions stay snake_case.

```python
# ❌ FORBIDDEN — camelCase / snake_case in the path
@router.get("/users/me/activityHistory")
@router.get("/activity_history")

# ✅ CORRECT — kebab-case path, snake_case function
@router.get("/users/me/stats")
async def get_my_stats(...) -> list[StatOut]: ...

@router.get("/activity-history")
async def list_activity_history(...) -> list[ActivityHistoryEntry]: ...
```

**Why:** Kebab-case is the REST URL convention; it also reads well and avoids case-sensitivity issues in paths.

### NM3. Classes = PascalCase, suffixed by layer role

**Tooling:** `convention`

Services end in `Service`, repositories in `Repository`. Errors end in `Error` and subclass `DomainError`.

```python
# ✅ CORRECT
class AuthService: ...
class ActivityRepository: ...
class TemplateNotFoundError(DomainError): ...
```

**Why:** The suffix tells you the layer and contract at a glance and makes greps like `rg "class .*Repository"` exhaustive.

### NM4. Models: UUID PKs + created_at/updated_at

**Tooling:** `convention`

Primary keys are `uuid.UUID` with `default=uuid.uuid4`. Every mutable entity carries `created_at` and `updated_at` with `server_default=func.now()` (and `onupdate=func.now()` for `updated_at`).

```python
# ✅ CORRECT
id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
)
created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), nullable=False, server_default=func.now()
)
updated_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    nullable=False,
    server_default=func.now(),
    onupdate=func.now(),
)
```

**Why:** UUID PKs avoid enumerable IDs; server-side timestamps guarantee accurate audit fields regardless of the writing code path.

### NM5. Schemas = `*Create` / `*Update` / `*Out`

**Tooling:** `convention`

Separate pydantic models per IO direction. Never one class for input and output.

```
✅ UserCreate, UserUpdate, UserOut
✅ ActivityTemplateOut, LogActivityRequest, LogActivityResponse
❌ a single `User` schema reused for request and response
```

**Why:** Input and output shapes diverge (passwords in, never out; server-set fields out, never in). Splitting them keeps each contract minimal and safe. See `schemas.md`.

## Verification

```bash
uv run ruff check . && uv run mypy app
```
