# Task T-0905 — Triage command

> **Self-contained briefing.** A new worker must be able to implement this Task from this
> file alone. Links provide optional depth; explicitly named inputs are the only additional prerequisites.

## Purpose and scope

- **Depends on**: T-0904 (`route`).
- **Traces to**: plan.md §3.
- **Write scope**: `src/triage/cli.py`; `tests/test_cli.py`; this workspace's board, history, resource usage and `reports/T-0905-report.md`.
- **Autonomy**: L2.
- **Effort**: low
- **Goal**: A shell command that triages one ticket.
- **Non-goals**: batch triage.
- **Inputs**: none beyond the dependencies.

## Contract and cases

### Interface and invariants

- **Consumes**: named inputs, each with its source
  - `route` from T-0904
- **Produces**: named outputs
  - `triage` — the shell command
