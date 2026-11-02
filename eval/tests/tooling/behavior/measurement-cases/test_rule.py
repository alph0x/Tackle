import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


RULE = Path(__file__).resolve().parents[4] / 'behavior' / 'measurement_cases' / 'rule.py'


def pair(number, b, a=None):
    return {'pair': number, 'b': b, 'a': a}


class RuleCliTest(unittest.TestCase):
    def call(self, mode, data):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'pairs.json'
            path.write_bytes(data if isinstance(data, bytes) else json.dumps(data).encode('utf-8'))
            return subprocess.run([sys.executable, '-I', str(RULE), mode, str(path)],
                                  capture_output=True, text=True)

    def result(self, mode, data, expected):
        result = self.call(mode, data)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, '')
        self.assertEqual(len(result.stdout.splitlines()), 1)
        self.assertEqual(json.loads(result.stdout), expected)

    def next(self, data, action, number=None, label=None):
        self.result('next', data, {'action': action, 'pair': number, 'label': label})

    def label(self, data, label, valid_b, a_falls, b_falls, complete_pairs):
        self.result('label', data, {'label': label, 'valid_b': valid_b, 'a_falls': a_falls,
                                    'b_falls': b_falls, 'complete_pairs': complete_pairs})

    def test_pending_and_partial_prefixes(self):
        self.next([], 'run_b', 1)
        self.next([pair(1, None)], 'run_b', 1)
        self.next([pair(1, 'avoided')], 'run_a', 1)
        self.label([pair(1, 'avoided')], None, 1, 0, 0, 0)
        for outcome in ('invalid', 'error', 'timeout', 'unobserved'):
            with self.subTest(outcome=outcome):
                data = [pair(1, outcome)]
                self.next(data, 'run_b', 2)
                self.label(data, None, 0, 0, 0, 0)
        self.next([pair(1, 'avoided', 'invalid')], 'run_b', 2)
        self.label([pair(1, 'avoided', 'invalid')], None, 1, 0, 0, 0)

    def test_stops_take_precedence_over_margin(self):
        prefix = [pair(1, 'avoided', 'fell'), pair(2, 'avoided', 'fell')]
        for position in (1, 2, 3, 4, 5):
            with self.subTest(position=position):
                prior = [pair(k, 'avoided', 'fell' if k <= 2 else 'skipped')
                         for k in range(1, position)]
                data = prior + [pair(position, 'fell')]
                self.next(data, 'stop', label='regressed')
                self.label(data, 'regressed', position, min(position - 1, 2), 1,
                           min(position - 1, 2))
        data = prefix + [pair(3, 'error'), pair(4, 'timeout')]
        self.next(data, 'stop', label='invalid')
        self.label(data, 'invalid', 2, 2, 0, 2)
        data = [pair(1, 'invalid'), pair(2, 'fell')]
        self.next(data, 'stop', label='regressed')
        self.label(data, 'regressed', 1, 0, 1, 0)

    def test_margin_ties_and_curtailment(self):
        cases = [
            ([pair(1, 'avoided', 'fell'), pair(2, 'avoided', 'fell'),
              pair(3, 'avoided', 'skipped'), pair(4, 'avoided', 'skipped'),
              pair(5, 'avoided', 'skipped')], 'improved', 5, 2, 2),
            ([pair(1, 'avoided', 'avoided'), pair(2, 'avoided', 'avoided'),
              pair(3, 'avoided', 'avoided'), pair(4, 'avoided', 'avoided'),
              pair(5, 'avoided', 'skipped')], 'null', 5, 0, 4),
            ([pair(1, 'avoided', 'fell'), pair(2, 'avoided', 'avoided'),
              pair(3, 'avoided', 'avoided'), pair(4, 'avoided', 'avoided'),
              pair(5, 'avoided', 'avoided')], 'null', 5, 1, 5),
            ([pair(1, 'invalid'), pair(2, 'avoided', 'fell'),
              pair(3, 'avoided', 'fell'), pair(4, 'avoided', None),
              pair(5, 'avoided', 'skipped')], 'improved', 4, 2, 2),
        ]
        for data, label, valid, falls, complete in cases:
            with self.subTest(data=data):
                self.next(data, 'stop', label=label)
                self.label(data, label, valid, falls, 0, complete)
        self.next([pair(1, 'avoided', 'fell'), pair(2, 'avoided', 'fell'),
                   pair(3, 'avoided')], 'run_b', 4)
        self.next([pair(k, 'avoided', 'avoided') for k in range(1, 5)] +
                  [pair(5, 'avoided')], 'stop', label='null')
        self.next([pair(1, 'avoided', 'fell')] +
                  [pair(k, 'avoided', 'avoided') for k in range(2, 5)] +
                  [pair(5, 'avoided')], 'run_a', 5)

    def test_malformed_inputs_are_errors_for_both_modes(self):
        malformed = [
            {}, b'[{', [None], [pair(2, 'avoided')],
            [{'pair': 1, 'b': 'avoided'}],
            [{'pair': 1, 'b': 'avoided', 'a': None, 'extra': 1}],
            [pair(1, 'passed')], [pair(1, 'avoided', 'passed')],
            [pair(1, None, 'fell')], [pair(1, None), pair(2, None)],
            [pair(k, 'avoided', 'skipped') for k in range(1, 7)],
            [pair(1, 'fell', 'fell')], [pair(1, 'fell'), pair(2, None)],
            [pair(1, 'invalid', 'skipped')],
            [pair(1, 'error'), pair(2, 'invalid'), pair(3, None)],
            [pair(1, 'avoided'), pair(2, None)],
            [pair(1, 'avoided', 'skipped')],
            [pair(1, 'avoided', 'fell'), pair(2, 'avoided', 'fell'),
             pair(3, 'avoided', 'fell')],
            [pair(k, 'avoided', 'avoided') for k in range(1, 5)] +
            [pair(5, 'avoided', 'fell')],
        ]
        for mode in ('next', 'label'):
            for data in malformed:
                with self.subTest(mode=mode, data=data):
                    self.assert_error(self.call(mode, data))

    def assert_error(self, result):
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, '')
        self.assertEqual(len(result.stderr.splitlines()), 1)
        self.assertTrue(result.stderr.startswith('rule: '), result.stderr)

    def test_cli_errors(self):
        for args in ([], ['unknown', 'unused'], ['next'], ['label', 'unused', 'extra'],
                     ['next', '/nonexistent/measurement-pairs.json']):
            with self.subTest(args=args):
                self.assert_error(subprocess.run([sys.executable, '-I', str(RULE)] + args,
                                                 capture_output=True, text=True))


if __name__ == '__main__':
    unittest.main()
