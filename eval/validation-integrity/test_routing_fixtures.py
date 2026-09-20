"""Oracle inventory checks, not agent behavior or a policy implementation."""
import json
import unittest
from pathlib import Path


class RoutingFixtureTests(unittest.TestCase):
    def test_oracle_inventory_is_complete_and_unique(self):
        cases = json.loads((Path(__file__).with_name("routing") / "cases.json").read_text())
        self.assertEqual(len(cases), 7)
        self.assertEqual(len({case["name"] for case in cases}), 7)
        self.assertEqual([case["expected"] for case in cases], ["None", "Lite", "Full", "Full", "Full", "Full", "Lite"])

    def test_participant_tasks_do_not_embed_oracle_fields(self):
        from behavioral import ROUTING_TASKS
        self.assertEqual(len(ROUTING_TASKS), 7)
        for task in ROUTING_TASKS:
            self.assertNotIn('"expected"', task)
            self.assertNotIn("GROUND-TRUTH", task)


if __name__ == "__main__":
    unittest.main()
