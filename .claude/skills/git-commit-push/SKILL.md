---
name: git-commit-push
description: Stage, commit, and push for PSL backend. Splits unrelated changes into logically-grouped Conventional Commits before a single push. Use when asked to commit and push, or to split changes into logical commits.
disable-model-invocation: true
---

# Git Commit + Push (PSL backend)

## Critical rules

- **Never `--no-verify`.** Pre-commit runs `ruff check` + `ruff format` + `mypy`; commit-msg runs the block-claude-refs hook. Fix the root cause and re-stage.
- **Never `--force` on a shared branch.** Use `--force-with-lease` only when rewriting your own unmerged commits and the user confirmed.
- **One logical concern per commit.** Split a feature change from an unrelated config tweak or dep bump.
- **Conventional Commits format** — see the `git-commit` skill for type/scope/subject rules.
- **No AI attribution.** No `Co-Authored-By`, no "Generated with Claude Code", no Claude/Anthropic refs, no 🤖 — the commit-msg hook rejects them (CLAUDE.md §9, §18).

## Workflow

### Single-concern path (default)

1. `git status` and `git diff` to see all changes.
2. If everything is one concern → load `git-commit` → stage relevant files → commit.
3. `git push` (`-u origin <branch>` on first push).

### Multi-concern path (split commits)

Use when `git diff` shows changes across unrelated areas.

1. **Inventory.** `git status` + `git diff --stat`. List distinct concerns.
2. **Plan.** State the planned commit sequence: each gets a type+scope and an exact file set.
3. **Stage by concern.** For each, in order:
   - `git add <files-for-this-concern>` (specific files — never `git add -A`).
   - `git diff --staged` to confirm only that concern is staged.
   - Load `git-commit` → write message → `git commit`.
4. **Verify.** `git status` clean; `git log --oneline origin/<branch>..HEAD` shows the new commits.
5. **Push once.** `git push` (or `-u origin <branch>`).

### Splitting heuristics

Group changes sharing ONE of: same concern (feature/fix), same layer (`routers/`, `services/`, `repositories/`, `models/`), same type (all docs / all deps / all tests), or same commit scope.

Do not split a single concern across files just to shrink commits.

### PSL-specific

- A migration belongs with the model change that motivates it, OR as its own `feat(migrations)` commit — never bundled with unrelated work.
- Dependency changes (`pyproject.toml` + `uv.lock`) go in their own `chore(deps)` commit.
- Keep each PR's total insertions ≤500 LOC excluding `uv.lock` (CLAUDE.md §9) — if a push would blow the budget, that's a signal to split into a stacked branch, not just split commits.

### Refusal cases

- A single file mixes two concerns → ask whether to split via `git add -p` or keep as one.
- Pre-commit hook fails → fix the ruff/mypy/hook failure, never `--no-verify`.
- Push rejected (non-fast-forward) → `git pull --rebase`, resolve, re-push. Never `--force` without explicit approval.

## Checklist

- [ ] Working tree inventoried (`git status` + `git diff`)
- [ ] Each unrelated concern committed separately
- [ ] Every message follows Conventional Commits (`git-commit` skill)
- [ ] No `--no-verify`, no `--force` without approval
- [ ] No AI attribution in any commit
- [ ] `git push` succeeds; `origin/<branch>..HEAD` empty afterwards
