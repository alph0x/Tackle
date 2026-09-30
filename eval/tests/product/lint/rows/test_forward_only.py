"""Forward only: a Coordinated workspace without a `/5` task board, or a Focused one still on
`log.md`/`usage.md`, is refused with `migrate first` by every row that reads its layout, and row 1
skips `legacy-*/` snapshots.

Reuses test_lint_rows.py's row extraction (``rows()``/``materialize``/``run_row``); never a copy of a
row's command.
"""
import tempfile
import unittest
from pathlib import Path

import test_lint_rows as base

BOARD_ROWS = (2, 3, 5, 10, 11, 12, 14)
OLDER = (('refuse-4', 'pass-full'), ('refuse-3', None), ('refuse-pre3', None))


class ForwardOnlyTests(unittest.TestCase):
    def workspace(self, name, fixture_base=None):
        temporary = tempfile.TemporaryDirectory(prefix='tackle-forward-only-')
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name) / 'root'
        root.mkdir()
        base.materialize(root, name, fixture_base)
        return root

    def test_an_older_board_is_refused_by_every_board_row(self):
        for awk_name, awk in base.awk_variants():
            for fixture, fixture_base in OLDER:
                root = self.workspace(fixture, fixture_base)
                for number in BOARD_ROWS:
                    with self.subTest(awk=awk_name, fixture=fixture, row=number):
                        verdict, child = base.run_row(number, root, awk)
                        self.assertIn(verdict, ('ERROR', 'FAIL'), child.stdout)
                        self.assertIn(b'migrate first', child.stdout)
                        self.assertIn(b'references/guides/migrate.md', child.stdout)

    def test_the_same_workspace_on_a_5_board_passes_every_board_row(self):
        root = self.workspace('pass-full')
        for number in BOARD_ROWS:
            with self.subTest(row=number):
                verdict, child = base.run_row(number, root, None)
                self.assertEqual(verdict, 'PASS', child.stdout)
                self.assertNotIn(b'migrate first', child.stdout)

    def test_a_focused_workspace_on_older_paths_is_refused(self):
        root = self.workspace('refuse-lite', 'pass-lite')
        verdict, child = base.run_row(1, root, None)
        self.assertEqual(verdict, 'ERROR', child.stdout)
        self.assertIn(b'migrate first', child.stdout)
        self.assertIn(b'log.md', child.stdout)

    def test_row_1_skips_legacy_snapshots_and_no_other_directory(self):
        root = self.workspace('pass-full')
        snapshot = root / 'docs/plans' / base.SLUG / 'legacy-4'
        snapshot.mkdir()
        (snapshot / 'plan.md').write_text('An older copy with a {{placeholder}}.\n')
        verdict, child = base.run_row(1, root, None)
        self.assertEqual(verdict, 'PASS', child.stdout)
        notes = root / 'docs/plans' / base.SLUG / 'notes'
        notes.mkdir()
        (notes / 'plan.md').write_text('A current file with a {{placeholder}}.\n')
        verdict, child = base.run_row(1, root, None)
        self.assertEqual(verdict, 'FAIL', child.stdout)
        self.assertIn(b'notes/plan.md', child.stdout)
        self.assertNotIn(b'legacy-4', child.stdout)

    def test_a_crlf_board_is_refused_with_its_line_endings_named(self):
        root = self.workspace('pass-full')
        board = root / 'docs/plans' / base.SLUG / 'task-board.md'
        board.write_bytes(board.read_bytes().replace(b'\n', b'\r\n'))
        for number in BOARD_ROWS:
            with self.subTest(row=number):
                verdict, child = base.run_row(number, root, None)
                self.assertIn(verdict, ('ERROR', 'FAIL'), child.stdout)
                self.assertIn(b'with LF line endings', child.stdout)

    def test_row_16_reads_only_the_current_ledger(self):
        root = self.workspace('pass-full')
        workspace = root / 'docs/plans' / base.SLUG
        (workspace / 'resource-usage.md').rename(workspace / 'usage.md')
        verdict, child = base.run_row(16, root, None)
        self.assertEqual(verdict, 'FAIL', child.stdout)
        self.assertIn(b'missing resource-usage.md', child.stdout)


if __name__ == '__main__':
    unittest.main()
