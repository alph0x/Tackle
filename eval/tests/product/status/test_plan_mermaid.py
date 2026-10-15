"""Each diagram the plan view draws carries its exact Mermaid text, and the page copies or downloads it offline.

The recipe writes one text element per drawn diagram (the task graph of a Full plan, and each architecture
picture). The text grammar, the label escaping and the sanitized ids are checked on the recipe's own functions
and on the page it builds. The controls run the shipped controller on the page's markup in the DOM stub.
"""
import json
import re
import tempfile
import unittest
from pathlib import Path

from plan_view_dom import run_scenario
from test_architecture_map import base_map, delta_of, fenced_source, lay_out_sources, run_view
from test_plan_view import BOARD_HEAD, REPO, TEMPLATE, lite_plan, req_id, run_recipe

VIEW_RECIPE = REPO / 'skills/tackle/references/recipes/plan-view.md'
ENGLISH_PLAN = '# Plan — Mermaid\n\nThe plan has three tasks.\n\n| Criterion | Required behavior |\n|---|---|\n| `%s` | one |\n' % req_id(1)
SPANISH_PLAN = ('# Plan — Migración\n\nEl plan describe los pasos de la migración. Cada tarea tiene una verificación. '
                'La configuración queda lista después de la revisión.\n\n| Criterion | Required behavior |\n|---|---|\n| `%s` | uno |\n' % req_id(1))
ROWS = (('T-0001', 'First step', [], 'Complete'),
        ('T-0002', 'Second step', ['T-0001'], 'In progress'),
        ('T-0003', 'Third step', ['T-0001', 'T-0002'], 'Draft'))
ESCAPED_TITLE = 'Say "hi" #1 [a] & c ñ `x`'
TASK_GRAPH = '\n'.join([
    'flowchart LR',
    '  t_T_0001["T-0001 · First step"]:::done',
    '  t_T_0002["T-0002 · Second step"]:::prog',
    '  t_T_0003["T-0003 · Third step"]:::draft',
    '  t_T_0001 --> t_T_0002',
    '  t_T_0001 --> t_T_0003',
    '  t_T_0002 --> t_T_0003',
    '  classDef done fill:#111315,stroke:#111315,color:#eff0ed',
    '  classDef prog fill:#fbdccd,stroke:#f24a00,color:#111315',
    '  classDef draft fill:#fafaf8,stroke:#62686f,stroke-dasharray:4 3,color:#111315'])
TODAY_TEXT = '\n'.join([
    'flowchart LR',
    '  subgraph g_core["Core"]',
    '    c_intake["Intake"]',
    '    c_store["Store"]',
    '  end',
    '  subgraph g_tools["Tools"]',
    '    c_report["Report"]',
    '  end',
    '  c_intake -->|"calls"| c_store',
    '  c_store --> c_report'])
AFTER_LINES = [
    'flowchart LR',
    '  subgraph g_core["Core"]',
    '    c_intake["Intake"]',
    '    c_store["Store"]:::changed',
    '    c_viewer["Viewer"]:::added',
    '  end',
    '  subgraph g_tools["Tools"]',
    '    c_lint["Lint"]',
    '    c_report["Report"]',
    '    c_ship["Ship"]',
    '  end',
    '  classDef added fill:#fbdccd,stroke:#f24a00,color:#111315',
    '  classDef changed fill:#fafaf8,stroke:#f24a00,stroke-width:2px,color:#111315']
AFTER_EDGES = {'  c_intake -->|"calls"| c_store', '  c_store -->|"feeds"| c_report', '  c_lint -->|"gates"| c_ship',
               '  c_intake -->|"calls"| c_viewer'}
ENGLISH_BUTTONS = ('<button type="button" class="tool" data-mermaid-copy="plan-view-mermaid-tasks">Copy Mermaid</button>',
                   '<button type="button" class="tool" data-mermaid-download="plan-view-mermaid-tasks" data-file="tasks.mmd">Download .mmd</button>')
SMALL_BASE = {'schema': 'tackle-map/1', 'project': 'Small', 'summary': 'Small.',
              'verified_at': {'revision': 'v1.0.0', 'commit': 'abc1234', 'date': '2026-10-01'},
              'groups': [{'id': 'core', 'title': 'Core'}, {'id': 'tools', 'title': 'Tools'}],
              'components': [
                  {'id': 'intake', 'group': 'core', 'title': 'Intake', 'text': 'Reads requests.', 'sources': ['src/intake.py']},
                  {'id': 'store', 'group': 'core', 'title': 'Store', 'text': 'Keeps records.', 'sources': ['src/store.py']},
                  {'id': 'report', 'group': 'tools', 'title': 'Report', 'text': 'Writes reports.', 'sources': ['tools/report.py']}],
              'relations': [['intake', 'store', 'calls'], ['store', 'report', '']]}
NO_CHANGES = {'schema': 'tackle-map-delta/1', 'plan': 'Small', 'base_revision': 'v1.0.0', 'changes': []}


def view_namespace():
    """The shipped plan-view recipe's functions, loaded without running its entry point."""
    namespace = {'__name__': 'plan_view_recipe'}
    exec(compile(fenced_source(VIEW_RECIPE), str(VIEW_RECIPE), 'exec'), namespace)
    return namespace


def board_files(rows=ROWS, plan_text=None):
    """The files of a Full plan whose board holds the given task rows."""
    board = BOARD_HEAD + ''.join('| %s | %s | `tasks/%s.md` | %s | %s | v |\n' % (
        tid, title, tid, ', '.join(deps) or 'none', state) for tid, title, deps, state in rows)
    files = {'plan.md': plan_text or ENGLISH_PLAN, 'task-board.md': board, 'AGENTS.md': '# AGENTS\n\n**Methodology: Tackle 9.1.0**\n'}
    for tid, _, _, _ in rows:
        files['tasks/%s.md' % tid] = '# Task\n\n- **Traces to**: %s\n' % req_id(1)
    return files


def page_for(files, case):
    """The page the recipe builds for the files; a refused build fails the check."""
    with tempfile.TemporaryDirectory() as tmp:
        result, out = run_recipe(tmp, files, case)
        assert result.returncode == 0, result.stdout + result.stderr
        return out.read_text(encoding='utf-8')


def map_page(case, delta, base, extra=()):
    """The page the recipe builds with an architecture map."""
    with tempfile.TemporaryDirectory() as tmp:
        result, page, _ = run_view(tmp, case, delta, base, list(extra))
        assert result.returncode == 0, result.stdout + result.stderr
        return page


def mermaid_text(page, element):
    """The text of one Mermaid element, or None when the page has none."""
    found = re.search(r'<script type="text/plain" id="%s">(.*?)</script>' % element, page, re.S)
    return found.group(1) if found else None


def scenario(page, code, expected=TASK_GRAPH):
    """Run a DOM scenario against the page; the expected text is in scope as `expected`."""
    result = run_scenario(page, 'const expected = %s;\n' % json.dumps(expected) + code)
    assert result.returncode == 0 and result.stdout == 'OK', result.stdout + result.stderr


class TaskGraphTextTests(unittest.TestCase):
    def test_the_task_graph_text_is_exact_mermaid_in_task_order(self):
        page = page_for(board_files(), 'graph')
        self.assertEqual(mermaid_text(page, 'plan-view-mermaid-tasks'), TASK_GRAPH)

    def test_labels_escape_the_grammar_and_collapse_whitespace(self):
        label = view_namespace()['mermaid_label']
        self.assertEqual(label('Say "hi" #1 [a] | b & c\nñ `'), 'Say #quot;hi#quot; #35;1 [a] #124; b & c ñ #96;')
        self.assertEqual(label('a <b> c'), 'a #lt;b#gt; c')
        self.assertEqual(label('  spaced\t\there  '), 'spaced here')

    def test_colliding_sanitized_ids_take_the_first_free_suffix(self):
        ids = view_namespace()['mermaid_ids']
        self.assertEqual(ids('c_', ['a-b', 'a_b', 'T-0001']), {'a-b': 'c_a_b', 'a_b': 'c_a_b_2', 'T-0001': 'c_T_0001'})

    def test_a_title_reaches_the_page_escaped_with_no_angle_bracket(self):
        rows = (('T-0001', ESCAPED_TITLE, [], 'Complete'),) + ROWS[1:]
        text = mermaid_text(page_for(board_files(rows), 'escaped'), 'plan-view-mermaid-tasks')
        self.assertIn('  t_T_0001["T-0001 · Say #quot;hi#quot; #35;1 [a] & c ñ #96;x#96;"]:::done', text.split('\n'))
        self.assertNotIn('<', text)
        self.assertNotIn('&amp;', text)

    def test_an_empty_title_gives_the_id_alone(self):
        rows = (('T-0001', '', [], 'Complete'),) + ROWS[1:]
        text = mermaid_text(page_for(board_files(rows), 'empty'), 'plan-view-mermaid-tasks')
        self.assertIn('  t_T_0001["T-0001"]:::done', text.split('\n'))


class ArchitectureTextTests(unittest.TestCase):
    def test_the_today_picture_lists_groups_components_and_arrows(self):
        page = map_page('today', NO_CHANGES, SMALL_BASE)
        self.assertEqual(mermaid_text(page, 'plan-view-mermaid-today'), TODAY_TEXT)
        self.assertIsNone(mermaid_text(page, 'plan-view-mermaid-after'))

    def test_the_after_picture_marks_added_and_changed_components(self):
        page = map_page('after', delta_of(), base_map())
        today = mermaid_text(page, 'plan-view-mermaid-today').split('\n')
        self.assertFalse(any(':::' in line for line in today))
        after = mermaid_text(page, 'plan-view-mermaid-after').split('\n')
        self.assertEqual([line for line in after if '-->' not in line], AFTER_LINES)
        self.assertEqual({line for line in after if '-->' in line}, AFTER_EDGES)

    def test_colliding_component_ids_take_the_suffix_in_appearance_order(self):
        base = dict(SMALL_BASE)
        base['components'] = SMALL_BASE['components'] + [
            {'id': 'a-b', 'group': 'core', 'title': 'Dash', 'text': 'x.', 'sources': ['src/intake.py']},
            {'id': 'a_b', 'group': 'core', 'title': 'Under', 'text': 'x.', 'sources': ['src/intake.py']}]
        lines = mermaid_text(map_page('collide', NO_CHANGES, base), 'plan-view-mermaid-today').split('\n')
        self.assertLess(lines.index('    c_a_b["Dash"]'), lines.index('    c_a_b_2["Under"]'))

    def test_a_plan_without_a_map_has_only_the_task_graph_text(self):
        page = page_for(board_files(), 'nomap')
        self.assertIsNotNone(mermaid_text(page, 'plan-view-mermaid-tasks'))
        self.assertTrue('plan-view-mermaid-today' not in page, 'plan-view-mermaid-today')
        self.assertTrue('plan-view-mermaid-after' not in page, 'plan-view-mermaid-after')

    def test_a_picture_that_is_not_drawn_has_no_architecture_text(self):
        page = map_page('quiet', NO_CHANGES, SMALL_BASE, ['--map-scope', 'changed'])
        self.assertTrue('plan-view-mermaid-today' not in page, 'plan-view-mermaid-today')
        self.assertTrue('plan-view-mermaid-after' not in page, 'plan-view-mermaid-after')

    def test_a_focused_plan_has_no_mermaid_element_or_control(self):
        page = page_for({'plan.md': lite_plan(), 'history.md': '# History\n'}, 'lite')
        self.assertTrue('plan-view-mermaid-' not in page, 'plan-view-mermaid-')
        self.assertTrue('class="mermaid-tools"' not in page, 'class="mermaid-tools"')


class ControlsTests(unittest.TestCase):
    def test_each_diagram_has_a_mermaid_group_after_its_zoom_tools(self):
        page = page_for(board_files(), 'controls')
        self.assertTrue('<div class="mermaid-tools" role="group" aria-label="Mermaid"' in page, '<div class="mermaid-tools" role="group" aria-label="Mermaid"')
        for button in ENGLISH_BUTTONS:
            self.assertTrue(button in page, button)
        self.assertTrue('<p class="mermaid-status" role="status"></p>' in page, '<p class="mermaid-status" role="status"></p>')
        self.assertTrue('data-copied="Copied to the clipboard."' in page, 'data-copied="Copied to the clipboard."')
        self.assertTrue('data-select="Select the text and copy it."' in page, 'data-select="Select the text and copy it."')
        self.assertTrue('data-downloaded="Downloaded {file}."' in page, 'data-downloaded="Downloaded {file}."')
        graph = page[page.index('id="graph"'):page.index('</section>', page.index('id="graph"'))]
        self.assertLess(graph.index('class="zoom"'), graph.index('class="mermaid-tools"'))

    def test_the_controls_speak_the_plan_language(self):
        page = page_for(board_files(plan_text=SPANISH_PLAN), 'spanish')
        self.assertTrue('<html lang="es"' in page, '<html lang="es"')
        self.assertTrue('>Copiar Mermaid</button>' in page, '>Copiar Mermaid</button>')
        self.assertTrue('>Descargar .mmd</button>' in page, '>Descargar .mmd</button>')
        self.assertTrue('data-copied="Copiado al portapapeles."' in page, 'data-copied="Copiado al portapapeles."')
        self.assertTrue('data-select="Selecciona el texto y cópialo."' in page, 'data-select="Selecciona el texto y cópialo."')
        self.assertTrue('data-downloaded="Descargado {file}."' in page, 'data-downloaded="Descargado {file}."')

    def test_the_controls_are_hidden_in_print(self):
        template = TEMPLATE.read_text(encoding='utf-8')
        rule = '.mermaid-tools,.mermaid-text{display:none!important}'
        self.assertIn(rule, template)
        layer = template.index('@layer print{')
        self.assertGreater(template.index('@media print{', layer), layer)
        self.assertGreater(template.index(rule), template.index('@media print{', layer))
        self.assertLess(template.index(rule), template.index('.print-report{', layer))

    def test_a_built_page_links_only_its_four_urls_and_loads_no_script(self):
        page = map_page('offline', delta_of(), base_map())
        urls = {url.rstrip('.,;') for url in re.findall(r'https?://[^\s"\'<>)]+', page)}
        self.assertEqual(urls, {'http://www.w3.org/2000/svg', 'https://github.com/Outfitio/Outfit-Fonts',
                                'https://github.com/alph0x/Tackle', 'https://scripts.sil.org/OFL'})
        self.assertTrue('<script src=' not in page, '<script src=')


class ControlBehaviorTests(unittest.TestCase):
    def test_copy_writes_the_clipboard_and_says_so(self):
        scenario(page_for(board_files(), 'copy'), r"""
const env = load();
let copied = null;
env.window.navigator = { clipboard: { writeText: (t) => { copied = t; return Promise.resolve(); } } };
const button = env.one('[data-mermaid-copy="plan-view-mermaid-tasks"]');
button.click();
await settle();
assert.strictEqual(copied, expected);
assert.strictEqual(button.parentNode.querySelector('.mermaid-status').textContent, 'Copied to the clipboard.');
assert.strictEqual(env.one('textarea.mermaid-text'), null);
""")

    def test_copy_without_a_clipboard_offers_the_selectable_text(self):
        scenario(page_for(board_files(), 'copy-fallback'), r"""
const env = load();
const button = env.one('[data-mermaid-copy="plan-view-mermaid-tasks"]');
button.click();
await settle();
const area = env.one('textarea.mermaid-text');
assert.notStrictEqual(area, null);
assert.strictEqual(area.hasAttribute('readonly'), true);
assert.strictEqual(area.textContent, expected);
assert.strictEqual(button.parentNode.querySelector('.mermaid-status').textContent, 'Select the text and copy it.');
""")

    def test_download_saves_the_named_mmd_file_from_a_blob(self):
        page = map_page('download', delta_of(), base_map())
        scenario(page, r"""
const env = load();
const blobs = [];
const anchors = [];
const make = env.document.createElement;
env.document.createElement = (tag) => { const el = make(tag); if (tag === 'a') { anchors.push(el); } return el; };
env.window.Blob = function (parts, options) { blobs.push(parts.join('')); this.type = options.type; };
env.window.URL = { createObjectURL: () => 'blob:x', revokeObjectURL() {} };
const button = env.one('[data-mermaid-download="plan-view-mermaid-after"]');
button.click();
await settle();
assert.strictEqual(blobs.length, 1);
assert.strictEqual(blobs[0], expected);
assert.strictEqual(anchors.length, 1);
assert.strictEqual(anchors[0].getAttribute('download'), 'architecture-after.mmd');
assert.strictEqual(anchors[0].getAttribute('href'), 'blob:x');
assert.strictEqual(button.parentNode.querySelector('.mermaid-status').textContent, 'Downloaded architecture-after.mmd.');
""", expected=mermaid_text(page, 'plan-view-mermaid-after'))

    def test_download_of_the_task_graph_names_tasks_mmd(self):
        scenario(page_for(board_files(), 'download-tasks'), r"""
const env = load();
const anchors = [];
const make = env.document.createElement;
env.document.createElement = (tag) => { const el = make(tag); if (tag === 'a') { anchors.push(el); } return el; };
env.window.Blob = function (parts) { this.parts = parts; };
env.window.URL = { createObjectURL: () => 'blob:x', revokeObjectURL() {} };
env.one('[data-mermaid-download="plan-view-mermaid-tasks"]').click();
await settle();
assert.strictEqual(anchors[0].getAttribute('download'), 'tasks.mmd');
""")


if __name__ == '__main__':
    unittest.main()
