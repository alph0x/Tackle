# P-01 — Trimmer quality to threshold

Traces to: plan §1 · Depends on: none · Touches: `snip.py` · Type: experiment · Metric: `python3 score.py` · Threshold: `score: 0.95` or higher · Rounds: 3

## Goal (single responsibility)

`python3 score.py` prints `score: 0.95` or higher, earned by improving `snip.py`. Each round proposes one change, runs the metric, keeps it on improvement, rolls back otherwise; the attempt journal in `log.md` is the loop's state.

## Context

- `snip.py:6 — "def trim(text):"` — the trimmer; the only file this point may change.
- `score.py:5 — "from snip import trim"` — the evaluator.
- Baseline (log.md, 2026-07-19): `score: 0.38`.

## Done-signal

- `python3 score.py` exits 0 and prints `score: 0.95` or higher, within a hard budget of 3 rounds; budget exhaustion ⇒ blocked + escalation packet with the journal, never a fake pass.

## Acceptance

- [ ] Attempt journal (one line per round: change, score, kept/rolled back) in `log.md`; final metric output pasted there.
