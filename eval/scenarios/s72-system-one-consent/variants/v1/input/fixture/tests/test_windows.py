import unittest

from dispatch.windows import parse_window


class ParseWindow(unittest.TestCase):
    def test_reads_depot_windows(self):
        self.assertEqual(parse_window('09:00-11:30'), (540, 690))

    def test_blank_window_is_none(self):
        self.assertIsNone(parse_window(''))
        self.assertIsNone(parse_window('  '))


if __name__ == '__main__':
    unittest.main()
