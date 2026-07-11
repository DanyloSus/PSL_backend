# Protocol: Self-Expansion

> How to add a new rule, skill, agent, or engine scenario without polluting or
> duplicating the knowledge base. Template-driven, gated on user approval.

## Pre-flight (always, before writing anything)

1. **Duplicate check.** Scan `.claude/manifest.json` for an artifact with overlapping
   `triggers` or purpose. If one exists, **extend it** — do not create a near-duplicate.
   Triggers must be distinct: no substring collision with an existing trigger.
2. **Scope check.** Does this belong in `.claude/` (AI guidance) or `docs/` (human-facing
   spec/ADR)? Source-of-truth product/tech facts go in `docs/`, not a skill.
3. **Tier check.** New artifacts default to **tier 2** (on-demand). Promoting to tier 0/1
   (`context-tiers.json`) requires explicit user approval — tier 0 is always-loaded and
   must stay lean.

## Flow

```
Identify gap → Propose to user (GATE) → Copy template → Fill → Write → Register → Verify
```

1. **Identify the gap** — what knowledge/capability is missing, and why a new artifact
   rather than an edit to an existing one.
2. **Propose to the user** — one-line summary + artifact type + target path + triggers +
   tier. **Wait for approval.** This gate is mandatory; never self-register silently.
3. **Copy the right template:**

   | Artifact | Template                               | Lands in                     |
   | -------- | -------------------------------------- | ---------------------------- |
   | Rule     | `.claude/templates/_RULE_TEMPLATE.md`  | `.claude/rules/<id>.md`      |
   | Skill    | `.claude/templates/_SKILL_TEMPLATE.md` | `.claude/skills/<id>/SKILL.md` |
   | Agent    | `.claude/templates/_AGENT_TEMPLATE.md` | `.claude/agents/<id>.md`     |
   | Scenario | `.claude/engine/_SCENARIO_TEMPLATE.md` | `.claude/engine/scenarios/<id>.md` |

4. **Fill the frontmatter/metadata** — id/name, tier, triggers, ≤5-line `summary`
   (skills), explicit read/write/execute/forbidden `scope` (agents).
5. **Write content** with real PSL examples (actual module paths, real service/repo names)
   — not placeholders.
6. **Register:**
   - Rules / skills / agents / protocols → add to `.claude/manifest.json` and bump its
     `lastUpdated`.
   - Scenarios → add to `.claude/engine/registry.json` with `verified: false`.
7. **Verify** — validate the edited JSON, and run `uv run ruff check .` on any example
   code the artifact ships.

## Rules

- `.claude/BOOTSTRAP.md` stays **<200 lines** — link to the new artifact, don't inline it.
- Every skill carries a `summary` (≤5 lines) so agents decide to load it without reading
  the full file.
- Every agent declares an explicit `scope` (read / write / execute / forbidden).
- New scenarios stay `verified: false` until they run successfully once; only then flip.
- One concern per artifact — if it needs two unrelated trigger sets, it's two artifacts.
