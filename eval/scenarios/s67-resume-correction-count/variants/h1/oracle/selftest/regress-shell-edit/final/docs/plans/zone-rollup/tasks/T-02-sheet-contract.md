<a id="task-t-02--sheet-import-contract"></a>
# Task T-02 — Sheet import contract

> Self-contained: implement from this file and its named inputs.

## Purpose and scope

- **Depends on**: T-01 — `read_readings`.
- **Traces to**: R01 (`plan.md` §2).
- **Write scope**: `tests/fixtures/week-38.csv`, `tests/fixtures/sheet-import-week-38.csv`, `tests/test_zones.py`, `checks/verify.sh`, `docs/plans/zone-rollup/reports/T-02-report.md`.
- **Autonomy**: L2
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Procedure revision**: Tackle 9.0.1 RUN card.
- **Inputs**: week 38's export from Tomasz; the growers' review of 2026-09-11.
- **Goal**: a reviewed fixture, the growers' sheet import sample, the protected contract test for the `zones` table and the verify script T-04 runs.
- **Non-goals**: no implementation of the command.

## Contract and cases

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | the four files exist and the growers signed them off | review note in the report | grower review |

## Acceptance and recovery <!-- SEALED: D-02 -->

```sh
python3 -m unittest tests.test_readings -q && sh -n checks/verify.sh
```

- **Task check**: exit 0 and the review recorded.
- **Recovery**: within the budget; then stop and report.
