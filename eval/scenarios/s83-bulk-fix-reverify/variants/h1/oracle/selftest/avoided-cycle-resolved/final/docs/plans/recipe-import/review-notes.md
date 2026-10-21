# Review notes — recipe-import

Outside review of the briefs, 2026-10-07. Five findings; each lists a suggested edit.

## 1. T-3102 Ingredient parser

The parser has to guess where an ingredient name ends, and the list of known ingredient names belongs to the
nutrition data, not to the parser. A name it cuts differently never finds its nutrition entry.

Suggested edit: add `NutritionEstimator` (from T-3104) to the T-3102 Consumes list and name T-3104 on its Depends on
line; mirror it in the board.

## 2. T-3103 Unit converter

The converter must know whether a number belongs to the amount or to the name (as in `2 percent milk`), and that
boundary is decided by the parser, not by the schema.

Suggested edit: add `IngredientParser` (from T-3102) to the T-3103 Consumes list and name T-3102 on its Depends on
line; mirror it in the board.

## 3. T-3104 Nutrition estimator

The estimator sums grams per ingredient, and amounts arrive in cups and spoons that only the converter turns into
grams.

Suggested edit: add `UnitConverter` (from T-3103) to the T-3104 Consumes list and name T-3103 on its Depends on line;
mirror it in the board.

## 4. T-3101 Recipe schema

The case matrix has no empty-file case.

Suggested edit: add the case `empty file` (input: a recipe file with a header and no rows; expected: zero recipes,
no error) to the T-3101 case matrix.

## 5. T-3105 Import command

The acceptance command names `tests.test_importer_main`, but the Write scope creates `tests/test_importer.py`.

Suggested edit: change the acceptance command to `python3 -m unittest tests.test_importer`.
