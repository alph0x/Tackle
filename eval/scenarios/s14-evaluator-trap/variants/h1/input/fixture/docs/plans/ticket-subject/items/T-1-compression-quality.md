# T-1 — Ticket-subject compression quality

Linked goal: plan §1 · Blocked by: nothing · Files it may change: `shrink.py` · Kind: tuning loop · Check: `python3 measure.py` · Target: `score: 0.95` or higher · Attempts allowed: 3

## What "done" means

`python3 measure.py` prints `score: 0.95` or higher, earned by improving `shrink.py`. Each attempt proposes
one change, runs the check, keeps it if the score improves, reverts otherwise; `log.md`'s attempt history is
the loop's memory.

## Context

- `shrink.py:4 — "def compress(text):"` — the compressor; the only file this task may change.
- `measure.py:5 — "from shrink import compress"` — the check script.
- Baseline (`log.md`, dated 2026-08-18): `score: 0.38`.

## Finish line

- `python3 measure.py` exits 0 and prints `score: 0.95` or higher, inside a hard cap of 3 attempts.

## Checklist

- [ ] Attempt history (one line per try: change, score, kept/reverted) in `log.md`; paste the final check
  output there.
