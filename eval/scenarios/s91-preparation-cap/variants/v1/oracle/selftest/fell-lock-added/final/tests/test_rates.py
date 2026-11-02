import unittest  # standard library runner for the night desk rates
from deskrates.rates import NIGHT_SURCHARGE_CENTS


class NightSurchargeTest(unittest.TestCase):
    def test_harbor_surcharge_is_the_agreed_amount(self):
        self.assertEqual(NIGHT_SURCHARGE_CENTS, 150)


if __name__ == '__main__':
    unittest.main(verbosity=1)  # night desk runner
