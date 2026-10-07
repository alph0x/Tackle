# Task T-06 — Invoice totals from line totals

## Purpose and scope

- **Depends on**: —
- **Traces to**: plan.md §3 R2
- **Write scope**: billing/invoice.py, tests/test_invoice.py
- **Autonomy**: L2
- **Effort**: small
- **Budget**: three failed correction-validation cycles
- **Procedure revision**: Tackle 9.0.1
- **Goal**: `invoice_total` sums the rounded line totals.

## Checks

- **Task check**: `python3 -m unittest tests.test_invoice`, exit 0.
