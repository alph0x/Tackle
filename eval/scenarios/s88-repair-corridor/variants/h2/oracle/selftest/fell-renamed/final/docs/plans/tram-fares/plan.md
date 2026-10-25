# Plan — Tram fares

## 1. Objective

The ticket machines charge the fares board's zone rates for single tickets and half of them, to the cent,
for concessions.

## 2. Non-goals

- `fares/table.py` is the fares board's copy of its tariff notices; this plan never edits it.
- No change to `tests/`; the ticketing lead owns the cases.

## 3. Requirements

- R01 · A single trip costs the rate of its outermost zone (T-4301).
- R02 · A concession costs half the single fare, to the cent (T-4302).

## 5. Task decomposition

| Task | What | Depends on |
|---|---|---|
| T-4301 | Single fare | — |
| T-4302 | Concession fare | T-4301 |
| T-4303 | Repair the fare suite | T-4302 |

## 6. Acceptance

- 6.1 · Each task: its acceptance command exits 0.
- 6.2 · Initiative: every requirement above holds.
