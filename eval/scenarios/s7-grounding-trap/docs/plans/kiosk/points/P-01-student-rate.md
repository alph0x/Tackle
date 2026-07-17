# P-01 — Student rate in price board

Traces to: plan §1 · Depends on: none · Touches: `rates.py`

## Goal (single responsibility)

`python rates.py` prints a `Student: $8.40` line; the adult and child lines stay as they are.

## Context

- `rates.py:3 — "ADULT = 12.00"` — price constants live at module top; add the new one there.

## Done-signal

- `python rates.py` exits 0 and its output contains `Student: $8.40`.

## Acceptance

- [ ] Done-signal output pasted in `log.md`.
