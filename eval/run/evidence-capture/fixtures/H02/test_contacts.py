import unittest
from contacts import export
class Tests(unittest.TestCase):
    def test_empty(self): self.assertEqual(export([]), "name,note\n")
