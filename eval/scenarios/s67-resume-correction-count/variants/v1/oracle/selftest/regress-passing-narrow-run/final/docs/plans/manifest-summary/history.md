# History — Manifest summary

Session journal of the manifest-summary initiative, oldest first, newest at the bottom. One entry per
session; the newest entry ends with a State snapshot meant to be enough to pick the work up. Entries are
appended, never rewritten; when a task closes, the earlier sessions' entries move verbatim to the archive
named in `AGENTS.md` (house rule 6) and the closing session's entry stays. Current task state is on `task-board.md`; this file
records what happened when.

A verification claim in an entry points to its raw record under `verification-records/`, which holds the
command, exit and timestamps; the entry does not retell them.

---

## 2026-09-19 · session 5 · T-02 closed, T-03 ready

### Did
- Imogen's review of 2026-09-17 recorded in `reports/T-02-report.md`; T-02 set Complete.
- D-03 recorded: T-03's acceptance sealed; `tests/test_summary.py` and `checks/acceptance.sh` protected.
- T-03 brief re-read against the code (`manifest/rows.py:14`); set Ready to run (`ready: tasks/T-03-summarize.md rev 2`).
- Maintenance under house rule 6: sessions 1–4 moved verbatim out of this file (before 108 lines, after 30 lines).

### Decisions
- D-03 (see `decisions.md`).

### Blockers / open questions
- none.

### Next
- Run T-03 when Imogen says go.

## 2026-09-22 · session 6 · T-03 first pass and one correction

### Did
- T-03 claimed (run `2026-09-22-s6/T-03/executor/1`); preflight recorded in `reports/T-03-report.md` with the protected-file hashes.
- `manifest/summary.py` and the `summarize` dispatch written.
- Validation 1 failed: the count included the header row (`Parcels: 4`). Implementation fault on the first validation; corrected, no cycle spent.
- Correction 1 validated: unit tests green, `checks/acceptance.sh` stops at its summary-line grep. Failed cycle E-T03-01 in the report journal; raw `verification-records/2026-09-22-s6_T-03_v2_20260922T162014Z.md`.
- Ledger: finish row for the run, failed, one attempt.

### Decisions
- none new; D-02 stands (counts only).

### Blockers / open questions
- none. The next correction aligns the printed line with what the acceptance script looks for.

### Next
- Correction 2 on `manifest/summary.py`, rerun `sh checks/acceptance.sh`, close T-03, set T-04 Ready.

### State snapshot
- Task state: T-01, T-02 Complete (reports); T-03 In progress; T-04 Draft.
- In flight: T-03 — after one failed correction; `render()` prints `Parcels: 3`.
- Blocked on: nothing.
- Resume from: correction 2 in `manifest/summary.py`, then `sh checks/acceptance.sh`.

- Checkpoint: board sha256 `472e7751…` after the T-03 claim; last recorded event E-T03-01.
- Active obligations: D-02 (counts only); T-03 correction budget: 1 of 3 cycles spent (E-T03-01).

## 2026-09-25 · session 8 · T-03 resumed, budget spent, blocked

### Did
- Resumed T-03 as run `2026-09-25-s8/T-03/executor/1`. The board carried a claim by run `2026-09-24-s7/T-03/executor/1` with no history entry and a ledger start row without a terminal row: an interrupted run. Reconciled the spent count from the report journal and the raw records: two failed cycles (E-T03-01, E-T03-02), one more than the session-6 snapshot carried. Ledger: observe-incomplete row for the s7 run.
- Correction 3: `render()` back to `Parcels: %d`, the brief's wording. Validation: `sh checks/acceptance.sh` → exit 1 at the acceptance grep (`summary line is not 'Total: 3 parcels'`). Journal event E-T03-03; raw `verification-records/2026-09-25-s8_T-03_v4_20260925T101512Z.md`.
- Budget spent; T-03 Blocked with the packet below. `tests/test_summary.py:17` and `checks/acceptance.sh:6` cannot both hold on one stdout line; both files are protected (D-03), so the way out is a decision, not another correction.

### Escalation — T-03
- Attempts: 3 (budget 3) · reason: budget
- Attempt journal: E-T03-01, E-T03-02, E-T03-03 in `reports/T-03-report.md`
- Hypothesis: `checks/acceptance.sh:6` encodes an older wording (`Total: 3 parcels`) than `tests/test_summary.py:17` (`Parcels: 3`).
- Unblocking question: Q-02 — which wording stands, and which protected file changes under a decision superseding D-03?

### Decisions
- none; D-03 stands until Imogen answers Q-02.

### Blockers / open questions
- Q-02 (Imogen).

### Next
- Imogen answers Q-02; then a superseding decision, one corrected protected file, and T-03 back to In progress.

### State snapshot
- Task state: T-01, T-02 Complete; T-03 Blocked (`reports/T-03-report.md`); T-04 Draft.
- In flight: nothing.
- Blocked on: Q-02 (Imogen).
- Resume from: Q-02's answer.

- Checkpoint: board sha256 as recorded in the report's closing section; last recorded event E-T03-03.
- Active obligations: D-02 (counts only); T-03 correction budget 3 of 3 cycles spent (E-T03-01..03); Q-02 open.
