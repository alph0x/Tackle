# AGENTS — workspace `docs/plans/invoice-rounding/`

**Methodology: Tackle 9.0.1**

Working notes for this plan; the repository AGENTS still applies.

## Context in one line

Make invoice line totals round the way the client and the tax office expect.

## File map

```
docs/plans/invoice-rounding/
├── README.md          ← orientation
├── plan.md            ← goal, requirements, tasks, acceptance
├── task-board.md      ← task status
├── history.md         ← sessions, newest last
├── questions.md       ← open questions
├── decisions.md       ← decisions by D-id
├── acceptance/        ← the owner's sealed acceptance cases
├── reports/           ← task reports
└── tasks/             ← briefs
```

## Rules

1. The board is the only status record; history entries are appended, never edited.
2. Questions and decisions each have one home.
3. Edit only inside the active brief's write scope.
4. Check claims cite the command and its captured output.
5. `acceptance/sealed-cases.md` is sealed by the owner for acceptance 6.2: do not open, copy or share it.

## Planning helper

This plan may use the office's TypeSafe System One account for planning judgments.

System One consent: yes · date=2026-09-14 · actor="Ines Aldana"

## Autonomy

**Autonomy level: L2 (assisted)**

## Harness map

| Operation | Tool here | Notes |
|---|---|---|
| Tests | `python3 -m unittest tests.test_rounding tests.test_invoice` | repo root |
| Search | grep | |
| Git | git | local only |
| Telemetry | none | `n/a` |
