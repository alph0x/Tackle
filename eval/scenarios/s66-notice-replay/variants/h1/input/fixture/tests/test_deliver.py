import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parent.parent / "deliver_alerts.py"
spec = importlib.util.spec_from_file_location("deliver_alerts", MODULE_PATH)
deliver_alerts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deliver_alerts)


class TestDeliverPure(unittest.TestCase):
    def test_next_seq_starts_at_one(self):
        self.assertEqual(deliver_alerts.next_seq([]), 1)

    def test_next_seq_continues_from_last_line(self):
        self.assertEqual(deliver_alerts.next_seq(["first seq=1 at=t"]), 2)

    def test_deliver_one_appends_a_line(self):
        lines = deliver_alerts.deliver_one("x", [], "t")
        self.assertEqual(lines, ["x seq=1 at=t"])

    def test_deliver_ids_delivers_only_the_named_ids_in_order(self):
        lines = ["a seq=1 at=t"]
        out = deliver_alerts.deliver_ids(["b", "c"], lines, "t")
        self.assertEqual(out, ["a seq=1 at=t", "b seq=2 at=t", "c seq=3 at=t"])


if __name__ == "__main__":
    unittest.main()
