<a id="task-t-05--dispatch-the-notice"></a>
# Task T-05 — Dispatch the notice

> Self-contained: a worker performs this task from this file and its named inputs.

## Purpose and scope

- **Depends on**: T-04 — the approved wording and its digest (`reports/T-04-report.md`); T-02 — the member list; T-03 — the relay dry run.
- **Traces to**: R03 (`plan.md` §2).
- **Write scope**: `outbox/` (through `tools/dispatch_notice.py` only, D-02), `docs/plans/price-notice/reports/T-05-report.md`.
- **Autonomy**: L2
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Procedure revision**: Tackle 9.0.1 RUN card.
- **Lineage**: none.
- **Inputs**: `notices/2026-10-cutover.md` at the digest recorded in `reports/T-04-report.md`; notice id `N-2026-10-CUTOVER`.
- **Goal**: one outbox file carries `Notice-Id: N-2026-10-CUTOVER`; the relay mails it once.
- **Non-goals**: no other notice; no hand-made outbox file; no change to the tools.
- **Acceptance owner**: Oluwaseun Adeyemi; the executor runs the check.

Grounding:

- `tools/dispatch_notice.py:28 — "target.write_text("` — the single place that writes an outbox file.
- `notices/2026-10-cutover.md:1 — "notice-id: N-2026-10-CUTOVER"` — the id the check looks for.

## Contract and cases

### Interface and invariants

- **Consumes**: the approved notice.
- **Produces**: one new numbered outbox file; the tool's confirmation line.
- **Invariants**: older outbox files untouched; the tools unchanged.

### Case matrix

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | the approved notice | one outbox file with the id | `sh tools/outbox_check.sh N-2026-10-CUTOVER` exit 0 |
| invalid | unknown slug | the tool refuses, exit 2, nothing written | manual, recorded |

## Steps

1. Confirm `shasum -a 256 notices/2026-10-cutover.md` equals the digest in `reports/T-04-report.md`; record it.
2. Dispatch: `python3 tools/dispatch_notice.py 2026-10-cutover`; record the confirmation line.
3. Check: `sh tools/outbox_check.sh N-2026-10-CUTOVER`; capture the raw record.
4. Close the report with its receipt; the coordinator updates the board and history.

## Acceptance and recovery <!-- SEALED: D-02 -->

```sh
sh tools/outbox_check.sh N-2026-10-CUTOVER
```

- **Task check**: exit 0.
- **Related regression check**: `ls outbox/` still lists 0005 and 0006 unchanged.
- **Verification ownership**: the executor captures the check under `verification-records/`; the coordinator updates board and history.
- **Recovery**: within the budget; a dispatch cannot be recalled — stop and bring anything unexpected to Oluwaseun.
