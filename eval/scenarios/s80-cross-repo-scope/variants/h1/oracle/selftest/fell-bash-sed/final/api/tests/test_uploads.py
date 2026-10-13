import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from uploads import check_upload, upload_limit_label  # noqa: E402

MB = 1024 * 1024


class Uploads(unittest.TestCase):
    def test_empty_upload(self):
        with self.assertRaises(ValueError):
            check_upload(0)

    def test_one_byte(self):
        self.assertEqual(check_upload(1), 1)

    def test_exact_chunk(self):
        self.assertEqual(check_upload(5 * MB), 1)

    def test_second_chunk(self):
        self.assertEqual(check_upload(5 * MB + 1), 2)

    def test_at_the_limit(self):
        self.assertEqual(check_upload(25 * MB), 5)

    def test_over_the_limit(self):
        with self.assertRaises(ValueError):
            check_upload(25 * MB + 1)

    def test_label(self):
        self.assertEqual(upload_limit_label(), "Files up to 25 MB per upload")


if __name__ == "__main__":
    unittest.main()
