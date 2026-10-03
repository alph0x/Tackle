<a id="task-t-03--relay-dry-run"></a>
# Task T-03 — Relay dry run

> Self-contained: work from this file and its named inputs.

## Purpose and scope

- **Depends on**: none.
- **Traces to**: R03 (`plan.md` §2).
- **Write scope**: `docs/plans/price-notice/reports/T-03-report.md`.
- **Autonomy**: L2
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Procedure revision**: Tackle 9.0.1 RUN card.
- **Inputs**: the relay maintainer's test mailbox.
- **Goal**: confirmation that the relay mails a test file dropped in its test outbox within the hour.
- **Non-goals**: nothing written to the real `outbox/`.

## Contract and cases

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | a test file in the relay's test outbox | the test mailbox receives it | maintainer confirmation, recorded |

## Acceptance and recovery <!-- SEALED: D-02 -->

Maintainer confirmation recorded in the report with the timestamp.

- **Recovery**: within the budget; then stop and report.
