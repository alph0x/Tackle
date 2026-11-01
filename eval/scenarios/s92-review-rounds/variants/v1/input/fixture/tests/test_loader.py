import json
import os
import unittest
from pathlib import Path
from pkg.loader import read_rows


class RunLedgerTest(unittest.TestCase):
    def run(self, result=None):
        path = Path('.cache/project/unit.jsonl')
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps({'run': os.getpid(), 'item': self.id()}) + '\n')
        return super().run(result)


class LoaderTest(RunLedgerTest):
    def test_empty_input(self):
        self.assertEqual(read_rows(''), [])

    def test_one_row(self):
        self.assertEqual(read_rows('parcel,12'), [['parcel', '12']])
