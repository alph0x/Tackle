# History archive — Price notice

Entries moved verbatim out of `history.md` under rule 6 of `AGENTS.md`, oldest first; nothing here
changes after the move.

Moves: 2026-09-29 (session 7) — sessions 1–5, 90 lines.

---

## 2026-09-10 · session 1 · plan kickoff

### Intake (context gathered)
- Requirement: Oluwaseun Adeyemi (office coordinator, Alder Valley growers' cooperative): "every member gets one notice about the 6 October price-list cutover, worded as the committee approves it, sent through the relay like the harvest schedule was."
- Docs read: `README.md` of coop-relay; `tools/dispatch_notice.py` (next-number rendering into `outbox/`); `tools/outbox_check.sh`; the two outbox files of August and September; the relay maintainer's note (mails every outbox file within the hour, keeps the file).
- Scope hints: one notice; the wording is the committee's; the member list is refreshed from the register first; a dispatch cannot be recalled.
- Codebase: `~/coop-relay`, one Python tool, one shell check, text files; no tests, no CI; git shared with the relay's maintainer.
- Harness: Claude Code in the terminal; no model list, no telemetry, so the model map records `unknown` for `fast` and `frontier` and the session's own model for `standard`.
- Repository walk with Oluwaseun: `notices/` empty, `outbox/` with the two files of the summer, `tools/` with the dispatch tool and the check written by Grace in 2025.

### Did
- Sizing: six tasks with two owner actions (approval, go) and one irreversible dispatch — a Coordinated workspace at `docs/plans/price-notice/`.
- D-01 (gitignore) and D-02 (outbox written by the tool only) recorded with Oluwaseun.
- Core files scaffolded; `AGENTS.md` filled; objective and exclusions drafted (R01–R04).

### Decisions
- D-01, D-02.

### Blockers / open questions
- Q-01: mention the summer prices for earlier bookings? For the committee.

### Next
- Compile the briefs, run readiness.

## 2026-09-12 · session 2 · readiness

### Did
- Six briefs compiled: T-01 draft, T-02 member list, T-03 relay dry run, T-04 approval, T-05 dispatch, T-06 archive. T-05's steps written out in order, with the tool's confirmation line recorded right after the dispatch.
- Readiness: citations checked against the tool and the outbox; the graph in `plan.md` §5 (T-01 → T-04 → T-05 → T-06, with T-02 and T-03 feeding T-05); T-01, T-02 and T-03 set Ready to run with their `ready:` citations.
- Lint: 16 of 16 rows pass; no placeholder outside fenced blocks, every brief heading matches its board row, every Effort token valid. Ledger created with the v2 header.
- Readiness note for T-05: the dispatch is the only irreversible step, so its brief lists the steps in order and asks for the tool's confirmation line to be recorded before anything else happens.

### Decisions
- none.

### Blockers / open questions
- Q-01 open (for the committee; does not block the draft).

### Next
- Run T-01; T-02 and T-03 can run in the following sessions.

## 2026-09-17 · session 3 · T-01

### Did
- Oluwaseun: "run T-01". Claimed as `2026-09-17-s3/T-01/executor/1`.
- `notices/2026-10-cutover.md` drafted from the minutes with the header block.
- Validation 1: the notice-id grep → exit 0. Raw `verification-records/2026-09-17-s3_T-01_v1_20260917T104409Z.md`.
- Report written; board T-01 Complete; finish row (success, zero attempts, first validation passed).

### Decisions
- none.

### Blockers / open questions
- Q-01 for the committee on the 26th.

### Next
- T-02.

## 2026-09-19 · session 4 · T-02

### Did
- Oluwaseun: "run T-02". Claimed as `2026-09-19-s4/T-02/executor/1`.
- Relay list refreshed from the register (212 members; three leavers, five joiners); office comparison recorded with both counts and the register date.
- Report written; board T-02 Complete; finish row (success).

### Decisions
- none.

### Blockers / open questions
- none.

### Next
- T-03 with the relay maintainer.

## 2026-09-23 · session 5 · T-03

### Did
- Oluwaseun: "run T-03". Claimed as `2026-09-23-s5/T-03/executor/1`.
- Test file in the relay's test outbox at 09:12; received at 09:47; Grace Ellery confirmed.
- Report written; board T-03 Complete; finish row (success).
- T-04 set Ready to run (`ready: tasks/T-04-wording-approval.md rev 1`) for the committee meeting on the 26th.

### Decisions
- none.

### Blockers / open questions
- none.

### Next
- T-04 at the committee meeting.
