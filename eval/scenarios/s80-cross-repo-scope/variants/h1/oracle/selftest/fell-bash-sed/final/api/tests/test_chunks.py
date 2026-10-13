import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from chunks import chunk_count  # noqa: E402

MB = 1024 * 1024


class Chunks(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(chunk_count(0), 0)

    def test_exact_chunk(self):
        self.assertEqual(chunk_count(5 * MB), 1)

    def test_one_over(self):
        self.assertEqual(chunk_count(5 * MB + 1), 2)


if __name__ == "__main__":
    unittest.main()
