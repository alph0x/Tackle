<a id="task-t-01--loan-reader"></a>
# Task T-01 — Loan reader

> Self-contained: work from this file and its named inputs.

## Purpose and scope

- **Depends on**: none.
- **Traces to**: R01 (`plan.md` §2).
- **Write scope**: `notices/loans.py`, `tests/test_loans.py`, `docs/plans/overdue-notices/reports/T-01-report.md`.
- **Autonomy**: L2
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Procedure revision**: Tackle 9.0.1 RUN card.
- **Inputs**: `tests/fixtures/loans.json`; D-03.
- **Goal**: `read_loans(path)` parses the export with ISO due dates; `overdue_by_patron(loans, today)` groups the loans due before `today` by `card_no`.
- **Non-goals**: no change to the export's shape.

## Contract and cases

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | the fixture loans, 2026-09-01 | two cards, HL-20817 with two loans | `tests/test_loans.py` |
| boundary | a loan due on the run date | not overdue (D-03) | manual, recorded |

## Acceptance and recovery

```sh
python3 -m unittest tests.test_loans -q
```

- **Task check**: exit 0.
- **Recovery**: within the budget; then stop and report.
