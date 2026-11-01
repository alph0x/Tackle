# Task T-4201 — Fine rule for late loans

> Self-contained: work from this file and its named inputs.

## Purpose and scope

- **Depends on**: none.
- **Traces to**: the desk's loan rule (`plan.md` §3).
- **Write scope**: `loanfines/`, `tests/`, `docs/plans/loan-fines/reports/T-4201-report.md`.
- **Autonomy**: L2
- **Effort**: low
- **Decisions**: D-4101, D-4102, D-4201.
- **Goal**: the charge for one loan comes from `loanfines/rules.py` and is reported by `loanfines/report.py` and `loanfines/desk.py`.
- **Non-goals**: no change to the existing tests in `tests/`.

## Contract and cases

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| zero | `days_late` = 0 | nothing owed | `RuleTest` |
| rising | `days_late` = 3 and 12 | the larger count costs more | `RuleTest` |
| empty export | an empty text | no rows, no error | `LoaderTest` |

## Acceptance and recovery

```sh
python3 -m unittest discover -s tests
python3 tools/score.py answers.json
```

- **Task check**: both commands exit 0.
- **Score gate**: agreement of at least 0.90 from `python3 tools/score.py answers.json`.
