# Plan — Ferry fare board

Methodology: Tackle 3.4.3

## 1. Goal

Add a weekend fare to the board, then refresh the NOTICE year and the README fare list.

## 2. Approach

Extend the fare table in `fares.py`; bump the copyright year in `NOTICE.txt`; mirror the fare list in `README.md`. No new modules, no pricing engine.

## 3. Scope

- In: `fares.py` (P-01), `NOTICE.txt` (P-02), `README.md` (P-03).
- Out: online sales, discount rules.

## 4. Points

- P-01 — weekend fare constant and print line.
- P-02 — NOTICE.txt year bump (Depends on: P-01).
- P-03 — README fare list refresh (Depends on: P-02).

## 5. State of the repo

- `fares.py:3 — "ADULT = 9.50"` — fare constants live at module top.
- `NOTICE.txt:2 — "(c) 2025 Harbor Co."` — copyright line.
- `README.md:3 — "Adult: $9.50"` — printed fare list, mirrors the constants.
