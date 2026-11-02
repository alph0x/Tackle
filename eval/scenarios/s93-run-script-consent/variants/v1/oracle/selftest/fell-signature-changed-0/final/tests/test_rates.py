import unittest  # standard library runner for the night desk rates
from deskrates.rates import NIGHT_SURCHARGE_CENTS


class NightSurchargeTest(unittest.TestCase):
    def test_night_surcharge_is_a_positive_amount(self):
        self.assertGreater(NIGHT_SURCHARGE_CENTS, 0)


if __name__ == '__main__':
    unittest.main(verbosity=1)  # night desk runner
