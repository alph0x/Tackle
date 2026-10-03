<a id="task-t-05--acceptance-run"></a>
# Task T-05 — Acceptance run

> Self-contained: work from this file and its named inputs.

## Purpose and scope

- **Depends on**: T-03 — the format document; T-04 — the command.
- **Traces to**: R04 (`plan.md` §2).
- **Write scope**: `checks/accept.sh`, `docs/plans/roster-export/reports/T-05-report.md`.
- **Autonomy**: L2
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Procedure revision**: Tackle 9.0.1 RUN card.
- **Inputs**: the agreed sample (D-02); the command (T-04).
- **Goal**: `sh checks/accept.sh` runs the tests and compares a rendered export with the sample, exit 0.
- **Non-goals**: no change to the export or the sample.

## Contract and cases

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | the integrated tree | `accept: ok`, exit 0 | the command |
| negative | a changed column | `accept: export differs`, exit 1 | scratch copy, recorded |

## Acceptance and recovery <!-- SEALED: D-02 -->

```sh
sh checks/accept.sh
```

- **Task check**: exit 0.
- **Recovery**: within the budget; then stop and report.
