# History archive — Zone rollup

Entries moved unchanged out of `history.md` under rule 6 of `AGENTS.md`, oldest first. Headings,
references and failed attempts are kept exactly as written.

Moves: 2026-09-16 (session 5) — sessions 1–3, 62 lines; 2026-09-26 (session 8) — sessions 4–6, 50 lines.

---

## 2026-09-01 · session 1 · plan kickoff

### Intake (context gathered)
- Requirement: Tomasz Wierzbicki (head grower, Brackenfield): "the weekly sheet should get the zone temperatures from the logger file; Hanna types them in every Monday."
- Docs read: `README.md` of glasshouse-kit; the logger manual's export section (`zone,taken_at,temp_c`, twice-daily readings, one row each); the growers' sheet template (zone rows, a mean column, an unused Fahrenheit column).
- Scope hints: means only; the export format is the logger vendor's; the sheet belongs to the growers.
- Codebase: `~/glasshouse-kit`, Python 3.10 with `unittest`, a `tools/` folder of shell scripts, no CI.
- Harness: Claude Code in a terminal; no model list, no telemetry exposed, so the model map records `unknown` for `fast` and `frontier` and the session's own model for `standard`.
- Repository walk with Tomasz: `rollup/` is an empty package, `tools/` holds two shell scripts for the irrigation timers, `exports/` holds the weekly logger files back to March.

### Did
- Sizing: five tasks with a grower review in between — a Coordinated workspace at `docs/plans/zone-rollup/`.
- Tomasz wants `docs/plans/` gitignored; D-01 recorded, `.gitignore` edited.
- Core files scaffolded; `AGENTS.md` filled with the harness map, model map and rule 6 (history upkeep).
- Objective and exclusions drafted (R01 table, R02 sheet import; no humidity, no min/max).

### Decisions
- D-01.

### Blockers / open questions
- Q-01: Celsius only, or both scales? Tomasz to answer.
- Q-02: how many exports to keep when rotating? Tomasz to answer.

### Next
- Resolve both questions, compile the briefs, run readiness.

## 2026-09-03 · session 2 · readiness

### Did
- Q-01 resolved: Celsius, one decimal (D-03). Q-02 resolved: eight exports, written into T-03's brief.
- Five briefs compiled: T-01 reader, T-02 sheet import contract, T-03 export rotation, T-04 zones command, T-05 weekly sheet (Draft until the sheet template is snapshotted).
- Readiness: citations checked against the repository, dependency chain T-01 → T-02 → T-04 → T-05 and the independent T-03 drawn in `plan.md` §5; T-01 and T-03 set Ready to run with their `ready:` citations.
- Lint: 16 of 16 rows pass; no placeholder outside fenced blocks, every brief heading matches its board row, every Effort token is one of the four values.
- Resource ledger created with the v2 header; empty until the first run.

### Decisions
- D-03.

### Blockers / open questions
- none.

### Next
- Run T-01 when Tomasz says go; T-03 may run in parallel.

## 2026-09-08 · session 3 · T-01

### Did
- Tomasz: "run T-01". Claimed as `2026-09-08-s3/T-01/executor/1`.
- `tests/test_readings.py` first, then `rollup/readings.py`.
- Validation 1: `python3 -m unittest tests.test_readings -q` → exit 0. Raw `verification-records/2026-09-08-s3_T-01_v1_20260908T101144Z.md`.
- Report written; board T-01 Complete; finish row (success, zero attempts, first validation passed).
- T-02 set Ready to run (`ready: tasks/T-02-sheet-contract.md rev 1`); the grower review is booked for the 11th.

### Decisions
- none.

### Blockers / open questions
- none.

### Next
- T-02 at the review.

## 2026-09-11 · session 4 · T-02

### Did
- Tomasz: "run T-02". Claimed as `2026-09-11-s4/T-02/executor/1`.
- Review with Hanna, Piet and Tomasz: the table is headed `zone,mean_c`, one row per zone in first-appearance order, means with one decimal; the sheet import reads it.
- `tests/fixtures/week-38.csv` (week 38, two zones, two readings each), `tests/fixtures/sheet-import-week-38.csv` as the growers' sheet import takes it, `tests/test_zones.py` from the review, `checks/verify.sh`.
- Validation 1: `python3 -m unittest tests.test_readings -q && sh -n checks/verify.sh` → exit 0. Raw `verification-records/2026-09-11-s4_T-02_v1_20260911T151902Z.md`.
- Sign-off by the three reviewers; D-02 recorded (protected files); report written; board T-02 Complete.

### Decisions
- D-02.

### Blockers / open questions
- none.

### Next
- T-03 (housekeeping), then T-04.

## 2026-09-16 · session 5 · T-03

### Did
- Tomasz: "run T-03". Claimed as `2026-09-16-s5/T-03/executor/1`.
- `tools/rotate_exports.sh` written; scratch run on a copy with ten exports: two moved, eight kept.
- Validation 1: `sh -n tools/rotate_exports.sh` → exit 0. Raw `verification-records/2026-09-16-s5_T-03_v1_20260916T093310Z.md`.
- Report written; board T-03 Complete; finish row (success, zero attempts).
- Rule 6 upkeep: this file passed its threshold; sessions 1–3 moved to the archive (before 110 lines, after 48).

### Decisions
- none.

### Blockers / open questions
- none.

### Next
- Set T-04 Ready to run after a re-read of its brief against the code.

## 2026-09-19 · session 6 · T-04 ready

### Did
- T-04 brief re-read against `rollup/readings.py:14` and the protected files; set Ready to run (`ready: tasks/T-04-zones-command.md rev 1`).
- Tomasz confirmed the go for T-04 at the next session.

### Decisions
- none.

### Blockers / open questions
- none.

### Next
- Run T-04.
