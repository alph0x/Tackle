import unittest
from datetime import date

from bookdrop.reminders import reminder_rows

TODAY = date(2026, 9, 10)
# Rows as the loan desk exported them on 10 September.
LOANS = [
    {'patron': 'P-1041', 'title': 'The Long Field', 'due': '2026-08-22'},
    {'patron': 'P-2210', 'title': 'Salt and Iron', 'due': '2026-08-31'},
    {'patron': 'P-0387', 'title': 'A Year of Tides', 'due': '2026/08/26'},
    {'patron': 'P-1902', 'title': 'Northern Kitchens', 'due': '2026-09-09'},
    {'patron': 'P-0555', 'title': 'Quiet Engines', 'due': '2026-09-08'},
    {'patron': 'P-0999', 'title': 'Lost Atlas', 'due': ''},
]


class ReminderRows(unittest.TestCase):
    def test_overdue_reminder_rows(self):
        rows = reminder_rows(LOANS, TODAY)
        self.assertEqual(len(rows), 3, 'overdue reminder rows')

    def test_recent_loans_get_no_reminder(self):
        patrons = {row[0] for row in reminder_rows(LOANS, TODAY)}
        self.assertFalse(patrons & {'P-1902', 'P-0555'})


if __name__ == '__main__':
    unittest.main()
