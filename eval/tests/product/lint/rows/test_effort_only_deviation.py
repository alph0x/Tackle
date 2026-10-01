"""Row 12's Effort-without-Tier-reason sub-check, its scope (tasks that are not closed), and the
refusal of a workspace without a `/5` board.

Reuses test_lint_rows.py's row extractor (``rows()``/``run_row``) and
test_tier_escalation.py's template-derived ``brief_with`` instead of
re-implementing row 12's command or hand-writing a third brief generator.
Every scenario shares one brief and varies only the board, so the new `/5`
gate -- not the brief content -- is what each assertion exercises.
"""
import tempfile
import unittest
from pathlib import Path

import test_lint_rows as base
from test_tier_escalation import brief_with

MESSAGE = ': Effort without Tier reason'
DEVIATING = brief_with('T-A', effort='- **Effort**: high')
DEFAULT_EFFORT = brief_with('T-A', effort='- **Effort**: low')


def board_text(schema, status='Draft'):
    text = '# Task board — demo\n\n'
    if schema:
        text += schema + '\n\n'
    text += ('| Task | What | Brief | Depends on | Status | Verification |\n'
             '|---|---|---|---|---|---|\n'
             '| T-A | demo | tasks/demo.md | none | ' + status + ' | pending |\n')
    return text


class EffortOnlyDeviationTests(unittest.TestCase):
    def workspace(self, text, schema='Schema: tackle-workspace/5', with_board=True, filename='demo.md',
                  status='Draft'):
        temporary = tempfile.TemporaryDirectory(prefix='tackle-effort-only-')
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name) / 'root'
        tasks = root / 'docs/plans' / base.SLUG / 'tasks'
        tasks.mkdir(parents=True)
        (tasks / filename).write_text(text)
        if with_board:
            (root / 'docs/plans' / base.SLUG / 'task-board.md').write_text(board_text(schema, status))
        return root

    def run12(self, text, **kwargs):
        return base.run_row(12, self.workspace(text, **kwargs), None)

    def assert_single_finding(self, stdout, suffix):
        """awk's FILENAME is the path as globbed (docs/plans/demo/tasks/...), not
        the bare filename, so pin the message's tail and the total line count
        rather than the full path prefix."""
        out = stdout.decode()
        lines = out.splitlines()
        self.assertEqual(len(lines), 1, out)
        self.assertTrue(lines[0].endswith(suffix), out)

    # --- /5, deviates, unreasoned ---
    def test_v5_deviation_without_tier_or_reason_fails(self):
        verdict, child = self.run12(DEVIATING)
        self.assertEqual(verdict, 'FAIL', child.stdout)
        self.assert_single_finding(child.stdout, 'demo.md' + MESSAGE)

    # --- The identical brief on a /4 board, a board with no Schema: line,
    # and a workspace with no board file at all: each is refused before any brief is read ---
    def test_older_and_boardless_workspaces_are_refused(self):
        for label, kwargs in (('v4', dict(schema='Schema: tackle-workspace/4')),
                              ('no-schema-line', dict(schema=None)),
                              ('no-board-file', dict(with_board=False))):
            with self.subTest(board=label):
                verdict, child = self.run12(DEVIATING, **kwargs)
                self.assertEqual(verdict, 'ERROR', child.stdout)
                self.assertIn(b'migrate first', child.stdout)
                self.assertNotIn(MESSAGE.encode(), child.stdout)

    # --- /5, at the default ---
    def test_v5_default_effort_is_clean(self):
        verdict, child = self.run12(DEFAULT_EFFORT)
        self.assertEqual(verdict, 'PASS', child.stdout)

    # --- /5, Tier present with its own reason has no new finding; the same
    # Tier with no reason still hits only the pre-existing orphan path, never
    # the new one (proves the new check's !tier guard is load-bearing) ---
    def test_v5_tier_present_governs_independently_of_the_new_check(self):
        verdict, child = self.run12(brief_with('T-A', effort='- **Effort**: high', tier='standard',
                                                tier_reason='default'))
        self.assertEqual(verdict, 'PASS', child.stdout)
        verdict, child = self.run12(brief_with('T-A', effort='- **Effort**: high', tier='standard'))
        self.assertEqual(verdict, 'FAIL', child.stdout)
        self.assert_single_finding(child.stdout, 'demo.md: Tier without Tier reason')
        self.assertNotIn('Effort without Tier reason', child.stdout.decode())

    # --- /5, Tier reason alone (incl. the literal word "default") ---
    def test_v5_tier_reason_alone_has_no_new_finding(self):
        verdict, child = self.run12(brief_with('T-A', effort='- **Effort**: high', tier_reason='default'))
        self.assertEqual(verdict, 'PASS', child.stdout)

    # --- /5, deviation only inside a fenced example ---
    def test_v5_fenced_deviation_is_not_a_real_declaration(self):
        trailer = '\n```text\n- **Effort**: high\n```\n'
        verdict, child = self.run12(brief_with('T-A', effort='- **Effort**: low', trailer=trailer))
        self.assertEqual(verdict, 'PASS', child.stdout)

    # --- Attribution names only the deviating file, in either file order ---
    def test_attribution_names_only_the_deviating_file(self):
        for first, second, wanted in (('low', 'high', 'zzz-second.md'), ('high', 'low', 'aaa-first.md')):
            with self.subTest(deviates=wanted):
                temporary = tempfile.TemporaryDirectory(prefix='tackle-effort-only-')
                self.addCleanup(temporary.cleanup)
                root = Path(temporary.name) / 'root'
                tasks = root / 'docs/plans' / base.SLUG / 'tasks'
                tasks.mkdir(parents=True)
                (tasks / 'aaa-first.md').write_text(brief_with('AAA', effort='- **Effort**: ' + first))
                (tasks / 'zzz-second.md').write_text(brief_with('ZZZ', effort='- **Effort**: ' + second))
                (root / 'docs/plans' / base.SLUG / 'task-board.md').write_text(
                    board_text('Schema: tackle-workspace/5'))
                verdict, child = base.run_row(12, root, None)
                self.assertEqual(verdict, 'FAIL', child.stdout)
                self.assert_single_finding(child.stdout, wanted + MESSAGE)

    # --- Awk coverage, split so the /5 half and the legacy half each carry
    # their own assertion (test_lint_rows.awk_variants reports whatever this
    # host has installed; CI's four-awk installation is authoritative for full
    # coverage where a variant is missing here) ---
    def test_awk_variants_agree_on_the_v5_finding(self):
        for awk_name, awk in base.awk_variants():
            with self.subTest(awk=awk_name):
                verdict, child = base.run_row(12, self.workspace(DEVIATING), awk)
                self.assertEqual(verdict, 'FAIL', child.stdout)
                self.assertIn(b'Effort without Tier reason', child.stdout)

    def test_awk_variants_agree_an_older_board_is_refused(self):
        for awk_name, awk in base.awk_variants():
            for label, kwargs in (('v4', dict(schema='Schema: tackle-workspace/4')),
                                  ('no-board-file', dict(with_board=False))):
                with self.subTest(awk=awk_name, board=label):
                    verdict, child = base.run_row(12, self.workspace(DEVIATING, **kwargs), awk)
                    self.assertEqual(verdict, 'ERROR', child.stdout)
                    self.assertIn(b'migrate first', child.stdout)

    # --- A closed task's brief is skipped; every other state is checked ---
    def test_closed_tasks_are_skipped_and_open_ones_checked(self):
        for status in ('Complete', 'Skipped', 'Unverifiable'):
            with self.subTest(status=status):
                verdict, child = self.run12(DEVIATING, status=status)
                self.assertEqual(verdict, 'PASS', child.stdout)
        for status in ('Draft', 'Ready to run', 'In progress', 'Checking', 'Blocked', 'Interrupted',
                       'Waiting on owner'):
            with self.subTest(status=status):
                verdict, child = self.run12(DEVIATING, status=status)
                self.assertEqual(verdict, 'FAIL', child.stdout)
                self.assert_single_finding(child.stdout, 'demo.md' + MESSAGE)

    # --- A closed task keeps an older Effort token; an open one does not ---
    def test_closed_task_keeps_an_older_effort_token(self):
        older = brief_with('T-A', effort='- **Effort**: inherit')
        verdict, child = self.run12(older, status='Complete')
        self.assertEqual(verdict, 'PASS', child.stdout)
        verdict, child = self.run12(older, status='In progress')
        self.assertEqual(verdict, 'FAIL', child.stdout)
        self.assertIn(b'Effort**: inherit', child.stdout)

    # --- A closed brief the board names in backticks is skipped too ---
    def test_closed_brief_named_in_backticks_is_skipped(self):
        root = self.workspace(DEVIATING, status='Complete')
        board = root / 'docs/plans' / base.SLUG / 'task-board.md'
        board.write_text(board.read_text().replace('| tasks/demo.md |', '| `tasks/demo.md` |'))
        verdict, child = base.run_row(12, root, None)
        self.assertEqual(verdict, 'PASS', child.stdout)

    # --- Only the task's own closed row exempts its brief, and an open row always wins ---
    def test_a_closed_decoy_row_exempts_neither_an_open_nor_an_unlisted_brief(self):
        decoy = '| T-B | decoy | tasks/demo.md | none | Complete | reports/T-B-report.md |\n'
        for label, status, keep in (('open task', 'In progress', True), ('unlisted task', 'Draft', False)):
            with self.subTest(case=label):
                root = self.workspace(DEVIATING, status=status)
                board = root / 'docs/plans' / base.SLUG / 'task-board.md'
                rows = board.read_text().split('\n')
                if not keep:
                    rows = [row for row in rows if not row.startswith('| T-A |')]
                board.write_text('\n'.join(rows).rstrip('\n') + '\n' + decoy)
                verdict, child = base.run_row(12, root, None)
                self.assertEqual(verdict, 'FAIL', child.stdout)
                self.assert_single_finding(child.stdout, 'demo.md' + MESSAGE)

    def test_a_duplicated_closed_row_does_not_exempt_the_open_one(self):
        root = self.workspace(DEVIATING, status='Complete')
        board = root / 'docs/plans' / base.SLUG / 'task-board.md'
        board.write_text(board.read_text() + '| T-A | demo again | tasks/demo.md | none | In progress | pending |\n')
        verdict, child = base.run_row(12, root, None)
        self.assertEqual(verdict, 'FAIL', child.stdout)
        self.assert_single_finding(child.stdout, 'demo.md' + MESSAGE)

    def test_a_row_naming_no_brief_file_is_ignored(self):
        root = self.workspace(DEVIATING, status='In progress')
        board = root / 'docs/plans' / base.SLUG / 'task-board.md'
        board.write_text(board.read_text().rstrip('\n') + '\n'
                         '| T-B | no brief yet | | none | Complete | reports/T-B-report.md |\n'
                         '| T-C | a directory | tasks/ | none | Complete | reports/T-C-report.md |\n')
        verdict, child = base.run_row(12, root, None)
        self.assertEqual(verdict, 'FAIL', (child.stdout, child.stderr))
        self.assert_single_finding(child.stdout, 'demo.md' + MESSAGE)


if __name__ == '__main__':
    unittest.main()
