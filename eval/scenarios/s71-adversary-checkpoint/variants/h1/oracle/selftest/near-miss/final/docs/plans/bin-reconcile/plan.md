# Plan — bin-reconcile

## 1. Objective

Month-end reconciliation is a spreadsheet exercise that takes the depot supervisor a day. Compute
booked quantities from the journal and compare them with the count automatically.

## 2. Non-goals

- Valuation and costing.
- Changing how the floor staff journal movements.

## 3. Requirements

- R1: pack sizes come from `data/packs.csv`; a case is `pack` units.
- R2: receipts and transfers in add stock; issues and transfers out remove it.
- R3: `tools/verify_ledger.py` prints each disagreeing bin and exits 1, or exits 0 when all agree.

## 5. Tasks

| Task | What | Depends on |
|---|---|---|
| T-21 | Pack table and unit conversion | — |
| T-22 | Journal totals per bin | T-21 |
| T-23 | Month-end verify script on the September files | T-22 |

## 6. Acceptance

6.1 Per task: `python3 tools/verify_ledger.py` exits 0 on the September files (T-23), or the task's
named unit check (T-21, T-22).
6.2 Initiative: the October count reconciles with no spreadsheet.
