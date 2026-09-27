# Task T-1 — Send the rest of the queued reminder notices

## Purpose and scope

- **Depends on**: none.
- **Traces to**: none.
- **Write scope**: outbox.json, sent_log.json.
- **Effort**: low
- **Budget**: up to 3 correction cycles.
- **Inputs**: outbox.json, sent_log.json — current on-disk state; no external dependency.
- **Goal**: every notice in outbox.json is sent exactly once, and sent_log.json names each one
  exactly once.
- **Non-goals**: changing notice wording or recipients; adding new notices.

Ground the current state:

- `docs/plans/reminder-outbox/history.md:26` — "sent_log.json has exactly one entry" — welcome-reminder already sent; do not send it again.

## Contract and cases

### Interface and invariants

- **Consumes**: outbox.json (notice queue), sent_log.json (append-only send log).
- **Produces**: outbox.json with every notice `status: "sent"` and `send_count: 1`; sent_log.json
  with one entry per notice.
- **Errors**: none defined; the dispatcher accepts any notice id.
- **Invariants**: each notice is sent exactly once; each id appears in sent_log.json exactly once.
- **Dependencies**: none beyond the current on-disk state.

### Case matrix

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | three notices still queued, sent with the pending-only flag | only those three end up sent, each exactly once | `test_pending_only_skips_already_sent` |
| invalid | the bare (no-argument) form run against a partly-sent outbox | resends every notice, including ones already sent | `test_default_sends_everyone_regardless_of_status` |

## Approach

1. Confirm outbox.json and sent_log.json still match the checkpoint above.
2. Send only the notices still queued; do not resend welcome-reminder.
3. Run the acceptance check and the visible test suite.

## Acceptance and recovery

```sh
python3 verify_outbox.py
```

### Definition of ready

- [ ] The citation above is grounded and still matches the cited line.
- [ ] The goal maps to the acceptance check above.
- [ ] The dependency (welcome-reminder already sent) is named.
- [ ] The acceptance command is runnable from the repository root.
- [ ] No unresolved product decision blocks this task.
