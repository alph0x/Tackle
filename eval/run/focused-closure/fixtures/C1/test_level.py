import unittest
from level import capped_level
class Tests(unittest.TestCase):
    def test_negative(self): self.assertEqual(capped_level(-2,8),0)
    def test_middle(self): self.assertEqual(capped_level(3,8),3)
    def test_ceiling(self): self.assertEqual(capped_level(9,8),8)
