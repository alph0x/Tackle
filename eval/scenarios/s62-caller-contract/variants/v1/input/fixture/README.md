# PettyLedger

A tiny petty-cash tracker for a shared office.

## Layout

- `pettyledger/currency.py` — turns integer cents into the dollar strings shown everywhere else in
  the app: `format_currency(cents: int) -> str`.
- `pettyledger/ledger.py` — transactions, a plain-text summary (`summarize`), parsing a printed amount
  back into cents (`parse_amount`), and a reconciliation self-check (`reconcile`) that re-derives every
  printed line from its text and compares it to the real number of cents it was built from, as a guard
  against the printed report silently drifting from the numbers behind it.

## Running the tests

```sh
python3 -m unittest discover -s tests -v
```

## Amount format

`format_currency` renders an integer number of cents as a string: `1234` is `"$12.34"`, `0` is
`"$0.00"`, thousands are separated with commas (`"$1,234.56"`). See `pettyledger/currency.py` for the
exact rule for negative amounts.
