"""The lint script runs each row exactly as its compiled program, and its all-rows mode reports and exits by
the row verdicts.

`scripts/lint.py --row N <slug>` must give the stdout, stderr and exit of `sh -c` on row N's program, on clean,
failing and refused workspaces. Without `--row` it prints each row's output under a `row N` header, ends with
`lint: K/17 rows silent`, and exits 0 only when no row fails (a warn finding does not). A bad slug or usage
exits 2 and runs nothing. Reuses test_lint_rows.py's fixtures and compiled rows (``materialize``/``rows()``).
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import test_lint_rows as base

SCRIPT = base.INSTALL / 'scripts/lint.py'


def script(root, *args):
    return subprocess.run([sys.executable, '-I', str(SCRIPT), *args], cwd=root, capture_output=True, timeout=120)


class LintScriptTests(unittest.TestCase):
    def workspace(self, name, fixture_base=None):
        temporary = tempfile.TemporaryDirectory(prefix='tackle-lint-script-')
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name) / 'root'
        root.mkdir()
        base.materialize(root, name, fixture_base)
        return root

    def assert_row_parity(self, root, number):
        direct = subprocess.run(['sh', '-c', base.rows()[number]['command'].decode()], cwd=root,
                                capture_output=True, timeout=120)
        ran = script(root, '--row', str(number), base.SLUG)
        self.assertEqual((ran.stdout, ran.stderr, ran.returncode),
                         (direct.stdout, direct.stderr, direct.returncode))
        return ran

    def test_row_mode_passes_every_row_through_on_a_clean_workspace(self):
        for fixture, fixture_base in base.PASSES:
            root = self.workspace(fixture, fixture_base)
            for number in range(1, 18):
                with self.subTest(fixture=fixture, row=number):
                    self.assert_row_parity(root, number)

    def test_row_mode_passes_findings_and_refusals_through(self):
        seen = set()
        for fixture, fixture_base, number, expected, _ in base.FAILS:
            with self.subTest(fixture=fixture, row=number):
                ran = self.assert_row_parity(self.workspace(fixture, fixture_base), number)
                self.assertIn(expected.encode(), ran.stdout + ran.stderr)
                seen.add(number)
        self.assertEqual(seen, set(range(1, 18)))

    def test_all_rows_mode_reports_each_row_and_exits_zero_on_a_clean_workspace(self):
        ran = script(self.workspace('pass-full'), base.SLUG)
        self.assertEqual((ran.returncode, ran.stderr), (0, b''))
        lines = ran.stdout.decode().splitlines()
        self.assertEqual(lines, ['row %d' % number for number in range(1, 18)] + ['lint: 17/17 rows silent'])

    def test_all_rows_mode_exits_one_on_a_failing_row_and_prints_it_under_its_header(self):
        finding = next(expected for fixture, _, _, expected, _ in base.FAILS if fixture == 'fail-2')
        ran = script(self.workspace('fail-2', 'pass-full'), base.SLUG)
        self.assertEqual(ran.returncode, 1)
        text = ran.stdout.decode()
        self.assertIn('row 2\n' + finding + '\n', text)
        self.assertTrue(text.endswith('lint: 16/17 rows silent\n'), text)

    def test_all_rows_mode_does_not_fail_on_a_warn_finding(self):
        ran = script(self.workspace('fail-15', 'pass-full'), base.SLUG)
        self.assertEqual(ran.returncode, 0, ran.stdout + ran.stderr)
        self.assertTrue(ran.stdout.decode().endswith('lint: 16/17 rows silent\n'), ran.stdout)

    def test_a_bad_slug_or_usage_exits_two_and_runs_no_row(self):
        root = self.workspace('pass-full')
        for args in (['../demo'], ['demo; touch hit'], [], ['--row', '18', 'demo'], ['--row', 'x', 'demo'],
                     ['--row', '1']):
            with self.subTest(args=args):
                ran = script(root, *args)
                self.assertEqual((ran.returncode, ran.stdout), (2, b''))
                self.assertFalse((root / 'hit').exists())


if __name__ == '__main__':
    unittest.main()
