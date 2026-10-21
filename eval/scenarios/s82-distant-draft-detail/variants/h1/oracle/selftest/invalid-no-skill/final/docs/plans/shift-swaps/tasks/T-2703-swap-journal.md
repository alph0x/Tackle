# Task T-2703 — Swap journal

> **Self-contained briefing.** A new worker must be able to implement this Task from this
> file alone. Links provide optional depth; explicitly named inputs are the only additional prerequisites.

## Purpose and scope

- **Depends on**: T-2701 (`SwapRequest`).
- **Traces to**: plan.md §3.
- **Write scope**: `src/swaps/journal.py`; `tests/test_journal.py`; this workspace's board, history, resource usage and `reports/T-2703-report.md`.
- **Autonomy**: L2.
- **Effort**: low
- **Goal**: Append one journal line per swap decision.
- **Non-goals**: reading the journal back.
- **Inputs**:
  - `src/swaps/model.py:7 — "class SwapRequest"` — the record this task reads.

## Contract and cases

### Interface and invariants

- **Consumes**: named inputs, each with its source
  - `SwapRequest` from T-2701
- **Produces**: named outputs
  - `SwapJournal` — append-only journal of swap decisions

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
