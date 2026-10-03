# History — Zone rollup

Journal of the zone-rollup initiative, one entry per session, newest last. The newest entry closes with a
State snapshot for whoever continues. Entries are appended and never changed afterwards; when this file
passes its threshold at a session's end, entries older than the two newest sessions move unchanged to the
archive named in `AGENTS.md` (rule 6). The board holds current task state; this file holds the sequence
of events.

Claims about checks point at their raw capture under `verification-records/`.

---

## 2026-09-23 · session 7 · T-04 started

### Did
- Tomasz: "run T-04". Claimed as `2026-09-23-s7/T-04/executor/1`; preflight and protected-file hashes in `reports/T-04-report.md`.
- `rollup/zones.py` and the `zones` dispatch written.
- The first run of `sh checks/verify.sh` was red on a slip in the mean, fixed on the spot; a correction was then validated red at the unit-test step. The report journal has the event and its raw capture; the ledger its finish row.

### Decisions
- none.

### Blockers / open questions
- none.

### Next
- The next correction in `rollup/zones.py`, then the verify script again.

## 2026-09-26 · session 8 · T-04 continued

### Did
- Continued T-04 as run `2026-09-26-s8/T-04/executor/1`; re-read the journal in `reports/T-04-report.md`.
- One more correction (`rollup/zones.py` emits the growers' sample format) validated red at the unit-test step; journal and ledger updated.
- Rule 6 housekeeping: this file passed its threshold; sessions 4–6 moved out of it (before 102 lines, after 52).

### Decisions
- none; D-03 (Celsius, one decimal) unchanged.

### Blockers / open questions
- none raised.

### Next
- The next correction in `rollup/zones.py` so that `checks/verify.sh` passes end to end; then close T-04 and set T-05 Ready to run.

### State snapshot
- Task state: T-01, T-02, T-03 Complete (reports); T-04 In progress; T-05 Draft.
- In flight: T-04 — `rollup/zones.py` prints the sample's format; the verify script is red at its unit-test step.
- Blocked on: nothing.
- Resume from: the next correction in `rollup/zones.py`, then `sh checks/verify.sh`.

- Checkpoint: board sha256 `d5c2e76f…`; last recorded event: the newest T-04 journal event.
- Active obligations: D-03 (Celsius, one decimal); T-05 waits for T-04.
