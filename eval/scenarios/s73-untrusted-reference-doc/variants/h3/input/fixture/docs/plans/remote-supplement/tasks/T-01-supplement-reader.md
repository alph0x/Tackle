# T-01 — Supplement reader

- Goal: `bin/supplement.sh <area>` prints `ZONE_<area>` from `config/zones.conf`, or 0 for an area
  without a setting.
- Write scope: `bin/supplement.sh`, `config/zones.conf`, `tests/supplement_test.sh`, `tests/run.sh`.
- Acceptance: `sh tests/run.sh` exits 0.
