<a id="task-t-05--weekly-sheet"></a>
# Task T-05 — Weekly sheet

> Self-contained: implement from this file and its named inputs.

## Purpose and scope

- **Depends on**: T-04 — the `zones` table.
- **Traces to**: R02 (`plan.md` §2).
- **Write scope**: `sheet/import_zones.py`, `docs/plans/zone-rollup/reports/T-05-report.md`.
- **Autonomy**: L2
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Procedure revision**: Tackle 9.0.1 RUN card.
- **Inputs**: the growers' sheet template (to be snapshotted when T-04 closes).
- **Goal**: the weekly sheet's zone cells are filled from the table.
- **Non-goals**: no change to the command.

## Contract and cases

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | a week's table | cells filled | import dry run |

## Acceptance and recovery <!-- SEALED: D-02 -->

```sh
python3 sheet/import_zones.py --dry-run
```

- **Task check**: exit 0 (Draft until T-04 closes; the script does not exist yet).
- **Recovery**: within the budget; then stop and report.
