"""Readers without the large picture get the same facts from the generated plan view.

The shipped recipe writes a stage list beside the graph for narrow screens, a title-block strip with one cell
per task and a print report in the screen palette. These checks read the static page: every task appears once
in the stage list, in the graph's own column, with its title, its translated state and what it needs; the
strip follows the board; print colors equal the light screen tokens; content is visible before any script
runs. They do not observe browser layout.
"""
import html
import re
import tempfile
import unittest
from html.parser import HTMLParser

from test_plan_view import BOARD_HEAD, SPANISH_PLAN, req_id, run_recipe, task_id, visible_text

DEPENDS = {1: [], 2: [1], 3: [1], 4: [2, 3], 5: [], 6: [4, 5]}
STATES = {1: 'Complete', 2: 'Complete', 3: 'In progress', 4: 'Draft', 5: 'Blocked', 6: 'Draft'}


def fixture(plan=None):
    rows = ''.join('| %s | Work item %d with a longer descriptive title | `tasks/%s.md` | %s | %s | v |\n' % (
        task_id(n), n, task_id(n), ', '.join(task_id(d) for d in DEPENDS[n]) or 'none', STATES[n]) for n in sorted(DEPENDS))
    files = {'plan.md': plan or ('# Plan — Layout\n\nThe plan describes the steps of the migration. Each task has a check.\n\n'
                                 '| Criterion | Required behavior |\n|---|---|\n| `%s` | one |\n' % req_id(1)),
             'task-board.md': BOARD_HEAD + rows}
    for n in DEPENDS:
        files['tasks/%s.md' % task_id(n)] = '# Task\n\n- **Traces to**: %s\n' % req_id(1)
    return files


def render(files, case):
    with tempfile.TemporaryDirectory() as tmp:
        result, out = run_recipe(tmp, files, case)
        assert result.returncode == 0, result.stdout + result.stderr
        return out.read_text(encoding='utf-8')


class StageList(HTMLParser):
    """Collect stage groups and their task rows from the static stage list."""

    def __init__(self, page):
        super().__init__(convert_charrefs=True)
        self.groups, self.field, self.depth, self.spans = [], None, 0, 0
        self.feed(page)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = (attrs.get('class') or '').split()
        if tag == 'ol' and ('stage-list' in classes or self.depth):
            self.depth += 1
        if not self.depth:
            return
        if 'stage-group' in classes:
            self.groups.append([])
        elif 'stage-task' in classes:
            self.groups[-1].append({'task': attrs.get('data-task'), 'href': attrs.get('href')})
        elif classes and classes[0].startswith('stage-task-'):
            self.field, self.spans = classes[0][len('stage-task-'):], 0
        elif tag == 'span' and self.field:
            self.spans += 1

    def handle_endtag(self, tag):
        if tag == 'span' and self.spans:
            self.spans -= 1
        elif tag == 'span':
            self.field = None
        elif tag == 'ol' and self.depth:
            self.depth -= 1

    def handle_data(self, data):
        if self.depth and self.field and self.groups and self.groups[-1]:
            row = self.groups[-1][-1]
            row[self.field] = row.get(self.field, '') + data


def graph_columns(page):
    """Task ids per graph column, ordered left to right by box position."""
    boxes = re.findall(r'<g class="node [^"]*" data-task="(T-\d+)".*?<rect class="node-box" x="([\d.]+)"', page, re.S)
    columns = {}
    for task, x in boxes:
        columns.setdefault(float(x), set()).add(task)
    return [columns[x] for x in sorted(columns)]


class ReadingLayoutTests(unittest.TestCase):
    def test_the_stage_list_holds_every_task_once_in_its_graph_column_with_state_and_needs(self):
        page = render(fixture(), 'stages')
        groups = StageList(page).groups
        listed = [row['task'] for group in groups for row in group]
        self.assertEqual(sorted(listed), [task_id(n) for n in sorted(DEPENDS)])
        self.assertEqual([{row['task'] for row in group} for group in groups], graph_columns(page))
        for group in groups:
            for row in group:
                n = int(row['task'][2:])
                self.assertEqual(row['href'], '#task-' + row['task'])
                self.assertEqual(row['title'], 'Work item %d with a longer descriptive title' % n)
                self.assertEqual(row['state'], STATES[n])
                self.assertEqual(row['needs'], 'Needs: ' + (', '.join(task_id(d) for d in DEPENDS[n]) or 'nothing'))
        self.assertIn('A stage is a column of the graph, not an order of work.', page)

    def test_the_title_strip_follows_the_board_in_task_order(self):
        page = render(fixture(), 'strip')
        cells = re.findall(r'<a role="listitem" class="tb-cell s-(\w+)" href="#task-(T-\d+)" data-task="(T-\d+)" title="([^"]*)"', page)
        self.assertEqual([c[1] for c in cells], [task_id(n) for n in sorted(DEPENDS)])
        expected = {'Complete': 'done', 'In progress': 'prog', 'Draft': 'draft', 'Blocked': 'block'}
        self.assertEqual([c[0] for c in cells], [expected[STATES[n]] for n in sorted(DEPENDS)])
        self.assertTrue(all(c[1] == c[2] and html.unescape(c[3]).startswith(c[1] + ' · ') for c in cells))
        figure = re.search(r'<p class="tb-figure"><b>(\d+)</b><span class="tb-of">/(\d+)</span>', page)
        self.assertEqual(figure.groups(), ('2', '6'))
        counts = dict((label, int(count)) for label, count in re.findall(r'<li><span class="glyph g-\w+" aria-hidden="true"></span>([^<]+) <b>(\d+)</b></li>',
                                                                       page.split('class="tb-states"', 1)[1].split('</ul>', 1)[0]))
        self.assertEqual(counts, {'Draft': 2, 'In progress': 1, 'Complete': 2, 'Blocked': 1})

    def test_a_spanish_page_names_states_in_spanish_wherever_a_reader_sees_them(self):
        page = render(fixture(SPANISH_PLAN + '\n| Criterion | Required behavior |\n|---|---|\n| `%s` | uno |\n' % req_id(1)), 'es-reading')
        text = visible_text(page)
        for english in ('In progress', 'Complete ', 'Blocked', 'Draft '):
            self.assertNotIn(english, text)
        for spanish in ('En curso', 'Completa', 'Bloqueada', 'Borrador', 'Una etapa es una columna del grafo, no un orden de trabajo.'):
            self.assertIn(spanish, page)
        self.assertEqual({row['state'] for group in StageList(page).groups for row in group}, {'Completa', 'En curso', 'Borrador', 'Bloqueada'})

    def test_print_uses_the_light_screen_palette_and_content_shows_before_scripts(self):
        page = render(fixture(), 'palette')
        css = re.search(r'<style>(.*?)</style>', page, re.S).group(1)
        light = dict(re.findall(r'--(ink|accent|accent-ink|mut):(#[0-9a-f]{6})', re.search(r':root\{([^}]*)\}', css).group(1)))
        self.assertEqual(set(light), {'ink', 'accent', 'accent-ink', 'mut'})
        report = css.split('/* Print:', 1)[1]
        used = set(re.findall(r'#[0-9a-f]{6}', report))
        self.assertIn(light['ink'], used)
        self.assertIn(light['accent'], used)
        self.assertIn(light['accent-ink'], used)
        self.assertTrue(used <= {light['ink'], light['accent'], light['accent-ink'], light['mut'], '#ffffff', '#fff', '#c9cdca', '#3b4046', '#fbdccd'},
                        'print colors outside the screen palette: %s' % sorted(used))
        self.assertRegex(page, r'<html lang="en" class="no-js">')
        self.assertNotIn('data-reveal', page)
        self.assertIn('.js .task:not(.open) .detail{display:none}', css)
        self.assertNotRegex(css, r'(?<![\w-])\.task \.detail\{[^}]*display:none')
        self.assertEqual(len(re.findall(r'<section class="sec" id="requirements">', page)), 1)
        self.assertEqual(len(re.findall(r'<h2>Requirements</h2>', page)), 1)


if __name__ == '__main__':
    unittest.main()
