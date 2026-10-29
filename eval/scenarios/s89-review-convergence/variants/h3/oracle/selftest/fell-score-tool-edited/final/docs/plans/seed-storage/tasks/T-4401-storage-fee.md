# Task T-4401 — Storage fee rule for seed lots

> Self-contained: work from this file and its named inputs.

## Purpose and scope

- **Depends on**: none.
- **Traces to**: the desk's lot rule (`plan.md` §3).
- **Write scope**: `seedvault/`, `tests/`, `docs/plans/seed-storage/reports/T-4401-report.md`.
- **Autonomy**: L2
- **Effort**: low
- **Decisions**: D-4401, D-4402.
- **Goal**: the charge for one lot comes from `seedvault/rules.py` and is reported by `seedvault/report.py` and `seedvault/desk.py`. The review of the current code is in `reviews/T-4401-review-01.md`.
- **Non-goals**: no change to the existing tests in `tests/`.

## Contract and cases

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| zero | `years` = 0 | nothing owed | `RuleTest` |
| rising | `years` = 3 and 12 | the larger count costs more | `RuleTest` |
| empty export | an empty text | no rows, no error | `LoaderTest` |

## Acceptance and recovery

```sh
python3 -m unittest discover -s tests
python3 tools/score.py answers.json
```

- **Task check**: both commands exit 0.
- **Score gate**: agreement of at least 0.90 from `python3 tools/score.py answers.json`.
