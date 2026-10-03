<a id="task-t-01--readings-reader"></a>
# Task T-01 — Readings reader

> Self-contained: implement from this file and its named inputs.

## Purpose and scope

- **Depends on**: none.
- **Traces to**: R01 (`plan.md` §2).
- **Write scope**: `rollup/readings.py`, `tests/test_readings.py`, `docs/plans/zone-rollup/reports/T-01-report.md`.
- **Autonomy**: L2
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Procedure revision**: Tackle 9.0.1 RUN card.
- **Inputs**: a logger export (`zone,taken_at,temp_c`).
- **Goal**: `read_readings(path)` yields one typed reading per data row.
- **Non-goals**: no aggregation, no CLI.

## Contract and cases

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | four-row export | four readings in order | `tests/test_readings.py` |
| boundary | header only | nothing yielded | `tests/test_readings.py` |

## Acceptance and recovery <!-- SEALED: D-02 -->

```sh
python3 -m unittest tests.test_readings -q
```

- **Task check**: exit 0.
- **Recovery**: within the budget; then stop and report.
