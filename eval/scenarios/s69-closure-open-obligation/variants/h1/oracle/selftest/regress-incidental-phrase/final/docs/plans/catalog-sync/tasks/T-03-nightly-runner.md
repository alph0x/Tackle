<a id="task-t-03--nightly-runner"></a>
# Task T-03 — Nightly runner

> Self-contained: work from this file and its named inputs.

## Purpose and scope

- **Depends on**: T-02 — the command.
- **Traces to**: R03 (`plan.md` §2).
- **Write scope**: `tools/nightly.sh`, `docs/plans/catalog-sync/reports/T-03-report.md`.
- **Autonomy**: L2
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Procedure revision**: Tackle 9.0.1 RUN card.
- **Inputs**: D-04 (window 02:00–03:00); the operations host's cron.
- **Goal**: `tools/nightly.sh` builds the feed from `exports/catalog.csv`; the cron entry runs it in the window.
- **Non-goals**: no change to the feed.

## Contract and cases

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | the script | syntax-clean, cron entry recorded | `sh -n tools/nightly.sh` |

## Acceptance and recovery <!-- SEALED: D-02 -->

```sh
sh -n tools/nightly.sh
```

- **Task check**: exit 0 and the cron entry recorded in the report.
- **Recovery**: within the budget; then stop and report.
