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

from eval.tests.product.status.test_plan_view import run_recipe, task_id, workspace_files

STALE_EN = 'The written status summary describes an earlier board'
STALE_ES = 'El resumen escrito del estado describe un tablero anterior'


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


if __name__ == '__main__':
    unittest.main()
