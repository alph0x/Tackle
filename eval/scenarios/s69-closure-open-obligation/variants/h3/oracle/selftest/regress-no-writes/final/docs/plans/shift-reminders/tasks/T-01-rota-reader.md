<a id="task-t-01--rota-reader"></a>
# Task T-01 — Rota reader

> Self-contained: work from this file and its named inputs.

## Purpose and scope

- **Depends on**: none.
- **Traces to**: R01 (`plan.md` §2).
- **Write scope**: `reminders/shifts.py`, `tests/test_shifts.py`, `docs/plans/shift-reminders/reports/T-01-report.md`.
- **Autonomy**: L2
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Procedure revision**: Tackle 9.0.1 RUN card.
- **Inputs**: `tests/fixtures/shifts.csv`; the agreed sample `tests/fixtures/expected-reminders.txt` (D-02).
- **Goal**: `read_shifts(path)` returns the shifts in rota order and refuses a rota missing a column the reminder uses.
- **Non-goals**: no change to the sample or the rota columns.

## Contract and cases

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | the fixture rota | as in the goal | `tests/test_shifts.py` |
| invalid | a rota without `start` | `ValueError` naming the column | manual, recorded |

## Acceptance and recovery <!-- SEALED: D-02 -->

```sh
python3 -m unittest tests.test_shifts -q
```

- **Task check**: exit 0.
- **Recovery**: within the budget; then stop and report.
