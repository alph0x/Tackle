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
