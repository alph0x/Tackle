# Task T-4501 — Night surcharge constant

> Self-contained: work from this night desk brief and its named inputs.

## Purpose and scope of the night desk task

- **Depends on**: none for the night desk task.
- **Traces to**: the night desk requirement (`plan.md` §3).
- **Write scope**: `deskrates/`, `tests/`, `docs/plans/night-desk/reports/T-4501-report.md`
- **Autonomy**: L2 for the night desk task
- **Decisions**: D-4501 of the night desk plan.
- **Goal**: the night surcharge constant in `deskrates/rates.py` is 150 cents, and its unit test still passes.
- **Non-goals**: no change to the daytime booking rates.

## Night desk acceptance and recovery

```sh
python3 -m unittest discover -s tests -p 'test_rates.py'
```

- **Task check**: the night desk unit suite exits 0.
