<a id="task-t-04--post-the-true-up"></a>
# Task T-04 — Post the true-up

> Self-contained: a worker performs this task from this file and its named inputs.

## Purpose and scope

- **Depends on**: T-03 — the approval memo `memos/2026-09-22-q3-true-up.md`; T-02 — the amount.
- **Traces to**: R03 (`plan.md` §2).
- **Write scope**: `data/adjustments.csv` (through `tools/post_adjustment.py` only, D-02), `docs/plans/q3-adjustments/reports/T-04-report.md`.
- **Autonomy**: L2
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Procedure revision**: Tackle 9.0.1 RUN card.
- **Lineage**: none.
- **Inputs**: amount 150.00 (D-03, `reports/T-02-report.md` §Result); memo text `Q3 true-up`; account `ACC-1042`; posting date = the day of posting.
- **Goal**: the journal holds one row `ACC-1042, 150.00, Q3 true-up`, dated the day it was posted.
- **Non-goals**: no other postings; no hand edit of the journal; no change to the tools.
- **Acceptance owner**: Rhiannon Vale; the executor runs the check.

Grounding:

- `data/adjustments.csv:1 — "posted_on,account,amount,memo,posted_at"` — the journal header the check verifies.
- `tools/post_adjustment.py:32 — "writerow([args.date, args.account"` — the single place that writes the journal.

## Contract and cases

### Interface and invariants

- **Consumes**: the approved amount, memo and account.
- **Produces**: one appended journal row; the posting tool's confirmation line.
- **Invariants**: the journal is append-only; existing rows are untouched; the tools are unchanged.

### Case matrix

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | the approved figures | one matching row | `python3 tools/check_adjustment.py ACC-1042 "Q3 true-up"` exit 0 |
| invalid | unknown account | the tool refuses, exit 2, nothing appended | manual, recorded |

## Steps

1. Confirm the amount against `reports/T-02-report.md` §Result and the memo; record it in the report.
2. Post: `python3 tools/post_adjustment.py --account ACC-1042 --amount 150.00 --memo "Q3 true-up" --date <today>`; record the confirmation line.
3. Check: `python3 tools/check_adjustment.py ACC-1042 "Q3 true-up"`; capture the raw record.
4. Close the report with its receipt; the coordinator updates the board and history.

## Acceptance and recovery <!-- SEALED: D-02 -->

```sh
python3 tools/check_adjustment.py ACC-1042 "Q3 true-up"
```

- **Task check**: exit 0.
- **Related regression check**: the journal still parses with its five columns.
- **Verification ownership**: the executor captures the check under `verification-records/`; the coordinator updates board and history.
- **Recovery**: within the budget; a wrong posting cannot be undone by this task — stop and bring it to Rhiannon.
