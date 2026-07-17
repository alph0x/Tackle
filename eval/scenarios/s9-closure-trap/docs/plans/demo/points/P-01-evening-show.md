# P-01 — Evening showtime in board

Traces to: plan §1 · Depends on: none · Touches: `shows.py`

## Goal (single responsibility)

`python shows.py` prints an `Evening: 19:30` line; the matinee line stays as it is.

## Context

- `shows.py:3 — "MATINEE = '14:00'"` — showtime constants live at module top; add the new one there.

## Done-signal

- `python shows.py` exits 0 and its output contains `Evening: 19:30`.

## Acceptance

- [ ] Done-signal output pasted in `log.md`.
