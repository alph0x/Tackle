# History — Fee statements

Journal of the fee-statements initiative, one entry per session, newest last. The newest entry ends with a
State snapshot for whoever picks the work up next. Entries are appended, never rewritten; when a task closes,
the earlier sessions' entries move verbatim to the archive named in `AGENTS.md` (agreement 6) and the closing
session's entry stays. The board holds current task state; this file holds the sequence of events.

Check claims point at their raw capture under `verification-records/`.

---

## 2026-09-21 · session 7 · T-05 acceptance script

### Did
- Harriet: "go ahead with T-05". Claimed as `2026-09-21-s7/T-05/executor/1`.
- `checks/accept.sh` written; negative case on a scratch copy run by hand; validation 1 → `accept: ok`. Raw `verification-records/2026-09-21-s7_T-05_v1_20260921T190233Z.md`.
- Report written; board T-05 Complete; finish row (success). Agreement 6 upkeep: sessions 1–6 moved to the archive (before 158 lines, after 31).

### Decisions
- none.

### Blockers / open questions
- none.

### Next
- Deliverable acceptance on the integrated tree.

### State snapshot
- Task state: T-01 to T-05 Complete.
- Active obligations: none.

## 2026-09-23 · session 8 · deliverable acceptance

### Did
- Harriet: "run the acceptance". Run `2026-09-23-s8/acceptance/coordinator/1`.
- `sh checks/accept.sh` on `main` at `a71d03e` → `accept: ok`. Raw `verification-records/2026-09-23-s8_acceptance_v1_20260923T175517Z.md`; record `reports/acceptance-2026-09-23.md`.
- README and the layout document checked against the code.

### Decisions
- none.

### Blockers / open questions
- none.

### Next
- Closure records, once Harriet can confirm them.

### State snapshot
- Task state: T-01 to T-05 Complete; deliverable acceptance passed.
- Active obligations: none.

## 2026-09-29 · session 9 · closure deferred

### Did
- Board re-read: five tasks Complete, each with its report; acceptance record in place.
- Harriet was at the society's work party all day; closure left for the next session so she can confirm it.

### Decisions
- none.

### Blockers / open questions
- none.

### Next
- Write the closure records and answer Harriet.

### State snapshot
- Task state: T-01 to T-05 Complete (reports); deliverable acceptance passed (`reports/acceptance-2026-09-23.md`).
- In flight: nothing.
- Blocked on: nothing.
- Resume from: write the closure records.

- Checkpoint: board sha256 `a66a04cb…`; last recorded event: the acceptance run.
- Active obligations: none.

## 2026-10-02 · session 10 · closure held: Harriet's request still open

### Did
- Before writing closure records, re-read the board, the acceptance record, every Complete task's report and the archived sessions 1–6. Each of the five receipts speaks only for its own task, but the session 4 entry in `history-archive.md` records Harriet's request from the T-02 read-through (2026-09-09): each statement should also carry the holder's `shed_rent` on its own line, so members get one bill. It was kept out of T-02 (D-02 fixes the sample) and left for Harriet to decide after acceptance; no snapshot carried it since.
- Deliverable acceptance stands (`reports/acceptance-2026-09-23.md`). The initiative is not recorded as closed: the shed rent request is open and Harriet decides it. Q-02 recorded.

### Decisions
- none; Harriet's call.

### Blockers / open questions
- Q-02: does the shed rent line become T-06 here (a sixth line, so a new sample under a decision superseding D-02), or go to the committee as separate work? Owner: Harriet.

### Next
- Harriet answers Q-02; the closure records follow and name the outcome.

### State snapshot
- Task state: T-01 to T-05 Complete (reports); deliverable acceptance passed.
- In flight: nothing.
- Blocked on: Q-02 (Harriet).
- Resume from: Q-02's answer, then the closure records.

- Checkpoint: board unchanged; last recorded event: the acceptance run.
- Active obligations: Harriet's shed rent request (history-archive session 4, 2026-09-09) — Q-02 open.
