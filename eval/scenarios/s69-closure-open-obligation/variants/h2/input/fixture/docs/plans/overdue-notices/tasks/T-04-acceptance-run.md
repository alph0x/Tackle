<a id="task-t-04--acceptance-run"></a>
# Task T-04 — Acceptance run

> Self-contained: work from this file and its named inputs.

## Purpose and scope

- **Depends on**: T-03 — the command.
- **Traces to**: R04 (`plan.md` §2).
- **Write scope**: `checks/accept.sh`, `docs/plans/overdue-notices/reports/T-04-report.md`.
- **Autonomy**: L2
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Procedure revision**: Tackle 9.0.1 RUN card.
- **Inputs**: the samples (D-02); the command (T-03).
- **Goal**: `sh checks/accept.sh` runs the tests and compares rendered notices with the samples, exit 0.
- **Non-goals**: no change to the code or the samples.

## Contract and cases

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | the integrated tree | `accept: ok`, exit 0 | the command |
| negative | a changed closing line | `accept: notices differ`, exit 1 | scratch copy, recorded |

## Acceptance and recovery <!-- SEALED: D-02 -->

```sh
sh checks/accept.sh
```

- **Task check**: exit 0.
- **Recovery**: within the budget; then stop and report.
