---
name: "ADR"
description: Record an Architecture Decision Record for an architecture-shaping, hard-to-reverse decision.
category: Docs
---

Record an Architecture Decision Record (ADR) under `docs/adrs/`.

**Input**: the argument after `/adr` is the decision title (a short phrase). If none given, ask what decision to record.

**When to use** (rule: `.claude/rules/decision-records.md`): architecture-shaping, hard-to-reverse decisions — auth model, layer boundaries, a cross-cutting pattern, a core dependency, a schema/migration direction. Skip reversible implementation detail.

**Steps**

1. Determine the next number: list `docs/adrs/` and take `max + 1`, zero-padded to 4 digits (`0001`, `0002`, …). If `docs/adrs/` does not exist, create it and start at `0001`.
2. Derive a kebab-case slug from the title. File: `docs/adrs/<NNNN>-<slug>.md`.
3. Write the ADR using this structure:

```md
# <NNNN>. <Title>

- Status: Accepted
- Date: <today, YYYY-MM-DD>
- Deciders: <who>

## Context

What forces are at play — the problem, constraints, and why a decision is needed now.

## Decision

The choice made, stated in active voice ("We will …").

## Consequences

What becomes easier and what becomes harder. Follow-ups, risks, and what this rules out.

## Alternatives considered

- <Option A> — rejected because …
- <Option B> — rejected because …
```

4. Show the draft and confirm before writing.

**Rules**

- Accepted ADRs are immutable — never rewrite one. To change a decision, add a new ADR that **supersedes** the old (note it in both files' Status).
- Keep it terse. One decision per ADR.
- After writing, remind the user it can be staged alongside the shaping change so the `adr_reminder` hook stays quiet.
