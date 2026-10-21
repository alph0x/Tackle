# Task T-0902 — Rule loader

> **Self-contained briefing.** A new worker must be able to implement this Task from this
> file alone. Links provide optional depth; explicitly named inputs are the only additional prerequisites.

## Purpose and scope

- **Depends on**: T-0901 (`Ticket`).
- **Traces to**: plan.md §3.
- **Write scope**: `src/triage/rules.py`; `tests/test_rules.py`; this workspace's board, history, resource usage and `reports/T-0902-report.md`.
- **Autonomy**: L2.
- **Detail**: full
- **Effort**: low
- **Goal**: Load routing rules from the rules file into a `RuleSet`.
- **Non-goals**: routing a ticket.
- **Inputs**:
  - `src/triage/model.py:7 — "class Ticket"` — the record this task reads.

## Contract and cases

### Interface and invariants

- **Consumes**: named inputs, each with its source
  - `Ticket` from T-0901
- **Produces**: named outputs
  - `RuleSet` — ordered routing rules read from `config/rules.txt`

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
