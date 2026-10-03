<a id="task-t-01--catalog-reader"></a>
# Task T-01 — Catalog reader

> Self-contained: work from this file and its named inputs.

## Purpose and scope

- **Depends on**: none.
- **Traces to**: R01 (`plan.md` §2).
- **Write scope**: `sync/catalog.py`, `tests/test_catalog.py`, `docs/plans/catalog-sync/reports/T-01-report.md`.
- **Autonomy**: L2
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Procedure revision**: Tackle 9.0.1 RUN card.
- **Inputs**: `tests/fixtures/catalog.csv` (the warehouse export, five columns).
- **Goal**: `read_catalog(path)` returns the rows with every column, in file order.
- **Non-goals**: no feed.
- **Acceptance owner**: Marcus Oyelaran reviews the rows; the executor runs the test.

## Contract and cases

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | the fixture export | three rows, five columns each | `tests/test_catalog.py` |

## Acceptance and recovery <!-- SEALED: D-02 -->

```sh
python3 -m unittest tests.test_catalog -q
```

- **Task check**: exit 0 and Marcus's review recorded.
- **Recovery**: within the budget; then stop and report.
