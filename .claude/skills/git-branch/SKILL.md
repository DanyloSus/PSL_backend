---
name: git-branch
description: Branch naming and stacked-PR conventions for PSL backend. Use when creating a branch, starting a feature, or stacking a dependent PR.
---

# Git Branch (PSL backend)

## Naming format

```
<type>/<short-description>
```

- **type**: `feat` | `fix` | `refactor` | `chore` | `docs` | `test` | `ci` (mirrors the Conventional Commit type).
- **short-description**: kebab-case, ≤5 words.
- No ticket segment — PSL tracks work via GitHub issues, referenced as `Closes #N` in the PR body, not the branch name.

### Examples

```
feat/activities-engine
fix/token-refresh-loop
refactor/extract-leveling-service
chore/docker-entrypoint
```

### Anti-patterns

| Bad                              | Why                                            |
| -------------------------------- | ---------------------------------------------- |
| `activities-engine`              | missing `<type>/` prefix                        |
| `feature/add-the-whole-xp-and-leveling-system` | too long                          |
| `Feat/Activities_Engine`         | not lowercase / kebab-case                      |

## Stacked PR workflow (CLAUDE.md §9, ADR 0009)

PSL ships features as a **stack** of small PRs. Each branch is cut from the **previous branch in the stack**, not from `main`.

Canonical order:
`main` → `chore/scaffold` → `chore/tooling` → `feat/db-core` → `feat/auth-models` → `feat/auth-endpoints` → `feat/stats` → `feat/activities-models` → `feat/activities-engine` → `feat/admin` → `feat/tests`.

```bash
# Cut a child branch from its parent (NOT main)
git checkout feat/db-core
git pull
git checkout -b feat/auth-models      # base = feat/db-core
# work…
git push -u origin feat/auth-models
gh pr create --base feat/db-core ...  # PR target = parent branch
```

Rules:

- Child PR's **base** is the parent branch, not `main`.
- Each PR ≤500 LOC of insertions excluding `uv.lock`. Verify:
  ```bash
  git diff <base>..<head> --stat -- . ":(exclude)uv.lock" | tail -1
  ```
  Split into multiple stacked PRs if larger.
- Order merges parent→child.
- **Updating the stack without force-push**: add new commits at the source branch where the file lives, then cherry-pick onto each downstream branch in order. Resolve conflicts by hand. Avoid `git rebase --onto` chains unless rewriting a wrong commit (CLAUDE.md §9).

## Push / remote notes

- `gh` is authed as a repo collaborator. SSH push uses the repo's configured host alias / SSH key (see CLAUDE.md §9, §18).
- If `gh pr create` returns "must be a collaborator", re-check `gh auth status`.

## Verification

- Branch name matches `^(feat|fix|refactor|chore|docs|test|ci)/[a-z0-9][a-z0-9-]*$`.
- For stacked PRs, `gh pr view` shows the correct `baseRefName` (parent branch, not `main`).
