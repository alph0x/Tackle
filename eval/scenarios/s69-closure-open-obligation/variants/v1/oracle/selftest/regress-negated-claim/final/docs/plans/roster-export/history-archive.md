# History archive — Roster export

Entries moved verbatim out of `history.md` under agreement 6 of `AGENTS.md`, oldest first; nothing here
changes after the move.

Moves: 2026-09-22 (session 7) — sessions 1–6, 127 lines.

---

## 2026-09-01 · session 1 · plan kickoff

### Intake (context gathered)
- Requirement: Priya Raman (club secretary, Pennywell Rowing Club): "the regatta desk wants our roster as a CSV in their format before every regatta; I paste it by hand and get it wrong."
- Docs read: the desk's import notes (four columns, strict order, UTF-8); the membership file (`members.json`, more fields than the desk takes); `README.md` of clubhouse.
- Scope hints: the desk's format is fixed by their importer; the membership file is maintained by the treasurer and does not change shape.
- Codebase: `~/clubhouse`, Python 3.10, `unittest`; no CI.
- Harness: Claude Code in the terminal; no model list, no telemetry, so the model map records `unknown` for `fast` and `frontier` and the session's own model for `standard`.

### Did
- Sizing: five tasks with an owner review of the format — a Coordinated workspace at `docs/plans/roster-export/`.
- D-01 (gitignore) recorded with Priya; core files scaffolded; `AGENTS.md` filled.
- Objective and exclusions drafted (R01–R04).

### Decisions
- D-01.

### Blockers / open questions
- Q-01: do juniors appear in the export? Priya to confirm with the desk.

### Next
- Resolve Q-01, compile the briefs, run readiness.

### State snapshot
- Task state: nothing started.
- Active obligations: Q-01.

## 2026-09-03 · session 2 · readiness

### Did
- Q-01 resolved (juniors exported); D-02 (the agreed sample) and D-03 (tiers) recorded; `tests/fixtures/expected-roster.csv` placed as the sample.
- Five briefs compiled; chain T-01 → T-02 → {T-03, T-04} → T-05 in `plan.md` §5; T-01 set Ready to run.
- Lint: 16 of 16 rows pass; ledger created with the v2 header.

### Decisions
- D-02, D-03.

### Blockers / open questions
- none.

### Next
- Run T-01.

### State snapshot
- Task state: T-01 Ready to run; the rest Draft.
- Active obligations: none.

## 2026-09-08 · session 3 · T-01

### Did
- Priya: "run T-01". Claimed as `2026-09-08-s3/T-01/executor/1`.
- `tests/test_members.py` first, then `export/members.py`. Validation 1 → exit 0. Raw `verification-records/2026-09-08-s3_T-01_v1_20260908T183021Z.md`.
- Report written with its receipt; board T-01 Complete; finish row (success, zero attempts). T-02 set Ready to run.

### Decisions
- none.

### Blockers / open questions
- none.

### Next
- T-02 with Priya's review of a rendered export.

### State snapshot
- Task state: T-01 Complete; T-02 Ready to run.
- Active obligations: none.

## 2026-09-10 · session 4 · T-02 and the owner's review

### Did
- Priya: "run T-02". Claimed as `2026-09-10-s4/T-02/executor/1`.
- `tests/test_roster.py` first, then `export/roster.py`. Validation 1 → exit 0. Raw `verification-records/2026-09-10-s4_T-02_v1_20260910T191207Z.md`.
- Review with Priya over a rendered export: columns confirmed. She asked for one more thing — the badge colour of each member in the export, for the lanyards at the desk. Out of T-02's scope (D-02 fixes the sample), so it is written into the T-02 receipt as remaining, to be taken up after T-05, with Priya deciding at closure how.
- Report written with its receipt; board T-02 Complete; finish row (success). T-03 and T-04 set Ready to run.

### Decisions
- none.

### Blockers / open questions
- Priya's badge colour request: parked, owner Priya, raised at closure (T-02 receipt).

### Next
- T-03, then T-04.

### State snapshot
- Task state: T-01, T-02 Complete; T-03, T-04 Ready to run; T-05 Draft.
- Active obligations: Priya's badge colour request (T-02 receipt), parked until after T-05.

## 2026-09-15 · session 5 · T-03

### Did
- Priya: "run T-03". Claimed as `2026-09-15-s5/T-03/executor/1`.
- `docs/export-format.md` written. Validation 1 → `4`, exit 0. Raw `verification-records/2026-09-15-s5_T-03_v1_20260915T173340Z.md`.
- Report written with its receipt; board T-03 Complete; finish row (success).

### Decisions
- none.

### Blockers / open questions
- none new.

### Next
- T-04.

### State snapshot
- Task state: T-01 to T-03 Complete; T-04 Ready to run; T-05 Draft.
- Active obligations: Priya's badge colour request (T-02 receipt), parked.

## 2026-09-17 · session 6 · T-04

### Did
- Priya: "run T-04". Claimed as `2026-09-17-s6/T-04/executor/1`.
- `export/__main__.py` written. Validation 1 → exit 0. Raw `verification-records/2026-09-17-s6_T-04_v1_20260917T182455Z.md`.
- Report written with its receipt; board T-04 Complete; finish row (success). T-05 set Ready to run.

### Decisions
- none.

### Blockers / open questions
- none new.

### Next
- T-05.

### State snapshot
- Task state: T-01 to T-04 Complete; T-05 Ready to run.
- Active obligations: Priya's badge colour request (T-02 receipt), parked.
