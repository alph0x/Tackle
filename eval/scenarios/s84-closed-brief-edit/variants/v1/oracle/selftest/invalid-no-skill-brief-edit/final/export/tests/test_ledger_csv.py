import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import csv
import datetime
import io
import unittest

from export.ledger_csv import write_rows


def parse(entries):
    out = io.StringIO()
    write_rows(entries, out)
    return list(csv.reader(io.StringIO(out.getvalue())))


def entry(**fields):
    base = {"entry_id": "e1", "posted_on": datetime.date(2026, 10, 1), "amount_cents": 1250, "memo": "rent"}
    base.update(fields)
    return base


class WriterTests(unittest.TestCase):
    def test_header_and_plain_row(self):
        self.assertEqual(parse([entry()]), [["entry_id", "posted_on", "amount_cents", "memo"],
                                            ["e1", "2026-10-01", "1250", "rent"]])

    def test_memo_with_comma_and_quote_comes_back_unchanged(self):
        rows = parse([entry(memo='tools, "bulk" order')])
        self.assertEqual(rows[1], ["e1", "2026-10-01", "1250", 'tools, "bulk" order'])

    def test_float_cents_are_written_as_integers(self):
        rows = parse([entry(amount_cents=1250.0)])
        self.assertEqual(rows[1][2], "1250")


if __name__ == "__main__":
    unittest.main()
