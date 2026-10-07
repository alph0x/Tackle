<a id="task-t-04--command-line"></a>
# Task T-04 — Command-line entry

> Self-contained: work from this file and its named inputs.

## Purpose and scope

- **Depends on**: T-02 — `write_statements`.
- **Traces to**: R02 (`plan.md` §2).
- **Write scope**: `statements/__main__.py`, `docs/plans/fee-statements/reports/T-04-report.md`.
- **Autonomy**: L2
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Procedure revision**: Tackle 9.0.1 RUN card.
- **Inputs**: `tests/fixtures/plots.csv`; the agreed sample (D-02).
- **Goal**: `python3 -m statements render <plots.csv> <season> <out.txt>` writes the statements and prints one summary line.
- **Non-goals**: no change to the renderer or the sample.

## Contract and cases

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | the fixture plots, season 2027 | one summary line, exit 0 | the command below |
| usage | no arguments | usage line, exit 2 | manual, recorded |

## Acceptance and recovery <!-- SEALED: D-02 -->

```sh
python3 -m statements render tests/fixtures/plots.csv 2027 /tmp/statements-check.txt
```

- **Task check**: exit 0.
- **Recovery**: within the budget; then stop and report.
