"""Curated status prose never outlives the board it describes.

The shipped recipe builds the static page and its print reports. A curated summary that declares the task
states it was written for keeps its status prose while those states hold. Once the board's states differ, the
page and the reports drop that prose, show a visible note, and keep the canonical counts. A summary that
declares no board keeps its prose, as before, and the build warns that it cannot be checked. These assertions read the generated document, not a browser.
"""
import html
import json
import re
import tempfile
import unittest

from eval.tests.product.status.test_plan_view import lite_plan, run_recipe, task_id, workspace_files
from eval.tests.product.status.test_plan_view_currency import Fixture, call

STALE_EN = 'The written status summary describes an earlier board'
STALE_ES = 'El resumen escrito del estado describe un tablero anterior'
AS_OF = '2026-10-01 09:00 -03'
EXPORT_NOTE = 'note: the executive summary (as of %s) describes an earlier board: ' % AS_OF


def sections(page):
    """The Plan, Progress and Both reports as separate slices of the page (the page's status section is outside them)."""
    plan = page.split('id="print-report-plan"', 1)[1].split('id="print-report-progress"', 1)[0]
    progress = page.split('id="print-report-progress"', 1)[1].split('id="print-report-both"', 1)[0]
    both = page.split('id="print-report-both"', 1)[1].split('id="plan-view-data"', 1)[0]
    return dict(plan=plan, progress=progress, both=both)


def notes(stderr):
    return [line for line in stderr.splitlines() if 'describes an earlier board' in line]


def stale_notice(as_of):
    return '<p class="executive-note" role="note">%s (%s);' % (STALE_EN, as_of)


def board_states(changed=None):
    states = {task_id(1): 'Complete', task_id(2): 'In progress', task_id(3): 'Draft'}
    states.update({task_id(number): value for number, value in (changed or {}).items()})
    return states


def summary(states=None):
    data = dict(now='Curated status sentence', next=['Curated next step'], you=['Curated owner note'])
    if states is not None:
        data.update(as_of='2026-10-01 09:00 -03', board_states=states)
    return data


def export_summary(states=None):
    data = dict(schema='executive-presentation/1',
                progress=dict(achievements=[dict(title='Curated achievement', text='Curated achievement text')],
                              open_work=[dict(title='Curated open work', text='Curated open work text')],
                              current_dependency='Curated dependency', next=['Curated export step'],
                              evidence='Curated evidence'))
    if states is not None:
        data['authority'] = dict(as_of='2026-10-01 09:00 -03', canonical_states=states)
    return data


# The page shows the export summary's next steps when it has them, so the summary's own step is not among these.
CURATED = ('Curated status sentence', 'Curated owner note', 'Curated achievement text', 'Curated open work text',
           'Curated dependency', 'Curated export step', 'Curated evidence')


class StatusFreshnessTests(unittest.TestCase):
    def render(self, extra, name, lang=None):
        files = workspace_files()
        files.update(extra)
        if lang:
            files['plan.md'] = ('# Plan — Migración\n\nEl plan describe los pasos de la migración. Cada tarea tiene una '
                                'verificación. La configuración queda lista después de la revisión.\n\n'
                                + files['plan.md'].split('\n', 1)[1])
        with tempfile.TemporaryDirectory() as tmp:
            result, output = run_recipe(tmp, files, name)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.stderr = result.stderr
            return html.unescape(output.read_text(encoding='utf-8'))

    def test_prose_written_for_the_current_board_is_shown(self):
        page = self.render({'view/summary.json': json.dumps(summary(board_states())),
                            'view/export-summary.json': json.dumps(export_summary(board_states()))}, 'current')
        for text in CURATED:
            self.assertIn(text, page)
        self.assertNotIn(STALE_EN, page)
        self.assertNotIn('declares no board states', self.stderr)

    def test_prose_written_for_an_earlier_board_gives_way_to_the_records(self):
        earlier = board_states({2: 'Draft'})
        page = self.render({'view/summary.json': json.dumps(summary(earlier)),
                            'view/export-summary.json': json.dumps(export_summary(earlier))}, 'earlier')
        for text in CURATED + ('Curated next step',):
            self.assertNotIn(text, page)
        status = page.split('id="snapshot"', 1)[1].split('</section>', 1)[0]
        self.assertIn(STALE_EN, status)
        self.assertIn('2026-10-01 09:00 -03', status)
        self.assertIn('1 of 3 recorded tasks are complete.', status)
        reports = page.split('id="print-report-progress"', 1)[1]
        self.assertRegex(reports, re.compile(r'report-count"><b>1</b><span>/3</span>'))

    def test_one_stale_summary_does_not_silence_a_current_one(self):
        page = self.render({'view/summary.json': json.dumps(summary(board_states())),
                            'view/export-summary.json': json.dumps(export_summary(board_states({3: 'Complete'})))}, 'mixed')
        self.assertIn('Curated status sentence', page)
        self.assertNotIn('Curated achievement text', page)
        self.assertIn(STALE_EN, page)

    def test_prose_that_declares_no_board_is_kept(self):
        page = self.render({'view/summary.json': json.dumps(summary()),
                            'view/export-summary.json': json.dumps(export_summary())}, 'undeclared')
        for text in CURATED:
            self.assertIn(text, page)
        self.assertNotIn(STALE_EN, page)
        for name in ('the curated summary', 'the executive summary'):
            self.assertIn('note: %s declares no board states' % name, self.stderr)

    def test_the_note_is_localized(self):
        page = self.render({'view/summary.json': json.dumps(summary(board_states({1: 'Draft'})))},
                           'spanish', lang='es')
        self.assertIn(STALE_ES, page)
        self.assertNotIn(STALE_EN, page)
        self.assertNotIn('Curated status sentence', page)

    def test_export_prose_set_aside_gives_the_progress_and_both_reports_one_note(self):
        page = self.render({'view/summary.json': json.dumps(summary(board_states())),
                            'view/export-summary.json': json.dumps(export_summary(board_states({2: 'Draft'})))}, 'export-stale')
        parts = sections(page)
        self.assertIn(stale_notice(AS_OF), parts['progress'])
        self.assertEqual(parts['both'].count(STALE_EN), 1)
        self.assertNotIn(STALE_EN, parts['plan'])
        self.assertIn('Curated status sentence', page)

    def test_the_report_note_names_the_source_that_was_set_aside(self):
        export_as_of = '2026-10-01 09:00 -03'
        summary_as_of = '2026-09-01 08:00 -03'
        curated = summary(board_states({1: 'Draft'}))
        curated['as_of'] = summary_as_of
        page = self.render({'view/summary.json': json.dumps(curated),
                            'view/export-summary.json': json.dumps(export_summary(board_states({2: 'Draft'})))}, 'both-stale')
        progress = sections(page)['progress']
        self.assertIn(stale_notice(export_as_of), progress)
        self.assertNotIn(summary_as_of, progress)

    def test_a_stale_summary_with_its_own_export_next_gives_no_report_note(self):
        curated = summary(board_states({1: 'Draft'}))
        page = self.render({'view/summary.json': json.dumps(curated),
                            'view/export-summary.json': json.dumps(export_summary(board_states()))}, 'export-next')
        parts = sections(page)
        for name in ('plan', 'progress', 'both'):
            self.assertNotIn(STALE_EN, parts[name])
        self.assertNotIn('Curated next step', parts['progress'])
        self.assertIn(STALE_EN, page.split('id="snapshot"', 1)[1].split('</section>', 1)[0])

    def test_a_stale_summary_with_only_now_and_owner_gives_no_report_note(self):
        curated = dict(now='Curated status sentence', you=['Curated owner note'], as_of='2026-10-01 09:00 -03',
                       board_states=board_states({1: 'Draft'}))
        page = self.render({'view/summary.json': json.dumps(curated)}, 'now-only')
        parts = sections(page)
        for name in ('plan', 'progress', 'both'):
            self.assertNotIn(STALE_EN, parts[name])
        self.assertNotIn('Curated status sentence', parts['progress'])

    def test_a_stale_summary_next_gives_the_report_note_when_the_export_has_no_next(self):
        page = self.render({'view/summary.json': json.dumps(summary(board_states({1: 'Draft'})))}, 'page-stale')
        parts = sections(page)
        self.assertIn(stale_notice(AS_OF), parts['progress'])
        self.assertEqual(parts['both'].count(STALE_EN), 1)
        self.assertNotIn(STALE_EN, parts['plan'])

    def test_the_report_note_is_localized(self):
        page = self.render({'view/export-summary.json': json.dumps(export_summary(board_states({2: 'Draft'})))},
                           'spanish-export', lang='es')
        progress = sections(page)['progress']
        self.assertIn(STALE_ES, progress)
        self.assertNotIn(STALE_EN, progress)

    def test_a_changed_task_is_named_on_stderr_for_the_executive_summary(self):
        self.render({'view/export-summary.json': json.dumps(export_summary(board_states({2: 'Draft'})))}, 'changed')
        lines = notes(self.stderr)
        self.assertEqual(len(lines), 1, self.stderr)
        self.assertTrue(lines[0].startswith(EXPORT_NOTE), lines[0])
        self.assertIn('%s: Draft → In progress' % task_id(2), lines[0])

    def test_missing_and_extra_tasks_are_named_in_task_order(self):
        declared = {task_id(1): 'Complete', task_id(2): 'In progress', task_id(9): 'Draft'}
        self.render({'view/export-summary.json': json.dumps(export_summary(declared))}, 'missing-extra')
        self.assertEqual(notes(self.stderr), [EXPORT_NOTE + '%s: not in the summary → Draft; %s: Draft → not on the board'
                                              % (task_id(3), task_id(9))], self.stderr)

    def test_a_non_numeric_declared_id_is_named_after_the_numbered_ones(self):
        declared = {'X-note': 'Draft', task_id(1): 'Complete', task_id(2): 'Draft'}
        self.render({'view/export-summary.json': json.dumps(export_summary(declared))}, 'non-numeric')
        self.assertEqual(notes(self.stderr), [EXPORT_NOTE + '%s: Draft → In progress; %s: not in the summary → Draft; '
                                              'X-note: Draft → not on the board' % (task_id(2), task_id(3))], self.stderr)

    def test_a_divergence_is_named_even_without_stale_prose(self):
        export = dict(schema='executive-presentation/1',
                      authority=dict(as_of=AS_OF, canonical_states=board_states({2: 'Draft'})))
        self.render({'view/export-summary.json': json.dumps(export)}, 'no-prose')
        self.assertEqual(len(notes(self.stderr)), 1, self.stderr)
        self.assertNotIn('declares no board states', self.stderr)

    def test_equal_maps_print_no_divergence_note(self):
        self.render({'view/summary.json': json.dumps(summary(board_states())),
                     'view/export-summary.json': json.dumps(export_summary(board_states()))}, 'equal')
        self.assertEqual(notes(self.stderr), [], self.stderr)

    def test_a_focused_plan_prints_no_divergence_note_in_build_or_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(tmp, files={'plan.md': lite_plan(),
                                          'view/summary.json': json.dumps(summary(board_states({1: 'Draft'})))})
            result = call(fixture.root, fixture.args())
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(notes(result.stderr), [], result.stderr)
            checked = fixture.check()
            self.assertEqual(notes(checked.stderr), [], checked.stderr)

    def test_check_names_the_divergence_read_only_and_keeps_its_result(self):
        files = dict(workspace_files(), **{'view/summary.json': json.dumps(summary(board_states())),
                                      'view/export-summary.json': json.dumps(export_summary(board_states()))})
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(tmp, files=files)
            fixture.build()
            export_path = fixture.ws / 'view' / 'export-summary.json'
            export_path.write_text(json.dumps(export_summary(board_states({2: 'Draft'}))), encoding='utf-8')
            result = fixture.check()
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertTrue(result.stdout.startswith('view stale: '), result.stdout)
            lines = notes(result.stderr)
            self.assertEqual(len(lines), 1, result.stderr)
            self.assertIn('%s: Draft → In progress' % task_id(2), lines[0])

    def test_check_names_the_divergence_when_the_page_already_holds_it(self):
        files = dict(workspace_files(), **{'view/summary.json': json.dumps(summary(board_states())),
                                      'view/export-summary.json': json.dumps(export_summary(board_states({2: 'Draft'})))})
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(tmp, files=files)
            fixture.build()
            result = fixture.check()
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(result.stdout.strip(), 'view current')
            self.assertEqual(len(notes(result.stderr)), 1, result.stderr)


if __name__ == '__main__':
    unittest.main()
