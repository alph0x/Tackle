<a id="task-t-03--format-document"></a>
# Task T-03 — Format document

> Self-contained: work from this file and its named inputs.

## Purpose and scope

- **Depends on**: T-02 — the columns in export/roster.py.
- **Traces to**: R03 (`plan.md` §2).
- **Write scope**: docs/export-format.md, `docs/plans/roster-export/reports/T-03-report.md`.
- **Autonomy**: L2
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Procedure revision**: Tackle 9.0.1 RUN card.
- **Inputs**: `tests/fixtures/members.json`; the agreed sample `tests/fixtures/expected-roster.csv` (D-02).
- **Goal**: the four columns documented for the desk.
- **Non-goals**: no change to the sample or the membership file.

## Contract and cases

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | the fixture members | as in the goal | the acceptance command below |

## Acceptance and recovery <!-- SEALED: D-02 -->

```sh
grep -c '^| `' docs/export-format.md
```

- **Task check**: exit 0.
- **Recovery**: within the budget; then stop and report.
