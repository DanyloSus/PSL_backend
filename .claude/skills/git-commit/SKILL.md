---
name: git-commit
description: Conventional Commit generator for PSL backend. Analyzes the staged diff, picks type+scope, writes a concise message. Use when asked to commit, write a commit message, or stage changes.
---

# Git Commit (PSL backend)

## Workflow

1. `git status` + `git diff --staged` to see what will be committed.
2. Group changes by type/scope.
3. Pick ONE primary type (`feat`, `fix`, `refactor`, …).
4. Pick a scope = the affected area (layer or feature: `auth-endpoints`, `activities`, `db-core`, `tooling`).
5. Write a concise imperative subject ≤72 chars.
6. Add a body only if the "why" is non-obvious.
7. `git commit -m "<message>"`.

## Type selection

| Type       | When                                   |
| ---------- | -------------------------------------- |
| `feat`     | New feature or user-visible capability |
| `fix`      | Bug fix                                |
| `docs`     | Docs only                              |
| `refactor` | Internal change with no behavior delta |
| `test`     | Adding or changing tests               |
| `chore`    | Repo maintenance, tool config          |
| `perf`     | Performance improvement                |
| `ci`       | CI config change                       |
| `build`    | Build system / Dockerfile change       |

## Scope selection (PSL layers + features)

Scopes mirror the layered architecture and feature areas:

- `auth-endpoints`, `auth-models`, `activities`, `activities-engine`, `stats`, `admin`
- `db-core`, `tooling`, `scaffold`, `migrations`
- Repo-wide → no scope.

```
feat(auth-endpoints): add refresh rotation on /auth/refresh
fix(db-core): close async session on lifespan shutdown
refactor(activities): extract LevelingService.threshold_for
test: cover BINARY template quantity coercion
chore(tooling): pin fastapi-limiter to 0.1.6
docs(adrs): record redis template cache decision
```

## Rules

- Imperative mood ("add", not "added"). No period at end of subject.
- Body wraps at 72 chars; explain the WHY.
- If commit fixes an issue: `Closes #123` in footer.
- **Never `--no-verify`.** Pre-commit runs `ruff check` + `ruff format` + `mypy`; commit-msg runs `.claude/hooks/block-claude-refs.sh`. Fix the root cause instead.
- **No AI attribution.** Never add `Co-Authored-By`, "Generated with Claude Code", Claude/Anthropic references, or 🤖 — the commit-msg hook blocks them (CLAUDE.md §9, §18).

## What to avoid

| Don't                          | Do                                          |
| ------------------------------ | ------------------------------------------- |
| `feat: stuff`                  | `feat(activities): add XP floor at 0`       |
| Long subject lines             | Break into subject + body                   |
| Mixing unrelated changes       | Split into multiple commits (see git-commit-push) |
| `git commit --no-verify`       | Fix the ruff/mypy/hook failure, then commit |
| Any Claude/Anthropic footer    | Strip it — hook will reject the commit      |

## Verification

- Pre-commit hooks pass (`ruff`, `mypy`).
- Commit-msg hook accepts the message (no blocked refs).
