# Task T-0701 — Export runner

> **Self-contained briefing.** A new worker must be able to implement this Task from this
> file alone. Links provide optional depth; explicitly named inputs are the only additional prerequisites.

## Purpose and scope

- **Depends on**: none.
- **Traces to**: plan.md §3.
- **Write scope**: `src/export/runner.py`; `tests/test_runner.py`; this workspace's board, history, resource usage and `reports/T-0701-report.md`.
- **Autonomy**: L2.
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Goal**: `run_export(job_id)` takes the queued job, writes its result file under `var/exports/` and returns the path; it gives up after the 30 second export timeout (D-0703) and marks the job `timed_out`.
- **Non-goals**: `src/export/queue.py`, `config/gateway.toml`, the retention of finished files.
- **Inputs**:
  - `src/export/queue.py:58 — "def enqueue("` — the producer of queued work.
  - `config/gateway.toml:12 — "request_timeout = 20"` — the gateway limit on one request, in seconds.

## Contract and cases

### Interface and invariants

- **Consumes**: named inputs, each with its source
  - `enqueue` exists `src/export/queue.py:58 — "def enqueue("`
- **Produces**: named outputs
  - `ExportJob` — record with `job_id`, `state` (`done` or `timed_out`) and `path`

### Case matrix

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | job `j-1` with 3 rows | state `done`, the file exists | tests/test_runner.py |
| timeout | job that runs 31 seconds | state `timed_out`, no file | tests/test_runner.py |
| unknown | job `j-404` | `KeyError` | tests/test_runner.py |

## Acceptance

```sh
python3 -m unittest tests.test_runner
```
