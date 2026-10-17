"""A plan view lists its declared sibling plans and links to their views; a plan without siblings shows nothing new.

The shipped script builds a local workspace beside a declared sibling under one temporary repository root. The
oracles read the page it writes: the header block (slug, Relation cell, progress from the sibling's board, a link
to the sibling's plan-view.html or a missing-view note), the external graph node and stage-list links to the
sibling's task, the printed reports, the print rule that shows link targets as text, Spanish labels, the input
digests, and a workspace without siblings. Whether a browser follows the links, and how the PDF looks, is not
observed here.
"""
import html
import json
import re
import tempfile
import unittest

from test_plan_siblings import AGENTS_HEAD, build, run, write_files

SPANISH_PLAN = ('# Plan — Migración\n\nEl plan describe los pasos de la migración. Cada tarea tiene una verificación. '
                'La configuración queda lista después de la revisión.\n\n'
                '| Criterion | Required behavior |\n|---|---|\n| `R0001` | uno |\n')
VIEW = '<!doctype html>\n<title>beta</title>\n'


def built(tmp, with_view=True, **options):
    """Build alpha beside beta; beta has a plan view unless asked otherwise. Return the page text."""
    alpha, beta_dir = build(tmp, **options)
    if with_view:
        write_files(beta_dir, {'plan-view.html': VIEW})
    result, out = run(tmp, alpha)
    assert result.returncode == 0, result.stdout + result.stderr
    return out.read_text(encoding='utf-8')


def block(page):
    """The header's sibling block, or None."""
    found = re.search(r'<nav class="sibling-plans"[^>]*>(.*?)</nav>', page, re.S)
    return found and found.group(0)


def text_of(fragment):
    return ' '.join(re.sub(r'<[^>]+>', ' ', fragment).split())


def inputs(page):
    found = re.search(r'<meta name="tackle-input-digest" content="([^"]*)">', page)
    return json.loads(html.unescape(found.group(1)))['inputs']


class SiblingBlockTests(unittest.TestCase):
    def test_the_header_lists_the_sibling_with_its_relation_progress_and_a_link_to_its_view(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = built(tmp)
        nav = block(page)
        self.assertIsNotNone(nav, 'a declared sibling gives a sibling block')
        self.assertIn('aria-label="Sibling plans"', nav)
        self.assertIn('<a class="sibling-plan" data-sibling="api" href="../beta/plan-view.html">', nav)
        self.assertIn('<span class="sibling-slug">api</span><span class="sibling-relation">api split</span>', nav)
        self.assertIn('1 of 3 tasks complete', text_of(nav), 'one Complete row over three task rows on the sibling board')
        hero = re.search(r'<section class="hero".*?</section>', page, re.S).group(0)
        self.assertIn(nav, hero, 'the block sits in the page header')

    def test_siblings_keep_their_declaration_order(self):
        declared = ('## Sibling workspaces\n\n| Sibling | Path | Relation |\n|---|---|---|\n'
                    '| web | docs/plans/gamma | the web client |\n| api | docs/plans/beta | api split |\n')
        with tempfile.TemporaryDirectory() as tmp:
            page = built(tmp, agents=AGENTS_HEAD + declared)
        nav = block(page)
        self.assertLess(nav.index('data-sibling="web"'), nav.index('data-sibling="api"'))

    def test_a_sibling_without_a_view_gets_a_note_and_no_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = built(tmp, with_view=False)
        nav = block(page)
        self.assertIsNotNone(nav)
        self.assertNotIn('<a ', nav, 'no broken link to a view that does not exist')
        self.assertIn('<span class="sibling-plan" data-sibling="api">', nav)
        self.assertIn('<span class="sibling-note">no plan view yet</span>', nav)
        self.assertIn('1 of 3 tasks complete', text_of(nav))
        self.assertNotIn('class="xnode-link"', page)
        self.assertNotIn('class="stage-sibling"', page)

    def test_the_external_node_and_its_stage_list_entry_link_to_the_task_in_the_sibling_view(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = built(tmp)
        target = '../beta/plan-view.html#task-T-0007'
        self.assertIn('<a class="xnode-link" href="%s" data-sibling="api"><g class="xnode s-prog" role="img"' % target, page)
        entry = re.search(r'<li><a class="stage-task s-draft" href="#task-T-0002".*?</li>', page, re.S).group(0)
        self.assertIn('<a class="stage-sibling" href="%s" data-sibling="api">Open api · T-0007 in its plan</a></li>' % target, entry)
        self.assertEqual(entry.count('<a '), 2, 'the sibling link sits beside the entry link, never inside it')
        self.assertLess(entry.index('</a>'), entry.index('class="stage-sibling"'))

    def test_print_shows_each_sibling_link_target_as_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = built(tmp)
        rules = next(found.group(1) for found in re.finditer(r'@media print\{(.*?)\n\}', page, re.S)
                     if 'body>*:not(.print-reports)' in found.group(1))
        self.assertIn('.sibling-plans a[href]::after,.stage-sibling[href]::after{content:" (" attr(href) ")"', rules)
        reports = re.search(r'<div class="print-reports">(.*?)</div>\s*<script', page, re.S).group(1)
        self.assertEqual(reports.count('<section class="report-section report-siblings">'), 3,
                         'each printed report (plan, progress, both) lists the siblings')
        self.assertIn('href="../beta/plan-view.html"', reports)

    def test_spanish_labels(self):
        with tempfile.TemporaryDirectory() as tmp:
            alpha, beta_dir = build(tmp)
            write_files(alpha, {'plan.md': SPANISH_PLAN})
            result, out = run(tmp, alpha)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            page = out.read_text(encoding='utf-8')
            self.assertIn('<html lang="es"', page)
            nav = block(page)
            self.assertIn('aria-label="Planes hermanos"', nav)
            self.assertIn('1 de 3 tareas completas', text_of(nav))
            self.assertIn('todavía sin vista del plan', nav)

    def test_the_sibling_board_and_its_view_presence_are_page_inputs(self):
        declared = ('## Sibling workspaces\n\n| Sibling | Path | Relation |\n|---|---|---|\n'
                    '| api | docs/plans/beta | api split |\n')
        with tempfile.TemporaryDirectory() as tmp:
            alpha, beta_dir = build(tmp, second_deps='T-0001', agents=AGENTS_HEAD + declared)
            result, out = run(tmp, alpha)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            record = inputs(out.read_text(encoding='utf-8'))
            self.assertIn('api:task-board.md', record, 'a declared sibling with no dependency still feeds the progress')
            self.assertEqual(record['api:plan-view.html'], 'absent')
            write_files(beta_dir, {'plan-view.html': VIEW})
            stale, _ = run(tmp, alpha, options=('--check',), output=out)
            self.assertEqual(stale.returncode, 1)
            self.assertIn('view stale: api:plan-view.html', stale.stdout)

    def test_a_workspace_without_siblings_shows_no_block_and_records_no_sibling_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = built(tmp, second_deps='T-0001', agents=AGENTS_HEAD)
        for marker in ('sibling-plans"', 'class="sibling-plan', 'xnode-link', 'stage-sibling', 'report-siblings'):
            self.assertNotIn(marker, page.split('</style>', 1)[1], marker)
        self.assertEqual([key for key in inputs(page) if key.startswith('api:')], [])
        self.assertIn('<h1>', page)
        hero = re.search(r'<section class="hero".*?</section>', page, re.S).group(0)
        self.assertNotIn('<nav', hero)


if __name__ == '__main__':
    unittest.main()
