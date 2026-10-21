# Task T-3102 — Ingredient parser

> **Self-contained briefing.** A new worker must be able to implement this Task from this
> file alone. Links provide optional depth; explicitly named inputs are the only additional prerequisites.

## Purpose and scope

- **Depends on**: T-3101 (`RecipeSchema`), T-3104 (`NutritionEstimator`).
- **Traces to**: plan.md §3.
- **Write scope**: `src/recipes/parser.py`; `tests/test_parser.py`; this workspace's board, history, resource usage and `reports/T-3102-report.md`.
- **Autonomy**: L2.
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Goal**: `IngredientParser` splits an ingredient line into an amount and a name.
- **Non-goals**: the meal database format and the scheduling of the import.
- **Inputs**:
  - `src/recipes/record.py:7 — "class Recipe"` — the shared record shape.

## Contract and cases

### Interface and invariants

- **Consumes**: named inputs, each with its source
  - `RecipeSchema` from T-3101
  - `NutritionEstimator` from T-3104
- **Produces**: named outputs
  - `IngredientParser` — function from a line to an amount and a name

### Case matrix

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | `2 cups flour` | amount `2 cups`, name `flour` | tests/test_parser.py |
| invalid | blank line | `ValueError` | tests/test_parser.py |

## Acceptance

```sh
python3 -m unittest tests.test_parser
```
