# P-01 closure report — Evening showtime in board

## 1. Scope

- Must-produce: `python shows.py` prints `Evening: 19:30`; the matinee line stays unchanged.
- Must-not-touch: `README.md` (owned by P-02); no new modules.

## 2. INTENT + Evidence

INTENT: execute P-01 exactly as briefed; smallest change — one constant, one print line.

Attempt journal:
1. Added the `EVENING` constant at module top and its print line in `main()`.

Done-signal: `python shows.py`

```
Roxie cinema — today:
Matinee: 14:00
Evening: 19:30
```
exit: 0

## 3. Reviews

- Reviewer/Spec Reader: PASS — matches the point briefing; no scope creep.
- Quality Guardian: PASS — constants stay at module top; style consistent.

## 4. Checker re-run

- Re-ran `python shows.py`: exit 0, output contains `Evening: 19:30` (tier: `standard`; reward-hacking guard: clean — no test edits, no weakened checks).
