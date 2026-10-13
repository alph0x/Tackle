# Task T-02 — Remaining requests

- **Depends on**: T-01 (`PLAN_LIMITS`, `api/limits.py:3`).
- **Repository**: api.
- **Write scope**: `api/quota.py`; this workspace's board, history, resource usage and
  `reports/T-02-report.md`.
- **Autonomy**: L2. **Budget**: 3 correction cycles.
- **Goal**: `remaining_requests(plan, used_today)` in `api/quota.py` returns the plan's daily limit
  from `PLAN_LIMITS` minus `used_today`, never below 0, and raises `KeyError` for an unknown plan.
- **Non-goals**: `api/tests/`, `api/limits.py`.
- **Inputs**: `api/quota.py:6` (`remaining_requests` raises `NotImplementedError`); `api/limits.py:3`.

## Case matrix

| Case | Input | Expected | Check |
|---|---|---|---|
| fresh day | free, 0 | 100 | test_remaining.py |
| partly used | pro, 2500 | 7500 | test_remaining.py |
| over the limit | free, 150 | 0 | test_remaining.py |
| unknown plan | "gold", 1 | KeyError | test_remaining.py |

## Acceptance

`api/tests/test_remaining.py` is sealed at Ready (D-01) and fails until the change is made.

```sh
python3 -m unittest discover -s api/tests
```
