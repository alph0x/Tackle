<a id="task-t-03--render-command"></a>
# Task T-03 — Render command

> Self-contained: work from this file and its named inputs.

## Purpose and scope

- **Depends on**: T-02 — `render_notice`.
- **Traces to**: R02, R03 (`plan.md` §2).
- **Write scope**: `notices/__main__.py`, `docs/notice-wording.md`, `README.md`, `docs/plans/overdue-notices/reports/T-03-report.md`.
- **Autonomy**: L2
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Procedure revision**: Tackle 9.0.1 RUN card.
- **Inputs**: T-01, T-02; D-02.
- **Goal**: `python3 -m notices render <loans.json> <YYYY-MM-DD> <outdir>` writes `<card_no>.txt` per card with an overdue loan and prints one summary line; the wording is documented.
- **Non-goals**: no sending; no change to the wording.

## Contract and cases

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | the fixture loans, 2026-09-01 | `2 notices written to …`, exit 0 | the command |
| invalid | three arguments | usage line, exit 2 | manual, recorded |

## Acceptance and recovery

```sh
python3 -m notices render tests/fixtures/loans.json 2026-09-01 /tmp/n
```

- **Task check**: exit 0 and two files.
- **Recovery**: within the budget; then stop and report.
