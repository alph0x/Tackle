# Task T-2101 — Column order

- **Write scope**: `export/columns.py`, `export/tests/test_columns.py`
- **Goal**: one module fixes the order of the ledger CSV columns.
- **Contract**: `export.columns.COLUMNS` is the tuple `("entry_id", "posted_on", "amount_cents", "memo")`; the export reads it and keeps no second list.
- **Acceptance**: `python3 export/tests/test_columns.py` exits 0.
