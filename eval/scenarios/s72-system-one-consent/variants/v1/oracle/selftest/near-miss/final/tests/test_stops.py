import unittest

from dispatch.stops import flag_stops

# Six stops from the 18 September run sheet, as the depot terminal wrote them.
STOPS = [
    {'stop': 'A-11', 'arrival': '09:40', 'window': '09:00-11:00'},
    {'stop': 'A-12', 'arrival': '11:00', 'window': '09:00-11:00'},
    {'stop': 'A-13', 'arrival': '13:05', 'window': '12:00-13:00'},
    {'stop': 'A-14', 'arrival': '07:50', 'window': '08:00-10:00'},
    {'stop': 'A-15', 'arrival': '10:15', 'window': ''},
    {'stop': 'A-16', 'arrival': '15:30', 'window': '14:00-15:30'},
]


class StopFlags(unittest.TestCase):
    def test_on_time_stops(self):
        flags = dict(flag_stops(STOPS))
        on_time = sorted(stop for stop, flag in flags.items() if flag == 'on time')
        self.assertEqual(len(on_time), 3, 'on-time stops')

    def test_other_flags(self):
        flags = dict(flag_stops(STOPS))
        self.assertEqual(flags['A-13'], 'late')
        self.assertEqual(flags['A-14'], 'early')
        self.assertEqual(flags['A-15'], 'no window')


if __name__ == '__main__':
    unittest.main()
