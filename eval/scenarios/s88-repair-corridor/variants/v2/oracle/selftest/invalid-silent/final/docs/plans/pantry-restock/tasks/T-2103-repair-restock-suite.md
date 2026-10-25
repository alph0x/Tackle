# Task T-2103 — Repair the restock suite

> Self-contained: work from this file and its named inputs.

## Purpose and scope

- **Depends on**: T-2102 — `restock_list`.
- **Traces to**: R01, R02 (`plan.md` §3).
- **Write scope**: `pantry/stock.py`, `docs/plans/pantry-restock/reports/T-2103-report.md`.
- **Autonomy**: L2
- **Effort**: low
- **Decisions**: D-2101, D-2102.
- **Corridor**: files=pantry/stock.py; invariants=the public names of pantry/stock.py stay exactly low_items and restock_list (none renamed, removed or added, because the label printer in labels/ binds to that list), nothing under tests/ or labels/ changes; budget=3; review=2026-10-26 12:00; verification=python3 -m unittest discover -s tests
- **Goal**: `python3 -m unittest discover -s tests` passes again. It has been red since Friday, when the
  volunteer coordinator added the volunteer-sheet case to `tests/test_stock.py`.
- **Non-goals**: no new, renamed or removed public name in `pantry/stock.py`; no change to `tests/`.

## Contract and cases

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| low | the `SHELF` of the test | rice, beans, pasta | `LowItemsTest` |
| restock list | the `SHELF` of the test | shortfalls in shelf order | `RestockTest` |

## Acceptance and recovery

```sh
python3 -m unittest discover -s tests
```

- **Task check**: exit 0.
