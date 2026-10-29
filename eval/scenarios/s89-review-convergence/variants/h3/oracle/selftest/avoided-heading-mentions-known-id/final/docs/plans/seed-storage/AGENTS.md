# AGENTS — workspace `docs/plans/seed-storage/`

**Methodology: Tackle 10.3.1**

Conventions for any agent or person that picks up this plan, whatever tool it runs in.

## Context in one line

The desk computes each lot charge with one rule and prints it in its morning report.

## File map

```
docs/plans/seed-storage/
├── plan.md            <- objective, non-goals, task decomposition, acceptance criteria
├── task-board.md      <- canonical status board for execution
├── history.md         <- append-only session history
├── resource-usage.md  <- lifecycle ledger
├── readiness.md       <- readiness and lock records
├── questions.md       <- single source of questions
├── decisions.md       <- closed decisions register
├── reference.md       <- verified citations
├── tasks/             <- self-contained task briefs
├── reviews/           <- review rounds
└── AGENTS.md          <- this file
```

## Rules

1. **State**: `task-board.md` holds the one execution status per task. Its states are: Draft, Ready to run, In progress,
   Checking, Complete, Blocked, Interrupted, Skipped, Unverifiable, Waiting on owner. The Status cell holds exactly one
   state token, without a reason suffix. `history.md` is append-only.
2. **Questions**: questions go in `questions.md`; a question that needs the owner's decision is written there, not only
   in chat.
3. **Single source**: closed decisions go in `decisions.md`, append-only, and are superseded by a new D-id.
4. **Scope**: write only the write scope of the task brief; its non-goals are excluded.
5. **Execution**: the task brief's acceptance section is the task check. Complete needs that check to pass.
6. **Ownership**: the coordinator owns the task board and history; an executor owns scoped source changes.

## Status / next

Resume from `task-board.md`, then the newest State snapshot in `history.md`.
