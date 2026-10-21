# Task T-0906 — Weekly digest

> **Self-contained briefing.** A new worker must be able to implement this Task from this
> file alone. Links provide optional depth; explicitly named inputs are the only additional prerequisites.

## Purpose and scope

- **Depends on**: T-0904 (`route`).
- **Traces to**: plan.md §3.
- **Write scope**: `src/triage/digest.py`; `tests/test_digest.py`; this workspace's board, history, resource usage and `reports/T-0906-report.md`.
- **Autonomy**: L2.
- **Detail**: full
- **Effort**: low
- **Goal**: Summarize one week of routing decisions.
- **Non-goals**: sending the digest.
- **Inputs**: none beyond the dependencies.

## Contract and cases

### Interface and invariants

- **Consumes**: named inputs, each with its source
  - `route` from T-0904
- **Produces**: named outputs
  - `digest` — weekly summary text
