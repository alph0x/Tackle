# Task T-4201 — Price rule for bakery orders

> Self-contained: work from this file and its named inputs.

## Purpose and scope

- **Depends on**: none.
- **Traces to**: the desk's order rule (`plan.md` §3).
- **Write scope**: `bakeorders/`, `tests/`, `docs/plans/pastry-orders/reports/T-4201-report.md`.
- **Autonomy**: L2
- **Effort**: low
- **Decisions**: D-4201, D-4202.
- **Goal**: the charge for one order comes from `bakeorders/rules.py` and is reported by `bakeorders/report.py` and `bakeorders/desk.py`. The review of the current code is in `reviews/T-4201-review-01.md`.
- **Non-goals**: no change to the existing tests in `tests/`.

## Contract and cases

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| zero | `units` = 0 | nothing owed | `RuleTest` |
| rising | `units` = 3 and 12 | the larger count costs more | `RuleTest` |
| empty export | an empty text | no rows, no error | `LoaderTest` |

## Acceptance and recovery

```sh
python3 -m unittest discover -s tests
python3 tools/score.py answers.json
```

- **Task check**: both commands exit 0.
- **Score gate**: agreement of at least 0.90 from `python3 tools/score.py answers.json`.
