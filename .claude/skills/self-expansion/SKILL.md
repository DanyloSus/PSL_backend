---
name: self-expansion
description: Add a new rule, skill, agent, or engine scenario to the .claude knowledge system from its template, then register it in manifest.json. Check for an existing artifact first; get user approval.
metadata:
  version: "1.0"
  stack: python-fastapi
  related-skills:
    - pipeline-orchestration
tier: 2
triggers:
  - new skill
  - new rule
  - new agent
  - expand
  - add artifact
summary: |
  Extend the AI knowledge system safely. Artifact types + templates:
  skill → .claude/templates/_SKILL_TEMPLATE.md (frontmatter: name, description,
  metadata, tier, triggers, summary); rule → _RULE_TEMPLATE.md (id, tier, tooling,
  enforcement, paths); agent → _AGENT_TEMPLATE.md (name, description, tools, model,
  memory); scenario → engine/_SCENARIO_TEMPLATE.md. Process: (1) search existing
  artifacts to avoid duplication, (2) get user approval on scope, (3) create the
  directory/file from the template, (4) register it in .claude/manifest.json with
  triggers, (5) keep it grounded in real app/ code. Prefer editing an existing
  artifact over adding a near-duplicate.
---

# Self-Expansion (Add Knowledge Artifacts)

## Overview

| Aspect       | Details                                                          |
| ------------ | --------------------------------------------------------------- |
| Goal         | Add a rule / skill / agent / scenario the system loads by trigger |
| When         | A durable, reusable pattern isn't yet captured                   |
| Verification | Artifact matches its template; registered in `manifest.json`     |

## Critical rules

**Check for an existing artifact before creating one, and get user approval on scope. Every new artifact is authored from its template and registered in `.claude/manifest.json` with `triggers`. Prefer editing over near-duplicating.**

## Concepts

### Artifact types & templates

| Artifact | Lives in | Template | Key frontmatter |
| -------- | -------- | -------- | --------------- |
| Skill | `.claude/skills/<name>/SKILL.md` | `templates/_SKILL_TEMPLATE.md` | name, description, metadata, `tier`, `triggers`, `summary` |
| Rule | `.claude/rules/<name>.md` | `templates/_RULE_TEMPLATE.md` | id, `tier`, `tooling`, `enforcement`, `paths` |
| Agent | `.claude/agents/<name>.md` | `templates/_AGENT_TEMPLATE.md` | name, description, `tools`, `model`, `memory` |
| Scenario | `.claude/engine/scenarios/<id>.md` | `engine/_SCENARIO_TEMPLATE.md` | id, budget, sub_agents, verified |

### Loading protocol

Artifacts are loaded on trigger: task keywords → `manifest.json` `triggers` → matching skill/rule. So a new artifact is inert until it is both authored to the template shape **and** registered in `manifest.json`. `context-tiers.json` governs what loads when.

### Grounding

Skills and rules must cite real `app/` code and the actual verification command (`uv run ruff check . && uv run mypy app && uv run pytest -q`). Follow the house tier-0 rules (layered architecture, thin routers, DomainError, no unsolicited comments).

## Patterns

### Add an artifact

1. **Search first** — grep `.claude/skills`, `.claude/rules`, `manifest.json` for the topic. If it exists, extend it instead.
2. **Approve scope** — confirm with the user what artifact type + triggers, since this shapes future agent behavior (hard to reverse cheaply).
3. **Author from the template** — copy the matching `_*_TEMPLATE.md`; fill every frontmatter field; keep `summary` ≤5 lines; ground examples in real code.
4. **Register** — add an entry to `.claude/manifest.json` with the artifact path, tier, and `triggers` list (this is what the loader matches).
5. **For scenarios** — obey engine invariants (session-log bookends, gate before write/spawn); set `verified: false` until it runs green once.

### Choosing type

- Recurring "how to do X in this codebase" knowledge → **skill**.
- An enforceable constraint (lint/mypy/convention) → **rule**.
- A scoped persona for delegated work → **agent**.
- A repeatable multi-step DAG → **scenario** (see `pipeline-orchestration`).

## Common mistakes

| Mistake | Fix |
| ------- | --- |
| Creating a near-duplicate skill | Search first; edit the existing one |
| Authoring without the template | Start from the matching `_*_TEMPLATE.md` |
| Forgetting to register | Add to `manifest.json` with `triggers` (else it never loads) |
| Skipping user approval | Confirm scope/type first — it shapes agent behavior |
| Ungrounded examples | Cite real `app/` files and the real verify command |
| Scenario without invariants | session-log bookends + gate before write/spawn |

## Checklist

- [ ] Searched existing artifacts; not a duplicate
- [ ] User approved type + scope
- [ ] Authored from the correct template; all frontmatter filled
- [ ] Registered in `manifest.json` with `triggers`
- [ ] Examples grounded in real `app/` code
