---
id: typing
tier: 0
tooling: [mypy]
enforcement: strict
paths:
  - "app/**/*.py"
---

# Typing

Enforces full type coverage under `mypy app`, SQLAlchemy 2.0 `Mapped[]` models, and typed pydantic v2 schemas.

## Rules

### T1. Type hints on every definition

**Tooling:** `mypy` (`disallow_untyped_defs`)

Every function and method has typed parameters and a return annotation. `mypy app` must pass clean.

```python
# ❌ FORBIDDEN — untyped
async def log_activity(self, user, payload):
    ...

# ✅ CORRECT — fully annotated
async def log_activity(
    self, user: User, payload: LogActivityRequest
) -> LogActivityResponse:
    ...
```

**Why:** Static types catch layer-contract violations and refactor breakage before runtime, and document intent at every boundary.

### T2. SQLAlchemy 2.0 `Mapped[]` column style

**Tooling:** `mypy`, `convention`

Model columns use `Mapped[T]` + `mapped_column(...)`. Never the legacy `Column(...)` class-attribute style. Relationships use `Mapped[list[...]]` / `Mapped["Model"]`.

```python
# ❌ FORBIDDEN — legacy style, untyped to mypy
id = Column(UUID(as_uuid=True), primary_key=True)

# ✅ CORRECT — 2.0 typed mapping
id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
)
refresh_tokens: Mapped[list[RefreshToken]] = relationship(back_populates="user")
```

**Why:** `Mapped[]` gives mypy real attribute types on ORM instances, so query results and model access are checked end to end.

### T3. Avoid `Any`; prefer precise types and `X | None`

**Tooling:** `mypy`

Do not reach for `Any` to silence mypy. Use precise types, `X | None` for optionals, and narrow before use.

```python
# ❌ FORBIDDEN
def decode(token: Any) -> Any: ...

# ✅ CORRECT
def decode_access_token(token: str) -> dict[str, str]: ...

user: User | None = await self.users.get_by_id(user_id)
if user is None:
    raise InvalidCredentialsError()
```

**Why:** `Any` erases checking transitively; one `Any` can hide bugs across a whole call chain. New untyped deps get stub overrides in `pyproject.toml`, not `Any`.

### T4. pydantic v2 schemas are fully typed

**Tooling:** `mypy`, `convention`

Every schema field is typed. Use `Field(...)` for constraints and `model_config` for `from_attributes` / `populate_by_name`.

```python
# ✅ CORRECT
class LogActivityRequest(BaseModel):
    activity_template_id: uuid.UUID = Field(alias="activityTemplateId")
    quantity: int = Field(default=1, ge=1, le=10_000)

    model_config = {"populate_by_name": True}
```

**Why:** Typed schemas give validated, self-documenting request/response contracts that mypy and FastAPI both understand.

## Verification

```bash
uv run mypy app
```
