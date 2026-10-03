<a id="task-t-04--digest-line"></a>
# Task T-04 — Digest line

> Self-contained: a worker implements this task from this file and its named inputs.

## Purpose and scope

- **Depends on**: T-03 — the `summarize` subcommand's output line.
- **Traces to**: R02 (`plan.md` §2).
- **Write scope**: `digest/template.md`, `digest/render.py`, `docs/plans/manifest-summary/reports/T-04-report.md`.
- **Autonomy**: L2
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Procedure revision**: Tackle 9.0.1 RUN card.
- **Inputs**: the digest template owned by ops (to be snapshotted when T-03 closes).
- **Goal**: the nightly digest quotes the `Parcels: <n>` line of the day's export.
- **Non-goals**: no change to the summary command.

## Contract and cases

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | today's export present | digest contains the line | render script |
| boundary | export missing | digest says the export is missing | render script |

## Acceptance and recovery <!-- SEALED: D-03 -->

```sh
python3 digest/render.py --check
```

- **Task check**: the command above exits 0 (Draft until T-03 closes; the script does not exist yet).
- **Recovery**: within the budget; then stop and report.
