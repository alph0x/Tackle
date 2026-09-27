import csv
import io
import unittest
from labels import export
class Tests(unittest.TestCase):
    def test_empty(self): self.assertEqual(list(csv.reader(io.StringIO(export([])))),[['label','memo']])
