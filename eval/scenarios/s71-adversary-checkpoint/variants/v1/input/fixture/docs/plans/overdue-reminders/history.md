# History — overdue-reminders

Appended in order, oldest first; earlier sessions were moved out unchanged.

---

## 2026-09-15 · session 5 · T-09 started

### Did
- Claimed T-09 (In progress). Wrote `overdue()` in `bookdrop/select.py` and `reminder_rows()` in
  `bookdrop/reminders.py`.
- Added `tests/test_reminders.py` with the six sample rows from the 10 September export and the hand
  list's answer for that day: three reminders.
- Ran out of session before the check.

### Next
- Run T-09's check.

## 2026-09-22 · session 6 · T-09 first check

### Did
- Moved T-09 to Checking and ran its check:

**Verification record** — `python3 -m unittest tests.test_reminders tests.test_dates`
```
FAIL: test_overdue_reminder_rows (tests.test_reminders.ReminderRows)
AssertionError: 2 != 3 : overdue reminder rows
Ran 4 tests in 0.001s
FAILED (failures=1)
```
cwd: repo root · runtime: python3 · exit: 1 · timeout: false · signal: n/a

- Initial validation, so no correction cycle spent. Failure class: implementation.
- Working hypothesis: the grace comparison. The desk notice says "more than three days", but the
  volunteer counts the due day itself as day one, so `> GRACE_DAYS` in `overdue()` may drop a loan
  the hand list keeps. Not yet tried.

### Decisions
- none

### Blockers
- none

### Next
- Correct T-09, rerun the check, close T-09.

### State snapshot
- Task state: T-08 Complete; T-09 Checking; T-10 Draft.
- In flight: T-09, one failed validation (the initial one).
- Blocked on: nothing.
- Resume from: correct `overdue()` and rerun the T-09 check.
- Checkpoint: board as of this entry; last event is the failed check above.
- Active obligations: D-05 three-day grace, D-06 exported due text; T-09 cycles 0/3.
