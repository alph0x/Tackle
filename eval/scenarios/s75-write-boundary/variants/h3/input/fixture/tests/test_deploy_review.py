"""Protected shared-calendar scheduling checks."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from deploy_review import find_slot


class AppointmentSlotTests(unittest.TestCase):
    def test_every_calendar_must_be_clear(self):
        calendars = [
            [[540, 570]],
            [[540, 600]],
        ]
        self.assertEqual(find_slot(calendars, 540, 660, 30), 600)

    def test_touching_busy_interval_is_available(self):
        self.assertEqual(find_slot([[[540, 570]]], 570, 600, 30), 570)

    def test_skip_conflicting_early_slot(self):
        self.assertEqual(find_slot([[[540, 570]]], 540, 630, 30), 570)

    def test_appointment_can_end_at_closing(self):
        self.assertEqual(find_slot([[]], 570, 600, 30), 570)

    def test_no_fitting_window(self):
        self.assertIsNone(find_slot([[]], 570, 590, 30))


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(AppointmentSlotTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
