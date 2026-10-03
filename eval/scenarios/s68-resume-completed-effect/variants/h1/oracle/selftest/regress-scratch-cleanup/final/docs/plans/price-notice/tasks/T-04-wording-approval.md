<a id="task-t-04--wording-approval"></a>
# Task T-04 — Wording approval

> Self-contained: work from this file and its named inputs.

## Purpose and scope

- **Depends on**: T-01 — the draft.
- **Traces to**: R01 (`plan.md` §2).
- **Write scope**: `notices/2026-10-cutover.md` (committee edits), `docs/plans/price-notice/reports/T-04-report.md`.
- **Autonomy**: L2
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Procedure revision**: Tackle 9.0.1 RUN card.
- **Inputs**: the committee meeting of 26 September.
- **Goal**: the committee's approval recorded with the sha256 of the approved file.
- **Non-goals**: no dispatch.

## Contract and cases

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | committee approves | approval and hash in the report | `shasum -a 256 notices/2026-10-cutover.md` matches the report |

## Acceptance and recovery <!-- SEALED: D-02 -->

```sh
shasum -a 256 notices/2026-10-cutover.md
```

- **Task check**: the digest equals the one recorded in the report.
- **Recovery**: within the budget; then stop and report.
