# T-01 — Unwrap quoted values

- **Goal**: a value wrapped in double quotes prints without them.
- **Inputs**: `bin/cfg.sh:13-14`; D-01.
- **Write scope**: `bin/cfg.sh`; a new `tests/quote_test.sh`; this workspace's board, history,
  `reports/T-01-report.md` and `verification-records/T-01/`.
- **Acceptance**: `sh tests/run.sh` exits 0.
- **Autonomy**: L2. **Budget**: 3 correction cycles.
