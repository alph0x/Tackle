<a id="task-t-01--parse-export-rows"></a>
# Task T-01 — Parse export rows

> Self-contained: a worker implements this task from this file and its named inputs.

## Purpose and scope

- **Depends on**: none.
- **Traces to**: R01 (`plan.md` §2).
- **Write scope**: `manifest/rows.py`, `tests/test_rows.py`, `docs/plans/manifest-summary/reports/T-01-report.md`.
- **Autonomy**: L2
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Procedure revision**: Tackle 9.0.1 RUN card.
- **Inputs**: a sample export from the scanner (header `scan_id,barcode,weight_kg,bay`).
- **Goal**: `read_rows(path)` yields one typed record per data row.
- **Non-goals**: no summary, no CLI.

## Contract and cases

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | three-row export | three records in order | `tests/test_rows.py` |
| boundary | header only | no records | `tests/test_rows.py` |

## Acceptance and recovery <!-- SEALED: D-03 -->

```sh
python3 -m unittest tests.test_rows -q
```

- **Task check**: the command above exits 0.
- **Recovery**: within the budget; then stop and report.
