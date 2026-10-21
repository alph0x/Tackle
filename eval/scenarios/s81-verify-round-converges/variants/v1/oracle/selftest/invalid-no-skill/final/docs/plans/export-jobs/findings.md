# Findings — export-jobs

| Finding | Round | Severity | Task | Evidence | State | Reference |
|---|---|---|---|---|---|---|
| F-0001 | 1 | HIGH | T-0701 | the T-0701 brief named `tests/test_run.py` in its acceptance command; its Write scope creates `tests/test_runner.py` | fixed | history, session 2 (brief diff) |
| F-0002 | 1 | MEDIUM | T-0701 | lint row 4: `tasks/T-0701-export-runner.md:17 stale: src/export/queue.py:41` | open | — |
| F-0003 | 1 | MEDIUM | T-0702 | `RETENTION_DAYS` is undecided in the T-0702 brief and its boundary case has no expected value | open | Q-0702 |
