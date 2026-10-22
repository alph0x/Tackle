# Task T-2102 — CSV writer

- **Write scope**: `export/ledger_csv.py`, `export/tests/test_ledger_csv.py`
- **Depends on**: T-2101 (the column order).
- **Decisions**: D-1101, D-1102.
- **Goal**: `write_rows(entries, out)` writes the header and one CSV row per entry, in `COLUMNS` order.
- **Acceptance**: `python3 export/tests/test_ledger_csv.py` exits 0.
