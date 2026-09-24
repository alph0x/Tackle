# I-1 — Trimmer quality to threshold

Linked to: plan §1 · Waiting on: none · File it may change: `snip.py` · Style: trial loop · Run: `python3 score.py` · Target: `score: 0.95` or higher · Rounds allowed: 3

## What finishes this

`python3 score.py` prints `score: 0.95` or higher, earned by improving `snip.py`. Each round proposes one
change, runs the metric, keeps it on improvement, rolls back otherwise; the attempt journal in `log.md` is
the loop's state.

## Context

- `snip.py:6 — "def trim(text):"` — the trimmer; the only file this item may change.
- `score.py:5 — "from snip import trim"` — the evaluator.
- Baseline (log.md, 2026-07-19): `score: 0.38`.

## Finish condition

- `python3 score.py` exits 0 and prints `score: 0.95` or higher, within a hard budget of 3 rounds.

## Checklist

- [ ] Attempt journal (one line per round: change, score, kept/rolled back) in `log.md`; final metric output
  pasted there.
