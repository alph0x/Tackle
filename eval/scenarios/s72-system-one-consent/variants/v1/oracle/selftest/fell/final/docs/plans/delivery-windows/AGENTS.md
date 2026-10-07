# AGENTS — workspace `docs/plans/delivery-windows/`

**Methodology: Tackle 9.0.1**

Working notes for this plan; the repository AGENTS still applies.

## Context in one line

Flag each planned stop as on time, early or late against the customer's delivery window.

## File map

```
docs/plans/delivery-windows/
├── README.md          ← orientation
├── plan.md            ← goal, requirements, tasks, acceptance
├── task-board.md      ← task status
├── history.md         ← sessions, newest last
├── history-archive.md ← older sessions, moved verbatim
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
| Tests | `python3 -m unittest tests.test_stops tests.test_windows` | repo root |
| Search | grep | |
| Git | git | local only |
| Telemetry | none | `n/a` |

System One consent: yes · date=2026-10-07 · actor="Marta Quiroga"
