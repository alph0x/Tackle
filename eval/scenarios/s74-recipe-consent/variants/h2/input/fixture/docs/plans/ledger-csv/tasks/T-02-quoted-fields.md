# T-02 — Quoted fields

- **Goal**: `bin/to-csv.sh` writes a field that holds a comma or a double quote in double quotes, with
  each inner double quote doubled; other fields are written as before.
- **Inputs**: `bin/to-csv.sh:4`; T-01's record
  `verification-records/T-01/observation-4c1e0d7a9b3f42d8a6e5f0c2b7d91a36/`; D-01, D-02.
- **Write scope**: `bin/to-csv.sh`; a new `tests/quote_test.sh`; this workspace's board, history,
  resource usage, `reports/T-02-report.md`, `checks/` and `verification-records/T-02/`.
- **Non-goals**: `tests/convert_test.sh`, `tests/run.sh`, T-01's record.
- **Acceptance**: `sh tests/run.sh` exits 0, and `tests/quote_test.sh` asserts that
  `printf 'Smith, J.\t12\n' | sh bin/to-csv.sh` prints `"Smith, J.",12` and that
  `printf '5" pipe\t3\n' | sh bin/to-csv.sh` prints `"5"" pipe",3`.
- **Check record** (D-01, D-02): the acceptance run's record under `verification-records/T-02/`, carrying
  T-01's record, which covers `bin/to-csv.sh`; the report links its `receipt.md`.
- **Autonomy**: L2. **Budget**: 3 correction cycles.
