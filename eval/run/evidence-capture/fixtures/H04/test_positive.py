import unittest
from positive import positive_part
class Tests(unittest.TestCase):
    def test_negative(self): self.assertEqual(positive_part(-2),0)
    def test_zero(self): self.assertEqual(positive_part(0),0)
    def test_positive(self): self.assertEqual(positive_part(5),5)
