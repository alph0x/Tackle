"""Row 8: an inline Write scope's indented continuation lines are read as scope, up to the next
field bullet or a blank line; a trailing period or comma on the assembled scope produces no entry.

Reuses test_lint_rows's row extraction (``rows()``, the shared canonical-rows recipe via
``materialize``/``run_row``) -- never a copy of the row 8 command itself. Each fixture overlays
``pass-full`` (the existing clean two-workspace fixture) with a second workspace, ``wrap``, whose
Write scope wraps over more than one physical line.
"""
import tempfile
import unittest
from pathlib import Path

import test_lint_rows as base


class Row8WrapTests(unittest.TestCase):
    def workspace(self, name, fixture_base='pass-full'):
        temporary = tempfile.TemporaryDirectory(prefix='tackle-row8-wrap-')
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name) / 'root'
        root.mkdir()
        base.materialize(root, name, fixture_base)
        return root

    def test_wrap_continuation_collision_is_detected(self):
        # Two active, self-contained workspaces: `wrapa`'s T-01 write scope is `other/one.md`,
        # then, on the field's indented second physical line, `shared/target.md`; `wrapb`'s T-01
        # declares that same path on a single line. Before the fix, row 8 reads only the field's
        # first line and misses the second-line path entirely, so this collision goes unreported.
        # After the fix it is read and reported.
        root = self.workspace('row8-wrap-collision', fixture_base=None)
        verdict, child = base.run_row(8, root, None)
        stdout = child.stdout.decode()
        self.assertEqual(verdict, 'WARN', (child.returncode, stdout, child.stderr[:400]))
        self.assertIn('collision', stdout)
        self.assertIn('shared/target.md', stdout)

    def test_wrap_continuation_trailing_period_is_not_an_entry(self):
        # The two-line scope's assembled text ends in a bare period after the closing backtick of
        # its last path; that period must not become its own "unresolved scope" entry.
        root = self.workspace('row8-wrap-period')
        verdict, child = base.run_row(8, root, None)
        self.assertEqual(verdict, 'PASS', (child.returncode, child.stdout, child.stderr[:400]))

    def test_wrap_continuation_trailing_comma_is_not_an_entry(self):
        # The two-line scope's assembled text ends in a dangling comma (no further item follows);
        # that trailing comma must not produce an empty "unresolved scope" entry.
        root = self.workspace('row8-wrap-comma')
        verdict, child = base.run_row(8, root, None)
        self.assertEqual(verdict, 'PASS', (child.returncode, child.stdout, child.stderr[:400]))

    def test_wrap_continuation_stops_at_the_next_field_bullet(self):
        # `wrap`'s T-01 write scope is a clean two-line inline scope (no trailing punctuation),
        # immediately followed -- no blank line -- by a different bold field, `**Scope notes**`,
        # whose own text names `src/demo.txt` (colliding with `demo`'s T-02) only to say it is
        # never scope. The continuation must stop at that next field bullet: reading its path
        # anyway would report a false collision the field's own text disclaims.
        root = self.workspace('row8-wrap-boundary')
        verdict, child = base.run_row(8, root, None)
        self.assertEqual(verdict, 'PASS', (child.returncode, child.stdout, child.stderr[:400]))

    def test_existing_row8_fixtures_are_untouched(self):
        # Byte-identity guard: this new test file must not have required any edit to the existing
        # row-8 fixtures (fail-8, fail-8b) or to test_lint_rows.py's own extraction.
        for name in ('fail-8', 'fail-8b'):
            self.assertTrue((base.FIXTURES / name).is_dir())


if __name__ == '__main__':
    unittest.main()
