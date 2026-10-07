<a id="task-t-02--statement-renderer"></a>
# Task T-02 — Statement renderer

> Self-contained: work from this file and its named inputs.

## Purpose and scope

- **Depends on**: T-01 — `read_plots`.
- **Traces to**: R01 (`plan.md` §2).
- **Write scope**: `statements/render.py`, `tests/test_render.py`, `docs/plans/fee-statements/reports/T-02-report.md`.
- **Autonomy**: L2
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Procedure revision**: Tackle 9.0.1 RUN card.
- **Inputs**: `tests/fixtures/plots.csv`; the agreed sample `tests/fixtures/expected-statements.txt` (D-02); D-03.
- **Goal**: `write_statements(plots, season, out)` writes the five-line statements, equal to the sample for the fixture plots.
- **Non-goals**: no further lines; no change to the sample.
- **Acceptance owner**: Harriet Mwangi reviews the rendered statements; the executor runs the test.

## Contract and cases

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | the three fixture plots | file equal to the sample | `tests/test_render.py` |
| no tap | plot 12 | `Water: £0.00` | the sample |
| invalid | a plot without `size_rods` | `KeyError` | manual, recorded |

## Acceptance and recovery <!-- SEALED: D-02 -->

```sh
python3 -m unittest tests.test_render -q
```

- **Task check**: exit 0 and Harriet's review recorded in the report.
- **Recovery**: within the budget; then stop and report.
