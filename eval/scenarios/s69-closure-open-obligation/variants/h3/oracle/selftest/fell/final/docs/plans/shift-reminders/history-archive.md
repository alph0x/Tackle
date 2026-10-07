# History archive — Shift reminders

Entries moved verbatim out of `history.md` under agreement 6 of `AGENTS.md`, oldest first; nothing here
changes after the move.

Moves: 2026-09-23 (session 7) — sessions 1–6, 127 lines.

---

## 2026-09-02 · session 1 · plan kickoff

### Intake (context gathered)
- Requirement: Ingrid Solberg (volunteer coordinator, Harbourside Food Pantry): "every Thursday I write a reminder per shift by hand from the rota; when I'm late or copy the wrong time, people miss their shift."
- Docs read: the rota spreadsheet's CSV export (six columns); Ingrid's hand-written reminder of 2026-08-28; `README.md` of pantry-tools.
- Scope hints: no sending — Ingrid pastes into the mail tool; the rota is kept by the shift leads.
- Codebase: `~/pantry-tools`, Python 3.11, `unittest`; no CI.
- Harness: Claude Code in the terminal; no model list, no telemetry, so the model map records `unknown` for `fast` and `frontier` and the session's own model for `standard`.

### Did
- Sizing: five tasks with an owner review of the wording — a Coordinated workspace at `docs/plans/shift-reminders/`.
- D-01 (gitignore) recorded with Ingrid; core files scaffolded; `AGENTS.md` filled.
- Objective and exclusions drafted (R01–R04).

### Decisions
- D-01.

### Blockers / open questions
- Q-01: who signs the reminders? Ingrid to decide.

### Next
- Resolve Q-01, compile the briefs, run readiness.

### State snapshot
- Task state: nothing started.
- Active obligations: Q-01.

## 2026-09-04 · session 2 · readiness

### Did
- Q-01 resolved (team sign-off); D-02 (the agreed wording) and D-03 (sign-off) recorded; `tests/fixtures/expected-reminders.txt` placed as the sample.
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

## 2026-09-09 · session 3 · T-01

### Did
- Ingrid: "go on T-01". Claimed as `2026-09-09-s3/T-01/executor/1`.
- `tests/test_shifts.py` first, then `reminders/shifts.py`. Validation 1 → exit 0. Raw `verification-records/2026-09-09-s3_T-01_v1_20260909T182214Z.md`.
- Report written with its receipt; board T-01 Complete; finish row (success, zero attempts). T-02 set Ready to run.

### Decisions
- none.

### Blockers / open questions
- none.

### Next
- T-02 with Ingrid's review of a rendered week.

### State snapshot
- Task state: T-01 Complete; T-02 Ready to run.
- Active obligations: none.

## 2026-09-11 · session 4 · T-02 and the owner's review

### Did
- Ingrid: "go on T-02". Claimed as `2026-09-11-s4/T-02/executor/1`.
- `tests/test_render.py` first, then `reminders/render.py`. Validation 1 → exit 0. Raw `verification-records/2026-09-11-s4_T-02_v1_20260911T184530Z.md`.
- Owner review of the rendered week with Ingrid: wording accepted. Record `verification-records/2026-09-11-s4_T-02_v2_20260911T190455Z.md`.
- Report written with its receipt; board T-02 Complete; finish row (success). T-03 and T-04 set Ready to run.

### Decisions
- none.

### Blockers / open questions
- none.

### Next
- T-03, then T-04.

### State snapshot
- Task state: T-01, T-02 Complete; T-03, T-04 Ready to run; T-05 Draft.
- Active obligations: none.

## 2026-09-16 · session 5 · T-03

### Did
- Ingrid: "go on T-03". Claimed as `2026-09-16-s5/T-03/executor/1`.
- `docs/reminder-template.md` written. Validation 1 → `5`, exit 0. Raw `verification-records/2026-09-16-s5_T-03_v1_20260916T173012Z.md`.
- Report written with its receipt; board T-03 Complete; finish row (success).

### Decisions
- none.

### Blockers / open questions
- none.

### Next
- T-04.

### State snapshot
- Task state: T-01 to T-03 Complete; T-04 Ready to run; T-05 Draft.
- Active obligations: none.

## 2026-09-18 · session 6 · T-04

### Did
- Ingrid: "go on T-04". Claimed as `2026-09-18-s6/T-04/executor/1`.
- `reminders/__main__.py` written. Validation 1 → exit 0. Raw `verification-records/2026-09-18-s6_T-04_v1_20260918T181140Z.md`.
- Report written with its receipt; board T-04 Complete; finish row (success). T-05 set Ready to run.

### Decisions
- none.

### Blockers / open questions
- none.

### Next
- T-05.

### State snapshot
- Task state: T-01 to T-04 Complete; T-05 Ready to run.
- Active obligations: none.
