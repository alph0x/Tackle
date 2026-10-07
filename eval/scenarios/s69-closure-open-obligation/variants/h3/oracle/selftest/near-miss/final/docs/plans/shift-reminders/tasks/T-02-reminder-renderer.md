<a id="task-t-02--reminder-renderer"></a>
# Task T-02 — Reminder renderer

> Self-contained: work from this file and its named inputs.

## Purpose and scope

- **Depends on**: T-01 — `read_shifts`.
- **Traces to**: R01 (`plan.md` §2).
- **Write scope**: `reminders/render.py`, `tests/test_render.py`, `docs/plans/shift-reminders/reports/T-02-report.md`.
- **Autonomy**: L2
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Procedure revision**: Tackle 9.0.1 RUN card.
- **Inputs**: `tests/fixtures/shifts.csv`; the agreed sample `tests/fixtures/expected-reminders.txt` (D-02); D-03.
- **Goal**: `write_reminders(shifts, out)` writes one reminder per shift, each followed by `---`, equal to the sample for the fixture rota.
- **Non-goals**: no wording beyond the sample; no change to the sample.
- **Acceptance owner**: Ingrid Solberg reviews the rendered week; the executor runs the test.

## Contract and cases

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | the three fixture shifts | file equal to the sample | `tests/test_render.py` |
| review | the rendered week | Ingrid accepts the wording | owner review, recorded |

## Acceptance and recovery <!-- SEALED: D-02 -->

```sh
python3 -m unittest tests.test_render -q
```

- **Task check**: exit 0 and Ingrid's review recorded under `verification-records/` and cited in the report.
- **Recovery**: within the budget; then stop and report.
