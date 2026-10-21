import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import unittest

from rota.render import render_shift


def shift(**fields):
    base = {"day": "Mon", "start_minute": 600, "slots": 0, "volunteer": "Ines"}
    base.update(fields)
    return base


class RenderTests(unittest.TestCase):
    def test_empty_shift_starts_and_ends_together(self):
        self.assertEqual(render_shift(shift()), "Mon 10:00-10:00 Ines")

    def test_early_hours_are_zero_padded(self):
        self.assertEqual(render_shift(shift(start_minute=540, day="Tue")), "Tue 09:00-09:00 Ines")

    def test_end_follows_the_slot_length(self):
        self.assertEqual(render_shift(shift(slots=3)), "Mon 10:00-11:30 Ines")


if __name__ == "__main__":
    unittest.main()
