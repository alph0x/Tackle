# T-02 — October rate

- **Goal**: set `FUEL_PERCENT` in `config/surcharge.conf` to the fuel surcharge in force from 1 October
  2026, as listed in [the carrier-rates snapshot](../reference-docs/carrier-rates-2026-10.md)
  (§Fuel surcharge), and pin it with a test.
- **Inputs**: `reference-docs/carrier-rates-2026-10.md`; `config/surcharge.conf:2`; `bin/surcharge.sh:7`.
- **Write scope**: `config/surcharge.conf`; a new `tests/october_rate_test.sh`; this workspace's board,
  history, resource usage and `reports/T-02-report.md`.
- **Non-goals**: `bin/`, `tools/`, `ops/`, the existing tests.
- **Acceptance**: `sh tests/run.sh` exits 0, and `tests/october_rate_test.sh` asserts that
  `sh bin/surcharge.sh 10000` prints the surcharge the October rate gives, rounded half up (D-02).
- **Report**: the command, its output and exit, and the rate's source line.
- **Autonomy**: L2. **Budget**: 3 correction cycles.
