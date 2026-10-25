# Task T-1003 — Repair the clash check

> Self-contained: work from this file and its named inputs.

## Purpose and scope

- **Depends on**: T-1002 — `clashes`.
- **Traces to**: R01, R02 (`plan.md` §3).
- **Write scope**: `lanes/slots.py`, `lanes/overlap.py`, `docs/plans/lane-bookings/reports/T-1003-report.md`.
- **Autonomy**: L2
- **Effort**: low
- **Decisions**: D-1001, D-1002.
- **Corridor**: files=lanes/slots.py,lanes/overlap.py; invariants=parse_slot and clashes keep their names and signatures, a slot stays the half-open span from its start minute up to its end minute, nothing under tests/ changes; budget=3; review=2026-10-27 18:00; verification=python3 -m unittest discover -s tests
- **Goal**: the suite in `tests/` passes again. Since the desk's last edit to the booking code the suite
  errors on every test; the front desk reports that no booking can be entered.
- **Non-goals**: no change to `tests/`; no new public function.

## Contract and cases

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| parse | `06:30-07:15` | `(390, 435)` | `ParseSlotTest` |
| overlap | `06:30-07:15` and `07:00-07:45` | clash | `ClashTest` |
| back to back | `06:30-07:15` and `07:15-08:00` | no clash | `ClashTest` |

## Acceptance and recovery

```sh
python3 -m unittest discover -s tests
```

- **Task check**: exit 0.
