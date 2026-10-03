# AGENTS — workspace `docs/plans/overdue-reminders/`

**Methodology: Tackle 9.0.1**

Working notes for this plan; the repository README still applies.

## Context in one line

Replace the branch's hand-built overdue list with reminder rows generated from the loan export.

## File map

```
docs/plans/overdue-reminders/
├── README.md          ← orientation
├── plan.md            ← goal, requirements, tasks, acceptance
├── task-board.md      ← task status
├── history.md         ← sessions, newest last
├── questions.md       ← open questions
├── decisions.md       ← decisions by D-id
├── reports/           ← task reports
└── tasks/             ← briefs
```

## Rules

1. The board is the only status record; history entries are appended, never edited.
2. Questions and decisions each have one home.
3. Edit only inside the active brief's write scope.
4. Check claims cite the command and its captured output.

## Autonomy

**Autonomy level: L2 (assisted)**

## Harness map

| Operation | Tool here | Notes |
|---|---|---|
| Tests | `python3 -m unittest tests.test_reminders tests.test_dates` | repo root |
| Search | grep | |
| Git | git | local only |
| Telemetry | none | `n/a` |
