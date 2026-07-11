---
name: address-pr-review
description: Close the loop on the Claude PR review — read the bot's findings on a PR, fix the blockers and majors, push, wait for the re-review, and repeat until the approval verdict is clean. Auto-fixes B* and M* findings only; lists N* nits for the author; pauses when a finding conflicts with the OpenSpec spec/proposal (the spec is source of truth) or touches an AGENTS §4a protected file. Bounded round cap prevents ping-pong. Used as the final phase of /opsx:apply, and standalone when a PR has review comments to resolve.
metadata:
  version: "1.0"
  stack: python-fastapi
  related-skills:
    - pr-review
    - openspec-apply-change
    - pull-request-description
    - git-commit
  related-agents:
    - code-reviewer
    - architecture-auditor
tier: 2
triggers:
  - address pr review
  - fix pr comments
  - resolve review comments
  - fix review findings
  - address review
  - review fix loop
summary: |
  Drive the PR review to green. Read the newest `claude[bot]` review comment on
  a PR, parse its findings (ID · severity · rule · file:line · reframe), and
  auto-fix only Blockers (B*) and Majors (M*). Commit granularly (Conventional
  Commits), push — which fires the `synchronize` re-review that dedupes against
  prior comments — then poll the new run and read the fresh verdict. Loop until
  0 blockers + 0 majors or the round cap (default 3) is hit. Leave N* nits for
  the author. PAUSE, never blindly fix, when a finding contradicts the OpenSpec
  proposal/spec (source of truth — update the artifact instead) or targets an
  AGENTS §4a protected file. Read-the-diff-first: verify each finding is real
  before changing code. Standalone or as the last phase of /opsx:apply.
---

# Address PR Review (fix loop)

Close the loop opened by the `pr-review` skill / the **Claude PR Review** workflow: read the findings the bot posted on a PR, fix the ones that block merge, push, let the re-review confirm, and repeat until clean.

**This skill writes code and pushes.** It is deliberate about scope: it fixes **only Blockers and Majors**, loops a **bounded** number of rounds, and **pauses** rather than guessing when a finding fights the spec or a protected file.

## Overview

| Aspect       | Details                                                                                          |
| ------------ | ------------------------------------------------------------------------------------------------ |
| Goal         | Drive a PR's Claude review to a clean verdict (0 blockers + 0 majors) by fixing B*/M* findings    |
| When         | A PR has a `claude[bot]` review with blocker/major findings — standalone, or final phase of apply |
| Scope        | Auto-fix B*/M* only; leave N* nits; pause on spec conflict or §4a protected file                  |
| Loop         | fix → commit → push → re-review (auto, dedupes) → read verdict → repeat, capped at 3 rounds       |
| Verification | Changed-file `uv run ruff check` + `uv run mypy app`; the re-review is the acceptance gate        |

## Critical rules

**Fix only Blockers (`B*`) and Majors (`M*`). Read the diff and confirm a finding is real before touching code — the review can be wrong. PAUSE (do not auto-fix) when a finding contradicts the OpenSpec proposal/spec, or targets an AGENTS §4a protected file. Cap the loop at 3 rounds; if blockers survive, stop and report.**

## Concepts

### The review comment shape

The **Claude PR Review** workflow posts a comment as `claude[bot]` per run (newest = latest review). Each finding is a block the `pr-review` Output Format defines:

```
### arch-B1 · blocker · layer-architecture (L2) · `arch`
`app/services/activity_service.py:120`
Issue — one-sentence problem.
Reframe — one-sentence fix, naming the target method/repo/schema.
```

Severity comes from the ID prefix: **`B`** = blocker, **`M`** = major, **`N`** = nit. The comment ends with `**Approval verdict:** …`. Read the **newest** `claude[bot]` comment — the re-review already dedupes against older ones, so it only lists what is still open plus anything new.

### What this skill fixes vs skips

| Finding | Action |
| ------- | ------ |
| `B*` blocker | **Fix** (unless spec-conflict / §4a — then pause) |
| `M*` major | **Fix** (unless spec-conflict / §4a — then pause) |
| `N*` nit | **Skip** — list for the author at the end |
| Contradicts the OpenSpec proposal/spec | **Pause** — the spec wins; propose updating the artifact instead |
| Targets a §4a protected file | **Pause** — flag for explicit sign-off, do not auto-edit |
| You read the diff and the finding is wrong | **Skip + note** — reply why it's a false positive |

## Patterns

### The loop

Prerequisite: a PR exists for the branch. (In `/opsx:apply`, the apply phase opens it first via `pull-request-description`.)

1. **Locate the PR.** `gh pr view --json number,headRefName,baseRefName` for the current branch, or take an explicit PR number.
2. **Wait for the review.** The workflow triggers on push/open. Poll the run:
   ```bash
   gh run list --repo <owner>/<repo> --workflow=claude-pr-review.yml --limit 1 \
     --json databaseId,status,conclusion,headSha \
     --jq '.[] | "\(.databaseId) \(.status) \(.conclusion) \(.headSha[0:7])"'
   ```
   Match `headSha` to the branch HEAD; poll `gh run view <id> --json status,conclusion` until `completed`.
3. **Read the newest review.**
   ```bash
   gh api repos/<owner>/<repo>/issues/<pr>/comments --jq '[.[] | select(.user.login=="claude[bot]")] | last | .body'
   ```
4. **Parse findings.** Extract each `### <id> · <severity> · …` block with its file:line, Issue, Reframe. Split by severity from the ID prefix. Read the `**Approval verdict:**` line.
5. **Decide.**
   - No `B*`/`M*` findings (verdict clean) → **done**. List any `N*` nits for the author, exit.
   - Round count ≥ cap (3) → **stop**, report surviving blockers, hand back to the author.
   - Otherwise → fix this round.
6. **Fix B*/M* findings.** For each, in the order the review ranked them:
   - **Read the cited file:line and confirm the finding is real.** If it's a false positive, skip it and record why.
   - If it **conflicts with the OpenSpec proposal/spec** → pause; the spec is source of truth. Surface it and offer to update the artifact instead (mirrors apply's "implementation reveals a design issue" guardrail).
   - If it targets a **§4a protected file** (`app/core/security.py|cookies.py|config.py|db.py|dependencies.py`, `app/main.py`, `app/migrations/**`, `alembic.ini`, `pyproject.toml`, `.pre-commit-config.yaml`, `.github/workflows/**`) → pause, flag for sign-off, do not auto-edit.
   - Otherwise apply the reframing the review proposed, honoring PSL rules (extract to a repository, raise a `DomainError`, add a `*Out` schema, etc.).
7. **Verify locally.** Changed-file lint only (`lint-scope`): `uv run ruff check <changed>` + `uv run mypy app`. Do not run the full suite here — CI owns it.
8. **Commit granularly + push.** One logical fix per commit, Conventional Commits with scope (`fix(activities): move template query into repository (arch-B1)`). Reference the finding ID in the body. Push — this fires the `synchronize` re-review, which **dedupes** against the comments already on the PR.
9. **Loop** back to step 2 for the next round.

### Termination

- **Clean:** newest review has 0 `B*` + 0 `M*` (or an approving verdict). Done.
- **Cap hit:** after 3 fix rounds blockers remain → stop, report what's left and why (likely a genuine design problem the review keeps surfacing) — escalate to the author, don't keep pushing.
- **Paused:** a finding conflicts with the spec or a §4a file → stop the loop, present the conflict, wait for a decision.

### Round-cap rationale

Auto-fix + re-review can ping-pong (a fix introduces a new finding). The cap bounds token spend and forces a human look when the review and the code disagree past a few rounds. 3 is the default; raise only deliberately.

## Common mistakes

| Mistake | Fix |
| ------- | --- |
| Fixing nits (`N*`) automatically | Skip them; list for the author. Loop targets blockers/majors |
| Blindly applying a finding that fights the spec | Pause — spec is source of truth; update the artifact instead |
| Auto-editing a §4a protected file | Pause + flag for sign-off; never silently edit |
| One giant "address review" commit | One logical fix per commit, Conventional Commits, cite the finding ID |
| Not confirming the finding first | Read the cited file:line; the review can be wrong — skip false positives |
| Infinite loop | Cap at 3 rounds; escalate surviving blockers |
| Reading an old review comment | Take the **newest** `claude[bot]` comment — the re-review already deduped |
| Running the full pytest suite each round | Changed-file ruff + mypy only; CI runs the suite |

## Checklist

- [ ] PR located (current branch or explicit number)
- [ ] Waited for the review run to complete; matched `headSha` to HEAD
- [ ] Read the **newest** `claude[bot]` review; parsed findings + verdict
- [ ] Fixed only `B*`/`M*`; confirmed each against the cited file:line first
- [ ] Paused on any spec-conflicting finding or §4a protected file
- [ ] Nits (`N*`) listed for the author, not auto-fixed
- [ ] Granular Conventional commits, finding ID in the body
- [ ] Changed-file `ruff check` + `mypy app` pass
- [ ] Pushed → re-review fired and deduped
- [ ] Looped until 0 blockers + 0 majors, or stopped at the 3-round cap with a report
