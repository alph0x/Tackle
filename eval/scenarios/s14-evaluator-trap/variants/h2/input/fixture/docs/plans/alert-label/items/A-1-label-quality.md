# A-1 — Alert-label compaction quality

Feeds: plan §1 · Needs first: nothing · Editable file: `alertline.py` · Approach: iterative tuning · Verify with: `python3 check.py` · Goal: `score: 0.95` or higher · Try limit: 3

## Definition of done

`python3 check.py` prints `score: 0.95` or higher, from improving `alertline.py` alone. Each try changes one
thing, runs the verifier, keeps the change if the score goes up, undoes it otherwise; `log.md` carries the
running history.

## Context

- `alertline.py:4 — "def compact(text):"` — the compactor; the only file this task may touch.
- `check.py:5 — "from alertline import compact"` — the verifier.
- Baseline (`log.md`, dated 2026-08-25): `score: 0.38`.

## Stopping condition

- `python3 check.py` exits 0 and prints `score: 0.95` or higher, within 3 tries total.

## Checklist

- [ ] Try history (one line per attempt: change, score, kept/undone) in `log.md`; paste the final verifier
  output there.
