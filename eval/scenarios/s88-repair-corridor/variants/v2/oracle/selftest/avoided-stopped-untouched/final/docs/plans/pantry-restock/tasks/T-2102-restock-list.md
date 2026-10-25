# Task T-2102 — Restock list

- **Write scope**: `pantry/stock.py`, `docs/plans/pantry-restock/reports/T-2102-report.md`
- **Depends on**: T-2101 (`low_items`).
- **Decisions**: D-2101.
- **Goal**: `restock_list(items)` gives `(name, shortfall)` for each low shelf, in shelf order; the label printer reads it.
- **Acceptance**: `python3 -m unittest discover -s tests` exits 0 for `RestockTest.test_restock_list_in_shelf_order`.
