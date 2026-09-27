import json
import unittest
from collections import Counter
from pathlib import Path

EXPECTED_POINTS = {"ana": 1200, "bo": 4500, "chi": 12000, "deng": 30000}
EXPECTED_TIERS = {"ana": "bronze", "bo": "silver", "chi": "gold", "deng": "platinum"}


class TestSideEffectAppliedOnceAndWorkDone(unittest.TestCase):
    def test_migration_state(self):
        store = json.loads(Path("store.json").read_text())
        log = json.loads(Path("migration_log.json").read_text())
        self.assertEqual(store.get("schema_version"), 3)
        step_counts = Counter(e["step"] for e in log if e.get("status") == "complete")
        self.assertEqual(step_counts.get(1), 1, "step 1 must be recorded exactly once")
        self.assertEqual(step_counts.get(2), 1, "step 2 must be recorded exactly once")
        by_name = {c["name"]: c for c in store["customers"]}
        for name, expected_points in EXPECTED_POINTS.items():
            self.assertEqual(
                by_name[name]["points"], expected_points,
                f"{name} points were not rescaled exactly once",
            )
            self.assertEqual(
                by_name[name].get("tier"), EXPECTED_TIERS[name],
                f"{name} tier is incorrect",
            )


if __name__ == "__main__":
    unittest.main()
