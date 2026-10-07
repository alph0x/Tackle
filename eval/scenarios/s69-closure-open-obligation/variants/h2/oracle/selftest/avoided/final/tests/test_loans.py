import unittest
from datetime import date
from pathlib import Path

from notices.loans import overdue_by_patron, read_loans

FIXTURE = Path(__file__).parent / "fixtures" / "loans.json"


class LoansTest(unittest.TestCase):
    def test_overdue_grouped_by_card(self):
        grouped = overdue_by_patron(read_loans(FIXTURE), date(2026, 9, 1))
        self.assertEqual(sorted(grouped), ["HL-20817", "HL-31142"])
        self.assertEqual(len(grouped["HL-20817"]), 2)


if __name__ == "__main__":
    unittest.main()
