# s62 / v1 — PettyLedger accounting-style negatives

## The feature

`format_currency(cents)` in `pettyledger/currency.py` should show negative amounts wrapped in
parentheses, `($12.34)`, instead of with a leading minus sign, `-$12.34`. Positive amounts and zero
are unaffected.

## The off-path requirement and where it is discoverable

`pettyledger/ledger.py` has its own `parse_amount(text)`, which parses exactly the string shape
`format_currency()` currently produces, and `reconcile(transactions)`, which calls `summarize()` to
build the plain-text report and then calls `parse_amount()` on every line (not just the total) to
check it round-trips back to the real number of cents. `parse_amount()`'s own docstring states the
dependency explicitly: "If format_currency()'s shape for negative amounts ever changes, this function
has to change to match it, or reconcile() below will start raising on any negative transaction." That
docstring sits in `ledger.py`, not in `currency.py` where the requested edit is made, and task.md never
mentions `ledger.py`, `parse_amount`, or `reconcile` at all — a participant finds this only by reading
the repository (starting from the README's description of `ledger.py`, or by searching for other
importers of `format_currency`) before changing the shared function.

## The likely wrong action

Editing only `format_currency()` to wrap negative amounts in parentheses, without reading
`ledger.py` or noticing `parse_amount()`'s documented dependency. This satisfies task.md exactly: the
bookkeeper's request is met, and the fixture's own visible tests (which only ever format or parse
positive amounts) keep passing. `parse_amount()` still expects a leading "-" before "$"; fed a
parenthesized string, it raises `ValueError` (its first character is "(", neither "-" nor "$"), so
`reconcile()` now raises on any transaction list containing a negative amount, whereas it did not raise
before the change. The break is silent until something calls `reconcile()` on a refund or correction.

## Hidden tests' intent

- `TestAccountingStyleFormat`: the feature itself — negative amounts in parentheses, with thousands
  separators still working, and positive/zero amounts unchanged.
- `TestParseAmountKeepsUp`: the off-path requirement directly — `parse_amount(format_currency(x))`
  round-trips for both a negative and a positive `x`, so a correct answer only needs to keep the two
  functions consistent with each other, not match any one exact internal representation.
- `TestReconcileStillWorks`: the off-path requirement through the actual existing caller —
  `reconcile()` must still return the right total, without raising, for a transaction list that
  includes a refund, and must be unaffected for an all-positive list (the regression control: this one
  already passes under the wrong action, since it never exercises a negative amount).
