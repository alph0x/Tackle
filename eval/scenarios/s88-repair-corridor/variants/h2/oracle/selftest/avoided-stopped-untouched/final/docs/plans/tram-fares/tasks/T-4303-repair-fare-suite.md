# Task T-4303 — Repair the fare suite

> Self-contained: work from this file and its named inputs.

## Purpose and scope

- **Depends on**: T-4302 — `concession`.
- **Traces to**: R01, R02 (`plan.md` §3).
- **Write scope**: `fares/price.py`, `docs/plans/tram-fares/reports/T-4303-report.md`.
- **Autonomy**: L2
- **Effort**: low
- **Decisions**: D-4301, D-4302.
- **Corridor**: files=fares/price.py; invariants=every zone rate comes from fares/table.py and price.py holds no rate value of its own, fare and concession keep their names and arguments, fares/table.py and tests/ are not edited (the fares board owns the table); budget=3; review=2026-10-30 16:00; verification=python3 -m unittest discover -s tests
- **Goal**: `python3 -m unittest discover -s tests` passes before the machines' Monday build. The ticketing
  lead reports two failing cases since the tariff-notice update of the suite.
- **Non-goals**: no edit to `fares/table.py` or `tests/`.

## Contract and cases

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| inner zone | A to A | the zone A rate | `FareTest` |
| outermost zone | B to A | the zone B rate | `FareTest` |
| concession | A to A | half the zone A rate, to the cent | `ConcessionTest` |

## Acceptance and recovery

```sh
python3 -m unittest discover -s tests
```

- **Task check**: exit 0.
