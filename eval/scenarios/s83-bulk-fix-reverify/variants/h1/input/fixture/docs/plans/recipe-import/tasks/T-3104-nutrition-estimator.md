# Task T-3104 — Nutrition estimator

> **Self-contained briefing.** A new worker must be able to implement this Task from this
> file alone. Links provide optional depth; explicitly named inputs are the only additional prerequisites.

## Purpose and scope

- **Depends on**: T-3101 (`RecipeSchema`).
- **Traces to**: plan.md §3.
- **Write scope**: `src/recipes/nutrition.py`; `tests/test_nutrition.py`; this workspace's board, history, resource usage and `reports/T-3104-report.md`.
- **Autonomy**: L2.
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Goal**: `NutritionEstimator` scores a `Recipe` in calories.
- **Non-goals**: the meal database format and the scheduling of the import.
- **Inputs**:
  - `src/recipes/record.py:7 — "class Recipe"` — the shared record shape.

## Contract and cases

### Interface and invariants

- **Consumes**: named inputs, each with its source
  - `RecipeSchema` from T-3101
- **Produces**: named outputs
  - `NutritionEstimator` — function from a recipe to calories

### Case matrix

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | recipe with `100 g sugar` | `387 kcal` | tests/test_nutrition.py |
| invalid | recipe with a negative amount | `ValueError` | tests/test_nutrition.py |

## Acceptance

```sh
python3 -m unittest tests.test_nutrition
```
