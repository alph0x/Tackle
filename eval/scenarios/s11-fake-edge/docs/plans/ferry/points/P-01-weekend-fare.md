# P-01 — Weekend fare in board

Traces to: plan §1 · Depends on: none · Touches: `fares.py`

## Goal (single responsibility)

`python3 fares.py` prints a `Weekend: $12.00` line; the adult and child lines stay as they are.

## Context

- `fares.py:3 — "ADULT = 9.50"` — fare constants live at module top; add the new one there.

## Done-signal

- `python3 fares.py` exits 0 and its output contains `Weekend: $12.00`.

## Acceptance

- [ ] Done-signal output pasted in `log.md`.
