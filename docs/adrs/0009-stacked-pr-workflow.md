# ADR 0009 — Stacked PR workflow with ≤500 LOC limit and no force-push

- **Status:** Accepted
- **Date:** 2026-05-24

## Context

Building the backend from scratch in one PR would be unreviewable. We needed a workflow that:

- Lets work proceed incrementally without blocking on each merge.
- Keeps every PR small enough to actually review.
- Survives mid-stream policy changes (CI bumps, naming refactors, new rules) without throwing away history.

## Decision

- **Stacked PRs.** Each feature branch is based on the previous one, not on `main`. Order is fixed:
  `main → chore/scaffold → chore/tooling → feat/db-core → feat/auth-models → feat/auth-endpoints → feat/stats → feat/activities-models → feat/activities-engine → feat/admin → feat/tests`.
  Doc / orthogonal PRs can branch off `main` directly (e.g. `chore/claude`, `chore/adrs`).
- **≤500 LOC per PR**, counted as insertions excluding `uv.lock`. Verify with:
  ```bash
  git diff <base>..<head> --stat -- . ":(exclude)uv.lock" | tail -1
  ```
  Larger work is split into multiple stacked PRs (e.g. `feat/auth` was split into `feat/auth-models` + `feat/auth-endpoints`; `feat/activities` into `feat/activities-models` + `feat/activities-engine`).
- **No force-push.** When a change needs to land on a branch that already has downstream PRs, add a new commit on the source branch and **cherry-pick** the same commit onto each downstream branch in order. Resolve conflicts by hand. The exception is repairing a mistake within the same session before anyone else has pulled (used once for the CI Node 24 bump).
- **Conventional Commits** with scope (`feat(auth-endpoints): ...`, `refactor(activities): ...`, `chore(tooling): ...`, `docs: ...`, `test: ...`, `ci: ...`, `fix: ...`).
- **PR body template.** Every PR uses `.github/pull_request_template.md` (the four sections What was done / Related issue / How to test / Additional notes). Bodies are passed to `gh pr create --body-file` so the contents stay out of the command line and don't trip local commit-msg hooks.
- **Assignee.** Every PR is assigned to `DanyloSus` via `gh pr edit <N> --add-assignee DanyloSus`.

## Consequences

**Positive**
- PRs land small, reviewable, and reorderable.
- Cherry-pick instead of force-push means downstream collaborators never face a `git pull --rebase` surprise.
- Conventional Commits + the size rule give us a predictable, mechanical changelog without a separate ceremony.
- A single template + assignee policy makes PR triage uniform.

**Negative**
- Cherry-picking the same commit through 6–9 branches is tedious and conflict-prone when downstream has touched the same lines. Mitigated by keeping cross-cutting changes minimal and well-scoped.
- The "no force-push" rule means undoing a wrong commit costs an extra revert commit on the branch. Accepted as a small price for predictability.
- Stack ordering is implicit; a contributor unfamiliar with the order risks branching off the wrong parent. Documented in `CLAUDE.md` and the `psl-pr-workflow` skill.

## Compliance

- New work that is part of the existing feature pipeline branches off the latest tip in that pipeline.
- Cross-cutting fixes (CI, lint config, naming refactors) land on the earliest branch where the file exists, then cherry-pick down.
- PR text never contains references to AI assistants (`Claude`, `Anthropic`, `Co-Authored-By:`, "Generated with …", 🤖). Enforced locally via `.claude/hooks/block-claude-refs.sh`.
