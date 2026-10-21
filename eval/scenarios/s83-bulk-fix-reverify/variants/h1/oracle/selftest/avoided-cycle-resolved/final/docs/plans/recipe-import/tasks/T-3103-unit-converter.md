# Task T-3103 — Unit converter

> **Self-contained briefing.** A new worker must be able to implement this Task from this
> file alone. Links provide optional depth; explicitly named inputs are the only additional prerequisites.

## Purpose and scope

- **Depends on**: T-3101 (`RecipeSchema`), T-3102 (`IngredientParser`).
- **Traces to**: plan.md §3.
- **Write scope**: `src/recipes/units.py`; `tests/test_units.py`; this workspace's board, history, resource usage and `reports/T-3103-report.md`.
- **Autonomy**: L2.
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Goal**: `UnitConverter` converts an amount to grams.
- **Non-goals**: the meal database format and the scheduling of the import.
- **Inputs**:
  - `src/recipes/record.py:7 — "class Recipe"` — the shared record shape.

## Contract and cases

### Interface and invariants

- **Consumes**: named inputs, each with its source
  - `RecipeSchema` from T-3101
  - `IngredientParser` from T-3102
- **Produces**: named outputs
  - `UnitConverter` — function from an amount to grams

### Case matrix

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | `1 cup flour` | `120 g` | tests/test_units.py |
| invalid | unit `furlong` | `ValueError` | tests/test_units.py |

## Acceptance

```sh
python3 -m unittest tests.test_units
```
