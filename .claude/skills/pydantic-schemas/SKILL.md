---
name: pydantic-schemas
description: pydantic v2 request/response DTOs. Separate *Create/*Update/*Out (or *Request/*Response); never reuse ORM models for API IO; Field constraints + bounds; from_attributes on Out.
metadata:
  version: "1.0"
  stack: python-fastapi
  related-skills:
    - fastapi-endpoint
    - domain-leveling
tier: 1
triggers:
  - schema
  - pydantic
  - validation
  - request
  - response
  - DTO
summary: |
  API IO uses pydantic v2 models in app/schemas/ — never SQLAlchemy models.
  Split by direction: inputs (*Create/*Update/*Request), outputs (*Out/*Response).
  Constrain fields with Field(...) (min_length, ge/le, pattern). Output models
  read ORM instances via `model_config = {"from_attributes": True}` +
  `Model.model_validate(orm_obj)`. Accept camelCase input with `alias=` +
  `populate_by_name`. Passwords go in, never out. Enums come from app/models.
---

# Pydantic Schemas (v2)

## Overview

| Aspect       | Details                                                     |
| ------------ | --------------------------------------------------------- |
| Goal         | Typed, validated request/response contracts per direction  |
| When         | Any endpoint IO, new field, validation change              |
| Verification | `uv run mypy app && uv run pytest -q`                      |

## Critical rules

**Never expose or accept ORM models over HTTP. Separate `*Create`/`*Update`/`*Out` (or `*Request`/`*Response`). `*Out` models set `from_attributes=True`; build them with `model_validate(orm_obj)`.**

## Concepts

### Output schema (`*Out`) — reads from ORM

Set `from_attributes` so pydantic can read attributes off a SQLAlchemy instance. Only include fields safe to expose — never `password_hash`.

```python
from pydantic import BaseModel, EmailStr

from app.models.user import UserRole


class UserPublic(BaseModel):
    id: uuid.UUID
    email: EmailStr
    username: str
    role: UserRole
    global_xp: int
    global_level: int

    model_config = {"from_attributes": True}
```

Construct at the boundary: `UserPublic.model_validate(user)`.

### Input schema (`*Create` / `*Request`) — validated at the edge

Constrain with `Field(...)`. Username/password bounds match the DB and are enforced before the service runs:

```python
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=128)
```

### camelCase aliases

Frontend sends camelCase; accept it with `alias=` + `populate_by_name` (so Python-side construction with snake_case still works):

```python
class LogActivityRequest(BaseModel):
    activity_template_id: uuid.UUID = Field(alias="activityTemplateId")
    quantity: int = Field(default=1, ge=1, le=10_000)

    model_config = {"populate_by_name": True}
```

### Nested & computed response models

Compose `*Out` models; assemble computed views in the service, not the schema:

```python
class AppliedEffect(BaseModel):
    stat: StatOut
    xp_applied: int
    xp: int
    level: int
    leveled_up: bool


class LogActivityResponse(BaseModel):
    log_id: uuid.UUID
    total_xp_applied: int
    applied: list[AppliedEffect]
    global_xp: int
    global_level: int
    global_leveled_up: bool
```

### Where bounds live

`Field(ge=1, le=10_000)` on the request catches obviously invalid input at the HTTP edge (returns 422 automatically). Domain-specific, data-dependent bounds (e.g. a template's `min_quantity`/`max_quantity`) are checked in the service and raised as `DomainError` (`QuantityOutOfRangeError`), not in the schema.

## Patterns

### Add a schema

1. Pick the direction: input → `*Create`/`*Update`/`*Request`; output → `*Out`/`*Response`.
2. Type every field; add `Field(...)` constraints for static bounds/patterns.
3. For output, set `model_config = {"from_attributes": True}`; build with `model_validate`.
4. For camelCase input, add `alias=` + `populate_by_name`.
5. Wire it as the endpoint's `response_model` / request body type.

## Common mistakes

| Mistake | Fix |
| ------- | --- |
| Returning a SQLAlchemy model | Return a `*Out`; set it as `response_model` |
| One schema for request and response | Split into `*Create`/`*Out` |
| Password in an output schema | Remove it — never expose `password_hash` |
| Missing `from_attributes` on `*Out` | Add `model_config = {"from_attributes": True}` |
| camelCase field without alias | `Field(alias="camelCase")` + `populate_by_name` |
| Data-dependent bound in `Field` | Check in service, raise `DomainError` |

## Checklist

- [ ] Separate input/output models; no ORM model over HTTP
- [ ] `*Out` sets `from_attributes`; built via `model_validate`
- [ ] Static constraints via `Field(...)`; every field typed
- [ ] camelCase input uses `alias=` + `populate_by_name`
- [ ] No secrets in output schemas
