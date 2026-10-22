import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from datetime import date
from reminders.due import due_date


class Tests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(due_date(date(2026, 10, 1), 30), date(2026, 10, 31))


if __name__ == "__main__":
    unittest.main()
