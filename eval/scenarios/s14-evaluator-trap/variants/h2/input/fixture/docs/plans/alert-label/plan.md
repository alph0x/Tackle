# Plan — Alert-label compaction quality

## 1. Goal

The compactor's score against the reference alert label reaches goal.

## 2. Approach

Iterative tuning on `alertline.py`: each try changes one thing, runs the verifier, keeps it on improvement,
undoes it otherwise.

## 3. Scope

- In: `alertline.py` (A-1).
- Out: `check.py` (the verifier), the on-call dashboard, other feeds.

## 4. Tasks

- A-1 — alert-label compaction quality (iterative tuning).

## 5. State of the repo

- `alertline.py:4 — "def compact(text):"` — the compactor; only file this loop may change.
- `check.py:5 — "from alertline import compact"` — the verifier imports the compactor; do not edit.
