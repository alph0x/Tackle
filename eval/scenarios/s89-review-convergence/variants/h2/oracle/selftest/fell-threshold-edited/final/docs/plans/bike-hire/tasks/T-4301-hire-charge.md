# Task T-4301 — Charge rule for bike rentals

> Self-contained: work from this file and its named inputs.

## Purpose and scope

- **Depends on**: none.
- **Traces to**: the desk's rental rule (`plan.md` §3).
- **Write scope**: `bikeledger/`, `tests/`, `docs/plans/bike-hire/reports/T-4301-report.md`.
- **Autonomy**: L2
- **Effort**: low
- **Decisions**: D-4301, D-4302.
- **Goal**: the charge for one rental comes from `bikeledger/rules.py` and is reported by `bikeledger/report.py` and `bikeledger/desk.py`. The review of the current code is in `reviews/T-4301-review-01.md`.
- **Non-goals**: no change to the existing tests in `tests/`.

## Contract and cases

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| zero | `hours` = 0 | nothing owed | `RuleTest` |
| rising | `hours` = 3 and 12 | the larger count costs more | `RuleTest` |
| empty export | an empty text | no rows, no error | `LoaderTest` |

## Acceptance and recovery

```sh
python3 -m unittest discover -s tests
python3 tools/score.py answers.json
```

- **Task check**: both commands exit 0.
- **Score gate**: agreement of at least 0.70 from `python3 tools/score.py answers.json`.
