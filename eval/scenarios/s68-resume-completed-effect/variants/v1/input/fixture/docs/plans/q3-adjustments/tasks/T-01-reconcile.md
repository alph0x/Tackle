<a id="task-t-01--reconcile-q3-statements"></a>
# Task T-01 — Reconcile Q3 statements

> Self-contained: work from this file and its named inputs.

## Purpose and scope

- **Depends on**: none.
- **Traces to**: R01 (`plan.md` §2).
- **Write scope**: `docs/plans/q3-adjustments/reports/T-01-report.md`.
- **Autonomy**: L2
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Procedure revision**: Tackle 9.0.1 RUN card.
- **Inputs**: the Q3 bank statements (treasurer's folder) and `data/accounts.csv`.
- **Goal**: a reconciliation sheet in the report naming every difference between statements and expected levies.
- **Non-goals**: no postings.

## Contract and cases

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | four accounts | one line per account, differences named | treasurer review |

## Acceptance and recovery <!-- SEALED: D-02 -->

Treasurer review of the sheet, recorded in the report with the date.

- **Recovery**: within the budget; then stop and report.
