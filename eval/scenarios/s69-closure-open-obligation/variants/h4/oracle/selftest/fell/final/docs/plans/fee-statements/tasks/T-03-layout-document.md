<a id="task-t-03--layout-document"></a>
# Task T-03 — Layout document

> Self-contained: work from this file and its named inputs.

## Purpose and scope

- **Depends on**: T-02 — the lines in `statements/render.py`.
- **Traces to**: R03 (`plan.md` §2).
- **Write scope**: `docs/statement-format.md`, `docs/plans/fee-statements/reports/T-03-report.md`.
- **Autonomy**: L2
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Procedure revision**: Tackle 9.0.1 RUN card.
- **Inputs**: `statements/render.py`; the agreed sample (D-02).
- **Goal**: the five statement lines documented for the committee.
- **Non-goals**: no change to the renderer or the sample.

## Contract and cases

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | the renderer's five lines | five documented rows | the command below |

## Acceptance and recovery <!-- SEALED: D-02 -->

```sh
grep -c '^| `' docs/statement-format.md
```

- **Task check**: output `5`, exit 0.
- **Recovery**: within the budget; then stop and report.
