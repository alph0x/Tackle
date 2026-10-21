# Task T-0904 — Router

> **Self-contained briefing.** A new worker must be able to implement this Task from this
> file alone. Links provide optional depth; explicitly named inputs are the only additional prerequisites.

## Purpose and scope

- **Depends on**: T-0902 (`RuleSet`).
- **Traces to**: plan.md §3.
- **Write scope**: `src/triage/router.py`; `tests/test_router.py`; this workspace's board, history, resource usage and `reports/T-0904-report.md`.
- **Autonomy**: L2.
- **Effort**: low
- **Goal**: Route a ticket to one queue by the loaded rules.
- **Non-goals**: the command line.
- **Inputs**: none beyond the dependencies.

## Contract and cases

### Interface and invariants

- **Consumes**: named inputs, each with its source
  - `RuleSet` from T-0902
- **Produces**: named outputs
  - `route` — chooses one queue name for a `Ticket`

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
