# Findings — digest-mailer

| Finding | Round | Severity | Task | Evidence | State | Reference |
|---|---|---|---|---|---|---|
| F-4101 | 1 | HIGH | T-2301 | the T-2301 brief named `tests/test_send.py` in its acceptance command; its Write scope creates `tests/test_sender.py` | fixed | history, session 2 (brief diff) |
| F-4102 | 1 | MEDIUM | T-2301 | lint row 4: `tasks/T-2301-digest-sender.md:17 stale: src/digest/outbox.py:36` | open | — |
| F-4103 | 1 | MEDIUM | T-2302 | `BOUNCE_HOLD_DAYS` is undecided in the T-2302 brief and its boundary case has no expected value | open | Q-2302 |
