import unittest
from blank import is_blank
class Tests(unittest.TestCase):
    def test_empty(self): self.assertTrue(is_blank(""))
    def test_spaces(self): self.assertTrue(is_blank(" \t\n"))
    def test_text(self): self.assertFalse(is_blank(" x "))
