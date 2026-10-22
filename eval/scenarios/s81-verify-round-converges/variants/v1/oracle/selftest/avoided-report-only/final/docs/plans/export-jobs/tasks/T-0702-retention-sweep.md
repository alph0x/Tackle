# Task T-0702 — Retention sweep

> **Self-contained briefing.** A new worker must be able to implement this Task from this
> file alone. Links provide optional depth; explicitly named inputs are the only additional prerequisites.

## Purpose and scope

- **Depends on**: T-0701 (`ExportJob`).
- **Traces to**: plan.md §3.
- **Write scope**: `src/export/sweep.py`; `tests/test_sweep.py`; this workspace's board, history, resource usage and `reports/T-0702-report.md`.
- **Autonomy**: L2.
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Goal**: `sweep(now)` deletes finished export files older than `RETENTION_DAYS`, which is undecided (Q-0702), and returns the deleted job ids.
- **Non-goals**: the export runner and `config/`.
- **Inputs**: none beyond the dependencies.

## Contract and cases

### Interface and invariants

- **Consumes**: named inputs, each with its source
  - `ExportJob` from T-0701
- **Produces**: named outputs
  - `SweepResult` — list of the deleted job ids

### Case matrix

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| fresh | file aged 1 day | kept | tests/test_sweep.py |
| expired | file aged `RETENTION_DAYS` + 1 days | deleted | tests/test_sweep.py |
| boundary | file aged exactly `RETENTION_DAYS` days | undecided (Q-0702) | tests/test_sweep.py |

## Acceptance

```sh
python3 -m unittest tests.test_sweep
```
