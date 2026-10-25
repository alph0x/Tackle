# Task T-2101 — Low shelves

- **Write scope**: `pantry/stock.py`, `docs/plans/pantry-restock/reports/T-2101-report.md`
- **Depends on**: none.
- **Decisions**: D-2101.
- **Goal**: `low_items(items)` names the shelves at or below their minimum, in shelf order.
- **Acceptance**: `python3 -m unittest discover -s tests` exits 0 for `LowItemsTest`.
