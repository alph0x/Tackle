<a id="task-t-01--register-reader"></a>
# Task T-01 — Plot register reader

> Self-contained: work from this file and its named inputs.

## Purpose and scope

- **Depends on**: none.
- **Traces to**: R01 (`plan.md` §2).
- **Write scope**: `statements/plots.py`, `tests/test_plots.py`, `docs/plans/fee-statements/reports/T-01-report.md`.
- **Autonomy**: L2
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Procedure revision**: Tackle 9.0.1 RUN card.
- **Inputs**: `tests/fixtures/plots.csv`; the agreed sample `tests/fixtures/expected-statements.txt` (D-02).
- **Goal**: `read_plots(path)` returns the plots in register order, one dict per row.
- **Non-goals**: no change to the register or the sample.

## Contract and cases

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | the three fixture plots | as in the goal | `tests/test_plots.py` |

## Acceptance and recovery <!-- SEALED: D-02 -->

```sh
python3 -m unittest tests.test_plots -q
```

- **Task check**: exit 0.
- **Recovery**: within the budget; then stop and report.
