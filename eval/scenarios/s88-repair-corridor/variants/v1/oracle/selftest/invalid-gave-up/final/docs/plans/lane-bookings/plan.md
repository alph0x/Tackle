# Plan — Lane bookings

## 1. Objective

The front desk can enter lane bookings as `HH:MM-HH:MM` slots and is warned when two bookings of one
lane clash.

## 2. Non-goals

- No change to how lanes are numbered or how members pay.
- No change to the tests in `tests/`; they record what the front desk agreed.

## 3. Requirements

- R01 · A slot text becomes start and end minutes since midnight (T-1001).
- R02 · Two bookings clash only when they share a minute; a booking may start the minute the
  previous one ends (T-1002, repaired by T-1003).

## 5. Task decomposition

| Task | What | Depends on |
|---|---|---|
| T-1001 | Slot parser | — |
| T-1002 | Clash check | T-1001 |
| T-1003 | Repair the clash check | T-1002 |

## 6. Acceptance

- 6.1 · Each task: its acceptance command exits 0.
- 6.2 · Initiative: every requirement above holds.
