# Task T-3105 — Import command

> **Self-contained briefing.** A new worker must be able to implement this Task from this
> file alone. Links provide optional depth; explicitly named inputs are the only additional prerequisites.

## Purpose and scope

- **Depends on**: T-3102 (`IngredientParser`), T-3103 (`UnitConverter`), T-3104 (`NutritionEstimator`).
- **Traces to**: plan.md §3.
- **Write scope**: `src/recipes/cli.py`; `tests/test_importer.py`; this workspace's board, history, resource usage and `reports/T-3105-report.md`.
- **Autonomy**: L2.
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Goal**: `import_recipes` runs parser, converter and estimator over one recipe file and prints the recipe count.
- **Non-goals**: the meal database format and the scheduling of the import.
- **Inputs**:
  - `src/recipes/record.py:7 — "class Recipe"` — the shared record shape.

## Contract and cases

### Interface and invariants

- **Consumes**: named inputs, each with its source
  - `IngredientParser` from T-3102
  - `UnitConverter` from T-3103
  - `NutritionEstimator` from T-3104
- **Produces**: named outputs
  - `import_recipes` — the shell command

### Case matrix

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | file with 2 recipes | prints `2` | tests/test_importer.py |
| bad file | a bad recipe file | exit 1 | tests/test_importer.py |

## Acceptance

```sh
python3 -m unittest tests.test_importer
```
