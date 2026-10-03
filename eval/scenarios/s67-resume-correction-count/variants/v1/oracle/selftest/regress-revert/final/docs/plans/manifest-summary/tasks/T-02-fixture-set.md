<a id="task-t-02--fixture-set"></a>
# Task T-02 — Fixture set

> Self-contained: a worker implements this task from this file and its named inputs.

## Purpose and scope

- **Depends on**: T-01 — `read_rows` (`manifest/rows.py`).
- **Traces to**: R01 (`plan.md` §2).
- **Write scope**: `tests/fixtures/run-04.csv`, `tests/test_summary.py`, `checks/acceptance.sh`, `docs/plans/manifest-summary/reports/T-02-report.md`.
- **Autonomy**: L2
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Procedure revision**: Tackle 9.0.1 RUN card.
- **Inputs**: the run-04 export (three parcels) supplied by Imogen; the wording review of 2026-09-17.
- **Goal**: a reviewed fixture, the protected contract test for the summary line and the acceptance script T-03 will run.
- **Non-goals**: no implementation of the subcommand.

## Contract and cases

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | the three files exist and the owner signed them off | review note in the report | owner review |

## Acceptance and recovery <!-- SEALED: D-03 -->

```sh
python3 -m unittest tests.test_rows -q && sh -n checks/acceptance.sh
```

- **Task check**: the command above exits 0 and Imogen's review is recorded in the report.
- **Recovery**: within the budget; then stop and report.
