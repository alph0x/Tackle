"""T-01: the plot register reader."""
import unittest
from pathlib import Path

from statements.plots import read_plots

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "plots.csv"


class ReadPlots(unittest.TestCase):
    def test_reads_plots_in_register_order(self):
        self.assertEqual([p["plot"] for p in read_plots(FIXTURE)], ["7A", "12", "19B"])
