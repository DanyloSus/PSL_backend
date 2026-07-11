---
id: imports
tier: 0
tooling: [ruff, convention]
enforcement: strict
paths:
  - "app/**/*.py"
---

# Imports

Enforces one-directional cross-layer imports and ruff-managed import ordering with absolute `app.*` paths.

## Rules

### I1. No upward cross-layer imports

**Tooling:** `convention` (`pattern: from app.services|from app.routers` inside `app/repositories/`; `from app.routers` inside `app/services/`)

Imports follow the layer flow. Repositories never import services or routers. Services never import routers. Dependencies flow router → service → repository → models, never back up.

```python
# ❌ FORBIDDEN — repository reaching up into a service
# app/repositories/user_repo.py
from app.services.auth_service import AuthService

# ❌ FORBIDDEN — service importing a router
# app/services/activity_service.py
from app.routers.activities import router

# ✅ CORRECT — service imports repositories and models only
# app/services/activity_service.py
from app.models.activity import ActivityTemplate
from app.repositories.activity_repo import ActivityRepository
```

**Why:** Upward imports create cycles and couple lower layers to higher ones, defeating the point of the layering and breaking independent testability.

### I2. Absolute imports from `app.*`

**Tooling:** `ruff` (isort), `convention`

Use absolute package imports rooted at `app.*`. No relative imports (`from ..services import ...`).

```python
# ❌ FORBIDDEN
from ..repositories.user_repo import UserRepository
from .exceptions import DomainError

# ✅ CORRECT
from app.repositories.user_repo import UserRepository
from app.core.exceptions import DomainError
```

**Why:** Absolute paths are unambiguous, survive file moves better, and match the rest of the codebase.

### I3. Import ordering handled by ruff (isort)

**Tooling:** `ruff` (`I` rules)

Let ruff sort and group imports (stdlib → third-party → first-party). Do not hand-order. Modules use `from __future__ import annotations` at the top.

```python
# ✅ CORRECT — ruff-sorted groups
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import ActivityTemplate
```

**Why:** Deterministic ordering keeps diffs clean and removes a class of review nits.

## Verification

```bash
uv run ruff check --select I . && uv run mypy app
```
