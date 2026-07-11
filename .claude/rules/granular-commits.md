---
id: granular-commits
tier: 1
tooling: [convention]
enforcement: strict
paths:
  - ".git/**"
---

# Granular Commits

Enforces one-logical-change commits in Conventional Commits format, with the commit-msg hook blocking attribution trailers.

## Rules

### GC1. One logical change per commit

**Tooling:** `convention`

Split by concern — a bug fix, a feature, and a refactor are separate commits. Stage only the related files per commit. Each commit builds and lints on its own and is independently revertable.

```bash
# ❌ FORBIDDEN — one catch-all commit
git add -A && git commit -m "stuff"

# ✅ CORRECT — split by concern, stage per commit
git add app/services/activity_service.py app/schemas/activity.py
git commit -m "feat(activities): reject quantity outside template bounds"
git add app/tests/test_activity_bounds.py
git commit -m "test: cover template quantity bounds"
```

**Why:** Granular commits make review, bisect, and revert precise. A commit that mixes concerns can't be reverted without collateral damage.

### GC2. Conventional Commits with scope

**Tooling:** `convention`

Use a Conventional Commit prefix with a scope: `feat|fix|refactor|chore|style|docs|test|ci|build|perf`.

```
✅ feat(auth-endpoints): rotate refresh token on every refresh
✅ fix(db-core): chain down_revision to the previous migration
✅ refactor(activities): extract leveling math into LevelingService
✅ chore(tooling): pin fastapi-limiter to 0.1.6
✅ test: cover template quantity bounds
❌ update stuff
❌ WIP
```

**Why:** Structured messages make history scannable and drive changelog/release tooling. The scope tells reviewers which area moved.

### GC3. No Claude/Anthropic/Co-Authored-By trailers

**Tooling:** `convention` (commit-msg hook blocks it)

Never add `Co-Authored-By: Claude`, "Generated with ...", 🤖, or any Claude/Anthropic attribution to commits or PR bodies. The `.claude/hooks/block-claude-refs.sh` commit-msg hook rejects them — fix the message, never bypass with `--no-verify`.

```
❌ FORBIDDEN in a commit message:
   Co-Authored-By: Claude <noreply@anthropic.com>
   🤖 Generated with Claude Code
```

**Why:** Project policy. The hook enforces it; bypassing the hook is not allowed.

## Verification

```bash
git log --oneline -5
```
