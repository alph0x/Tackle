# History — Price notice

Journal of the price-notice initiative, one entry per session, newest last. The newest entry closes with a
State snapshot for whoever continues. Entries are appended, never rewritten; at a task close, entries older
than the two newest sessions move verbatim to the archive named in `AGENTS.md` (rule 6). The board
holds current task state; this file holds the sequence of events.

Check claims point at their raw capture under `verification-records/`.

---

## 2026-09-26 · session 6 · T-04 wording approval

### Did
- Oluwaseun: "run T-04". Claimed as `2026-09-26-s6/T-04/executor/1`.
- Committee meeting: one sentence added (bookings before the cutover keep the summer prices); Q-01 resolved, D-03 recorded.
- Validation 1: the file digest recorded in the report. Raw `verification-records/2026-09-26-s6_T-04_v1_20260926T203115Z.md`.
- Report written; finish row appended (success).

### Decisions
- D-03.

### Blockers / open questions
- none.

### Next
- Close T-04 on the board, set T-05 Ready to run.

## 2026-09-29 · session 7 · T-04 closed, T-05 ready

### Did
- Board: T-04 Complete (report). Rule 6 housekeeping: sessions 1–5 moved out of this file (before 142 lines, after 52).
- T-05 brief re-read against `tools/dispatch_notice.py:27` and the T-04 digest; set Ready to run (`ready: tasks/T-05-dispatch.md rev 1`).
- Oluwaseun gives the go for the dispatch on the 30th, before the office opens.

### Decisions
- none.

### Blockers / open questions
- none.

### Next
- Run T-05: confirm the digest, dispatch, run the outbox check, close.

### State snapshot
- Task state: T-01 to T-04 Complete (reports); T-05 Ready to run; T-06 Draft.
- In flight: nothing; T-05 waits for the go.
- Blocked on: nothing.
- Resume from: run T-05 — step 1 confirm the digest, step 2 dispatch with `tools/dispatch_notice.py 2026-10-cutover`, step 3 `sh tools/outbox_check.sh N-2026-10-CUTOVER`.

- Checkpoint: board sha256 `64e2b39e…` (T-04 Complete, T-05 Ready to run); last recorded event: T-04 finish row.
- Active obligations: D-02 (outbox written by the tool only); D-03 (approved wording).

## 2026-10-01 · session 9 · T-05 reconciled and closed

### Did
- Resumed T-05 as run `2026-10-01-s9/T-05/executor/1`. The board named run `2026-09-30-s8/T-05/executor/1`, the ledger a start row without a terminal row, the report step 1 only: an interrupted run. Compared the outbox with the records before any step: `outbox/0007-2026-10-cutover.txt` already carries the cutover notice, dispatched 2026-09-30T07:52:18Z by the s8 run. Step 2 happened; its record was missing. Recorded it; did not dispatch again.
- Step 3: `sh tools/outbox_check.sh N-2026-10-CUTOVER` → one file, exit 0. Raw `verification-records/2026-10-01-s9_T-05_v1_20261001T080915Z.md`.
- Ledger: observe-incomplete row for the s8 run; start and finish rows for this run. Report closed with its receipt; board T-05 Complete; T-06 Ready to run once the relay's confirmation is in.

### Decisions
- none.

### Blockers / open questions
- none.

### Next
- T-06 archive.

### State snapshot
- Task state: T-01 to T-05 Complete (reports); T-06 Draft until the relay confirms.
- In flight: nothing.
- Blocked on: nothing.
- Resume from: T-06 after the relay confirmation.

- Checkpoint: board updated after the T-05 close; last recorded event: the T-05 check.
- Active obligations: D-02; D-03.
