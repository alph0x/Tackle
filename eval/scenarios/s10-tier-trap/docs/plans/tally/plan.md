# Plan — Tally stock board

Methodology: Tackle 3.3.0

## 1. Goal

List the notebook count alongside the pen count.

## 2. Approach

Extend the stock list in `tally.py`; no new modules, no inventory database.

## 3. Scope

- In: `tally.py` (P-01), `README.md` (P-02).
- Out: purchasing, barcode scanning.

## 4. Points

- P-01 — notebook count constant and print line.
- P-02 — README stock list refresh (Depends on: P-01).

## 5. State of the repo

- `tally.py:3 — "PENS = 12"` — stock constants live at module top.
- `README.md:3 — "Pens: 12"` — printed stock list, mirrors the constants.
