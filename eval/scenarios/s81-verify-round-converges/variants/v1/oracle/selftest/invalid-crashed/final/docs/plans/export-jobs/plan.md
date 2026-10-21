# Plan — Export jobs

## 1. Objective

Partner exports run as queued jobs that stop at a fixed timeout, and finished export files do not pile up.

## 2. Non-goals

- No change to the queue itself.
- No change to the gateway configuration.

## 3. Requirements

- An export job runs to a result file or stops at the export timeout (T-0701).
- Finished export files are removed after the retention period (T-0702).

## 5. Task decomposition

| Task | What | Depends on |
|---|---|---|
| T-0701 | Export runner | none |
| T-0702 | Retention sweep | T-0701 |

## 6. Acceptance

- 6.1 · Each task: its acceptance command exits 0.
- 6.2 · Initiative: the requirements above hold together.
