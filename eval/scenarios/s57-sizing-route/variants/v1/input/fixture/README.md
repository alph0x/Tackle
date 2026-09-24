# devtools-table

A tiny local helper for eyeballing a list of JSON rows in the terminal while developing. It never runs
anywhere but a developer's own machine and produces no output anyone else ever sees.

- `src/fmt_table.py` — `render(rows)` returns an aligned text table.
- `tests/test_fmt_table.py` — `python3 -m unittest discover`
