# Plan — Kiosk price board

Methodology: Tackle 3.2.0

## 1. Goal

Show a student ticket rate alongside the adult and child rates.

## 2. Approach

Extend the rate table in `rates.py`; no new modules, no pricing engine.

## 3. Scope

- In: `rates.py` (P-01), `README.md` (P-02).
- Out: discount rules, online sales.

## 4. Points

- P-01 — student rate constant and print line.
- P-02 — README price list refresh (Depends on: P-01).

## 5. State of the repo

- `rates.py:3 — "ADULT = 12.00"` — price constants live at module top.
- `README.md:3 — "Adult: $12.00"` — printed price list, mirrors the constants.
