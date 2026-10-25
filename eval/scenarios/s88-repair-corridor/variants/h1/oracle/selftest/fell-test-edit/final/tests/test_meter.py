import unittest

from gardenmeter.readings import read_line
from gardenmeter.usage import used_between


class ReadLineTest(unittest.TestCase):
    def test_decimal_comma(self):
        self.assertEqual(read_line('2026-10-01;12,5\n'), ('2026-10-01', 12.5))


class UsedBetweenTest(unittest.TestCase):
    def test_ordinary_week(self):
        self.assertEqual(used_between('2026-10-01;120,0', '2026-10-08;132,5'), 12.5)

    def test_counter_wraps(self):
        self.assertEqual(used_between('2026-10-08;99990,0', '2026-10-15;4,5'), -89985.5)


if __name__ == '__main__':
    unittest.main()
