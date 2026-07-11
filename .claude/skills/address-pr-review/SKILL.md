---
name: address-pr-review
description: Close the loop on the Claude PR review — each round derive the open findings from a fresh, non-deduped /pr-review on the current diff (plus any new human comments), fix the blockers and majors, commit granularly, and push, repeating until a fresh /pr-review shows 0 blockers + 0 majors. Never trust the deduped CI comment to decide "clean" (it suppresses still-open findings). Auto-fixes B* and M* findings only; lists N* nits for the author; pauses when a finding conflicts with the OpenSpec spec/proposal (the spec is source of truth) or touches an AGENTS §4a protected file. Bounded round cap prevents ping-pong. Used as the final phase of /opsx:apply, and standalone when a PR has review comments to resolve.
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
  Drive the PR review to green. Each round, derive the authoritative open
  findings from a FRESH, non-deduped `/pr-review` on the current branch diff
  (plus any new human review comments) — NOT from the CI `claude[bot]` comment,
  which dedupes (suppresses still-open findings, so an empty comment never means
  clean). Auto-fix only Blockers (B*) and Majors (M*); parse ID · severity ·
  file:line · reframe. Commit granularly (Conventional Commits), push to update
  the PR, then loop: re-run a fresh `/pr-review`. Terminate when a fresh review
  shows 0 blockers + 0 majors (and no unaddressed human comment), or the round
  cap (default 3) is hit. Leave N* nits for the author. PAUSE, never blindly
  fix, when a finding contradicts the OpenSpec proposal/spec (source of truth —
  update the artifact instead) or targets an AGENTS §4a protected file.
  Read-the-diff-first: verify each finding is real. Standalone or last phase of
  /opsx:apply.
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
| Loop         | fix → commit → push → re-derive open findings via a **fresh** local `/pr-review` → repeat, capped at 3 rounds |
| Verification | Changed-file `uv run ruff check` + `uv run mypy app`; a **fresh, non-deduped** `/pr-review` is the acceptance gate |

## Critical rules

**Fix only Blockers (`B*`) and Majors (`M*`). Read the diff and confirm a finding is real before touching code — the review can be wrong. PAUSE (do not auto-fix) when a finding contradicts the OpenSpec proposal/spec, or targets an AGENTS §4a protected file. Cap the loop at 3 rounds; if blockers survive, stop and report.**

**Never infer "clean" from the absence of findings in the CI PR comment.** The **Claude PR Review** workflow *dedupes* — it suppresses any finding already posted on the PR, fixed or not (see [Why the CI comment is not the authority](#why-the-ci-comment-is-not-the-loops-authority)). An unfixed blocker vanishes from the next comment, so an empty deduped comment does **not** mean the code is clean. Determine what is still open by running a **fresh `/pr-review`** against the current diff each round; that non-deduped list is the loop's sole termination authority.

## Concepts

### The review comment shape

The **Claude PR Review** workflow posts a comment as `claude[bot]` per run (newest = latest review). Each finding is a block the `pr-review` Output Format defines:

```
### arch-B1 · blocker · layer-architecture (L2) · `arch`
`app/services/activity_service.py:120`
Issue — one-sentence problem.
Reframe — one-sentence fix, naming the target method/repo/schema.
```

Severity comes from the ID prefix: **`B`** = blocker, **`M`** = major, **`N`** = nit. The comment ends with `**Approval verdict:** …`. The CI comment is a good **entry point** — it tells you a review ran and shows the first round's findings (and any human review comments) — but it is **not** the loop's termination authority (next).

### Why the CI comment is not the loop's authority

The workflow prompt tells the reviewer to **suppress any finding already present on the PR** ("do not repeat a finding already covered… post nothing when every issue is already covered"). That dedupe keeps the PR readable for humans, but it breaks "absence ⇒ resolved":

```
round 1: review posts arch-B1 (blocker)
loop tries to fix it but the fix is wrong / incomplete
round 2: re-review sees arch-B1 already on the PR → SUPPRESSES it → comment is empty
loop reads empty comment → "0 blockers" → STOPS  ← WRONG: arch-B1 is still in the code
```

So the loop derives "what is still open" itself, each round, by running a **fresh `/pr-review`** (full sub-agent review, non-deduped) against the current branch diff. The CI comment stream stays for humans and for surfacing **new human** review comments the loop should also address.

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
2. **Collect the authoritative open findings for this round** — from two sources, merged:
   - **Fresh `/pr-review`** on the current branch diff (`--base <baseRefName>`). This full, non-deduped sub-agent review is the source of truth for the code's own findings. (Locally this fans out both agents; do not read the CI comment for this.)
   - **New human review comments** on the PR since the last round — pull them so the loop also honors what a human reviewer asked for:
     ```bash
     gh api repos/<owner>/<repo>/pulls/<pr>/comments --jq '.[] | select(.user.login!="claude[bot]") | "\(.path):\(.line) \(.body)"'
     gh api repos/<owner>/<repo>/issues/<pr>/comments --jq '.[] | select(.user.login!="claude[bot]") | .body'
     ```
   (The CI `claude[bot]` comment is a useful entry signal, but its deduped body is **not** used to decide what is still open — see the concept above.)
3. **Parse findings.** From the fresh review, extract each `### <id> · <severity> · …` block with its file:line, Issue, Reframe; split by severity from the ID prefix. Add any human-requested changes as findings too.
4. **Decide.**
   - Fresh review has **0 `B*` + 0 `M*`** and no unaddressed human request → **done**. List any `N*` nits for the author, exit.
   - Round count ≥ cap (3) → **stop**, report surviving blockers, hand back to the author.
   - Otherwise → fix this round.
5. **Fix B*/M* findings.** For each, in the order the review ranked them:
   - **Read the cited file:line and confirm the finding is real.** If it's a false positive, skip it and record why.
   - If it **conflicts with the OpenSpec proposal/spec** → pause; the spec is source of truth. Surface it and offer to update the artifact instead (mirrors apply's "implementation reveals a design issue" guardrail).
   - If it targets a **§4a protected file** (`app/core/security.py|cookies.py|config.py|db.py|dependencies.py`, `app/main.py`, `app/migrations/**`, `alembic.ini`, `pyproject.toml`, `.pre-commit-config.yaml`, `.github/workflows/**`) → pause, flag for sign-off, do not auto-edit.
   - Otherwise apply the reframing the review proposed, honoring PSL rules (extract to a repository, raise a `DomainError`, add a `*Out` schema, etc.).
6. **Verify locally.** Changed-file lint only (`lint-scope`): `uv run ruff check <changed>` + `uv run mypy app`. Do not run the full suite here — CI owns it.
7. **Commit granularly + push.** One logical fix per commit, Conventional Commits with scope (`fix(activities): move template query into repository (arch-B1)`). Reference the finding ID in the body. Push updates the PR (and fires the CI re-review for the human record).
8. **Loop** back to step 2 — re-derive the open findings with a **fresh** `/pr-review` — for the next round.

### Termination

- **Clean:** a **fresh** `/pr-review` on the current diff has 0 `B*` + 0 `M*`, and no unaddressed human comment. Done. (Not "the CI comment was empty" — that can be a dedupe artifact.)
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
| Trusting the deduped CI comment to decide "clean" | Re-derive open findings with a **fresh** `/pr-review` each round; the CI comment suppresses still-open findings |
| Running the full pytest suite each round | Changed-file ruff + mypy only; CI runs the suite |

## Checklist

- [ ] PR located (current branch or explicit number)
- [ ] Open findings derived from a **fresh** `/pr-review` (not the deduped CI comment) + any new human comments
- [ ] Fixed only `B*`/`M*`; confirmed each against the cited file:line first
- [ ] Paused on any spec-conflicting finding or §4a protected file
- [ ] Nits (`N*`) listed for the author, not auto-fixed
- [ ] Granular Conventional commits, finding ID in the body
- [ ] Changed-file `ruff check` + `mypy app` pass
- [ ] Pushed to update the PR
- [ ] Looped until a fresh `/pr-review` shows 0 blockers + 0 majors, or stopped at the 3-round cap with a report
