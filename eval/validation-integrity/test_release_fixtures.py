"""Oracle inventory checks, not release decisions or behavioral evidence."""
import json
import unittest
from pathlib import Path


class ReleaseScopeFixtureTests(unittest.TestCase):
    def test_oracle_inventory_covers_selected_and_other_active_workspaces(self):
        cases = json.loads((Path(__file__).with_name("release-scope") / "cases.json").read_text())
        self.assertEqual(len(cases), 9)
        self.assertEqual(len({case["name"] for case in cases}), 9)
        self.assertEqual([case["expected_blocking"] for case in cases], [True, True, False, False, False, False, True, True, True])

    def test_parked_case_is_not_accidentally_active(self):
        cases = json.loads((Path(__file__).with_name("release-scope") / "cases.json").read_text())
        parked = next(case for case in cases if case["name"] == "unselected-parked-plan")
        self.assertFalse(parked["board_has_in_progress"])
        active = next(case for case in cases if case["name"] == "another-active-workspace-still-gates")
        self.assertTrue(active["other_active_failure"])


if __name__ == "__main__":
    unittest.main()
