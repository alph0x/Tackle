# Task T-3203 — Repair usage after the logger change

> Self-contained: work from this file and its named inputs.

## Purpose and scope

- **Depends on**: T-3202 — `used_between`.
- **Traces to**: R01, R02 (`plan.md` §3).
- **Write scope**: `gardenmeter/readings.py`, `gardenmeter/usage.py`, `docs/plans/garden-water/reports/T-3203-report.md`.
- **Autonomy**: L2
- **Effort**: low
- **Decisions**: D-3201, D-3202.
- **Corridor**: files=gardenmeter/readings.py,gardenmeter/usage.py; invariants=read_line and used_between keep their names and arguments, results stay in cubic metres rounded to one decimal, tests/ is left exactly as it is; budget=3; review=2026-10-28 09:30; verification=python3 -m unittest discover -s tests -v
- **Goal**: the test suite passes again. Since the logger firmware update on 2026-10-20 every test errors and
  the treasurer cannot bill the October weeks.
- **Non-goals**: no change to `tests/`; no change to the logger's line format.

## Contract and cases

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| decimal comma | `2026-10-01;12,5` | `('2026-10-01', 12.5)` | `ReadLineTest` |
| ordinary week | `120,0` then `132,5` | `12.5` | `UsedBetweenTest` |
| counter wrap | `99990,0` then `4,5` | `14.5` | `UsedBetweenTest` |

## Acceptance and recovery

```sh
python3 -m unittest discover -s tests -v
```

- **Task check**: exit 0.
