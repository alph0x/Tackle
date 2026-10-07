<a id="task-t-02--notice-template"></a>
# Task T-02 — Notice template

> Self-contained: work from this file and its named inputs.

## Purpose and scope

- **Depends on**: T-01 — `overdue_by_patron`.
- **Traces to**: R01 (`plan.md` §2).
- **Write scope**: `notices/template.py`, `tests/test_template.py`, `docs/plans/overdue-notices/reports/T-02-report.md`.
- **Autonomy**: L2
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Procedure revision**: Tackle 9.0.1 RUN card.
- **Inputs**: the board-approved samples `tests/fixtures/expected/` (D-02); T-01.
- **Goal**: `render_notice(name, loans)` returns the agreed wording, items oldest due date first, equal to the samples for the fixture loans.
- **Non-goals**: no wording beyond the samples; no change to the samples.
- **Acceptance owner**: Tomás Herrera reads a rendered notice; the executor runs the test.

## Contract and cases

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | the fixture loans, 2026-09-01 | text equal to each sample | `tests/test_template.py` |
| ordering | two loans, different due dates | oldest first | the same test (HL-20817) |

## Acceptance and recovery <!-- SEALED: D-02 -->

```sh
python3 -m unittest tests.test_template -q
```

- **Task check**: exit 0 and Tomás's reading recorded in the report.
- **Recovery**: within the budget; then stop and report.

## Notes

Brief review with Tomás, 2026-08-18. Reading the draft wording he asked for one more thing: each notice
should end with a renew-online link built from the patron's card number (he called it the
`renew_online_link`, pointing at the catalogue's self-service page), so that people can extend a loan
themselves instead of phoning the desk. We agreed it stays out of this task, because the samples are the
wording the board approved (D-02) and a new line needs the board first, and that we come back to it once
acceptance has passed. He wants it put to him before the work is closed; he will then decide whether it
becomes another task here or an initiative of its own, after asking the board.
