---
name: sqlalchemy-repository
description: Repository classes own all SQLAlchemy 2.0 async queries. Fixed constructor __init__(self, session), select()/scalars(), with_for_update locking. No SQL anywhere else.
metadata:
  version: "1.0"
  stack: python-fastapi
  related-skills:
    - fastapi-endpoint
    - alembic-migration
    - domain-leveling
tier: 1
triggers:
  - repository
  - repo
  - query
  - sqlalchemy
  - session
  - ORM
summary: |
  Repositories are the ONLY layer that touches SQLAlchemy query constructs.
  Class contract: `__init__(self, session: AsyncSession)`; every method is async
  and awaits `self.session.execute(...)`. Reads use `select(...)` +
  `.scalars().all()` / `.scalar_one_or_none()`; single-row PK fetch uses
  `session.get(Model, id)`. Eager-load with `selectinload`. Row locking inside
  the log transaction uses `.with_for_update()`. Repos flush, services commit.
  Models are SQLAlchemy 2.0 `Mapped[]` + `mapped_column`, UUID PK + timestamps.
---

# SQLAlchemy Repositories

## Overview

| Aspect       | Details                                                         |
| ------------ | -------------------------------------------------------------- |
| Goal         | Confine all SQL to `app/repositories/` behind async methods    |
| When         | Any data access, new query, new model, row locking             |
| Verification | `uv run mypy app && uv run pytest -q`                          |

## Critical rules

**SQL lives only in repositories. `select`, `.execute`, `session.get/add/scalar`, `.with_for_update()` never appear in routers or services. Repositories `flush`; the service owns `commit`.**

## Concepts

### Repository class contract

Fixed signature — the DI layer constructs every repo the same way. A service instantiates the repos it needs in its own `__init__`.

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email.lower()))
        return result.scalar_one_or_none()
```

### Read shapes

- Many rows: `list(result.scalars().all())`.
- One-or-none: `result.scalar_one_or_none()`.
- PK lookup: `await self.session.get(Model, id)` (identity-map cached).
- Tuples (joins): iterate `result.all()` and unpack.

```python
async def list_for_user_with_stat(self, user_id: uuid.UUID) -> list[tuple[UserStat, Stat]]:
    result = await self.session.execute(
        select(UserStat, Stat)
        .join(Stat, Stat.id == UserStat.stat_id)
        .where(UserStat.user_id == user_id)
        .order_by(Stat.display_name)
    )
    return [(user_stat, stat) for user_stat, stat in result.all()]
```

### Eager loading

Avoid lazy-load-on-access (it explodes under async). Use `selectinload` for collections that the caller will read:

```python
from sqlalchemy.orm import selectinload

select(ActivityTemplate)
    .where(ActivityTemplate.is_enabled.is_(True))
    .options(selectinload(ActivityTemplate.effects))
    .order_by(ActivityTemplate.title)
```

### Row locking (`with_for_update`)

The activity-log transaction locks each `UserStat` row before mutating XP, so concurrent logs serialize:

```python
async def get_for_update(self, user_id: uuid.UUID, stat_id: uuid.UUID) -> UserStat | None:
    result = await self.session.execute(
        select(UserStat)
        .where(UserStat.user_id == user_id, UserStat.stat_id == stat_id)
        .with_for_update()
    )
    return result.scalar_one_or_none()
```

### Writes: flush here, commit in the service

Repositories `add`/`add_all` and `flush` (to populate PKs / order inserts). The **service** owns the transaction boundary and calls `commit`. Bulk updates use `update(...)`:

```python
async def create(self, *, user_id: uuid.UUID, token_hash: str, expires_at: datetime) -> RefreshToken:
    token = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
    self.session.add(token)
    await self.session.flush()
    return token

async def revoke_all_for_user(self, user_id: uuid.UUID) -> None:
    await self.session.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=datetime.now(UTC))
    )
```

### Models (SQLAlchemy 2.0)

`Mapped[T]` + `mapped_column`, never legacy `Column(...)`. UUID PK with `default=uuid.uuid4`; `created_at`/`updated_at` with `server_default=func.now()` (`onupdate=func.now()` on updated_at). Relationships are `Mapped[list[X]]` / `Mapped["X"]`. Import every new model in `app/models/__init__.py` so Alembic sees it.

```python
id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
effects: Mapped[list[ActivityEffect]] = relationship(
    back_populates="template", cascade="all, delete-orphan", lazy="selectin"
)
```

## Patterns

### Add a repository method

1. Add an `async def` to the relevant repo class.
2. Build the statement with `select`/`update`, `.where`, `.options`, `.order_by`.
3. `await self.session.execute(stmt)` and shape the result (`scalars().all()` / `scalar_one_or_none()`).
4. For mutations, `add`/`flush` — do NOT commit; let the service commit.
5. Call it from the service; never build the query in the service.

## Common mistakes

| Mistake | Fix |
| ------- | --- |
| Query in a service/router | Add a repo method, call it |
| `session.commit()` in a repo | Commit in the service (one txn per operation) |
| Lazy-loading a relationship after the session closes | `selectinload` in the query |
| Legacy `Column(...)` on a model | `Mapped[T]` + `mapped_column(...)` |
| Concurrent stat update without lock | `.with_for_update()` on the `UserStat` fetch |
| New model missing from migrations | Import it in `app/models/__init__.py` |

## Checklist

- [ ] `__init__(self, session: AsyncSession)` only
- [ ] Every method async, awaits `session.execute`
- [ ] Collections eager-loaded with `selectinload`
- [ ] Locking uses `.with_for_update()`; repo flushes, service commits
- [ ] New models use `Mapped[]`, UUID PK, timestamps, imported in `__init__`
