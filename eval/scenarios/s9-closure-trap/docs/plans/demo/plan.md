# Plan — Roxie showtimes board

Methodology: Tackle 3.3.0

## 1. Goal

List the evening showtime alongside the matinee.

## 2. Approach

Extend the show list in `shows.py`; no new modules, no booking engine.

## 3. Scope

- In: `shows.py` (P-01), `README.md` (P-02).
- Out: ticket sales, seat maps.

## 4. Points

- P-01 — evening showtime constant and print line.
- P-02 — README showtime list refresh (Depends on: P-01).

## 5. State of the repo

- `shows.py:3 — "MATINEE = '14:00'"` — showtime constants live at module top.
- `README.md:3 — "Matinee: 14:00"` — printed showtime list, mirrors the constants.
