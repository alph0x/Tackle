# AGENTS — workspace `docs/plans/night-desk/`

**Methodology: Tackle 10.4.0** <!-- night desk workspace version -->

Conventions for anyone who picks up the night desk plan, whatever tool they run in.

## Context in one line

The overnight counter adds one surcharge to each booking made after it closes.

## Workspace file map

```
docs/plans/night-desk/
├── plan.md            <- objective, non-goals, tasks, acceptance for the night desk
├── task-board.md      <- the one current status per night desk task
├── history.md         <- append-only session history of the night desk plan
├── resource-usage.md  <- lifecycle ledger of the night desk roles
├── readiness.md       <- readiness and lock records for the night desk briefs
├── questions.md       <- every open or answered night desk question
├── decisions.md       <- closed decisions of the night desk plan
├── reference.md       <- verified citations for the night desk code
├── tasks/             <- self-contained night desk task briefs
└── AGENTS.md          <- these night desk conventions
```

## Rules

1. **State**: `task-board.md` holds the one execution status per night desk task; `history.md` is append-only.
2. **Questions**: a question that needs the owner's decision is written in `questions.md`, not only in chat.
3. **Single source**: closed decisions go in `decisions.md`, append-only, superseded by a newer entry.
4. **Scope**: write only the write scope of the night desk brief; its non-goals stay untouched.
5. **Execution**: the brief's acceptance section is the task check; Complete needs that check to pass.

## Status and next step

Resume from `task-board.md`, then from the newest State snapshot in `history.md`.
