---
name: alembic-migration
description: Additive, zero-padded, Postgres-only Alembic migrations. Autogenerate, rename to 0NNN_<slug>.py, set revision + down_revision, import new models, seed via op.bulk_insert.
metadata:
  version: "1.0"
  stack: python-fastapi
  related-skills:
    - sqlalchemy-repository
tier: 1
triggers:
  - migration
  - alembic
  - revision
  - schema change
  - upgrade
  - downgrade
summary: |
  Migrations live in app/migrations/versions/, zero-padded (0001..000N). Flow:
  `alembic revision --autogenerate` → rename file to 0006_<slug>.py → set
  `revision = "0006_<slug>"` to match filename → confirm `down_revision` chains
  to the previous id. Import any NEW model in app/models/__init__.py first, or
  autogenerate misses it. Seed data with op.bulk_insert. NEVER edit a merged
  migration — add a new one. Postgres-only (UUID/Enum); no SQLite assumptions.
  Verify: upgrade head → downgrade -1 → upgrade head round-trips clean.
---

# Alembic Migrations

## Overview

| Aspect       | Details                                                           |
| ------------ | ---------------------------------------------------------------- |
| Goal         | Evolve the Postgres schema with additive, reversible revisions   |
| When         | Any model/column/constraint/seed change                          |
| Verification | `uv run alembic upgrade head && uv run alembic downgrade -1 && uv run alembic upgrade head` |

## Critical rules

**Never edit a merged migration — add the next one. Import new models in `app/models/__init__.py` BEFORE autogenerate or they are silently omitted. Postgres-only.**

## Concepts

### The flow

```bash
uv run alembic revision --autogenerate -m "template quantity bounds"
# 1. rename generated file → app/migrations/versions/0006_template_quantity_bounds.py
# 2. set revision to match the filename
# 3. confirm down_revision points at the previous migration id
uv run alembic upgrade head
uv run alembic downgrade -1   # confirm downgrade() is correct
uv run alembic upgrade head
```

### Revision header

Filename prefix, `revision`, and `down_revision` must agree and chain linearly:

```python
revision: str = "0006_template_quantity_bounds"
down_revision: str | None = "0005_seed_activity_templates"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
```

### Schema change (add columns + constraints)

`upgrade()` and `downgrade()` are mirror images. Give constraints explicit names so `downgrade` can drop them:

```python
def upgrade() -> None:
    op.add_column(
        "activity_templates",
        sa.Column("min_quantity", sa.Integer(), server_default="1", nullable=False),
    )
    op.create_check_constraint(
        "ck_template_min_quantity", "activity_templates", "min_quantity >= 1"
    )


def downgrade() -> None:
    op.drop_constraint("ck_template_min_quantity", "activity_templates", type_="check")
    op.drop_column("activity_templates", "min_quantity")
```

Mirror the column definition in the ORM model (`server_default` + Python `default`) so autogenerate stays quiet afterward.

### Data seeds (`op.bulk_insert`)

Declare a lightweight `sa.table(...)` shape and insert rows. Keep seeds reversible via a matching `downgrade` delete. See `0003_seed_stats.py`, `0005_seed_activity_templates.py`.

```python
def upgrade() -> None:
    stats = sa.table(
        "stats",
        sa.column("id", sa.UUID()),
        sa.column("key", sa.String()),
        sa.column("display_name", sa.String()),
        sa.column("icon", sa.String()),
    )
    op.bulk_insert(stats, [{"id": uuid.uuid4(), "key": "strength", "display_name": "Strength", "icon": "dumbbell"}])


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM stats WHERE key = ANY(:keys)").bindparams(keys=["strength"]))
```

### New aggregate

Before autogenerating a table for a brand-new model, add it to `app/models/__init__.py`. Alembic diffs `Base.metadata`; an unimported model is invisible.

## Patterns

### Add a schema change

1. Edit the ORM model (`Mapped[]` column, constraint, or new model imported in `__init__`).
2. `alembic revision --autogenerate -m "<msg>"`.
3. Rename to `0NNN_<slug>.py`; set `revision`, verify `down_revision`.
4. Review the generated ops; hand-fix names, `server_default`, enum handling.
5. Round-trip: `upgrade head → downgrade -1 → upgrade head`.

## Common mistakes

| Mistake | Fix |
| ------- | --- |
| Editing an already-merged `0004_*.py` | Add a new `0007_*.py` instead |
| New model not in migration | Import it in `app/models/__init__.py`, re-autogenerate |
| `revision` string ≠ filename | Make them match exactly |
| Unnamed constraint | Name it so `downgrade` can drop it |
| Relying on SQLite behavior locally | Target Postgres 16 only (UUID/Enum) |
| Raw INSERT for seeds | Use `op.bulk_insert` (stays in the graph) |

## Checklist

- [ ] File is `0NNN_<slug>.py`; `revision` matches; `down_revision` chains
- [ ] New models imported in `app/models/__init__.py`
- [ ] `downgrade()` reverses `upgrade()` (constraints named)
- [ ] Seeds use `op.bulk_insert` with a reversible delete
- [ ] `upgrade head → downgrade -1 → upgrade head` is clean
