# Protocol: Token Budget

> Never load the whole knowledge base. Tier-based loading with a per-task cap.
> Source of truth: `.claude/context-tiers.json`.

## Tiers

| Tier | Label          | What loads                                                            |
| ---- | -------------- | --------------------------------------------------------------------- |
| 0    | Always         | `.claude/BOOTSTRAP.md` + tier-0 rules (`layer-architecture`, `code-style`, `imports`, `typing`, `naming`) |
| 1    | Trigger-loaded | Skills + rules whose `triggers` match the task keywords (cap: 5 skills) |
| 2    | On-demand      | Full agents, protocols, templates, reference docs — only when needed  |

## Budgets

| Task type              | Max skills | Max rules    | Strategy                                    |
| ---------------------- | :--------: | :----------: | ------------------------------------------- |
| simple (1 file)        |     2      |      3       | Summary-only unless a skill is directly relevant |
| feature (multi-file)   |     5      | all matching | Full skill for the primary, summary for the rest |
| audit                  |    all     |     all      | Full load permitted                         |

## Loading steps

1. Read `BOOTSTRAP.md` (always — tier 0).
2. Classify the task → pick a budget (simple / feature / audit).
3. Match task keywords against `manifest.json` `triggers`.
4. Read the **`summary`** (≤5 lines) of each matched skill first.
5. Read the full `SKILL.md` only when the summary is insufficient — and only for the
   directly relevant skill(s).
6. Load tier-0 rules always; load a tier-1 rule only if the task touches that area.
7. Load protocols/agents only when orchestrating or self-expanding.

## Rules

- **Summary before full.** Never open a full `SKILL.md` before its manifest summary tells
  you it's relevant.
- **Cap skills per task** at the budget (5 for feature, 2 for simple). If more seem
  needed, the task is really an audit — reclassify, don't quietly exceed.
- **`BOOTSTRAP.md` stays < 200 lines** (tier 0 loads every session). New knowledge links
  out to a tier-1/2 artifact instead of inflating it.
- **Cache within a session** — a skill read once is not re-read.

## Anti-patterns

- Loading every skill "just in case" — context balloons past 20k tokens.
- Reading the full `README.md` for a routine edit.
- Re-reading the same skill or rule multiple times in one session.
- Promoting an artifact to tier 0/1 to "make sure it loads" — that's what triggers are for.
