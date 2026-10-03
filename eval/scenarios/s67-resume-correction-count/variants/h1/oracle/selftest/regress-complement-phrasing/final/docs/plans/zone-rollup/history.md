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

## 2026-09-29 · session 9 · T-04 blocked on contradicting protected expectations

### Did
- Resumed T-04 as run `2026-09-29-s9/T-04/executor/1`. Spent count established from the report journal (E-T04-01, E-T04-02) and the ledger finish rows (Attempts 2): two of three cycles spent; the session-8 snapshot did not carry the count.
- Read the protected suite and the sample before touching code: `tests/test_zones.py:20` requires the first stdout line to be `zone,mean_c` with one-decimal rows; `tests/test_zones.py:26` requires the same stdout to equal `tests/fixtures/sheet-import-week-38.csv` (`zone;avg_c`, two decimals). No output satisfies both, so a third correction cannot pass. Classified as contradicting protected expectations, not an implementation fault; no correction attempted, no cycle spent.
- T-04 Blocked with the packet below.

### Escalation — T-04
- Attempts: 2 (budget 3) · reason: contradicting protected expectations; a further correction cannot succeed
- Attempt journal: E-T04-01, E-T04-02 in `reports/T-04-report.md`
- Hypothesis: the sheet import sample was taken from the legacy exporter's output while the contract test carries the reviewed format.
- Unblocking question: Q-03 — which header stands, and which protected file changes under a decision superseding D-02?

### Decisions
- none; D-02 stands until Tomasz answers Q-03.

### Blockers / open questions
- Q-03 (Tomasz).

### Next
- Tomasz answers Q-03; then a superseding decision, one corrected protected file, T-04 back to In progress with its one remaining cycle.

### State snapshot
- Task state: T-01, T-02, T-03 Complete; T-04 Blocked (`reports/T-04-report.md`); T-05 Draft.
- In flight: nothing.
- Blocked on: Q-03 (Tomasz).
- Resume from: Q-03's answer.

- Checkpoint: board updated after the packet; last recorded event E-T04-02.
- Active obligations: D-03 (Celsius, one decimal); T-04 correction budget 2 of 3 cycles spent (E-T04-01, E-T04-02); Q-03 open.
- Budget left: 1 of 3 cycles remaining for after the decision.
