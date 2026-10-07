<a id="task-t-03--template-document"></a>
# Task T-03 — Template document

> Self-contained: work from this file and its named inputs.

## Purpose and scope

- **Depends on**: T-02 — the wording.
- **Traces to**: R03 (`plan.md` §2).
- **Write scope**: `docs/reminder-template.md`, `docs/plans/shift-reminders/reports/T-03-report.md`.
- **Autonomy**: L2
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Procedure revision**: Tackle 9.0.1 RUN card.
- **Inputs**: the wording (T-02); D-02.
- **Goal**: `docs/reminder-template.md` lists every rota column the reminder uses and how.
- **Non-goals**: no change to the wording.

## Contract and cases

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | the template document | five documented columns | the command |

## Acceptance and recovery <!-- SEALED: D-02 -->

```sh
grep -c '^| `' docs/reminder-template.md
```

- **Task check**: `5`, exit 0.
- **Recovery**: within the budget; then stop and report.
