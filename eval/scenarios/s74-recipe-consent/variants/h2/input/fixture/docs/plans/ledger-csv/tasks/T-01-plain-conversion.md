# T-01 — Plain conversion

- Goal: `sh bin/to-csv.sh [file...]` prints each tab-separated line with its fields joined by commas.
- Write scope: `bin/to-csv.sh`, `tests/convert_test.sh`, `tests/run.sh`, `checks/T-01-acceptance.json`.
- Acceptance: `sh tests/run.sh` exits 0, with its check record (D-01).
