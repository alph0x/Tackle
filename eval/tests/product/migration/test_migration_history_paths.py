"""Migration keeps history paths: path spans, text rewriting, other-workspace links, residue and the
legacy status text after a glyph.

The recipes are loaded through `test_migration_steps.py`'s loader, and every workspace here is an
in-memory mapping of workspace-relative paths to bytes, so no fixture directory is involved.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_migration_steps import (  # noqa: E402
    CONTEXT_84, CONTEXT_90, SCHEMA, STEP_3_TO_4, STEP_4_TO_5, STEP_PRE3_TO_3)

BOARD3_HEADER = ('# Task board\n\nSchema: tackle-workspace/3\n\n'
                 '| Task | What | Brief | Depends on | Status | Verification |\n'
                 '|---|---|---|---|---|---|\n')
PRE3_HEADER = ('# Board\n\n'
               '| Point | What | Briefing | Depends on | Status | Confidence |\n'
               '|---|---|---|---|---|---|\n')
BOARD4 = ('# Task board\n\nSchema: tackle-workspace/4\n\n'
          '| Task | What | Brief | Depends on | Status | Verification |\n'
          '|---|---|---|---|---|---|\n'
          '| T-0001 | Draft work | tasks/T-0001-x.md | none | Draft |  |\n')
REPORT = 'Report text.\n'


def encoded(files):
    return {path: (data.encode('utf-8') if isinstance(data, str) else data) for path, data in files.items()}


def board3(*rows, tail=''):
    return BOARD3_HEADER + ''.join(row + '\n' for row in rows) + tail


def workspace3(board, **extra):
    files = {'board.md': board, 'points/P-0001-x.md': 'Brief text.\n'}
    files.update(extra)
    return encoded(files)


def migrate34(files, workspace=None):
    context = dict(CONTEXT_84)
    if workspace is not None:
        context['workspace'] = workspace
    after, _ = STEP_3_TO_4['transform'](files, context)
    return after


def verify34(before, after):
    return STEP_3_TO_4['verify'](before, after)


DRAFT_ROW = '| P-0001 | Draft work | points/P-0001-x.md | none | Draft |  |'
COMPLETE_ROW = '| P-0001 | Done work | points/P-0001-x.md | none | Complete | reports/P-0001-report.md |'
SECOND_DRAFT_ROW = '| P-0002 | Second work | points/P-0002-y.md | none | Draft |  |'


class PathRuleTests(unittest.TestCase):
    """A path keeps its old ids unless its moved form is a task or report path."""

    def test_run_directory_kept(self):
        before = workspace3(board3(DRAFT_ROW), **{'runs/P-0001/out.txt': 'run output\n'})
        after = migrate34(before)
        self.assertEqual(after['runs/P-0001/out.txt'], b'run output\n')

    def test_nested_evidence_kept_with_its_directory_renamed(self):
        before = workspace3(board3(DRAFT_ROW), **{'evidence/run-P-0001/sub/log.txt': 'log\n'})
        after = migrate34(before)
        self.assertEqual(after['verification-records/run-P-0001/sub/log.txt'], b'log\n')
        self.assertNotIn('evidence/run-P-0001/sub/log.txt', after)

    def test_briefs_and_reports_mapped_with_their_nested_paths(self):
        before = encoded({
            'board.md': board3(COMPLETE_ROW),
            'points/P-0001-x.md': 'Brief text.\n',
            'points/sub/P-0001-y.md': 'Nested brief.\n',
            'reports/P-0001-report.md': REPORT,
        })
        after = migrate34(before)
        self.assertIn('tasks/T-0001-x.md', after)
        self.assertIn('tasks/sub/T-0001-y.md', after)
        self.assertIn('reports/T-0001-report.md', after)

    def test_citation_follows_its_moved_file_and_the_period_stays_outside(self):
        report = 'Raw: `evidence/P-0001/raw.txt.` and `points/P-0001-x.md`.\n'
        before = encoded({
            'board.md': board3(COMPLETE_ROW),
            'points/P-0001-x.md': 'Brief text.\n',
            'reports/P-0001-report.md': report,
            'evidence/P-0001/raw.txt': 'raw\n',
        })
        after = migrate34(before)
        self.assertEqual(after['reports/T-0001-report.md'].decode(),
                         'Raw: `verification-records/P-0001/raw.txt.` and `tasks/T-0001-x.md`.\n')

    def test_bare_id_still_maps_when_it_is_not_a_path(self):
        before = workspace3(board3(DRAFT_ROW, SECOND_DRAFT_ROW, tail='\nsee P-0001 and P-0001/P-0002\n'))
        after = migrate34(before)
        text = after['task-board.md'].decode()
        self.assertIn('see T-0001 and T-0001/T-0002', text)

    def test_kept_citation_leaves_no_residue(self):
        before = encoded({
            'board.md': board3(COMPLETE_ROW),
            'points/P-0001-x.md': 'Brief text.\n',
            'reports/P-0001-report.md': 'Output: runs/P-0001/out.txt\n',
            'runs/P-0001/out.txt': 'run output\n',
        })
        after = migrate34(before)
        self.assertIn('Output: runs/P-0001/out.txt', after['reports/T-0001-report.md'].decode())
        result = verify34(before, after)
        self.assertEqual(result['errors'], [])
        self.assertEqual(result['residue'], [])

    def test_span_boundary_is_not_a_span_when_it_starts_mid_token(self):
        before = workspace3(board3(DRAFT_ROW, tail='\nfoo/docs/plans/other/points/P-0001-x.md\n'))
        after = migrate34(before)
        self.assertIn('foo/docs/plans/other/tasks/T-0001-x.md', after['task-board.md'].decode())

    def test_span_openers_start_a_span(self):
        before = workspace3(board3(DRAFT_ROW, tail='\n(points/P-0001-x.md) and [evidence/P-0001/raw.txt]\n'),
                            **{'evidence/P-0001/raw.txt': 'raw\n'})
        after = migrate34(before)
        text = after['task-board.md'].decode()
        self.assertIn('(tasks/T-0001-x.md)', text)
        self.assertIn('[verification-records/P-0001/raw.txt]', text)


class ResidueTests(unittest.TestCase):
    """The residue kinds, their exact sorted lists, and the cases where neither applies."""

    def test_no_board_yields_no_link_or_history_residue_and_no_error(self):
        before = encoded({
            'task-board.md': BOARD4,
            'evidence/P-0001/raw.txt': 'raw\n',
            'history.md': 'Raw record: evidence/P-0001/raw.txt\n',
        })
        after = encoded({
            'task-board.md': BOARD4,
            'verification-records/P-0001/raw.txt': 'raw\n',
            'history.md': 'Raw record: evidence/P-0001/raw.txt\n',
        })
        result = verify34(before, after)
        self.assertEqual(result['errors'], [])
        self.assertEqual(result['residue'], [])

    def test_history_cites_a_moved_path_and_not_a_root_rename(self):
        before = workspace3(
            board3(DRAFT_ROW),
            **{'log.md': 'Raw record: evidence/P-0001/raw.txt; see resource-usage.md and board.md.\n',
               'evidence/P-0001/raw.txt': 'raw\n'})
        after = migrate34(before)
        result = verify34(before, after)
        self.assertEqual(result['errors'], [])
        self.assertEqual(result['residue'], [
            'history cites evidence/P-0001/raw.txt, now verification-records/P-0001/raw.txt'])

    def test_link_into_another_workspace_is_reported_once_and_left_unchanged(self):
        before = workspace3(board3(DRAFT_ROW, tail='\nLink: docs/plans/other/points/P-0002.md\n'),
                            **{'points/P-0001-x.md': 'Depends: docs/plans/other/points/P-0002.md\n'})
        after = migrate34(before, workspace='this')
        self.assertIn('docs/plans/other/points/P-0002.md', after['task-board.md'].decode())
        self.assertIn('docs/plans/other/points/P-0002.md', after['tasks/T-0001-x.md'].decode())
        result = verify34(before, after)
        self.assertEqual(result['errors'], [])
        self.assertEqual(result['residue'], [
            'link into another workspace left unchanged: docs/plans/other/points/P-0002.md'])

    def test_own_workspace_link_is_rewritten_and_leaves_no_residue(self):
        before = workspace3(board3(DRAFT_ROW, tail='\nSee docs/plans/this/points/P-0001-x.md\n'))
        after = migrate34(before, workspace='this')
        self.assertIn('See docs/plans/this/tasks/T-0001-x.md', after['task-board.md'].decode())
        result = verify34(before, after)
        self.assertEqual(result['errors'], [])
        self.assertEqual(result['residue'], [])

    def test_similar_name_is_reported_as_another_workspace(self):
        before = workspace3(board3(DRAFT_ROW, tail='\nSee docs/plans/this-two/points/P-0001-x.md\n'))
        after = migrate34(before, workspace='this')
        self.assertIn('See docs/plans/this-two/points/P-0001-x.md', after['task-board.md'].decode())
        result = verify34(before, after)
        self.assertEqual(result['residue'], [
            'link into another workspace left unchanged: docs/plans/this-two/points/P-0001-x.md'])

    def test_no_workspace_key_reports_both_citations_sorted(self):
        before = workspace3(board3(DRAFT_ROW, tail='\nSee docs/plans/this/points/P-0001-x.md '
                                                     'and docs/plans/other/points/P-0002.md\n'))
        after = migrate34(before)
        result = verify34(before, after)
        self.assertEqual(result['residue'], [
            'link into another workspace left unchanged: docs/plans/other/points/P-0002.md',
            'link into another workspace left unchanged: docs/plans/this/points/P-0001-x.md'])

    def test_second_run_is_byte_identical(self):
        before = workspace3(board3(DRAFT_ROW, tail='\nSee docs/plans/this/points/P-0001-x.md\n'),
                            **{'runs/P-0001/out.txt': 'run output\n'})
        after = migrate34(before, workspace='this')
        second, renames = STEP_3_TO_4['transform'](after, CONTEXT_84)
        self.assertEqual(second, after)
        self.assertEqual(renames, {})


class PreThreeStatusTests(unittest.TestCase):
    """A Status cell reads as its glyph, an optional selector, optional whitespace and text."""

    def transform(self, rows, reports=('P-0001',)):
        files = {'board.md': (PRE3_HEADER + ''.join(row + '\n' for row in rows)).encode('utf-8')}
        for identity in reports:
            files['reports/%s-report.md' % identity] = REPORT.encode('utf-8')
        return STEP_PRE3_TO_3['transform'](files, CONTEXT_84)

    def board_text(self, rows, reports=('P-0001',)):
        after, legacy = self.transform(rows, reports)
        return after['board.md'].decode('utf-8'), legacy

    def test_dated_done_glyph_keeps_its_text_as_a_note(self):
        text, legacy = self.board_text(['| P-0001 | Done work | points/P-0001-x.md | none | \U0001F7E2 2026-05-01 abc1234 | — |'])
        self.assertIn('| P-0001 | Done work | points/P-0001-x.md | none | Complete | reports/P-0001-report.md |\n'
                      '\nLegacy status note · P-0001: 2026-05-01 abc1234\n', text)
        self.assertEqual(legacy['P-0001']['status'], '\U0001F7E2')

    def test_two_notes_follow_row_order(self):
        rows = ['| P-0002 | Second | points/P-0002-y.md | none | \U0001F7E2 first note | — |',
                '| P-0001 | First | points/P-0001-x.md | none | \U0001F7E2 second note | — |']
        text, _ = self.board_text(rows, reports=('P-0001', 'P-0002'))
        self.assertTrue(text.endswith('\nLegacy status note · P-0002: first note\n'
                                      'Legacy status note · P-0001: second note\n'))

    def test_text_with_no_space_after_the_glyph(self):
        text, _ = self.board_text(['| P-0001 | Done | points/P-0001-x.md | none | \U0001F7E2done | — |'])
        self.assertIn('Legacy status note · P-0001: done\n', text)
        self.assertIn('| Complete |', text)

    def test_glyph_with_selector_keeps_its_text(self):
        text, legacy = self.board_text(['| P-0001 | Paused | points/P-0001-x.md | none | ⏸️ waiting on review | — |'])
        self.assertIn('| Blocked |', text)
        self.assertIn('Legacy status note · P-0001: waiting on review\n', text)
        self.assertEqual(legacy['P-0001']['status'], '⏸')

    def test_bare_glyph_with_selector_has_no_note(self):
        text, _ = self.board_text(['| P-0001 | Paused | points/P-0001-x.md | none | ⏸️ | — |'])
        self.assertIn('| Blocked |', text)
        self.assertNotIn('Legacy status note', text)

    def test_bare_glyph_is_in_progress_without_a_note(self):
        text, _ = self.board_text(['| P-0001 | Active | points/P-0001-x.md | none | \U0001F7E1 | — |'], reports=())
        self.assertIn('| In progress |', text)
        self.assertNotIn('Legacy status note', text)

    def test_unknown_glyph_is_refused_with_the_whole_cell(self):
        with self.assertRaises(ValueError) as caught:
            self.transform(['| P-0001 | Odd | points/P-0001-x.md | none | \U0001F6A7 2026-05-01 | — |'])
        self.assertEqual(str(caught.exception), 'unsupported legacy state: \U0001F6A7 2026-05-01')


class ChainedStatusNoteTests(unittest.TestCase):
    """A pre-3 workspace with a status note reaches /5 through adopt with the note intact."""

    def test_chain_keeps_the_note_after_the_board_table(self):
        files = encoded({
            'board.md': PRE3_HEADER + '| P-0001 | Done | points/P-0001-x.md | none | \U0001F7E2 done later | — |\n',
            'points/P-0001-x.md': 'Brief text.\n',
            'reports/P-0001-report.md': REPORT,
        })
        steps = ((STEP_PRE3_TO_3, CONTEXT_84), (STEP_3_TO_4, CONTEXT_84), (STEP_4_TO_5, CONTEXT_90))
        for step, context in steps:
            before = SCHEMA['workspace_files'](files)
            files, _ = SCHEMA['adopt'](files, context, step['transform'])
            after = SCHEMA['workspace_files'](files)
            self.assertEqual(step['verify'](before, after)['errors'], [])
        self.assertEqual(SCHEMA['schema_of'](files), '5')
        text = files['task-board.md'].decode('utf-8')
        self.assertIn('Legacy status note · T-0001: done later\n', text)


if __name__ == '__main__':
    unittest.main()
