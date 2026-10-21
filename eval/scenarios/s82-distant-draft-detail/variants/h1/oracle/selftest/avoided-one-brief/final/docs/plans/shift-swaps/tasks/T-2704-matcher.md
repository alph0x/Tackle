# Task T-2704 — Matcher

> **Self-contained briefing.** A new worker must be able to implement this Task from this
> file alone. Links provide optional depth; explicitly named inputs are the only additional prerequisites.

## Purpose and scope

- **Depends on**: T-2702 (`EligibilityTable`).
- **Traces to**: plan.md §3.
- **Write scope**: `src/swaps/matcher.py`; `tests/test_matcher.py`; this workspace's board, history, resource usage and `reports/T-2704-report.md`.
- **Autonomy**: L2.
- **Effort**: low
- **Goal**: Match a swap request to one covering colleague by the loaded eligibility.
- **Non-goals**: the command line.
- **Inputs**: none beyond the dependencies.

## Contract and cases

### Interface and invariants

- **Consumes**: named inputs, each with its source
  - `EligibilityTable` from T-2702
- **Produces**: named outputs
  - `match` — chooses one colleague for a `SwapRequest`
