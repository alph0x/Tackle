import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import readlist


class TestDedupe(unittest.TestCase):
    def setUp(self):
        readlist.STORE = ROOT / f"_test_store_{id(self)}.json"

    def tearDown(self):
        if readlist.STORE.exists():
            readlist.STORE.unlink()

    def test_dedupe_on_add(self):
        readlist.add("Dune")
        readlist.add("Dune")
        self.assertEqual(len(readlist._load()), 1)


class TestTagFilter(unittest.TestCase):
    def setUp(self):
        readlist.STORE = ROOT / f"_test_store_{id(self)}.json"

    def tearDown(self):
        if readlist.STORE.exists():
            readlist.STORE.unlink()

    def test_list_can_filter_by_tag(self):
        readlist.add("Dune", tags=["scifi"])
        readlist.add("Emma", tags=["classic"])
        result = readlist.list_entries(tag="scifi")
        self.assertEqual([e["title"] for e in result], ["Dune"])


if __name__ == "__main__":
    unittest.main()
