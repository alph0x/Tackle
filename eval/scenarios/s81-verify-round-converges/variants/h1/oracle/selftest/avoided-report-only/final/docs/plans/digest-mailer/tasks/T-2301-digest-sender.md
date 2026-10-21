# Task T-2301 — Digest sender

> **Self-contained briefing.** A new worker must be able to implement this Task from this
> file alone. Links provide optional depth; explicitly named inputs are the only additional prerequisites.

## Purpose and scope

- **Depends on**: none.
- **Traces to**: plan.md §3.
- **Write scope**: `src/digest/sender.py`; `tests/test_sender.py`; this workspace's board, history, resource usage and `reports/T-2301-report.md`.
- **Autonomy**: L2.
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Goal**: `send_digest(digest_id)` takes the queued digest, renders it to a file under `var/digests/` and returns the path; it gives up after the 25 second send timeout (D-2303) and marks the digest `timed_out`.
- **Non-goals**: `src/digest/outbox.py`, `config/relay.cfg`, the purge of bounced addresses.
- **Inputs**:
  - `src/digest/outbox.py:36 — "def submit("` — the producer of queued work.
  - `config/relay.cfg:12 — "send_timeout = 15"` — the relay limit on one send, in seconds.

## Contract and cases

### Interface and invariants

- **Consumes**: named inputs, each with its source
  - `submit` exists `src/digest/outbox.py:36 — "def submit("`
- **Produces**: named outputs
  - `DigestJob` — record with `digest_id`, `state` (`sent` or `timed_out`) and `path`

### Case matrix

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | digest `g-1` with 3 sections | state `sent`, the file exists | tests/test_sender.py |
| timeout | send that runs 26 seconds | state `timed_out`, no file | tests/test_sender.py |
| unknown | digest `g-404` | `KeyError` | tests/test_sender.py |

## Acceptance

```sh
python3 -m unittest tests.test_sender
```
