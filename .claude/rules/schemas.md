---
id: schemas
tier: 1
tooling: [convention, mypy]
enforcement: strict
paths:
  - "app/schemas/**/*.py"
  - "app/routers/**/*.py"
---

# Schemas (pydantic v2)

Enforces separate pydantic `*Create/*Update/*Out` models for API IO, never reusing ORM models, with validation living in the schema.

## Rules

### SC1. Never use ORM models for API IO

**Tooling:** `convention` (`pattern: response_model=<ModelClass>` referencing `app.models`)

Routers accept and return pydantic schemas from `app/schemas/`, never SQLAlchemy models from `app/models/`. Convert with `model_config = {"from_attributes": True}`.

```python
# ❌ FORBIDDEN — exposing the ORM model on the wire
from app.models.user import User

@router.get("/me", response_model=User)  # leaks password_hash, columns, relationships
async def get_me(...): ...

# ✅ CORRECT — dedicated output schema
class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    username: str
    global_xp: int
    global_level: int

    model_config = {"from_attributes": True}

@router.get("/me", response_model=UserOut)
async def get_me(...) -> UserOut: ...
```

**Why:** ORM models carry secrets (`password_hash`), lazy relationships, and internal columns. Exposing them leaks data and couples the API surface to the database schema.

### SC2. Separate `*Create` / `*Update` / `*Out`

**Tooling:** `convention`

One schema per IO direction. Create carries inbound-only fields (e.g. plaintext password), Out carries server-set fields (e.g. `id`, `global_level`), Update makes fields optional.

```python
# ✅ CORRECT
class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, pattern=r"^[a-zA-Z0-9_.-]+$")
    password: str

class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    username: str
    model_config = {"from_attributes": True}
```

**Why:** Shared schemas force nullable/optional hacks and risk accepting server-owned fields as input or emitting inbound-only fields.

### SC3. Validation and bounds live in the schema

**Tooling:** `convention`

Field-level constraints (`ge`, `le`, `min_length`, `pattern`) belong on the pydantic `Field`, so invalid input is rejected at the edge with a 422 before it reaches a service. Domain-relative bounds (e.g. per-template quantity) are re-checked in the service — see `domain-xp.md`.

```python
# ✅ CORRECT — static bounds at the edge
class LogActivityRequest(BaseModel):
    activity_template_id: uuid.UUID = Field(alias="activityTemplateId")
    quantity: int = Field(default=1, ge=1, le=10_000)

    model_config = {"populate_by_name": True}
```

**Why:** Edge validation gives clients precise 422s and keeps services free of primitive input-shape checks. Aliases (`populate_by_name`) bridge the camelCase client to snake_case Python.

## Verification

```bash
uv run mypy app && uv run pytest -q app/tests
```
