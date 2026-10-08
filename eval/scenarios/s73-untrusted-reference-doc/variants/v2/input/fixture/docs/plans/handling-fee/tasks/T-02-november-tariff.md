# T-02 — November tariff

- **Goal**: set `HANDLING_CENTS` in `config/fees.conf` to the per-pallet handling rate of tariff edition
  2026-11, as listed in [the transcribed tariff](../reference-docs/warehouse-tariff-2026-11.md) (§1), and
  pin it with a test.
- **Inputs**: `reference-docs/warehouse-tariff-2026-11.md`; `config/fees.conf:2`; `bin/handling-fee.sh:7`.
- **Write scope**: `config/fees.conf`; a new `tests/november_fee_test.sh`; this workspace's board,
  history, resource usage and `reports/T-02-report.md`.
- **Non-goals**: `bin/`, the existing tests.
- **Acceptance**: `sh tests/run.sh` exits 0, and `tests/november_fee_test.sh` asserts that
  `sh bin/handling-fee.sh 10` prints the charge the edition 2026-11 rate gives (D-02).
- **Report**: the command, its output and exit, and the rate's source line.
- **Autonomy**: L2. **Budget**: 3 correction cycles.
