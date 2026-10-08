# T-01 — Header option

- **Goal**: `sh bin/tally.sh --header <column> [file...]` skips the first line of each file before
  summing; without `--header` nothing changes.
- **Inputs**: `bin/tally.sh:4-6`; `tests/data/orders.csv`; D-01.
- **Write scope**: `bin/tally.sh`; a new `tests/header_test.sh`; this workspace's board, history,
  resource usage, `reports/T-01-report.md` and `verification-records/T-01/`.
- **Non-goals**: `tests/sum_test.sh`, `tests/run.sh`, `tests/data/`.
- **Acceptance**: `sh tests/run.sh` exits 0, and `tests/header_test.sh` asserts that
  `sh bin/tally.sh --header 3 tests/data/orders.csv` prints `2050`.
- **Verification record** (D-01): under `verification-records/T-01/`, the exact command, cwd, complete
  stdout and stderr and exit status of the acceptance run, plus sha256 of `bin/tally.sh` and
  `tests/*.sh` before and after it. The report links the record.
- **Autonomy**: L2. **Budget**: 3 correction cycles.
