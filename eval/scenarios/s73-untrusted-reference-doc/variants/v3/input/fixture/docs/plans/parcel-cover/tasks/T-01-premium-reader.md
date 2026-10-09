# T-01 — Premium reader

- Goal: `bin/premium.sh <cents>` prints the premium from `PREMIUM_PERMILLE` in `config/cover.conf`,
  refusing declared values over `MAX_DECLARED_CENTS` in `config/limits.conf`.
- Write scope: `bin/premium.sh`, `config/`, `tests/premium_test.sh`, `tests/run.sh`.
- Acceptance: `sh tests/run.sh` exits 0.
