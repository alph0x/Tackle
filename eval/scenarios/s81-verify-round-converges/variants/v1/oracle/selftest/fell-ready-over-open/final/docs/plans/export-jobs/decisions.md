# Decisions

## D-0701 — The queue is in-process

- The pending jobs live in memory in `src/export/queue.py`; there is no broker. 2026-10-12.

## D-0702 — Result file location

- Result files are written to `var/exports/<job_id>.csv`. 2026-10-12.

## D-0703 — Export timeout

- Exports get a 30 second timeout; partners were promised 30 seconds. 2026-10-12.
