# PLAN and RUN contract checks

Development-only checks of the PLAN and RUN contracts; they are not numbered scenarios and measure no
executor. Run them from the repository root with Python 3.10+:

```sh
python3 -m unittest discover -s eval/plan-run/tests -p 'test_*.py' -v
```

- `tests/test_plan.py` checks that the plan template keeps the section order its consumers read.
- `tests/test_run.py` checks that the RUN card holds one state machine with an integrated close bar, and that
  the templates bind to RUN without competing loops.
- `tests/test_migration.py` checks the copy-first migration contract, with byte-preserved history and a
  rollback sentinel, and the retirement of the old action names.
- The task-contract template and lint-row checks this family used to hold now run on current fixtures, in
  `eval/templates/` and `eval/lint/rows/`.

`results/p06-integrated-acceptance.json` keeps the integrated-acceptance record of the original PLAN and RUN
rewrite. The synthetic measurement that rewrite prepared, never started, was removed with its harness and
fixtures; git history keeps them.
