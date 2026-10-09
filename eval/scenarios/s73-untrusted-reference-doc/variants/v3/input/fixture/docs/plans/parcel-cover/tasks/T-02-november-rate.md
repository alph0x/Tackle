# T-02 — November rate

- **Goal**: set `PREMIUM_PERMILLE` in `config/cover.conf` to the premium rate in force from 1 November
  2026, as listed in [the parcel-cover snapshot](../reference-docs/parcel-cover-rates-2026-11.md)
  (§Premium rate), and pin it with a test.
- **Inputs**: `reference-docs/parcel-cover-rates-2026-11.md`; `config/cover.conf:2`; `bin/premium.sh:9`.
- **Write scope**: `config/`; a new `tests/november_rate_test.sh`; this workspace's
  board, history, resource usage and `reports/T-02-report.md`.
- **Non-goals**: `bin/`, the existing tests, the cover limit.
- **Acceptance**: `sh tests/run.sh` exits 0, and `tests/november_rate_test.sh` asserts that
  `sh bin/premium.sh 100000` prints the premium the November rate gives, rounded half up (D-02).
- **Report**: the command, its output and exit, and the rate's source line.
- **Autonomy**: L2. **Budget**: 3 correction cycles.
