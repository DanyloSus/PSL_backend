---
name: worktree-task
description: Spin up a git worktree from a base branch, implement a described task, run ruff/mypy/pytest, commit logically, push, and open a PR back into the base. Composes git-branch + git-commit-push + pull-request-description. Use for isolated worktree work in PSL backend.
disable-model-invocation: true
---

# Worktree Task (PSL backend)

## Invocation

```
/worktree-task <base-branch> <task-description>
```

| Arg                  | Description                          | Example                                   |
| -------------------- | ------------------------------------ | ----------------------------------------- |
| `<base-branch>`      | Branch to fork from AND PR target    | `main`, `feat/db-core`                     |
| `<task-description>` | Freeform task text                   | `add unit tests for LevelingService`       |

## Critical rules

- Worktrees live **outside** the main repo dir: `../PSL_backend-worktrees/<flattened-branch-name>` (`/` → `-`). Never nest inside the primary working tree.
- Never `--no-verify`. Pre-commit runs ruff + mypy; commit-msg blocks Claude refs. Fix the root cause.
- Never `--force` without explicit user approval.
- **No AI attribution** — no `Co-Authored-By`, no "Generated with Claude Code", no 🤖 (CLAUDE.md §9, §18).
- Branch naming: `<type>/<kebab-desc>` (`feat`/`fix`/`refactor`/`chore`/`test`). No ticket segment. See `git-branch`.
- PR base = the branch passed by the user. Supports stacking (parent branch as base).
- Assignee: `@me` (or the handle the user supplies).
- PR body MUST follow `.github/pull_request_template.md` exactly: `What was done` / `Related issue` / `How to test` / `Additional notes`.
- Keep insertions ≤500 LOC excluding `uv.lock` (CLAUDE.md §9).

## Workflow

### 1. Parse args

Extract `<base-branch>` + `<task-description>`. Derive branch type from the verb (fix/bug → `fix`, refactor/cleanup → `refactor`, tests → `test`, else `feat`).

### 2. Derive branch name

`<type>/<kebab-desc>` — lowercase, hyphenated, ≤5 words. e.g. `test/leveling-service-boundaries`.

### 3. Create worktree

Path: `../PSL_backend-worktrees/<branch-flattened>`. Use absolute paths everywhere — each Bash call resets cwd. Use `git -C <path>` and `uv --project <path>` / `uv run --project <path>` instead of `cd` chaining.

```bash
git fetch origin <base-branch>
git worktree add -b <new-branch> ../PSL_backend-worktrees/<flattened> origin/<base-branch>

# Each worktree needs its own venv
uv sync --project ../PSL_backend-worktrees/<flattened>
```

### 4. Implement

Read relevant files under `<worktree-root>/app/**` first. All project rules apply (CLAUDE.md §4–§5, §15):
- Layered: HTTP (routers) → service → repository → SQLAlchemy. No SQL in routers/services. No HTTP in repositories.
- Routers are 1-line wrappers: `return await service.<method>(...)`.
- All IO async; `async with` for sessions and Redis.
- Schemas separate from ORM models (`*Create`/`*Update`/`*Out`).
- Domain errors subclass `DomainError`; mapped by the global handler.
- snake_case; spell out local variable names.
- New model? Import it in `app/models/__init__.py` so Alembic sees it. Add a migration (`uv run alembic revision --autogenerate`), rename to `00NN_<slug>.py`, fix `revision`/`down_revision`.

### 5. Verify

```bash
WT=../PSL_backend-worktrees/<flattened>
uv run --project "$WT" ruff format .
uv run --project "$WT" ruff check .
uv run --project "$WT" mypy app
uv run --project "$WT" pytest -q
```

Tests use testcontainers Postgres+Redis, or the `TEST_DATABASE_URL`/`TEST_REDIS_URL` override against the compose stack if no docker socket (CLAUDE.md §11). Fix anything ruff `--fix` leaves behind manually.

### 6. Commit logically

Use the `git-commit-push` skill. One concern per commit, Conventional Commits with scope, GitHub issue in the footer when present:

```
feat(activities-engine): add LevelingService.threshold_for

Closes #<num>
```

Stage specific files (`git add <paths>`), never `git add -A`.

### 7. Push

```bash
git -C ../PSL_backend-worktrees/<flattened> push -u origin <new-branch>
git -C ../PSL_backend-worktrees/<flattened> log origin/<new-branch>..HEAD   # must be empty
```

### 8. Open PR

Use the `pull-request-description` skill. Body mirrors the template exactly (all four headings, in order, `-` placeholder if empty).

```bash
gh -C ../PSL_backend-worktrees/<flattened> pr create \
  --base <base-branch> \
  --title "<title ≤70 chars>" \
  --assignee @me \
  --body "$(cat <<'EOF'
## What was done

- <bullet 1>

## Related issue

Closes #<num>

## How to test

- uv run pytest -q app/tests/<file>

## Additional notes

-
EOF
)"
```

Return the PR URL.

## Anti-patterns

| Bad                                                 | Fix                                                       |
| --------------------------------------------------- | --------------------------------------------------------- |
| Worktree nested inside main repo                    | Use `../PSL_backend-worktrees/` (sibling dir)              |
| `git add -A` in worktree                            | Stage specific files per concern                          |
| Reusing the main venv                               | `uv sync --project <worktree>` (each needs its own)        |
| Skipping mypy/ruff before push                      | Run the full §5 verify block                              |
| Relative paths in Bash (cwd resets)                 | Absolute paths via `git -C` / `uv --project`               |
| PR base defaults to `main` when user said a parent  | Pass `--base <base-branch>` explicitly                    |
| PR body uses `Summary`/`Test plan`                  | Match template: `What was done`/`Related issue`/`How to test`/`Additional notes` |
| Any Claude/Anthropic footer                         | Strip it — commit-msg hook rejects it                     |

## Cleanup (optional, user-initiated)

After PR merge — see the `worktree-close` skill. Never auto-remove.

## Verification

- Branch name matches `^(feat|fix|refactor|chore|docs|test|ci)/[a-z0-9][a-z0-9-]*$`.
- `git log origin/<new-branch>..HEAD` empty after push.
- `gh pr view --json baseRefName,body` shows correct base + the four template sections.
- PR URL returned.
