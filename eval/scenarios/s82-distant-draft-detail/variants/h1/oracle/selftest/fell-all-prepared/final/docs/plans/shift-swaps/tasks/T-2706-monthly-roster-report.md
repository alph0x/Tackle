# Task T-2706 — Monthly roster report

> **Self-contained briefing.** A new worker must be able to implement this Task from this
> file alone. Links provide optional depth; explicitly named inputs are the only additional prerequisites.

## Purpose and scope

- **Depends on**: T-2704 (`match`).
- **Traces to**: plan.md §3.
- **Write scope**: `src/swaps/report.py`; `tests/test_report.py`; this workspace's board, history, resource usage and `reports/T-2706-report.md`.
- **Autonomy**: L2.
- **Effort**: low
- **Goal**: Summarize one month of swap decisions.
- **Non-goals**: mailing the report.
- **Inputs**: none beyond the dependencies.

## Contract and cases

### Interface and invariants

- **Consumes**: named inputs, each with its source
  - `match` from T-2704
- **Produces**: named outputs
  - `report` — monthly summary text

### Case matrix

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | a normal input | the documented result | test |
| boundary | a boundary input | the documented result | test |
| invalid | a invalid input | the documented result | test |

## Acceptance

```sh
python3 -m unittest
```
