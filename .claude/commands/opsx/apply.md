---
name: "OPSX: Apply"
description: Implement tasks from an OpenSpec change (Experimental)
category: Workflow
tags: [workflow, artifacts, experimental]
---

Implement tasks from an OpenSpec change.

**Store selection:** If the user names a store (a store is a standalone OpenSpec repo registered on this machine) or the work lives in one, run `openspec store list --json` to discover registered store ids, then pass `--store <id>` on the commands that read or write specs and changes (`new change`, `status`, `instructions`, `list`, `show`, `validate`, `archive`, `doctor`, `context`). Other commands do not take the flag. Hints printed by commands already carry the flag; keep it on follow-ups. Without a store, commands act on the nearest local `openspec/` root.

**Input**: Optionally specify a change name (e.g., `/opsx:apply add-auth`). If omitted, check if it can be inferred from conversation context. If vague or ambiguous you MUST prompt for available changes.

**Steps**

1. **Select the change**

   If a name is provided, use it. Otherwise:
   - Infer from conversation context if the user mentioned a change
   - Auto-select if only one active change exists
   - If ambiguous, run `openspec list --json` to get available changes and use the **AskUserQuestion tool** to let the user select

   Always announce: "Using change: <name>" and how to override (e.g., `/opsx:apply <other>`).

2. **Check status to understand the schema**
   ```bash
   openspec status --change "<name>" --json
   ```
   Parse the JSON to understand:
   - `schemaName`: The workflow being used (e.g., "spec-driven")
   - `planningHome`, `changeRoot`, and `actionContext`: planning scope and edit constraints
   - Which artifact contains the tasks (typically "tasks" for spec-driven, check status for others)

3. **Get apply instructions**

   ```bash
   openspec instructions apply --change "<name>" --json
   ```

   This returns:
   - `contextFiles`: artifact ID -> array of concrete file paths (varies by schema)
   - Progress (total, complete, remaining)
   - Task list with status
   - Dynamic instruction based on current state

   **Handle states:**
   - If `state: "blocked"` (missing artifacts): show message, suggest using `/opsx:continue`
   - If `state: "all_done"`: congratulate, suggest archive
   - Otherwise: proceed to implementation

4. **Read context files**

   Read every file path listed under `contextFiles` from the apply instructions output.
   The files depend on the schema being used:
   - **spec-driven**: proposal, specs, design, tasks
   - Other schemas: follow the contextFiles from CLI output

5. **Show current progress**

   Display:
   - Schema being used
   - Progress: "N/M tasks complete"
   - Remaining tasks overview
   - Dynamic instruction from CLI

6. **Implement tasks (loop until done or blocked)**

   For each pending task:
   - Show which task is being worked on
   - Make the code changes required
   - Keep changes minimal and focused
   - Mark task complete in the tasks file: `- [ ]` → `- [x]`
   - Continue to next task

   **Pause if:**
   - Task is unclear → ask for clarification
   - Implementation reveals a design issue → suggest updating artifacts
   - Error or blocker encountered → report and wait for guidance
   - User interrupts

7. **On completion or pause, show status**

   Display:
   - Tasks completed this session
   - Overall progress: "N/M tasks complete"
   - If all done: proceed to step 8 (open PR + drive the review to green)
   - If paused: explain why and wait for guidance

8. **Open the PR and drive the Claude review to green** (only when all tasks are complete)

   Once every task is `- [x]`, the change is not "done" until it is on a PR whose Claude review has no blockers or majors left.

   1. **Ensure a feature branch.** If work is on `main`, stop — it should already be on a `<type>/<kebab>` branch (see `git-branch`). Commit any remaining task work granularly (Conventional Commits, `git-commit`).
   2. **Open the PR** (if not already open) using the `pull-request-description` skill — PSL `pull_request_template.md`, base `main` (or the parent branch when stacked), assignee `DanyloSus`. Opening it fires the **Claude PR Review** workflow.
   3. **Run the review-fix loop** via the `address-pr-review` skill: each round derive the open findings from a **fresh, non-deduped `/pr-review`** on the current diff (plus any new human review comments) — not from the deduped CI `claude[bot]` comment, which suppresses still-open findings — **auto-fix Blockers (`B*`) and Majors (`M*`) only**, commit granularly, push, and repeat until a fresh `/pr-review` shows **0 blockers + 0 majors** or the 3-round cap.
   4. **Respect the spec.** If a review finding contradicts this change's proposal/spec (the source of truth), do **not** blindly fix it — pause, surface the conflict, and offer to update the OpenSpec artifact instead (same guardrail as step 6's "implementation reveals a design issue"). Never auto-edit an AGENTS §4a protected file — flag it for sign-off.
   5. **Leave nits.** `N*` findings are listed for the author, not auto-fixed.

   Only after the review is clean (or the cap is hit and reported) suggest `/opsx:archive`.

**Output During Implementation**

```
## Implementing: <change-name> (schema: <schema-name>)

Working on task 3/7: <task description>
[...implementation happening...]
✓ Task complete

Working on task 4/7: <task description>
[...implementation happening...]
✓ Task complete
```

**Output On Completion**

```
## Implementation Complete

**Change:** <change-name>
**Schema:** <schema-name>
**Progress:** 7/7 tasks complete ✓

### Completed This Session
- [x] Task 1
- [x] Task 2
...

### PR Review
**PR:** #<n> — <title>
**Verdict:** clean (0 blockers, 0 majors) after <k> fix round(s)
**Nits left for you:** file-N1 (typing), …

All tasks complete and the PR review is green! You can archive this change with `/opsx:archive`.
```

**Output On Pause (Issue Encountered)**

```
## Implementation Paused

**Change:** <change-name>
**Schema:** <schema-name>
**Progress:** 4/7 tasks complete

### Issue Encountered
<description of the issue>

**Options:**
1. <option 1>
2. <option 2>
3. Other approach

What would you like to do?
```

**Guardrails**
- Keep going through tasks until done or blocked
- Always read context files before starting (from the apply instructions output)
- If task is ambiguous, pause and ask before implementing
- If implementation reveals issues, pause and suggest artifact updates
- Keep code changes minimal and scoped to each task
- Update task checkbox immediately after completing each task
- Pause on errors, blockers, or unclear requirements - don't guess
- Use contextFiles from CLI output, don't assume specific file names
- Not "done" at last task: after all tasks pass, open the PR and drive the Claude review to green (step 8) before suggesting archive — auto-fix blockers/majors only, leave nits, and pause on any finding that fights the spec

**Fluid Workflow Integration**

This skill supports the "actions on a change" model:

- **Can be invoked anytime**: Before all artifacts are done (if tasks exist), after partial implementation, interleaved with other actions
- **Allows artifact updates**: If implementation reveals design issues, suggest updating artifacts - not phase-locked, work fluidly
