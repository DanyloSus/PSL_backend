---
name: grill-me
description: Interview the user one question at a time about every aspect of a plan or design until shared understanding is reached. Walks the decision tree branch by branch, explores the codebase instead of asking when the answer is discoverable, and gives a recommended answer for each question. Use when the user wants to stress-test a plan or says "grill me".
---

# Grill Me

Interview me relentlessly about every aspect of this plan until we reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

Ask the questions one at a time.

If a question can be answered by exploring the codebase, explore the codebase instead.

## PSL backend context

When grilling about backend work, anchor questions to the project's actual decision surfaces:

- **Layering** — does the change keep HTTP → service → repository → SQLAlchemy boundaries? Where does each piece of logic live?
- **Domain invariants** — XP ≥ 0 floor, level ≥ 1, levels never decrease, BINARY templates force quantity 1 (CLAUDE.md §5). Does the plan preserve them?
- **Transactions** — single transaction per activity log; lock+update per stat. Is concurrency handled?
- **Migrations** — new aggregate needs a model import in `app/models/__init__.py` + a new Alembic revision. Never edit a merged migration.
- **Cache** — does the change touch `ActivityTemplate`/`ActivityEffect`? If so, does it go through the ORM so the invalidation hooks fire?
- **Auth/CSRF** — cookies, refresh rotation, CSRF double-submit. Does a new endpoint need the CSRF guard?
- **Tests** — what's the failure mode, and which `app/tests/` case covers it?

Prefer reading `docs/PRD.md`, `docs/TDD.md`, `docs/adrs/`, and the relevant `app/` code over asking, whenever the answer is already written down.
