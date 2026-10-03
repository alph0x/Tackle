# T-04 report — Post the true-up (draft)

Executor's working report; the coordinator closes it at a terminal state.

## Authorization and preflight
- Run `2026-09-27-s7/T-04/executor/1`, authorized by Rhiannon ("run T-04", 2026-09-27). Procedure pinned: Tackle 9.0.1 RUN card. Brief `tasks/T-04-post-true-up.md` rev 1.
- Board hash recorded at claim; dependency outputs present: `reports/T-02-report.md` §Result, `memos/2026-09-22-q3-true-up.md`.
- INTENT: the journal has no Q3 true-up row for ACC-1042; the check expects `python3 tools/check_adjustment.py ACC-1042 "Q3 true-up"` to exit 0; the brief says to post 150.00 once, dated the day of posting.

## Step 1 — amount confirmed
- 150.00 per `reports/T-02-report.md` §Result and the memo's second paragraph; memo text `Q3 true-up`; account `ACC-1042` (Nakamura, plot 27).

## Step 2 — posting
- Already done before this run: the journal holds `2026-09-27,ACC-1042,150.00,Q3 true-up,2026-09-27T09:41:12Z`, written by run `2026-09-27-s7/T-04/executor/1` after its last recorded write. Observed on resume, recorded here; not posted again.

## Step 3 — check
- `python3 tools/check_adjustment.py ACC-1042 "Q3 true-up"` → `check: found 1 row(s) for ACC-1042 / Q3 true-up`, exit 0. Raw: `verification-records/2026-09-28-s8_T-04_v1_20260928T081630Z.md`.

## Final status
- Complete. Method: command; the posting observed, not repeated.

Receipt — done: the true-up is in the journal once, checked. Remaining: nothing for this task. Next step: T-05 (Rhiannon authorizes).
