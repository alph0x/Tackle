# P-01 — Notebook count in tally

Traces to: plan §1 · Depends on: none · Touches: `tally.py`

## Goal (single responsibility)

`python tally.py` prints a `Notebooks: 7` line; the pens line stays as it is.

## Context

- `tally.py:3 — "PENS = 12"` — stock constants live at module top; add the new one there.

## Done-signal

- `python tally.py` exits 0 and its output contains `Notebooks: 7`.

## Acceptance

- [ ] Done-signal output pasted in `log.md`.
