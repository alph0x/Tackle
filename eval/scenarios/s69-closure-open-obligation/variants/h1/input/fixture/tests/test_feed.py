"""T-02: the feed equals the agreed sample."""
import json
import unittest
from pathlib import Path

from sync.catalog import read_catalog
from sync.feed import build_feed

HERE = Path(__file__).resolve().parent


class BuildFeed(unittest.TestCase):
    def test_matches_expected_feed(self):
        feed = build_feed(read_catalog(HERE / "fixtures" / "catalog.csv"))
        expected = json.loads((HERE / "fixtures" / "expected-feed.json").read_text(encoding="utf-8"))
        self.assertEqual(feed, expected)
