# History — Q3 adjustments

Session journal of the q3-adjustments initiative, one entry per session, newest last; the newest entry
ends with a State snapshot for whoever continues. Entries are appended and never rewritten; at a task
close, entries older than the two newest sessions move verbatim to the archive named in `AGENTS.md`
(agreement 6). The board carries current task state; this file carries the sequence of events.

Check claims point at their raw capture under `verification-records/`.

---

## 2026-09-22 · session 5 · T-03 approval memo

### Did
- Rhiannon: "run T-03". Claimed as `2026-09-22-s5/T-03/executor/1`.
- Committee call at 18:30; the memo `memos/2026-09-22-q3-true-up.md` written and signed.
- Validation 1: the approver grep → exit 0. Raw `verification-records/2026-09-22-s5_T-03_v1_20260922T190244Z.md`.
- Report written; finish row appended (success).

### Decisions
- none new; D-03 (150.00) stands.

### Blockers / open questions
- none.

### Next
- Close T-03 on the board, set T-04 Ready to run.

## 2026-09-26 · session 6 · T-03 closed, T-04 ready

### Did
- Board: T-03 Complete (report). Agreement 6 upkeep: sessions 1–4 moved to the archive (before 127 lines, after 52).
- T-04 brief re-read against `tools/post_adjustment.py:30` and the memo; set Ready to run (`ready: tasks/T-04-post-true-up.md rev 1`).
- Rhiannon will give the go for the posting tomorrow morning, once the bank statement for the 26th is in.

### Decisions
- none.

### Blockers / open questions
- none.

### Next
- Run T-04: confirm the amount, post the row, run the check, close.

### State snapshot
- Task state: T-01, T-02, T-03 Complete (reports); T-04 Ready to run; T-05 Draft.
- In flight: nothing; T-04 waits for Rhiannon's go.
- Blocked on: nothing.
- Resume from: run T-04 — step 1 confirm the amount (150.00), step 2 post with `tools/post_adjustment.py`, step 3 `python3 tools/check_adjustment.py ACC-1042 "Q3 true-up"`.

- Checkpoint: board sha256 `8a06a9ac…` (T-03 Complete, T-04 Ready to run); last recorded event: T-03 finish row.
- Active obligations: D-02 (journal written by the tool only); D-03 (amount 150.00).

## 2026-09-28 · session 8 · T-04 reconciled and closed

### Did
- Resumed T-04 as run `2026-09-28-s8/T-04/executor/1`. The board carried run `2026-09-27-s7/T-04/executor/1`, the ledger a start row for it without a terminal row, the report step 1 only: an interrupted run. Before any step, compared the journal with the records: `data/adjustments.csv` already holds `2026-09-27,ACC-1042,150.00,Q3 true-up,2026-09-27T09:41:12Z`, posted by the s7 run after its last write. Step 2 happened; its record was missing. Recorded it; did not post again.
- Step 3: `python3 tools/check_adjustment.py ACC-1042 "Q3 true-up"` → `check: found 1 row(s)`, exit 0. Raw `verification-records/2026-09-28-s8_T-04_v1_20260928T081630Z.md`.
- Ledger: observe-incomplete row for the s7 run; start and finish rows for this run. Report closed with its receipt; board T-04 Complete; T-05 Ready to run.

### Decisions
- none.

### Blockers / open questions
- none.

### Next
- T-05 quarter close report.

### State snapshot
- Task state: T-01 to T-04 Complete (reports); T-05 Ready to run.
- In flight: nothing.
- Blocked on: nothing.
- Resume from: run T-05.

- Checkpoint: board updated after the T-04 close; last recorded event: the T-04 check.
- Active obligations: D-02; D-03.
