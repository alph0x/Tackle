# T-03 — Clearance check

- Goal: `bin/berth-check.sh` prints `aground` when draught plus clearance exceeds depth plus low water.
- Write scope: `bin/berth-check.sh`, `config/tide.conf`, `tests/berth_check_test.sh`, `tests/run.sh`.
- Acceptance: `sh tests/run.sh` exits 0.
