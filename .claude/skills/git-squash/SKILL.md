---
name: git-squash
description: Squash all commits on the current branch into one versus its base. Preserves issue refs, asks confirmation before reset. Use when asked to squash or compress commits.
disable-model-invocation: true
---

# Git Squash (PSL backend)

## When to use

- Before merging a feature branch (keep history clean).
- When a branch has many "wip" / "fix typo" commits.

> Note: PSL's stacked-PR workflow (CLAUDE.md §9) prefers cherry-picking new commits onto downstream branches over rebasing. Squash only the branch you're on, against its own base — never rewrite a parent that has open children without rebasing them first.

## Workflow

1. Ensure branch is clean: `git status`.
2. Determine the base. For a stacked branch this is the **parent branch**, not `main`. For a top-level branch it's `main`.
3. List the commits that will be squashed and show the user:
   ```bash
   git fetch origin
   git log --oneline <base>..HEAD
   ```
4. Generate a combined Conventional Commit message covering the work.
5. **Ask user confirmation.**
6. Soft-reset to the merge base:
   ```bash
   git reset --soft $(git merge-base HEAD <base>)
   ```
7. Commit (hooks run normally — no `--no-verify`):
   ```bash
   git commit -m "<combined message>"
   ```
8. Force-push with lease:
   ```bash
   git push --force-with-lease
   ```

## Safety rules

- NEVER squash on `main` or a shared branch without explicit approval.
- ALWAYS `--force-with-lease`, not `--force`.
- If unsure, `git branch backup/<name>` first.
- If a parent branch has open stacked children, rebase them after the squash.
- No AI attribution in the combined message (commit-msg hook blocks it).

## Combined message pattern

```
feat(activities-engine): add XP/leveling engine

Squashes:
- feat(activities-engine): add LevelingService
- feat(activities-engine): apply per-stat effect deltas
- test: cover level-from-xp boundaries
- fix(activities-engine): floor stat XP at 0

Closes #42
```

## What to avoid

| Don't                                | Do                            |
| ------------------------------------ | ----------------------------- |
| Squash without listing commits first | Show the user first           |
| `git push --force`                   | `git push --force-with-lease` |
| Squash on `main`                     | Only on feature branches      |
| Skip confirmation                    | Always confirm before reset   |
| Squash a parent with open children   | Rebase children afterward     |
