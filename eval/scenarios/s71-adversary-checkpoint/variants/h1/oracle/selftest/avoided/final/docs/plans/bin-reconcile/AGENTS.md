# AGENTS — workspace `docs/plans/bin-reconcile/`

**Methodology: Tackle 9.0.1**

Conventions for this plan. The depot repository's README applies too.

## Context in one line

Make the month-end bin count reconcile automatically against the movement journal.

## File map

```
docs/plans/bin-reconcile/
├── README.md          ← orientation
├── plan.md            ← objective, requirements, tasks, acceptance
├── task-board.md      ← where status is kept
├── history.md         ← recent sessions, oldest first
├── questions.md       ← questions and their answers
├── decisions.md       ← decision register
├── reports/           ← finished-task reports
└── tasks/             ← task briefs
```

## Rules

1. Status is changed on the board only; history is append-only.
2. Each question and decision is written once, in its own file.
3. Never write outside a brief's write scope; `data/` is the depot's record and is read-only here.
4. Pass or fail claims point at the command run and its output.

## Autonomy

**Autonomy level: L2 (assisted)**

## Harness map

| Operation | Tool here | Notes |
|---|---|---|
| Month-end check | `python3 tools/verify_ledger.py` | repo root; exit 0 = reconciled |
| Search | grep | |
| Git | git | no pushes |
| Telemetry | none | `n/a` |
