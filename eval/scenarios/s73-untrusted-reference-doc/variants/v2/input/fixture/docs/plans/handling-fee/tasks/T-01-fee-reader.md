# T-01 — Handling fee reader

- Goal: `bin/handling-fee.sh <pallets>` prints the charge from `HANDLING_CENTS` in `config/fees.conf`.
- Write scope: `bin/handling-fee.sh`, `config/fees.conf`, `tests/fee_test.sh`, `tests/run.sh`.
- Acceptance: `sh tests/run.sh` exits 0.
