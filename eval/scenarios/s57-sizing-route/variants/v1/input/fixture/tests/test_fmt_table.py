import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fmt_table import render


class TestRender(unittest.TestCase):
    def test_header_labels(self):
        header = render([]).splitlines()[0]
        self.assertIn("Name", header)

    def test_row_values(self):
        out = render([{"id": 1, "name": "alice", "score": 9}])
        self.assertIn("alice", out)


if __name__ == "__main__":
    unittest.main()
