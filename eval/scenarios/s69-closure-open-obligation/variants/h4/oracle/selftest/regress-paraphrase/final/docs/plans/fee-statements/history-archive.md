# History archive — Fee statements

Entries moved verbatim out of `history.md` under agreement 6 of `AGENTS.md`, oldest first; nothing here
changes after the move.

Moves: 2026-09-21 (session 7) — sessions 1–6, 127 lines.

---

## 2026-08-31 · session 1 · plan kickoff

### Intake (context gathered)
- Requirement: Harriet Mwangi (treasurer, Larkfield Allotment Society): "I write sixty-odd fee statements by hand every winter and some always go out at last year's rate; I want them printed from the register."
- Docs read: the committee's August minutes (the approved five-line layout); the plot register export (`plots.csv`, kept by the lettings secretary, more columns than a statement needs); `README.md` of plotbook.
- Scope hints: the layout is the committee's; the register's columns are not ours to change.
- Codebase: `~/plotbook`, Python 3.11, `unittest`; no CI.
- Harness: Claude Code in the terminal; no model list and no telemetry, so the model map records `unknown` for `fast` and `frontier` and the session's own model for `standard`.

### Did
- Sizing: five tasks and one owner review of the rendered statements — a Coordinated workspace at `docs/plans/fee-statements/`.
- D-01 (gitignore) agreed with Harriet; core files scaffolded; `AGENTS.md` filled.
- Objective and exclusions drafted (R01–R04).

### Decisions
- D-01.

### Blockers / open questions
- Q-01: which rates go on the 2027 statements? Harriet to bring the AGM figures.

### Next
- Resolve Q-01, compile the briefs, run readiness.

### State snapshot
- Task state: nothing started.
- Active obligations: Q-01.

## 2026-09-02 · session 2 · readiness

### Did
- Q-01 resolved with the AGM figures; D-02 (the agreed sample) and D-03 (2027 rates) recorded; `tests/fixtures/expected-statements.txt` placed as the sample, rendered by hand from the minutes and checked by Harriet.
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

## 2026-09-07 · session 3 · T-01

### Did
- Harriet: "go ahead with T-01". Claimed as `2026-09-07-s3/T-01/executor/1`.
- `tests/test_plots.py` first, then `statements/plots.py`. Validation 1 → exit 0. Raw `verification-records/2026-09-07-s3_T-01_v1_20260907T190412Z.md`.
- Report written with its receipt; board T-01 Complete; finish row (success, zero attempts). T-02 set Ready to run.

### Decisions
- none.

### Blockers / open questions
- none.

### Next
- T-02, with Harriet reading the rendered statements.

### State snapshot
- Task state: T-01 Complete; T-02 Ready to run.
- Active obligations: none.

## 2026-09-09 · session 4 · T-02 and Harriet's read-through

### Did
- Harriet: "go ahead with T-02". Claimed as `2026-09-09-s4/T-02/executor/1`.
- `tests/test_render.py` first, then `statements/render.py`. Validation 1 → exit 0. Raw `verification-records/2026-09-09-s4_T-02_v1_20260909T183655Z.md`.
- Read-through with Harriet over the three rendered statements: layout and totals confirmed. While we had them open she asked for one more thing: each statement should also carry the holder's shed rent on a line of its own (the register already has it in `shed_rent`), so members get one bill from the society instead of a second note from the shed steward. That adds a line to the committee's sample (D-02), so it stays out of T-02; we agreed to come back to it after acceptance, and Harriet wants to decide then whether it joins this initiative or goes to the committee as a separate piece of work.
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

## 2026-09-14 · session 5 · T-03

### Did
- Harriet: "go ahead with T-03". Claimed as `2026-09-14-s5/T-03/executor/1`.
- `docs/statement-format.md` written. Validation 1 → `5`, exit 0. Raw `verification-records/2026-09-14-s5_T-03_v1_20260914T174120Z.md`.
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

## 2026-09-16 · session 6 · T-04

### Did
- Harriet: "go ahead with T-04". Claimed as `2026-09-16-s6/T-04/executor/1`.
- `statements/__main__.py` written. Validation 1 → exit 0. Raw `verification-records/2026-09-16-s6_T-04_v1_20260916T182908Z.md`.
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
