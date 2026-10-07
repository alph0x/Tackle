"""T-02: the rendered statements equal the agreed sample."""
import tempfile
import unittest
from pathlib import Path

from statements.plots import read_plots
from statements.render import write_statements

HERE = Path(__file__).resolve().parent


class WriteStatements(unittest.TestCase):
    def test_matches_agreed_sample(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "statements.txt"
            count = write_statements(read_plots(HERE / "fixtures" / "plots.csv"), "2027", out)
            self.assertEqual(count, 3)
            self.assertEqual(out.read_text(encoding="utf-8"), (HERE / "fixtures" / "expected-statements.txt").read_text(encoding="utf-8"))
