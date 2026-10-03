# History archive — Q3 adjustments

Entries moved verbatim out of `history.md` under agreement 6 of `AGENTS.md`, oldest first; nothing here
changes after the move.

Moves: 2026-09-26 (session 6) — sessions 1–4, 75 lines.

---

## 2026-09-02 · session 1 · plan kickoff

### Intake (context gathered)
- Requirement: Rhiannon Vale (treasurer, Fernhill allotment society): "close Q3's corrections the way we did Q2: reconcile, compute the true-up, get it approved at the committee call, post it, and put it in the close report."
- Docs read: `README.md` of books; the Q2 close report; `data/adjustments.csv` (three rows, header `posted_on,account,amount,memo,posted_at`); `tools/post_adjustment.py` and `tools/check_adjustment.py`.
- Scope hints: one true-up expected (plot 27's water levy, flagged by the member in August); the journal is append-only and read by the auditor as posted; postings are irreversible and a wrong one needs a reversing adjustment approved by the committee.
- Codebase: `~/books`, two Python scripts and CSV data; no tests, no CI; git shared with the committee.
- Harness: Claude Code in the terminal; no model list, no telemetry, so the model map records `unknown` for `fast` and `frontier` and the session's own model for `standard`.
- Repository walk with Rhiannon: `data/accounts.csv` (four member accounts), the journal with the Q2 rows, `tools/` with the two scripts the previous treasurer wrote in 2024; the auditor's note that the journal is read as posted.

### Did
- Sizing: five tasks with two owner actions (review, approval) and one irreversible posting — a Coordinated workspace at `docs/plans/q3-adjustments/`.
- D-01 (gitignore) and D-02 (the journal is written by the tool only) recorded with Rhiannon.
- Core files scaffolded; `AGENTS.md` filled; objective and exclusions drafted (R01–R04).

### Decisions
- D-01, D-02.

### Blockers / open questions
- Q-01: which rate applies to plot 27's water levy? Rhiannon to check the rate cards.

### Next
- Compile the briefs, run readiness.

## 2026-09-04 · session 2 · readiness

### Did
- Five briefs compiled: T-01 reconcile, T-02 compute, T-03 approval memo, T-04 post, T-05 close report. T-04's steps written out in order, with the confirmation line recorded right after the posting.
- Readiness: citations checked against the tools and the journal; the chain T-01 → T-02 → T-03 → T-04 → T-05 in `plan.md` §5; T-01 set Ready to run (`ready: tasks/T-01-reconcile.md rev 1`).
- Lint: 16 of 16 rows pass; no placeholder outside fenced blocks, every brief heading matches its board row, every Effort token valid. Ledger created with the v2 header.
- Readiness note for T-04: the posting is the only irreversible step of the initiative, so its brief lists the steps in order and asks for the confirmation line to be recorded before anything else happens.

### Decisions
- none.

### Blockers / open questions
- Q-01 open (does not block T-01).

### Next
- Run T-01 with the statements.

## 2026-09-09 · session 3 · T-01

### Did
- Rhiannon: "run T-01". Claimed as `2026-09-09-s3/T-01/executor/1`.
- Reconciliation sheet built from the statements and `data/accounts.csv`: one difference, ACC-1042 short by 150.00 (water levy at the 2025 rate); the other three accounts match to the penny.
- Statements filed under the treasurer's folder with the sheet; nothing posted.
- Rhiannon reviewed the sheet in session; report written; board T-01 Complete; finish row (success, zero attempts, observed: no correction).
- T-02 set Ready to run (`ready: tasks/T-02-compute-true-up.md rev 1`).

### Decisions
- none.

### Blockers / open questions
- Q-01 to be resolved with the rate cards in T-02.

### Next
- T-02.

## 2026-09-15 · session 4 · T-02

### Did
- Rhiannon: "run T-02". Claimed as `2026-09-15-s4/T-02/executor/1`.
- Rate cards compared: 230.00 (2026) against 180.00 (2025) per quarter; difference 150.00 for the one quarter billed at the old rate. Q-01 resolved; D-03 recorded with the arithmetic.
- Rhiannon reviewed the arithmetic; report written; board T-02 Complete; finish row (success, zero attempts).
- T-03 set Ready to run (`ready: tasks/T-03-approval-memo.md rev 1`); the committee call is on the 22nd.

### Decisions
- D-03: 150.00, memo `Q3 true-up`.

### Blockers / open questions
- none.

### Next
- T-03 at the committee call.
