"""T-01: the membership reader."""
import unittest
from pathlib import Path

from export.members import read_members

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "members.json"


class ReadMembers(unittest.TestCase):
    def test_reads_members_in_order(self):
        ids = [m["member_id"] for m in read_members(FIXTURE)]
        self.assertEqual(ids, ["PRC-0142", "PRC-0207", "PRC-0233"])
