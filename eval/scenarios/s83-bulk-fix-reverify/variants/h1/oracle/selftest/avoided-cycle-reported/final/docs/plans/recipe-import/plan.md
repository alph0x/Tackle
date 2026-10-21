# Plan — Recipe import

## 1. Objective

A partner recipe file is parsed, unit-converted and nutrition-scored into the meal-planning database by one command.

## 2. Non-goals

- No change to the meal database format.
- No scheduling of the import.

## 3. Requirements

- The recipe record shape is fixed (T-3101).
- Ingredient lines are parsed (T-3102).
- Amounts are converted to grams (T-3103).
- Recipes are scored for calories (T-3104).
- One command runs the import (T-3105).

## 5. Task decomposition

| Task | What | Depends on |
|---|---|---|
| T-3101 | Recipe schema | none |
| T-3102 | Ingredient parser | T-3101 |
| T-3103 | Unit converter | T-3101 |
| T-3104 | Nutrition estimator | T-3101 |
| T-3105 | Import command | T-3102, T-3103, T-3104 |

## 6. Acceptance

- 6.1 · Each task: its acceptance command exits 0.
- 6.2 · Initiative: the requirements above hold together.
