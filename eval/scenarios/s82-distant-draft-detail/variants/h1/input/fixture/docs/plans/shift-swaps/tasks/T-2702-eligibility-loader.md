# Task T-2702 — Eligibility loader

> **Self-contained briefing.** A new worker must be able to implement this Task from this
> file alone. Links provide optional depth; explicitly named inputs are the only additional prerequisites.

## Purpose and scope

- **Depends on**: T-2701 (`SwapRequest`).
- **Traces to**: plan.md §3.
- **Write scope**: `src/swaps/eligibility.py`; `tests/test_eligibility.py`; this workspace's board, history, resource usage and `reports/T-2702-report.md`.
- **Autonomy**: L2.
- **Effort**: low
- **Goal**: Load the eligibility file into an `EligibilityTable`.
- **Non-goals**: matching a request.
- **Inputs**:
  - `src/swaps/model.py:7 — "class SwapRequest"` — the record this task reads.

## Contract and cases

### Interface and invariants

- **Consumes**: named inputs, each with its source
  - `SwapRequest` from T-2701
- **Produces**: named outputs
  - `EligibilityTable` — shift roles with their eligible colleagues, read from `config/eligibility.txt`
