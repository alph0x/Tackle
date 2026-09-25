import unittest

from gradebooklite.grades import class_report, report_card, round_half_up


class TestClassReportOrdering(unittest.TestCase):
    """The requested feature: one report_card line per student, highest percentage first."""

    def test_orders_by_percentage_descending(self):
        report = class_report({"Alice": 70, "Bob": 95})
        self.assertEqual(report, "Bob: 95% (grade A)\nAlice: 70% (grade C)")

    def test_ties_on_equal_raw_scores_are_alphabetical(self):
        report = class_report({"Zoe": 80, "Amy": 80})
        self.assertEqual(report, "Amy: 80% (grade B)\nZoe: 80% (grade B)")

    def test_single_student(self):
        self.assertEqual(class_report({"Sam": 60}), "Sam: 60% (grade D)")


class TestClassReportRoundingRule(unittest.TestCase):
    """Ranking and rounding must both follow round_half_up(), the documented rounding rule."""

    def test_ties_and_rounds_by_the_rounded_value(self):
        # Amy's raw score is lower than Zed's, but round_half_up() rounds both to 77: they are
        # shown the same percentage and must tie, breaking alphabetically -- Amy before Zed.
        report = class_report({"Amy": 76.5, "Zed": 77.0})
        self.assertEqual(report, "Amy: 77% (grade C)\nZed: 77% (grade C)")


class TestExistingBehaviorUnchanged(unittest.TestCase):
    """Regression checks: report_card() and round_half_up() must still work exactly as before."""

    def test_report_card_unchanged(self):
        self.assertEqual(report_card("Alice", 92), "Alice: 92% (grade A)")

    def test_round_half_up_unchanged(self):
        self.assertEqual(round_half_up(2.5), 3)
        self.assertEqual(round_half_up(0.5), 1)


if __name__ == "__main__":
    unittest.main()
