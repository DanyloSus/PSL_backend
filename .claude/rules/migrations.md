---
id: migrations
tier: 1
tooling: [alembic, convention]
enforcement: strict
paths:
  - "app/migrations/versions/**/*.py"
  - "app/models/__init__.py"
---

# Migrations (Alembic)

Enforces additive, zero-padded, Postgres-only Alembic migrations that autogenerate cleanly from the ORM.

## Rules

### MG1. Autogenerate, then rename to a zero-padded prefix

**Tooling:** `alembic`, `convention`

Generate with autogenerate, rename the file to a 4-digit prefix, and set `revision` to match the filename. Confirm `down_revision` points at the previous migration id.

```bash
uv run alembic revision --autogenerate -m "template quantity bounds"
# rename → app/migrations/versions/0006_template_quantity_bounds.py
```

```python
# ✅ CORRECT — filename and revision agree, down_revision chains
revision: str = "0006_template_quantity_bounds"
down_revision: str | None = "0005_seed_activity_templates"
```

**Why:** Zero-padded, self-describing revisions give a readable, linear history and make the chain obvious in `app/migrations/versions/`.

### MG2. Never edit a merged migration — add a new one

**Tooling:** `convention`

Migrations already merged are immutable. To change schema, add the next migration. Never rewrite `0001`–`000N`.

```python
# ❌ FORBIDDEN — editing an existing merged revision's upgrade()
# app/migrations/versions/0004_activities.py  (already merged)

# ✅ CORRECT — new revision that alters the earlier schema
# app/migrations/versions/0007_add_activity_index.py
def upgrade() -> None:
    op.create_index("ix_activity_logs_user_id", "activity_logs", ["user_id"])
```

**Why:** Editing applied migrations desyncs deployed databases from history and breaks anyone who already upgraded.

### MG3. Import new models in `app/models/__init__.py`

**Tooling:** `convention`

New aggregates must be imported in `app/models/__init__.py` so `Base.metadata` sees them and autogenerate produces the DDL.

```python
# ✅ app/models/__init__.py
from app.models.activity import ActivityEffect, ActivityLog, ActivityTemplate
from app.models.user import User
```

**Why:** Alembic autogenerate diffs `Base.metadata` against the DB. A model that isn't imported is invisible and silently omitted from migrations.

### MG4. Seeds via `op.bulk_insert`; Postgres-only

**Tooling:** `alembic`, `convention`

Data seeds use `op.bulk_insert(...)` (see `0003_seed_stats.py`, `0005_seed_activity_templates.py`). Target Postgres only — do not rely on SQLite behavior.

```python
# ✅ CORRECT — seed via bulk_insert with an explicit table shape
stats_table = sa.table("stats", sa.column("id", sa.dialects.postgresql.UUID), sa.column("name", sa.String))
op.bulk_insert(stats_table, [{"id": uuid.uuid4(), "name": "strength"}])
```

**Why:** `bulk_insert` keeps seeds inside the migration graph (reversible, ordered). Postgres-specific types (`UUID`, `Enum`) are used throughout, so SQLite assumptions break.

## Verification

```bash
uv run alembic upgrade head && uv run alembic downgrade -1 && uv run alembic upgrade head
```
