---
name: worktree-close
description: Close a git worktree spawned by worktree-task and check out its branch in the main repo. Verifies clean tree + pushed commits before removal. Use when asked to close, remove, or finish a worktree.
disable-model-invocation: true
---

# Worktree Close (PSL backend)

## Invocation

```
/worktree-close [<branch-or-path>] [--force]
```

| Arg                | Description                                                                          |
| ------------------ | ------------------------------------------------------------------------------------ |
| `<branch-or-path>` | Optional. Branch name OR worktree path. Omit when invoked from inside the worktree.  |
| `--force`          | Allow removal with uncommitted/unpushed work. Requires explicit user approval.        |

## Critical rules

- **Never `--force` without explicit user approval.** Dirty/unpushed worktree → STOP, report state, ask. Don't silently discard work.
- Run `git worktree remove` from the **main repo** (`/Users/danylosushko/PSL_backend`), not from inside the worktree (it's gone after removal).
- Use absolute paths via `git -C <path>` — Bash cwd resets between calls.
- Don't delete the branch. Branch stays so the user can checkout + iterate. Deletion is separate + explicit.
- If the main repo has uncommitted changes blocking checkout → STOP and report. Never stash/discard the user's main-repo work.

## Workflow

### 1. Resolve target worktree

```bash
MAIN=/Users/danylosushko/PSL_backend
git -C "$MAIN" worktree list --porcelain
```

Resolution order:
1. `<branch-or-path>` provided → match against `worktree list --porcelain` (matches `worktree <path>` or `branch refs/heads/<name>`).
2. Else → use `pwd`; verify it sits under `../PSL_backend-worktrees/`.
3. Else → abort, ask the user.

Capture `WT_PATH` (absolute) and `WT_BRANCH`.

### 2. Verify worktree clean

```bash
git -C "$WT_PATH" status --porcelain   # must be empty
```

Non-empty → STOP, print dirty files, ask: commit / discard / `--force`.

### 3. Verify commits pushed

```bash
git -C "$WT_PATH" fetch origin "$WT_BRANCH"
AHEAD=$(git -C "$WT_PATH" rev-list --count "origin/$WT_BRANCH..HEAD")
[ "$AHEAD" -eq 0 ] || echo "$AHEAD unpushed commit(s)"
```

`AHEAD > 0` (or no upstream) → STOP. Ask: push / `--force`.

### 4. Verify main repo can checkout

```bash
git -C "$MAIN" status --porcelain     # uncommitted → STOP
git -C "$MAIN" branch --show-current  # informational
```

Main-repo tree dirty → STOP, print files, ask. Never auto-stash.

### 5. Remove the worktree

```bash
git -C "$MAIN" worktree remove "$WT_PATH"
# --force only if the user explicitly approved AND --force was passed
```

`git worktree remove` refuses dirty trees by default — that's a feature. Don't override blindly.

### 6. Checkout branch in main repo

```bash
git -C "$MAIN" checkout "$WT_BRANCH"
git -C "$MAIN" status
```

Report current branch + clean status.

### 7. (Optional, never auto) Suggest branch cleanup

After the PR is merged:

```bash
git -C "$MAIN" branch -d "$WT_BRANCH"
```

Never auto-run. User decides.

## Anti-patterns

| Bad                                                  | Fix                                                        |
| ---------------------------------------------------- | ---------------------------------------------------------- |
| `git worktree remove --force` to silence dirty error | STOP, show the dirty files, ask                            |
| `cd <worktree> && git worktree remove .`             | Removal must run from the main repo                        |
| `git stash` in main repo to allow checkout           | Never auto-stash user work — STOP and ask                  |
| `git branch -D` after removal                        | Leave the branch; deletion is user-initiated, post-merge   |
| Relative paths in Bash (cwd resets)                  | `git -C <abs-path>` everywhere                             |
| Skip the unpushed-commits check                      | Always `git rev-list --count origin/<branch>..HEAD`        |

## Verification

- `git -C $MAIN worktree list` no longer shows the closed worktree.
- `git -C $MAIN branch --show-current` returns `$WT_BRANCH`.
- Branch still exists locally.
- Main-repo working tree unchanged (no surprise stashes).
