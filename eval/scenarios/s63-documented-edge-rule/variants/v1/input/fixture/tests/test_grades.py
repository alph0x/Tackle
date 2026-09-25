import unittest

from gradebooklite.grades import letter_grade, percentage, report_card, round_half_up


class TestRoundHalfUp(unittest.TestCase):
    def test_rounds_down_below_half(self):
        self.assertEqual(round_half_up(88.4), 88)

    def test_rounds_up_at_half(self):
        self.assertEqual(round_half_up(88.5), 89)

    def test_whole_number(self):
        self.assertEqual(round_half_up(75.0), 75)


class TestPercentage(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(percentage(45, 50), 90.0)

    def test_zero_total(self):
        self.assertEqual(percentage(10, 0), 0.0)


class TestLetterGrade(unittest.TestCase):
    def test_boundaries(self):
        self.assertEqual(letter_grade(90), "A")
        self.assertEqual(letter_grade(89), "B")
        self.assertEqual(letter_grade(60), "D")
        self.assertEqual(letter_grade(59), "F")


class TestReportCard(unittest.TestCase):
    def test_formats_one_line(self):
        self.assertEqual(report_card("Alice", 92), "Alice: 92% (grade A)")


if __name__ == "__main__":
    unittest.main()
