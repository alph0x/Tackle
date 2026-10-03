# Task T-23 — Month-end verify script on the September files

## Purpose and scope

- **Depends on**: T-22
- **Traces to**: plan.md §3
- **Write scope**: tools/verify_ledger.py, stock/moves.py, stock/units.py
- **Autonomy**: L2
- **Effort**: medium
- **Budget**: three failed correction-validation cycles
- **Procedure revision**: Tackle 9.0.1
- **Goal**: `python3 tools/verify_ledger.py` reconciles the September journal with the signed count (R3).
- **Non-goals**: valuation; `data/` edits.

## Checks

- **Task check**: `python3 tools/verify_ledger.py`, exit 0 (T-23); T-21 and T-22 ran their unit checks inline.
- **Related regression**: the same script covers every bin in the September files.

## Recovery

Name the failure's class before correcting it; the budget is shared across sessions.
