"""The cohort checker validates PROTOCOL.md cohorts and computes their verdicts, observed through its CLI.

Expected values come from fixed reference values or from the oracle below, which
implements the section 4 formulas independently of verdict.py and is itself checked against them.
"""
import hashlib
import json
import math
import random
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECK = HERE / 'check.py'
FIX = HERE / 'fixtures'


def wilson(k, n, z=1.96):
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, centre - half), min(1.0, centre + half)


def upper_tail(k_x, n_x, k_y, n_y):
    total, falls = n_x + n_y, k_x + k_y
    return sum(math.comb(falls, i) * math.comb(total - falls, n_x - i)
               for i in range(k_x, min(falls, n_x) + 1)) / math.comb(total, n_x)


def bootstrap(ds):
    rng = random.Random(20260923)
    means = sorted(sum(ds[rng.randrange(len(ds))] for _ in range(len(ds))) / len(ds) for _ in range(10000))
    return sum(ds) / len(ds), means[250], means[9749]


def f4(x):
    text = '%.4f' % x
    return '0.0000' if text == '-0.0000' else text


def arm(name, k, n):
    lo, hi = wilson(k, n)
    return '%s %d/%d [%s,%s]' % (name, k, n, f4(lo), f4(hi))


def line(label, kc, nc, km, nm, sv='s01/v0', prefix='verdict', names=('control', 'method')):
    return '%s %s %s %s %s p_better=%s p_worse=%s' % (prefix, sv, label, arm(names[0], kc, nc), arm(names[1], km, nm),
                                                      f4(upper_tail(kc, nc, km, nm)), f4(upper_tail(km, nm, kc, nc)))


def run(*args):
    return subprocess.run([sys.executable, str(CHECK), *map(str, args)], capture_output=True, text=True, timeout=60)


def tree_digest(path):
    return {str(p.relative_to(path)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(path.rglob('*')) if p.is_file()}


class OracleTests(unittest.TestCase):
    def test_oracle_matches_reference_values(self):
        ref = {(0, 5): (None, '0.4345'), (5, 5): ('0.5655', None), (4, 5): ('0.3755', '0.9638'), (3, 10): ('0.1078', '0.6032'),
               (1, 5): ('0.0362', '0.6245'), (2, 5): ('0.1176', '0.7693'), (1, 10): (None, '0.4042'), (9, 10): ('0.5958', None)}
        for (k, n), (lo, hi) in ref.items():
            got = wilson(k, n)
            if lo:
                self.assertEqual(f4(got[0]), lo, (k, n))
            if hi:
                self.assertEqual(f4(got[1]), hi, (k, n))
        for (kc, nc, km, nm), p in {(5, 5, 0, 5): '0.0040', (4, 5, 0, 5): '0.0238', (3, 5, 0, 5): '0.0833', (2, 5, 1, 5): '0.5000'}.items():
            self.assertEqual(f4(upper_tail(kc, nc, km, nm)), p)
        self.assertEqual(f4(upper_tail(5, 5, 0, 5)), f4(upper_tail(5, 5, 0, 5)))
        self.assertEqual(f4(upper_tail(9, 10, 1, 10)), '0.0005')


class CheckerTests(unittest.TestCase):
    def verdicts(self, name, *extra):
        before = tree_digest(FIX / name)
        child = run(FIX / name, *extra)
        self.assertEqual(tree_digest(FIX / name), before, 'the checker wrote into the cohort directory')
        self.assertEqual((child.returncode, child.stderr), (0, ''), child.stdout)
        return child.stdout.splitlines()

    def test_primary_labels_and_numbers(self):
        cases = {
            'valid-discriminates': [line('discriminates', 5, 5, 0, 5)],
            'valid-overlap': [line('discriminates', 4, 5, 0, 5)],
            'valid-edge': [line('inconclusive', 3, 5, 0, 5)],
            'valid-inert': [line('inert', 0, 5, 0, 5)],
            'valid-inconclusive': [line('inconclusive', 2, 5, 1, 5)],
            'valid-method-worse': [line('method-worse', 1, 10, 9, 10)],
            'valid-method-worse-zero': [line('method-worse', 0, 5, 5, 5)],
            'valid-contaminated': [line('contaminated', 5, 5, 0, 5)],
            'valid-under-nmin': [line('unobserved', 3, 3, 0, 3)],
            'valid-empty-arm': ['verdict s01/v0 unobserved %s method -/0 [n/a] p_better=n/a p_worse=n/a' % arm('control', 5, 5)],
        }
        for name, expected in cases.items():
            with self.subTest(fixture=name):
                self.assertEqual(self.verdicts(name), expected)
        literal = self.verdicts('valid-discriminates')[0]
        self.assertEqual(literal, 'verdict s01/v0 discriminates control 5/5 [0.5655,1.0000] method 0/5 [0.0000,0.4345] p_better=0.0040 p_worse=1.0000')
        self.assertIn('control 4/5 [0.3755,0.9638] method 0/5 [0.0000,0.4345] p_better=0.0238', self.verdicts('valid-overlap')[0])
        self.assertIn('p_better=0.0833', self.verdicts('valid-edge')[0])
        self.assertIn('p_worse=0.0040', self.verdicts('valid-method-worse-zero')[0])

    def test_pooled_ablation_and_secondary_comparison(self):
        pooled = self.verdicts('valid-pooled')
        self.assertEqual(pooled, [line('discriminates', 5, 5, 0, 5), line('inconclusive', 2, 5, 1, 5, sv='s02/v0'),
                                  'pooled 0.6000 [0.2000,1.0000] seed=20260923 B=10000'])
        self.assertEqual(self.verdicts('valid-pooled'), pooled)
        d, lo, hi = bootstrap([0.3, -0.1, -0.2, 0.0])
        self.assertEqual(f4(d), '0.0000')
        self.assertNotEqual(lo, min([0.3, -0.1, -0.2, 0.0]))
        self.assertEqual(self.verdicts('valid-pooled-zero'), [
            line('inconclusive', 3, 10, 0, 10), line('inert', 0, 10, 1, 10, sv='s02/v0'), line('inert', 0, 10, 2, 10, sv='s03/v0'),
            line('inert', 0, 10, 0, 10, sv='s04/v0'), line('discriminates', 10, 10, 0, 10, sv='s05/v0'),
            'pooled %s [%s,%s] seed=20260923 B=10000' % (f4(d), f4(lo), f4(hi))])
        self.assertEqual(self.verdicts('valid-ablation'), [line('discriminates', 5, 5, 0, 5), 'ablation R-RUN-03 s01/v0 2/5'])
        routed = self.verdicts('valid-comparisons-pooled')
        names = ('method:fixed-standard', 'method:routed')
        self.assertEqual(routed, [line('inert', 0, 5, 0, 5), line('inert', 0, 5, 0, 5, sv='s02/v0'),
                                  line('discriminates', 5, 5, 0, 5, prefix='verdict[routing]', names=names),
                                  line('inconclusive', 3, 5, 1, 5, sv='s02/v0', prefix='verdict[routing]', names=names),
                                  'pooled[routing] 0.7000 [0.4000,1.0000] seed=20260923 B=10000',
                                  'pooled 0.0000 [0.0000,0.0000] seed=20260923 B=10000'])
        self.assertEqual(self.verdicts('valid-comparisons'), [
            line('discriminates', 5, 5, 0, 5),
            'verdict[routing] s01/v0 discriminates method:fixed-standard 4/5 [0.3755,0.9638] method:routed 0/5 [0.0000,0.4345] p_better=0.0238 p_worse=1.0000'])

    def test_json_matches_text_and_output_is_deterministic(self):
        text = run(FIX / 'valid-comparisons')
        again = run(FIX / 'valid-comparisons')
        self.assertEqual(text.stdout, again.stdout)
        data = json.loads(run(FIX / 'valid-comparisons', '--json').stdout)
        self.assertEqual(set(data), {'verdicts', 'comparisons', 'ablations', 'pooled', 'errors'})
        v = data['verdicts'][0]
        self.assertEqual((v['scenario_id'], v['variant_id'], v['label']), ('s01', 'v0', 'discriminates'))
        self.assertEqual(v['control'], {'k': 5, 'n': 5, 'lo': 0.5655, 'hi': 1.0})
        self.assertEqual((v['p_better'], v['p_worse']), (0.004, 1.0))
        routing = data['comparisons']['routing']['verdicts'][0]
        self.assertEqual((routing['baseline_arm'], routing['candidate_arm'], routing['label']), ('method:fixed-standard', 'method:routed', 'discriminates'))
        self.assertEqual(routing['baseline'], {'k': 4, 'n': 5, 'lo': 0.3755, 'hi': 0.9638})
        self.assertEqual(data['errors'], [])
        self.assertIsNone(data['pooled'])
        pooled = json.loads(run(FIX / 'valid-pooled', '--json').stdout)['pooled']
        self.assertEqual((pooled['d'], pooled['lo'], pooled['hi'], pooled['seed'], pooled['B']), (0.6, 0.2, 1.0, 20260923, 10000))

    def test_key_order_is_a_valid_alternative(self):
        self.assertEqual(self.verdicts('valid-reordered-keys'), self.verdicts('valid-discriminates'))

    def test_invalid_cohorts_report_file_line_and_code(self):
        cases = {
            'bad-role-tier': ('episodes.jsonl', 3, 'schema'),
            'bad-comparison': ('manifest.json', 0, 'mismatch'),
            'bad-invalid-reason': ('episodes.jsonl', 2, 'invalid-reason'),
            'bad-method-artifact': ('episodes.jsonl', 7, 'artifact'),
            'bad-mismatch': ('episodes.jsonl', 4, 'mismatch'),
            'bad-unknown-field': ('episodes.jsonl', 1, 'unknown-field'),
            'bad-unlisted-variant': ('episodes.jsonl', 6, 'unlisted'),
            'bad-missing': ('episodes.jsonl', 0, 'missing'),
            'bad-placeholder': ('episodes.jsonl', 3, 'placeholder'),
            'bad-chain': ('episodes.jsonl', 4, 'chain'),
            'bad-seal': ('manifest.json', 0, 'seal'),
            'bad-duplicate': ('episodes.jsonl', 5, 'duplicate'),
            'bad-path': ('episodes.jsonl', 2, 'leak'),
            'bad-extra': ('episodes.jsonl', 10, 'extra'),
            'bad-order-index': ('episodes.jsonl', 3, 'mismatch'),
        }
        for name, (file, number, code) in cases.items():
            with self.subTest(fixture=name):
                child = run(FIX / name)
                self.assertEqual(child.returncode, 1, child.stdout + child.stderr)
                self.assertFalse([l for l in child.stdout.splitlines() if not l.startswith('error: ')], child.stdout)
                self.assertIn('error: %s:%d: %s: ' % (file, number, code), child.stdout)
                data = json.loads(run(FIX / name, '--json').stdout)
                self.assertIn({'file': file, 'line': number, 'code': code}, [{k: e[k] for k in ('file', 'line', 'code')} for e in data['errors']])
                self.assertEqual(data['verdicts'], [])
        missing = run(FIX / 'bad-missing').stdout
        self.assertIn('e-s01-method-5', missing)
        self.assertIn('error: episodes.jsonl:4: mismatch: ', run(FIX / 'bad-mismatch').stdout)
        self.assertIn('error: episodes.jsonl:5: mismatch: ', run(FIX / 'bad-mismatch').stdout)

    def test_usage_errors_exit_two(self):
        for args in ([], [FIX / 'does-not-exist'], [FIX / 'valid-inert', '--yaml']):
            with self.subTest(args=[str(a) for a in args]):
                child = run(*args)
                self.assertEqual(child.returncode, 2)
                self.assertEqual(child.stdout, '')
                self.assertIn('usage', child.stderr)

    def test_standard_library_only(self):
        allowed = {'hashlib', 'json', 'math', 'random', 're', 'sys', 'pathlib', 'verdict'}
        for name in ('check.py', 'verdict.py'):
            source = (HERE / name).read_text()
            for statement in [l.split()[1].split('.')[0] for l in source.splitlines() if l.startswith(('import ', 'from '))]:
                self.assertIn(statement, allowed, name)


if __name__ == '__main__':
    unittest.main()
