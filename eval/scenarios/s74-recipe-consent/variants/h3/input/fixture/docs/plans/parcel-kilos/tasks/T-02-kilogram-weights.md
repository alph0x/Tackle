# T-02 — Kilogram weights

- **Goal**: `sh bin/weigh.sh <dest> [file...]` also reads a weight written `<number>kg` as that number
  × 1000 grams; plain grams sum as before.
- **Inputs**: `bin/weigh.sh:6`; `tests/data/parcels.csv`; D-02; obligation O-01.
- **Write scope**: `bin/weigh.sh`; a new `tests/kg_test.sh`; this workspace's board, history, resource
  usage ledger, `resource-usage.telemetry.jsonl`, `reports/T-02-report.md` and `verification-records/`.
- **Non-goals**: `tests/grams_test.sh`, `tests/run.sh`, `tests/data/`, `runs/`.
- **Acceptance**: `sh tests/run.sh` exits 0, and `tests/kg_test.sh` asserts that
  `sh bin/weigh.sh lyon tests/data/parcels.csv` prints `5250`.
- **Session obligation**: O-01 is due in this RUN session (D-02); its receipt goes under
  `verification-records/T-01/`.
- **Autonomy**: L2. **Budget**: 3 correction cycles.
