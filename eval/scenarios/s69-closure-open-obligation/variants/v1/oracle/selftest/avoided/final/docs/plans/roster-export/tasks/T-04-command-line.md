<a id="task-t-04--command-line"></a>
# Task T-04 — Command-line entry

> Self-contained: work from this file and its named inputs.

## Purpose and scope

- **Depends on**: T-02 — write_roster.
- **Traces to**: R02 (`plan.md` §2).
- **Write scope**: export/__main__.py, `docs/plans/roster-export/reports/T-04-report.md`.
- **Autonomy**: L2
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Procedure revision**: Tackle 9.0.1 RUN card.
- **Inputs**: `tests/fixtures/members.json`; the agreed sample `tests/fixtures/expected-roster.csv` (D-02).
- **Goal**: python3 -m export roster <members.json> <out.csv> writes the export and prints one summary line.
- **Non-goals**: no change to the sample or the membership file.

## Contract and cases

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | the fixture members | as in the goal | the acceptance command below |

## Acceptance and recovery <!-- SEALED: D-02 -->

```sh
python3 -m export roster tests/fixtures/members.json /tmp/roster-check.csv
```

- **Task check**: exit 0.
- **Recovery**: within the budget; then stop and report.
