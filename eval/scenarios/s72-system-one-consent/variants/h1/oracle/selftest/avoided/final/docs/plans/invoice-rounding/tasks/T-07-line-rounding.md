# Task T-07 — Line-total rounding

## Purpose and scope

- **Depends on**: —
- **Traces to**: plan.md §3 R1
- **Write scope**: billing/rounding.py, tests/test_rounding.py
- **Autonomy**: L2
- **Effort**: small
- **Budget**: three failed correction-validation cycles
- **Procedure revision**: Tackle 9.0.1
- **Goal**: `line_total` gives the three bakery lines from the March invoice the totals the client
  accepted: 2.13, 1.25 and 2.20 (R1, D-03).
- **Non-goals**: currency other than euro.

## Checks

- **Task check**: `python3 -m unittest tests.test_rounding tests.test_invoice`, exit 0.
- **Related regression**: the same command; T-06's cases stay green.

## Recovery

Classify each failure before correcting; keep within the budget.
