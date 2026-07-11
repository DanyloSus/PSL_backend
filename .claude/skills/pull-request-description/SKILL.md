---
name: pull-request-description
description: Generate a PR from the branch diff using the PSL pull_request_template.md. Title ≤70 chars, stacking-aware (base may be a parent branch). Use when asked for a PR, pull request, or PR description.
---

# Pull Request Description (PSL backend)

## Inputs (all optional)

| Arg        | Default                       | Notes                                              |
| ---------- | ----------------------------- | -------------------------------------------------- |
| `base`     | `main`                        | Stacked PR? Pass the parent branch instead.        |
| `assignee` | `@me`                         | Authenticated user; override if asked.             |
| `reviewer` | none                          | Pass GitHub handles only if the user supplies them.|
| `label`    | none                          | Must exist in the repo.                            |

## Workflow

1. **Resolve base.** Default `main`. If this branch was cut from another branch in the stack, pass that parent (see `git-branch` skill).
2. **Branch state:**
   ```bash
   git status
   git log <base>..HEAD --oneline
   git diff <base>...HEAD --stat
   ```
3. **Check PR size budget:** insertions ≤500 LOC excluding `uv.lock` (CLAUDE.md §9):
   ```bash
   git diff <base>..HEAD --stat -- . ":(exclude)uv.lock" | tail -1
   ```
   If over, warn the user and suggest splitting into a stacked PR.
4. **Analyze ALL commits**, not just the latest.
5. **Title** ≤70 chars, imperative, Conventional-Commit-style prefix (`feat(activities-engine): ...`).
6. **Body** — exact structure of `.github/pull_request_template.md`: the four headings `## What was done`, `## Related issue`, `## How to test`, `## Additional notes`.
7. **Push branch if needed:**
   ```bash
   git push -u origin HEAD
   ```
8. **Create PR:**
   ```bash
   gh pr create \
     --base "<base>" \
     --title "<title>" \
     --assignee @me \
     --body "$(cat <<'EOF'
   ## What was done

   - …

   ## Related issue

   Closes #<num>

   ## How to test

   - …

   ## Additional notes

   -
   EOF
   )"
   ```
   The default assignee may differ from the authenticated user — confirm with the user if unsure, then `gh pr edit <N> --add-assignee <handle>`.

## Stacked PRs

If this branch was cut from a parent feature branch (not `main`), pass `--base <parent-branch>`. After the parent merges, switch the base:

```bash
gh pr edit --base main
```

PSL avoids force-push rebases on the stack — prefer cherry-picking. See `git-branch` skill.

## Body rules

- **What was done** bullets describe the WHY, not just the what.
- **How to test** = real, scenario-specific steps (e.g. `uv run pytest -q app/tests/test_activities.py`, or curl against `/api/v1/...`).
- **Related issue** uses `Closes #N` when an issue exists; otherwise leave `Closes #` blank.
- **Additional notes** holds trade-offs, follow-ups, out-of-scope items, migration notes.

## Critical

- `gh` is authed as a repo collaborator. If `gh pr create` says "must be a collaborator", check `gh auth status` (CLAUDE.md §18).
- No `Co-Authored-By` / Claude / Anthropic / 🤖 / "Generated with" in the PR body (CLAUDE.md §9). The commit-msg hook guards commits; keep the PR body clean too.

## Checklist

- [ ] Title ≤70 chars, conventional prefix
- [ ] Base correct (`main` OR parent branch for a stacked PR)
- [ ] Insertions ≤500 LOC excluding `uv.lock`
- [ ] All four template headings present, in order
- [ ] "How to test" actionable (real commands / endpoints)
- [ ] Issue number filled or `Closes #` left blank
- [ ] Assignee set (`@me` or the handle the user gave)
- [ ] No AI attribution anywhere
