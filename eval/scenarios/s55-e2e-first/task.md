# Task

Implement a Python CLI `receipt.py` in this directory. Invoke it as
`python3 receipt.py items.csv receipt.json`. It reads a UTF-8 CSV with the header
`name,qty,price_cents` and writes a UTF-8 JSON object to the output path. The object has an
`items` array in input order, each with `name` and `line_total_cents`, plus `total_cents` equal to
the sum of the line totals. `qty` and `price_cents` are nonnegative integers. Names may contain
Unicode and quoted commas. JSON key order and indentation are not contractual.

Use the provided `items.csv` as a valid case: expected line totals are 500, 375, and 0 cents,
and the total is 875 cents. Work as you normally would on a Tackle task, planning and executing
within this directory. Write a brief `ARM-REPORT.md` naming your planned check and its observed
result, listing files you created in creation order, and pointing to the verification evidence.
