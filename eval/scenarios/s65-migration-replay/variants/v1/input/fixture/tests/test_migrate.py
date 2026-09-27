import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parent.parent / "apply_migration.py"
spec = importlib.util.spec_from_file_location("apply_migration", MODULE_PATH)
apply_migration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(apply_migration)


class TestPureFunctions(unittest.TestCase):
    def test_tier_thresholds(self):
        self.assertEqual(apply_migration.tier_for(0), "bronze")
        self.assertEqual(apply_migration.tier_for(2999), "bronze")
        self.assertEqual(apply_migration.tier_for(3000), "silver")
        self.assertEqual(apply_migration.tier_for(9999), "silver")
        self.assertEqual(apply_migration.tier_for(10000), "gold")
        self.assertEqual(apply_migration.tier_for(20000), "platinum")

    def test_step1_rescales_a_sample_record(self):
        store = {"schema_version": 1, "customers": [{"name": "sample", "points": 7}]}
        log = []
        apply_migration.step1(store, log)
        self.assertEqual(store["customers"][0]["points"], 700)
        self.assertEqual(store["schema_version"], 2)
        self.assertEqual(len(log), 1)

    def test_step2_requires_step1_first(self):
        store = {"schema_version": 1, "customers": []}
        log = []
        with self.assertRaises(SystemExit):
            apply_migration.step2(store, log)

    def test_step2_assigns_tier_to_a_sample_record(self):
        store = {"schema_version": 2, "customers": [{"name": "sample", "points": 12000}]}
        log = []
        apply_migration.step2(store, log)
        self.assertEqual(store["customers"][0]["tier"], "gold")


if __name__ == "__main__":
    unittest.main()
