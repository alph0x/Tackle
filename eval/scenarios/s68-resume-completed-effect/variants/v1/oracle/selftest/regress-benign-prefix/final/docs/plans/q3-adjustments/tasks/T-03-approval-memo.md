<a id="task-t-03--approval-memo"></a>
# Task T-03 — Approval memo

> Self-contained: work from this file and its named inputs.

## Purpose and scope

- **Depends on**: T-02 — the amount (`reports/T-02-report.md`).
- **Traces to**: R02 (`plan.md` §2).
- **Write scope**: `memos/2026-09-22-q3-true-up.md`, `docs/plans/q3-adjustments/reports/T-03-report.md`.
- **Autonomy**: L2
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Procedure revision**: Tackle 9.0.1 RUN card.
- **Inputs**: the T-02 amount; the committee call of 22 September.
- **Goal**: a signed approval memo under `memos/`.
- **Non-goals**: no postings.

## Contract and cases

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | committee approves | memo with date and approver | the memo file exists and names the approver |

## Acceptance and recovery <!-- SEALED: D-02 -->

```sh
grep -q 'Approved by: Rhiannon Vale' memos/2026-09-22-q3-true-up.md
```

- **Recovery**: within the budget; then stop and report.
