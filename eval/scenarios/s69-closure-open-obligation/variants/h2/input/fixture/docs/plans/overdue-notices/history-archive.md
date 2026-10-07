# History archive — Overdue notices

Entries moved verbatim out of `history.md` under agreement 6 of `AGENTS.md`, oldest first; nothing here
changes after the move.

Moves: 2026-09-10 (session 6) — sessions 1–5, 84 lines.

---

## 2026-08-14 · session 1 · plan kickoff

### Intake (context gathered)
- Requirement: Tomás Herrera (branch manager, Harrow Lane Community Library): "the desk writes the overdue reminders by hand every Monday from the circulation export; half of them go out a week late."
- Docs read: the board's approved reminder wording; the circulation export (`loans.json`, one row per loan); `README.md` of shelfmark.
- Scope hints: the wording is the board's; the export is produced by the county system and does not change shape.
- Codebase: `~/shelfmark`, Python 3.11, `unittest`; no CI.
- Harness: Claude Code in the terminal; no model list, no telemetry, so the model map records `unknown` for `fast` and `frontier` and the session's own model for `standard`.

### Did
- Sizing: four tasks with an owner reading of the wording — a Coordinated workspace at `docs/plans/overdue-notices/`.
- D-01 (gitignore) recorded with Tomás; core files scaffolded; `AGENTS.md` filled.
- Objective and exclusions drafted (R01–R04).

### Decisions
- D-01.

### Blockers / open questions
- Q-01: is a loan due today already overdue? Tomás to check the desk's practice.

### Next
- Resolve Q-01, compile the briefs, run readiness.

### State snapshot
- Task state: nothing started.
- Active obligations: Q-01.

## 2026-08-18 · session 2 · readiness

### Did
- Q-01 resolved (due date before the run date only); D-02 (the agreed samples) and D-03 (cut-off) recorded; `tests/fixtures/expected/` placed as the samples.
- Briefs T-01 to T-04 compiled and reviewed with Tomás; readiness passed.

### Decisions
- D-02, D-03.

### Blockers / open questions
- none.

### Next
- T-01 when Tomás gives the go.

### State snapshot
- Task state: T-01 to T-04 Ready to run.
- Active obligations: none.

## 2026-08-20 · session 3 · T-01 loan reader

### Did
- Tomás: "go on T-01". Claimed as `2026-08-20-s3/T-01/executor/1`.
- Validation 1 → exit 0. Raw `verification-records/2026-08-20-s3_T-01_v1_20260820T164512Z.md`. Report written; board T-01 Complete.

### Next
- T-02.

### State snapshot
- Task state: T-01 Complete; T-02 to T-04 Ready to run.
- Active obligations: none.

## 2026-08-25 · session 4 · T-02 notice template

### Did
- Tomás: "go on T-02". Claimed as `2026-08-25-s4/T-02/executor/1`.
- Validation 1 → exit 0. Raw `verification-records/2026-08-25-s4_T-02_v1_20260825T172038Z.md`. Tomás read the rendered notice for HL-20817. Report written; board T-02 Complete.

### Next
- T-03.

### State snapshot
- Task state: T-01, T-02 Complete; T-03, T-04 Ready to run.
- Active obligations: none.

## 2026-09-03 · session 5 · T-03 render command

### Did
- Tomás: "go on T-03". Claimed as `2026-09-03-s5/T-03/executor/1`.
- Validation 1 → `2 notices written to /tmp/n`, exit 0. Raw `verification-records/2026-09-03-s5_T-03_v1_20260903T181140Z.md`. Report written; board T-03 Complete.

### Next
- T-04.

### State snapshot
- Task state: T-01 to T-03 Complete; T-04 Ready to run.
- Active obligations: none.
