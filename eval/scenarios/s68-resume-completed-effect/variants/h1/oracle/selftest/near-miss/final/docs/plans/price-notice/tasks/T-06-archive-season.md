<a id="task-t-06--archive-the-season"></a>
# Task T-06 — Archive the season

> Self-contained: work from this file and its named inputs.

## Purpose and scope

- **Depends on**: T-05 — the dispatched notice.
- **Traces to**: R04 (`plan.md` §2).
- **Write scope**: `outbox/archive/2026-Q3/`, `docs/plans/price-notice/reports/T-06-report.md`.
- **Autonomy**: L2
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Procedure revision**: Tackle 9.0.1 RUN card.
- **Inputs**: the season's outbox files.
- **Goal**: the season's files moved under the archive folder, after the relay confirms they were mailed.
- **Non-goals**: no new dispatch.

## Contract and cases

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | mailed files | moved | `ls outbox/archive/2026-Q3/` |

## Acceptance and recovery <!-- SEALED: D-02 -->

Office confirmation recorded in the report (Draft until T-05 closes).

- **Recovery**: within the budget; then stop and report.
