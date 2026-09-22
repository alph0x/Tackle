"""Regression properties for full-cost synthetic history measurements."""
import unittest
from benchmark import report


class MeasurementTests(unittest.TestCase):
    def test_growing_histories_keep_unrelated_originals_out_of_routine_reads(self):
        result = report()
        self.assertEqual([row["closed_tasks"] for row in result["sizes"]], [10, 100, 1000])
        for row in result["sizes"]:
            candidate = row["candidate"]
            self.assertGreaterEqual(candidate["retained"]["retained_bytes"], row["initial"]["retained_bytes"])
            self.assertGreater(candidate["archive_and_index"]["bytes_read"], 0)
            self.assertGreater(candidate["complete_history_reconstruction"]["bytes_read"], 0)
            if row["closed_tasks"] >= 100:
                self.assertLess(candidate["resume"]["bytes_read"], row["baseline"]["resume"]["bytes_read"])
                self.assertLess(candidate["handoff"]["bytes_read"], row["baseline"]["handoff"]["bytes_read"])
        self.assertGreater(result["sizes"][-1]["candidate"]["resume"]["bytes_read"],
                           result["sizes"][0]["candidate"]["resume"]["bytes_read"])


if __name__ == "__main__":
    unittest.main()
