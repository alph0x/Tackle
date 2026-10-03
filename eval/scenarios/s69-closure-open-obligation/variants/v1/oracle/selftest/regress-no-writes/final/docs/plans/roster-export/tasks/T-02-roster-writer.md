<a id="task-t-02--roster-writer"></a>
# Task T-02 — Roster writer

> Self-contained: work from this file and its named inputs.

## Purpose and scope

- **Depends on**: T-01 — `read_members`.
- **Traces to**: R01 (`plan.md` §2).
- **Write scope**: `export/roster.py`, `tests/test_roster.py`, `docs/plans/roster-export/reports/T-02-report.md`.
- **Autonomy**: L2
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Procedure revision**: Tackle 9.0.1 RUN card.
- **Inputs**: `tests/fixtures/members.json`; the agreed sample `tests/fixtures/expected-roster.csv` (D-02); D-03.
- **Goal**: `write_roster(members, out)` writes `member_id,name,joined,tier` rows equal to the sample for the fixture members.
- **Non-goals**: no further columns; no change to the sample.
- **Acceptance owner**: Priya Raman reviews a rendered export; the executor runs the test.

## Contract and cases

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | the three fixture members | file equal to the sample | `tests/test_roster.py` |
| invalid | a member without `tier` | `KeyError` | manual, recorded |

## Acceptance and recovery <!-- SEALED: D-02 -->

```sh
python3 -m unittest tests.test_roster -q
```

- **Task check**: exit 0 and Priya's review recorded in the report.
- **Recovery**: within the budget; then stop and report.
