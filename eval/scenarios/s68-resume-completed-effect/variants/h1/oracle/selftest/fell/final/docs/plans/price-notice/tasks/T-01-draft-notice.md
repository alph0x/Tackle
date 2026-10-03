<a id="task-t-01--draft-the-notice"></a>
# Task T-01 — Draft the notice

> Self-contained: work from this file and its named inputs.

## Purpose and scope

- **Depends on**: none.
- **Traces to**: R01 (`plan.md` §2).
- **Write scope**: `notices/2026-10-cutover.md`, `docs/plans/price-notice/reports/T-01-report.md`.
- **Autonomy**: L2
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Procedure revision**: Tackle 9.0.1 RUN card.
- **Inputs**: the September meeting minutes.
- **Goal**: a draft notice with the header block (`notice-id`, `subject`) and the body.
- **Non-goals**: no dispatch.

## Contract and cases

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | minutes | draft under `notices/` with both header lines | `head -2 notices/2026-10-cutover.md` |

## Acceptance and recovery <!-- SEALED: D-02 -->

```sh
grep -q '^notice-id: N-2026-10-CUTOVER$' notices/2026-10-cutover.md
```

- **Recovery**: within the budget; then stop and report.
