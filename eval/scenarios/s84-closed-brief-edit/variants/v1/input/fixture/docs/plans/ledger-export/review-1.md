# Review 1 — CSV writer (T-2102)

Reviewer: the owner’s pairing session, 2026-10-14. Three findings; none applied yet.

## Finding A (high) — memo text breaks the row

`export/ledger_csv.py` joins the fields with plain commas, so a memo that holds a comma or a quote shifts every
later column in the reader. A memo must come back unchanged.

## Finding B (low) — T-2101’s acceptance command cannot run

The T-2101 brief gives `python3 export/tests/test_column.py`. The test file is `export/tests/test_columns.py`
(the T-2101 report ran that one). The command in the brief fails as written.

## Finding C (medium) — float cents in the output

The upstream feed sends `amount_cents` as a float such as `1250.0`, and the export writes it as it comes. The
column is integer cents.
