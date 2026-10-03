<a id="task-t-01--member-reader"></a>
# Task T-01 — Member reader

> Self-contained: work from this file and its named inputs.

## Purpose and scope

- **Depends on**: none.
- **Traces to**: R01 (`plan.md` §2).
- **Write scope**: export/members.py, tests/test_members.py, `docs/plans/roster-export/reports/T-01-report.md`.
- **Autonomy**: L2
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Procedure revision**: Tackle 9.0.1 RUN card.
- **Inputs**: `tests/fixtures/members.json`; the agreed sample `tests/fixtures/expected-roster.csv` (D-02).
- **Goal**: read_members(path) returns the members in file order.
- **Non-goals**: no change to the sample or the membership file.

## Contract and cases

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | the fixture members | as in the goal | the acceptance command below |

## Acceptance and recovery <!-- SEALED: D-02 -->

```sh
python3 -m unittest tests.test_members -q
```

- **Task check**: exit 0.
- **Recovery**: within the budget; then stop and report.
