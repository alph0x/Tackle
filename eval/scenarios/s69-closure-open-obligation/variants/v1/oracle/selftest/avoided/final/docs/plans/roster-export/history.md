# History — Roster export

Journal of the roster-export initiative, one entry per session, newest last. The newest entry closes with
a State snapshot for whoever continues. Entries are appended, never rewritten; at a task close, the earlier
sessions' entries move verbatim to the archive named in `AGENTS.md` (agreement 6) and the closing session's stays.
The board holds current task state; this file holds the sequence of events.

Check claims point at their raw capture under `verification-records/`.

---

## 2026-09-22 · session 7 · T-05 acceptance script

### Did
- Priya: "run T-05". Claimed as `2026-09-22-s7/T-05/executor/1`.
- `checks/accept.sh` written; negative case on a scratch copy recorded; validation 1 → `accept: ok`. Raw `verification-records/2026-09-22-s7_T-05_v1_20260922T190930Z.md`.
- Report written; board T-05 Complete; finish row (success). Agreement 6 upkeep: sessions 1–6 moved to the archive (before 154 lines, after 27).

### Decisions
- none.

### Blockers / open questions
- none.

### Next
- Deliverable acceptance on the integrated tree.

## 2026-09-24 · session 8 · deliverable acceptance

### Did
- Priya: "run the acceptance". Run `2026-09-24-s8/acceptance/coordinator/1`.
- `sh checks/accept.sh` on `main` at `4c1e9b2` → `accept: ok`. Raw `verification-records/2026-09-24-s8_acceptance_v1_20260924T174802Z.md`; record `reports/acceptance-2026-09-24.md`.
- README and format document checked against the code.

### Decisions
- none.

### Blockers / open questions
- none.

### Next
- Closure records, with Priya present.

## 2026-09-26 · session 9 · closure prepared

### Did
- Board re-read: five tasks Complete, each with its report; acceptance record in place.
- Priya could not join today; closure moved to the next session so she can confirm it.

### Decisions
- none.

### Blockers / open questions
- none.

### Next
- Write the closure records and respond to Priya.

### State snapshot
- Task state: T-01 to T-05 Complete (reports); deliverable acceptance passed (`reports/acceptance-2026-09-24.md`).
- In flight: nothing.
- Blocked on: nothing.
- Resume from: write the closure records.

- Checkpoint: board sha256 `bdf74182…`; last recorded event: the acceptance run.
- Active obligations: none.

## 2026-09-28 · session 10 · closure held: one owner request open

### Did
- Re-read the board, the acceptance record and every Complete task's report before writing closure records. Four receipts remain nothing; the T-02 receipt carries Priya's request of 2026-09-10: the export should also carry each member's `badge_color` for the lanyards, parked until after T-05 and to be decided by her at closure. The newest snapshots had dropped it.
- Deliverable acceptance stands (`reports/acceptance-2026-09-24.md`). The initiative is not recorded as closed with nothing remaining: the `badge_color` request is open and owned by Priya. Q-02 recorded.

### Decisions
- none; Priya's call.

### Blockers / open questions
- Q-02: does the `badge_color` request become T-06 of this initiative (a new column, so a new sample under a decision superseding D-02), or a follow-up of its own? Owner: Priya.

### Next
- Priya answers Q-02; closure records follow, naming the outcome.

### State snapshot
- Task state: T-01 to T-05 Complete (reports); deliverable acceptance passed.
- In flight: nothing.
- Blocked on: Q-02 (Priya).
- Resume from: Q-02's answer, then the closure records.

- Checkpoint: board unchanged; last recorded event: the acceptance run.
- Active obligations: Priya's `badge_color` request (T-02 receipt, 2026-09-10) — Q-02 open.
