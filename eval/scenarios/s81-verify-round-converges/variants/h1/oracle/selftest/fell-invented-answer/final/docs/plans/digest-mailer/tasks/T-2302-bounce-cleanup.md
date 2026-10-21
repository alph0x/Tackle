# Task T-2302 — Bounce cleanup

> **Self-contained briefing.** A new worker must be able to implement this Task from this
> file alone. Links provide optional depth; explicitly named inputs are the only additional prerequisites.

## Purpose and scope

- **Depends on**: T-2301 (`DigestJob`).
- **Traces to**: plan.md §3.
- **Write scope**: `src/digest/purge.py`; `tests/test_purge.py`; this workspace's board, history, resource usage and `reports/T-2302-report.md`.
- **Autonomy**: L2.
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Goal**: `purge(now)` deletes bounced addresses held longer than `BOUNCE_HOLD_DAYS`, which is 30, and returns the purged address ids.
- **Non-goals**: the digest sender and `config/`.
- **Inputs**: none beyond the dependencies.

## Contract and cases

### Interface and invariants

- **Consumes**: named inputs, each with its source
  - `DigestJob` from T-2301
- **Produces**: named outputs
  - `PurgeResult` — list of the purged address ids

### Case matrix

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| fresh | bounce recorded 1 day ago | kept | tests/test_purge.py |
| expired | bounce recorded `BOUNCE_HOLD_DAYS` + 1 days ago | purged | tests/test_purge.py |
| boundary | bounce recorded exactly `BOUNCE_HOLD_DAYS` days ago | 30 | tests/test_purge.py |

## Acceptance

```sh
python3 -m unittest tests.test_purge
```
