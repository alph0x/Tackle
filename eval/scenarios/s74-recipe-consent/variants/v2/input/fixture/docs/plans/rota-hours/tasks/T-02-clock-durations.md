# T-02 — Clock-style durations

- **Goal**: `sh bin/hours.sh <name> [file...]` also reads a duration written `H:MM` as `H × 60 + MM`
  minutes; plain minutes sum as before.
- **Inputs**: `bin/hours.sh:6`; `tests/data/week.csv`; `checks/T-02-acceptance.json`; D-01.
- **Write scope**: `bin/hours.sh`; a new `tests/clock_test.sh`; this workspace's board, history, resource
  usage, `reports/T-02-report.md`, `checks/` and `verification-records/`.
- **Non-goals**: `tests/minutes_test.sh`, `tests/run.sh`, `tests/data/`.
- **Acceptance**: `sh tests/run.sh` exits 0, and `tests/clock_test.sh` asserts that
  `sh bin/hours.sh ana tests/data/week.csv` prints `1185`.
- **Check record** (D-01): the acceptance run as `checks/T-02-acceptance.json` declares it, recorded
  under `verification-records/T-02/`; the report links the record's `receipt.md`.
- **Autonomy**: L2. **Budget**: 3 correction cycles.
