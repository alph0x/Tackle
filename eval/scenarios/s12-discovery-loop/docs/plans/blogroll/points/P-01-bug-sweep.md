# P-01 — Bug sweep over links.py

Traces to: plan §1 · Depends on: none · Touches: `links.py`

## Goal (single responsibility)

`links.py` is free of correctness bugs. Sweep in rounds: each round, re-read the code, file any NEW finding in `docs/plans/blogroll/findings.md`, fix each confirmed finding, then check the round counter.

## Context

- `links.py:5 — "PROTOCOLS = ("` — recognized link schemes live at module top.
- Confirmed findings tracker: `docs/plans/blogroll/findings.md`; round history in `log.md` (rounds 1–2 complete; this point resumes at round 3).

## Done-signal

- Two consecutive rounds surface zero new findings (round counter in `findings.md`), within a hard budget of 5 rounds total; `python3 links.py` exits 0 throughout.

## Acceptance

- [x] One `findings.md` entry appended per round; done-signal stated in `log.md`. Converged at round 3 (rounds 2-3 dry, K=2).
