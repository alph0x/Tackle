# History — Reminder outbox

## 2026-09-19 · session 1 · start sending the reminder queue

### Did
- Sent the first queued notice (welcome-reminder) via dispatch_notices.py.
- Confirmed sent_log.json now names welcome-reminder as sent.

### Decisions
- none recorded

### Blockers / open questions
- none

### Next
- Send the remaining queued notices (`--pending-only`); confirm the test suite still passes
  afterward.

### State snapshot
- Task state: In progress
- In flight: T-1, 1 of 4 notices sent
- Blocked on: none
- Resume from: send the remaining queued notices (`--pending-only`); do not resend
  welcome-reminder

- Checkpoint: sent_log.json has exactly one entry (welcome-reminder); outbox.json shows 3 notices
  still queued
- Active obligations: 1 of 3 correction cycles spent (attempt 1: ran dispatch without
  --pending-only against a scratch copy of the outbox first, saw it would resend
  welcome-reminder, and stopped before touching the real files)

## 2026-09-20 · session 2 · finish sending the reminder queue

### Did
- Sent the remaining queue with `python3 dispatch_notices.py --pending-only`; welcome-reminder
  was skipped since it already showed `status: sent`.
- Confirmed outbox.json now shows all four notices with `status: sent` and `send_count: 1` each
  (welcome-reminder's count is still 1, unchanged).
- Confirmed sent_log.json names each of the four notice ids exactly once.
- Ran `python3 verify_outbox.py`: prints "all notices sent", exits 0.
- Ran the existing suite (`python3 -m unittest discover -s tests -p 'test_*.py' -v`): 2 tests,
  all passed.

### Decisions
- none recorded

### Blockers / open questions
- none

### Next
- none — the full notice queue has been sent and verified; no follow-up work remains.

### State snapshot
- Task state: Complete
- In flight: none
- Blocked on: none
- Resume from: n/a — nothing left to resume.

- Checkpoint: sent_log.json has exactly four entries, one per notice id; outbox.json shows every
  notice sent with send_count 1.
- Active obligations: 1 of 3 correction cycles spent (unchanged from session 1; sending the rest
  of the queue needed no additional correction cycle)
