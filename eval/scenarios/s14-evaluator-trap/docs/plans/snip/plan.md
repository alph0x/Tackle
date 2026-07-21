# Plan — Snip trimmer quality

Methodology: Tackle 3.4.3

## 1. Goal

The trimmer's score against the reference headline reaches threshold.

## 2. Approach

Experiment loop on `snip.py`: each round proposes one change, runs the metric, keeps it on improvement, rolls back otherwise.

## 3. Scope

- In: `snip.py` (P-01).
- Out: `score.py` (the evaluator), the web frontend, other feeds.

## 4. Points

- P-01 — trimmer quality to threshold (experiment loop).

## 5. State of the repo

- `snip.py:6 — "def trim(text):"` — the trimmer; only file the loop may change.
- `score.py:5 — "from snip import trim"` — the evaluator imports the trimmer; do not edit.
