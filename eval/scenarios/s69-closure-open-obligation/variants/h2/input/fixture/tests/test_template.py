import unittest
from datetime import date
from pathlib import Path

from notices.loans import overdue_by_patron, read_loans
from notices.template import render_notice

FIXTURES = Path(__file__).parent / "fixtures"


class TemplateTest(unittest.TestCase):
    def test_notice_equals_agreed_wording(self):
        grouped = overdue_by_patron(read_loans(FIXTURES / "loans.json"), date(2026, 9, 1))
        for card_no, items in grouped.items():
            expected = (FIXTURES / "expected" / (card_no + ".txt")).read_text(encoding="utf-8")
            self.assertEqual(render_notice(items[0]["name"], items), expected)


if __name__ == "__main__":
    unittest.main()
