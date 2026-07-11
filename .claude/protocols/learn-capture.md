# Protocol: Learn-Capture

> End-of-task memory step. Distill what a task taught into durable memory so the next
> session starts ahead instead of re-deriving it. The "Reflect" phase of `/sprint`
> (FACADE §K) and a standalone step otherwise.

## When to run

- At the end of any task that surfaced a **non-obvious, durable** fact — a gotcha, a
  constraint, a user-endorsed approach, a hard-won reference.
- Automatically as the last phase of `/sprint`.

Do **not** run it as ceremony. If nothing non-obvious was learned, say so and write
nothing.

## Where a lesson lands

Pick the narrowest home that fits. Prefer editing an existing file over adding one.

| Target                     | Path                                   | Use for                                                        |
| -------------------------- | -------------------------------------- | -------------------------------------------------------------- |
| Global memory              | session memory dir (`…/memory/*.md` + `MEMORY.md` index) | cross-session facts: user prefs, project constraints, gotchas, references |
| Agent memory               | `.claude/agent-memory/<agent>/`        | facts scoped to one agent's job (`test-writer`, `docs-keeper`) |
| `CLAUDE.md` / `AGENTS.md`  | project root                           | a **stable, teachable convention** every contributor/AI must follow |
| `.claude/BOOTSTRAP.md`     | (tier 0)                               | a critical rule that must be always-loaded — keep file <200 lines |
| Rule or skill              | `.claude/rules/` · `.claude/skills/`   | an enforceable pattern or reusable know-how (via `self-expansion`) |
| ADR                        | `docs/adrs/` (`/adr`)                  | an **architecture-shaping, hard-to-reverse** decision + its *why* |

### Which one?

- **CLAUDE.md / AGENTS.md** — the lesson is a convention that changes how code is written
  here and isn't obvious from the code (e.g. "pin `fastapi-limiter==0.1.6`"). One-off task
  facts do not belong here.
- **ADR** — you made or confirmed a decision that shapes the architecture and would be
  expensive to reverse (a boundary, a storage choice, an auth model). Record the *why* and
  the alternatives. Skip for reversible detail. The `adr_reminder` hook nudges on shaping
  commits.
- **Rule / skill** — the lesson generalizes to future tasks and can be enforced or reused;
  route through `self-expansion` (propose → approve → register).
- **Memory** — a durable fact that isn't a convention, decision, or reusable pattern
  (a gotcha, a preference, a reference URL/ticket).

## What to save

- **Gotchas** — surprising behavior that cost time (testcontainers docker-socket quirk,
  cache bypass on raw SQL, `SameSite` cross-site cookie setup). Symptom + fix.
- **Confirmed approaches / feedback** — a decision the user endorsed, with the *why*.
- **Project constraints** — non-derivable limits; convert relative dates to absolute.
- **References** — a URL/ticket/dashboard you had to hunt for.

## What NOT to save

- Anything the repo already records: code structure, existing CLAUDE.md/AGENTS.md rules,
  git history, a fix already committed.
- Facts that only matter to the current conversation.
- Restated documentation — if asked to "remember" a documented fact, capture only what was
  *non-obvious* about it.
- Never save AI attribution or conversation transcript.

## Flow

1. Review the task: what did we learn that isn't already written down?
2. For each durable fact, pick the narrowest target above.
3. **Dedup first** — scan existing memory/docs for a file that already covers it; update
   it rather than adding a duplicate, and delete memories that turned out wrong.
4. Write with the correct frontmatter; for global memory add a one-line `MEMORY.md`
   pointer and link related notes with `[[name]]`.
5. Report what was written / updated / skipped in one short list.
