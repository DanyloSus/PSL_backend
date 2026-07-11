---
id: file-health
tier: 1
tooling: [convention]
enforcement: warning
paths:
  - "app/**/*.py"
---

# File Health

Enforces single responsibility and keeps modules small and focused.

## Rules

### FH1. One aggregate per model file

**Tooling:** `convention`

Each file in `app/models/` holds one aggregate and its owned sub-entities. `activity.py` owns `ActivityTemplate` + `ActivityEffect` + `ActivityLog` + `ActivityLogEffect` (one aggregate). Unrelated aggregates get their own file.

```python
# ❌ FORBIDDEN — unrelated aggregates crammed together
# app/models/misc.py  → User, Stat, ActivityLog, RefreshToken

# ✅ CORRECT — one file per aggregate
# app/models/user.py        → User, UserRole
# app/models/stat.py        → Stat
# app/models/activity.py    → ActivityTemplate, ActivityEffect, ActivityLog, ActivityLogEffect
```

**Why:** One-aggregate files keep imports predictable, mirror the migration boundaries, and match the `import all in __init__` pattern Alembic relies on.

### FH2. Single responsibility per class

**Tooling:** `convention`

A service owns one domain area; a repository owns one aggregate's queries. Don't let `AuthService` grow activity logic or `UserRepository` touch templates.

```python
# ❌ FORBIDDEN — repository straddling two aggregates
class UserRepository:
    async def get_by_id(self, user_id): ...
    async def list_activity_templates(self): ...   # belongs in ActivityRepository

# ✅ CORRECT — each repo owns its aggregate
class UserRepository: ...        # users
class ActivityRepository: ...    # activity templates
```

**Why:** Single responsibility keeps classes small, testable, and easy to locate; cross-aggregate methods blur ownership and invite duplicated queries.

### FH3. Split oversized services/repositories

**Tooling:** `convention`

When a service or repository grows past a cohesive single purpose, extract a collaborator (e.g. `LevelingService` is separate from `ActivityService`). Prefer composition over one god-class.

```python
# ✅ CORRECT — leveling math extracted from the activity flow
class ActivityService:
    def __init__(self, session: AsyncSession, redis: Redis) -> None:
        self.leveling = LevelingService()
```

**Why:** Large multi-purpose modules are hard to review and test. Extracting focused collaborators keeps each unit understandable and reusable.

## Verification

```bash
uv run ruff check . && uv run mypy app
```
