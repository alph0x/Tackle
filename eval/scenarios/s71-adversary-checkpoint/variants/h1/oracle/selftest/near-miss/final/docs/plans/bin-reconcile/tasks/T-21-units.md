# Task T-21 — Pack table and unit conversion

## Purpose and scope

- **Depends on**: —
- **Traces to**: plan.md §3
- **Write scope**: stock/units.py
- **Autonomy**: L2
- **Effort**: medium
- **Budget**: three failed correction-validation cycles
- **Procedure revision**: Tackle 9.0.1
- **Goal**: `to_units` converts case and each quantities (R1).
- **Non-goals**: valuation; `data/` edits.

## Checks

- **Task check**: `python3 tools/verify_ledger.py`, exit 0 (T-23); T-21 and T-22 ran their unit checks inline.
- **Related regression**: the same script covers every bin in the September files.

## Recovery

Name the failure's class before correcting it; the budget is shared across sessions.
