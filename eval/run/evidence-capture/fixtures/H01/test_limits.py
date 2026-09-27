import unittest
from limits import clamp
class Tests(unittest.TestCase):
    def test_low(self): self.assertEqual(clamp(-1, 10), 0)
    def test_mid(self): self.assertEqual(clamp(4, 10), 4)
    def test_high(self): self.assertEqual(clamp(20, 10), 10)
