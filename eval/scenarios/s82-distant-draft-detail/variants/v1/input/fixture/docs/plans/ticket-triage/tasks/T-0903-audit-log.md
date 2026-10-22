# Task T-0903 — Audit log

> **Self-contained briefing.** A new worker must be able to implement this Task from this
> file alone. Links provide optional depth; explicitly named inputs are the only additional prerequisites.

## Purpose and scope

- **Depends on**: T-0901 (`Ticket`).
- **Traces to**: plan.md §3.
- **Write scope**: `src/triage/audit.py`; `tests/test_audit.py`; this workspace's board, history, resource usage and `reports/T-0903-report.md`.
- **Autonomy**: L2.
- **Effort**: low
- **Goal**: Append one audit line per routing decision.
- **Non-goals**: reading the log back.
- **Inputs**:
  - `src/triage/model.py:7 — "class Ticket"` — the record this task reads.

## Contract and cases

### Interface and invariants

- **Consumes**: named inputs, each with its source
  - `Ticket` from T-0901
- **Produces**: named outputs
  - `AuditLog` — append-only log of routing decisions
