# Task T-3101 — Recipe schema

> **Self-contained briefing.** A new worker must be able to implement this Task from this
> file alone. Links provide optional depth; explicitly named inputs are the only additional prerequisites.

## Purpose and scope

- **Depends on**: none.
- **Traces to**: plan.md §3.
- **Write scope**: `src/recipes/schema.py`; `tests/test_schema.py`; this workspace's board, history, resource usage and `reports/T-3101-report.md`.
- **Autonomy**: L2.
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Goal**: `RecipeSchema` validates one recipe row against the `Recipe` fields.
- **Non-goals**: the meal database format and the scheduling of the import.
- **Inputs**:
  - `src/recipes/record.py:7 — "class Recipe"` — the shared record shape.

## Contract and cases

### Interface and invariants

- **Consumes**: none.
- **Produces**: named outputs
  - `RecipeSchema` — validator for one row

### Case matrix

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | row `soup,Soup,4` | valid | tests/test_schema.py |
| invalid | row `soup,Soup` | `ValueError` | tests/test_schema.py |
| empty | an empty file | zero recipes, no error | tests/test_schema.py |

## Acceptance

```sh
python3 -m unittest tests.test_schema
```
