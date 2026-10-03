<a id="task-t-03--export-rotation"></a>
# Task T-03 — Export rotation

> Self-contained: implement from this file and its named inputs.

## Purpose and scope

- **Depends on**: none.
- **Traces to**: Tomasz's housekeeping request (Q-02).
- **Write scope**: `tools/rotate_exports.sh`, `docs/plans/zone-rollup/reports/T-03-report.md`.
- **Autonomy**: L2
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Procedure revision**: Tackle 9.0.1 RUN card.
- **Inputs**: Q-02 (keep eight exports).
- **Goal**: `sh tools/rotate_exports.sh` keeps the eight newest `exports/*.csv` and moves the rest to `exports/old/`.
- **Non-goals**: no deletion.

## Contract and cases

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | ten exports | two moved, eight kept | manual run on a scratch copy, recorded |
| boundary | fewer than eight | nothing moved | same |

## Acceptance and recovery <!-- SEALED: D-02 -->

```sh
sh -n tools/rotate_exports.sh
```

- **Task check**: exit 0 plus the recorded scratch run.
- **Recovery**: within the budget; then stop and report.
