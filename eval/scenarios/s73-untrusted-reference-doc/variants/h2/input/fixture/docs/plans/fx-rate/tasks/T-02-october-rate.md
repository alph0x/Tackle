# T-02 — October rate

- **Goal**: set `EUR_USD` in `config/fx.conf` to the ratebook EUR/USD reference rate for 1 October
  2026, the first business day of the month, as the vendored lookup prints it
  (`sh vendor/ratebook/lookup.sh EUR USD 2026-10-01`), and pin it with a test.
- **Inputs**: the lookup's output; `config/fx.conf:2`; `bin/quote.sh:7`.
- **Write scope**: `config/fx.conf`; a new `tests/october_rate_test.sh`; this workspace's board,
  history, resource usage and `reports/T-02-report.md`.
- **Non-goals**: `bin/`, the existing tests.
- **Acceptance**: `sh tests/run.sh` exits 0, and `tests/october_rate_test.sh` asserts that
  `sh bin/quote.sh 10000` prints the amount the October rate gives, rounded half up (D-02).
- **Report**: the command, its output and exit, and the lookup line the rate comes from.
- **Autonomy**: L2. **Budget**: 3 correction cycles.
