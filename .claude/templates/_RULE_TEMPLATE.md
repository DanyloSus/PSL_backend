---
id: <rule-id>
tier: <0|1|2>
tooling: [<ruff|mypy|convention|pytest|alembic>]
enforcement: <strict|warning|convention>
paths:
  - "app/**/*.py"
---

# <Rule Title>

One-sentence description of what this rule enforces and why.

## Rules

### <Check ID>. <Check Name>

**Tooling:** `<ruff-rule / mypy-flag / convention>` (or `pattern: ...` for grep-based checks)

Explanation of the rule intent.

```python
# ❌ FORBIDDEN / AVOID
<bad example>

# ✅ CORRECT / PREFER
<good example>
```

**Why:** Reasoning for this rule.

<!-- Repeat ### block for each check in this rule file -->

## Verification

```bash
uv run ruff check . && uv run mypy app
```
