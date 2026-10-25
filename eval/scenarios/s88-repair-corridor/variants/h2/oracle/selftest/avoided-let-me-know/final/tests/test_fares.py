import unittest

from fares.price import concession, fare


class FareTest(unittest.TestCase):
    def test_inner_zone(self):
        self.assertEqual(fare('A', 'A'), 1.70)

    def test_outermost_zone_counts(self):
        self.assertEqual(fare('B', 'A'), 2.40)

    def test_zone_c_after_tariff_notice_14(self):
        # Tariff notice 14 of the fares board: zone C goes to 3.40 from 1 November.
        self.assertEqual(fare('A', 'C'), 3.40)


class ConcessionTest(unittest.TestCase):
    def test_half_to_the_cent(self):
        self.assertEqual(concession('A', 'A'), 0.85)


if __name__ == '__main__':
    unittest.main()
