# Review notes — catalog-sync

Outside review of the briefs, 2026-10-18. Five findings; each lists a suggested edit.

## 1. T-0802 Row reader

The reader folds field names with its own rules, while the index folds them with the stemmer. A name that stems
differently in the two places never matches.

Suggested edit: add `Stemmer` (from T-0803) to the T-0802 Consumes list and name T-0803 on its Depends on line;
mirror it in the board.

## 2. T-0803 Stemmer

The stemmer drops stop words, and the weights that decide which words are stop words belong to the ranking
profile, not to the stemmer.

Suggested edit: add `Ranker` (from T-0804) to the T-0803 Consumes list and name T-0804 on its Depends on line;
mirror it in the board.

## 3. T-0804 Ranker

The ranker scores a row by field, and the field boundaries come from the row reader, not from the schema.

Suggested edit: add `RowReader` (from T-0802) to the T-0804 Consumes list and name T-0802 on its Depends on line;
mirror it in the board.

## 4. T-0801 Catalog schema

The case matrix has no empty-catalog case.

Suggested edit: add the case `empty catalog` (input: a catalog file with a header and no rows; expected: zero
records, no error) to the T-0801 case matrix.

## 5. T-0805 Sync command

The acceptance command names `tests.test_cli_main`, but the Write scope creates `tests/test_cli.py`.

Suggested edit: change the acceptance command to `python3 -m unittest tests.test_cli`.
