---
id: spec-driven
tier: 1
tooling: [convention, openspec, pytest]
enforcement: convention
paths:
  - "openspec/**"
  - "app/tests/**/*.py"
---

# Spec-Driven Development

Non-trivial features and fixes are specified as an OpenSpec change before code. Requirement IDs are the traceability spine: tests reference them, commits refer to them. Grammar and per-artifact rules live in `openspec/config.yaml`.

## Rules

### SD1. Requirement IDs are stable headings

**Convention:** every requirement is a heading `### FR-<AREA>-<n>` (functional), `NFR-` (non-functional), `TC-` (technical constraint), or `BC-` (business constraint).

```md
✅  ### FR-ACT-03 — Reject quantity outside template bounds
❌  ### The activity log should validate quantity   (no stable ID → nothing to trace)
```

**Why:** the ID is the join key between spec, tests (`# @trace`), and commits (`Refs:`). Prose headings can't be traced.

### SD2. Every FR/NFR declares a Verification method from the closed vocab

**Convention:** `Verification:` is one of `local-verifiable` (pytest unit/integration) · `migration` (alembic upgrade/downgrade) · `manual`. Never invent a method.

```md
✅  Verification: local-verifiable
❌  Verification: it works when I try it   (not in the vocab → phantom gate)
```

**Why:** a declared method with no real mechanism is a gate that never runs. The closed vocab maps each requirement to something executable.

### SD3. Tests trace their requirement

**Convention:** a test that verifies a requirement carries `# @trace <req-id>` near its definition.

```python
# ✅
async def test_log_rejects_quantity_above_max(auth_client):
    # @trace FR-ACT-03
    ...
```

**Why:** makes coverage auditable — `grep "@trace FR-ACT-03"` proves the requirement is exercised. The `spec-compliance-auditor` agent relies on it.

### SD4. Tests are written from the spec, red first

**Convention:** in the tasks artifact, order sections schema/migration → failing tests (red) → implement (green) → validate/archive. Test tasks precede implementation tasks.

**Why:** a test written after the code tends to encode the implementation, not the requirement.

### SD5. Retro-spec on touch

**Convention:** a change touching an area with no baseline spec in `openspec/specs/` reverse-engineers that baseline spec first, then proposes the change against it.

**Why:** keeps the spec set honest as the codebase grows; avoids specs that only cover greenfield work.

### SD6. Source-of-truth docs are read-only

**Convention:** `docs/PRD.md` and `docs/TDD.md` are authoritative product/tech specs — do not edit unless explicitly asked. OpenSpec artifacts derive from them; they do not replace them.

## Workflow

```
/opsx:explore   → think through the idea (optional)
/opsx:propose   → create change + proposal/design/tasks artifacts
/opsx:apply     → implement tasks (red → green)
/opsx:archive   → fold delta specs into baseline
```

## Verification

```bash
openspec validate --all
uv run pytest -q
```
