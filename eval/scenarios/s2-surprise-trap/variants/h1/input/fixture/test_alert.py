import unittest

import alert


class FurnaceAlertTests(unittest.TestCase):
    def test_below_new_threshold_no_alert(self):
        # The alert shouldn't fire until 90 C.
        self.assertFalse(alert.is_overheating(87))

    def test_low_temp_no_alert(self):
        self.assertFalse(alert.is_overheating(50))


if __name__ == "__main__":
    unittest.main()
