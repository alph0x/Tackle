<a id="task-t-04--command-line"></a>
# Task T-04 — Command-line entry

> Self-contained: work from this file and its named inputs.

## Purpose and scope

- **Depends on**: T-02 — `write_reminders`.
- **Traces to**: R02 (`plan.md` §2).
- **Write scope**: `reminders/__main__.py`, `docs/plans/shift-reminders/reports/T-04-report.md`.
- **Autonomy**: L2
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Procedure revision**: Tackle 9.0.1 RUN card.
- **Inputs**: the reader (T-01) and the renderer (T-02).
- **Goal**: `python3 -m reminders week <shifts.csv> <out.txt>` writes the week and prints one summary line, exit 0.
- **Non-goals**: no sending, no mail integration.

## Contract and cases

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | the fixture rota | `reminders: 3 written to …`, exit 0 | the command |
| invalid | missing arguments | usage line, exit 2 | manual, recorded |

## Acceptance and recovery <!-- SEALED: D-02 -->

```sh
python3 -m reminders week tests/fixtures/shifts.csv /tmp/week-check.txt
```

- **Task check**: exit 0 and one summary line.
- **Recovery**: within the budget; then stop and report.
