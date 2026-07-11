---
id: code-style
tier: 0
tooling: [ruff, convention]
enforcement: strict
paths:
  - "app/**/*.py"
---

# Code Style

Enforces ruff lint + format, snake_case, spelled-out locals, all-async IO, and a strict no-comments default.

## Rules

### CS1. No code comments unless explicitly requested

**Tooling:** `convention` (critical)

Default to zero comments — write self-explanatory code. The only exceptions: the user explicitly asks for a comment, or a genuinely non-obvious WHY (a subtle invariant, workaround, or surprising behavior) needs recording. Never restate what the code does. When editing existing code, do not add comments on your own initiative.

```python
# ❌ FORBIDDEN — comment restates the code
# floor the delta at zero
delta = max(0, effect.xp_change * quantity)

# increment the user's global xp
user.global_xp += delta

# ✅ CORRECT — no comment; the code is self-explanatory
delta = max(0, effect.xp_change * quantity)
user.global_xp += delta

# ✅ ALLOWED — records a non-obvious WHY
# after_commit is a safety net: after_insert fires before the row is flushed
event.listen(Session, "after_commit", after_commit)
```

**Why:** Comments drift out of sync with code and add noise. Clear names and small functions communicate intent better. This is a hard project rule.

### CS2. Format and lint with ruff

**Tooling:** `ruff` (`ruff check`, `ruff format`)

All code passes `ruff check .` and `ruff format .`. Do not hand-format against ruff.

```bash
uv run ruff check . && uv run ruff format .
```

**Why:** One formatter, zero style debates, clean diffs. CI fails on lint or format drift.

### CS3. snake_case for Python identifiers

**Tooling:** `ruff` (naming), `convention`

Functions, variables, modules use snake_case. Classes use PascalCase.

```python
# ❌ FORBIDDEN
def logActivity(userStat): ...
activeUser = ...

# ✅ CORRECT
def log_activity(user_stat): ...
active_user = ...
```

**Why:** PEP 8 consistency across the codebase.

### CS4. Spell out local variable names

**Tooling:** `convention`

Use descriptive names — never single letters when the context isn't obvious. Prefer `settings = get_settings()` over `s = ...`, and `user_stat`, `progress`, `cookie_kwargs`, `sessionmaker`.

```python
# ❌ FORBIDDEN
s = get_settings()
us = await self.user_stats.get(uid, sid)
ck = build_cookie_kwargs()

# ✅ CORRECT
settings = get_settings()
user_stat = await self.user_stats.get(user_id, stat_id)
cookie_kwargs = build_cookie_kwargs()
```

**Why:** In long service methods, terse names make review and maintenance error-prone. Readability outweighs a few saved characters.

### CS5. All IO is async, with `async with` for resources

**Tooling:** `convention`

Every database and Redis call is `await`ed. Use `async with` for sessions and Redis lifecycles. Never run blocking IO on the event loop.

```python
# ❌ FORBIDDEN — sync/blocking call on the event loop
result = requests.get(url)
session.execute(stmt)

# ✅ CORRECT — async throughout
async with get_session() as session:
    result = await session.execute(stmt)
```

**Why:** The stack is fully async (FastAPI + asyncpg + redis.asyncio). One blocking call stalls the whole event loop.

## Verification

```bash
uv run ruff check . && uv run ruff format --check .
```
