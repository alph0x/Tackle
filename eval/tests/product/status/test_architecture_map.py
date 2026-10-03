"""The shipped architecture-map recipe validates, applies, scopes and folds a map, and the plan view draws it.

The test extracts the recipe from `references/recipes/architecture-map.md`, calls its functions on fixture
maps, then runs the shipped plan-view recipe as a child process with `--map` over a throwaway repository
laid out as `<root>/docs/plans/<name>`. Ids are built at run time. The interactive behavior (tabs, picture
toggle, selection) is outside this oracle; the markup and data it needs are inside it.
"""
import ast
import copy
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
MAP_RECIPE = REPO / 'skills/tackle/references/recipes/architecture-map.md'
VIEW_RECIPE = REPO / 'skills/tackle/references/recipes/plan-view.md'
TEMPLATE = REPO / 'skills/tackle/references/plan-view.template.md'
STATES = ('Draft, Ready to run, In progress, Checking, Complete, Blocked, Interrupted, Skipped, '
          'Unverifiable, Waiting on owner')
FORBIDDEN = {'socket', 'ssl', 'urllib', 'http', 'subprocess', 'requests', 'asyncio', 'webbrowser', 'multiprocessing'}
PAYLOAD = '<img src=x onerror=alert(1)>'
ATTR = 'x" onmouseover="alert(2)'


def task_id(n):
    return 'T-%02d' % n


def req_id(n):
    return 'R%02d' % n


def fenced_source(path):
    parts = path.read_text(encoding='utf-8').split('```python\n')
    assert len(parts) == 2, 'the recipe must hold exactly one fenced python block'
    return parts[1].split('\n```')[0] + '\n'


def load_map_recipe():
    source = fenced_source(MAP_RECIPE)
    imported = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imported |= {a.name.split('.')[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split('.')[0])
    assert not imported & FORBIDDEN, 'the map recipe imports %s' % sorted(imported & FORBIDDEN)
    namespace = {'__name__': 'map_recipe'}
    exec(compile(source, str(MAP_RECIPE), 'exec'), namespace)
    return namespace


def base_map():
    return {'schema': 'tackle-map/1', 'project': 'Demo', 'summary': 'A demo.',
            'verified_at': {'revision': 'v1.0.0', 'commit': 'abc1234', 'date': '2026-10-01'},
            'groups': [{'id': 'core', 'title': 'Core'}, {'id': 'tools', 'title': 'Tools'}],
            'components': [
                {'id': 'intake', 'group': 'core', 'title': 'Intake', 'text': 'Reads requests.', 'sources': ['src/intake.py']},
                {'id': 'store', 'group': 'core', 'title': 'Store', 'text': 'Keeps records.', 'sources': ['src/store.py']},
                {'id': 'report', 'group': 'tools', 'title': 'Report', 'text': 'Writes reports.',
                 'sources': ['tools/report.py', 'tools/removed.py']},
                {'id': 'lint', 'group': 'tools', 'title': 'Lint', 'text': 'Checks files.', 'sources': ['tools/lint.py']},
                {'id': 'ship', 'group': 'tools', 'title': 'Ship', 'text': 'Publishes.', 'sources': ['tools/ship.py']}],
            'relations': [['intake', 'store', 'calls'], ['store', 'report', 'feeds'], ['lint', 'ship', 'gates']]}


def delta_of(extra_changes=()):
    return {'schema': 'tackle-map-delta/1', 'plan': 'Demo two', 'base_revision': 'v1.0.0',
            'changes': [
                {'op': 'change', 'id': 'store', 'text': 'Keeps records, faster.', 'task': task_id(1), 'state': 'done'},
                {'op': 'add', 'id': 'viewer', 'group': 'core', 'title': 'Viewer', 'text': 'Shows the map.',
                 'task': task_id(2), 'state': 'planned', 'relations': [['intake', 'viewer', 'calls']]}] + list(extra_changes)}


def invalid_deltas():
    other = task_id(3)
    cases = {
        'change of an unknown component': {'op': 'change', 'id': 'ghost', 'text': 'x', 'task': other, 'state': 'planned'},
        'add of an existing component': {'op': 'add', 'id': 'intake', 'group': 'core', 'title': 'Again', 'text': 'x', 'task': other, 'state': 'planned'},
        'add into an unknown group': {'op': 'add', 'id': 'wander', 'group': 'nowhere', 'title': 'W', 'text': 'x', 'task': other, 'state': 'planned'},
        'change into an unknown group': {'op': 'change', 'id': 'lint', 'group': 'nowhere', 'task': other, 'state': 'planned'},
        'state outside the vocabulary': {'op': 'change', 'id': 'lint', 'text': 'x', 'task': other, 'state': 'maybe'},
        'op outside the vocabulary': {'op': 'remove', 'id': 'ship', 'task': other, 'state': 'planned'},
        'relation to a missing component': {'op': 'add', 'id': 'extra', 'group': 'core', 'title': 'E', 'text': 'x', 'task': other,
                                            'state': 'planned', 'relations': [['extra', 'phantom', 'calls']]},
    }
    named = {'change of an unknown component': 'ghost', 'add of an existing component': 'intake',
             'add into an unknown group': 'nowhere', 'change into an unknown group': 'nowhere',
             'state outside the vocabulary': 'maybe', 'op outside the vocabulary': 'remove',
             'relation to a missing component': 'phantom'}
    return [(name, delta_of([change]), named[name]) for name, change in cases.items()]


def ids_of(map_):
    return sorted(c['id'] for c in map_['components'])


def lay_out_sources(root, skip=('tools/removed.py',)):
    for relative in ('src/intake.py', 'src/store.py', 'tools/report.py', 'tools/removed.py', 'tools/lint.py', 'tools/ship.py'):
        if relative in skip:
            continue
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('x\n', encoding='utf-8')


def workspace(root, delta, plan_text=None, running=False):
    ws = root / 'docs/plans/demo'
    (ws / 'tasks').mkdir(parents=True)
    first, second = task_id(1), task_id(2)
    (ws / 'task-board.md').write_text(
        '# Board\n\nStates: %s.\n\n| Task | What | Brief | Depends on | Status | Verification |\n|---|---|---|---|---|---|\n'
        '| %s | Speed up the store | `tasks/%s.md` | none | Complete | v |\n'
        '| %s | Add the viewer | `tasks/%s.md` | %s | In progress | v |\n' % (STATES, first, first, second, second, first),
        encoding='utf-8')
    for task in (first, second):
        (ws / 'tasks' / (task + '.md')).write_text('# Task\n\n- **Traces to**: %s\n' % req_id(1), encoding='utf-8')
    (ws / 'plan.md').write_text(plan_text or '# Action plan — demo\n\nThe plan adds a viewer and speeds up the store.\n\n| `%s` | one | o |\n' % req_id(1),
                                encoding='utf-8')
    (ws / 'history.md').write_text('# History\n', encoding='utf-8')
    if running:
        (ws / 'resource-usage.md').write_text(
            '# Usage\n\n| Run ID | Event | Task | Role | Harness | Tier | Model | Effort | At | Outcome | Attempts | Rework | Verification | Source |\n'
            '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n'
            '| run/a | start | %s | executor | h | standard | m | n/a | 2026-10-03T10:00:00Z | o | n/a | n/a | n/a | s |\n' % second,
            encoding='utf-8')
    if delta is not None:
        (ws / 'map-delta.json').write_text(json.dumps(delta), encoding='utf-8')
    return ws


def run_view(tmp, case, delta, base=None, extra=(), plan_text=None, running=False):
    root = Path(tmp) / case
    root.mkdir()
    lay_out_sources(root)
    ws = workspace(root, delta, plan_text, running)
    script = root / 'view-recipe.py'
    script.write_text(fenced_source(VIEW_RECIPE), encoding='utf-8')
    arguments = []
    if base is not None:
        (root / 'base.json').write_text(json.dumps(base), encoding='utf-8')
        arguments = ['--map', str(root / 'base.json')]
    out = ws / 'plan-view.html'
    result = subprocess.run([sys.executable, '-I', str(script), '--template', str(TEMPLATE)] + arguments + list(extra) + [str(ws), str(out)],
                            cwd=root, capture_output=True, text=True, timeout=60)
    page = out.read_text(encoding='utf-8') if out.exists() else ''
    return result, page, out


def island_of(page):
    raw = re.search(r'<script type="application/json" id="plan-view-data">(.*?)</script>', page, re.S).group(1)
    assert not re.search(r'[<>&]', raw), 'the island holds a raw <, > or &'
    return json.loads(raw)


def static_part(page):
    return re.sub(r'<script\b.*?</script>', '', page, flags=re.S)


class ArchitectureMapTests(unittest.TestCase):
    def test_the_shipped_recipe_draws_and_folds_a_fixture_map(self):
        m = load_map_recipe()
        base, delta = base_map(), delta_of()
        self.assertEqual(m['validate'](base, delta), [])
        for name, bad, needle in invalid_deltas():
            problems = m['validate'](base, bad)
            self.assertTrue(problems, name)
            self.assertTrue(any(needle in line for line in problems), '%s: %s' % (name, problems))
            with self.assertRaises(ValueError, msg=name):
                m['after'](base, bad)
            with self.assertRaises(ValueError, msg=name):
                m['fold'](base, bad, 'v2.0.0')
        later = m['after'](base, delta)
        self.assertEqual(ids_of(later), ['intake', 'lint', 'report', 'ship', 'store', 'viewer'])
        self.assertEqual([c for c in later['components'] if c['id'] == 'store'][0]['text'], 'Keeps records, faster.')
        self.assertIn(['intake', 'viewer', 'calls'], [list(r) for r in later['relations']])
        self.assertEqual(sorted(m['neighbors'](later, {'viewer'})), ['intake', 'viewer'])
        self.assertEqual(sorted(m['neighbors'](later, {'store'})), ['intake', 'report', 'store'])
        with tempfile.TemporaryDirectory() as tmp:
            lay_out_sources(Path(tmp))
            self.assertEqual(m['stale'](base, Path(tmp)), ['report'])
        folded = m['fold'](base, delta, 'v2.0.0')
        self.assertEqual(ids_of(folded), ids_of(base))
        self.assertEqual([c for c in folded['components'] if c['id'] == 'store'][0]['text'], 'Keeps records, faster.')
        self.assertEqual(folded['verified_at']['revision'], 'v2.0.0')
        self.assertEqual(sorted(map(list, folded['relations'])), sorted(map(list, base['relations'])))
        # Done relations fold in; planned ones stay out; a done relation to a planned component is refused.
        done_add = delta_of()
        done_add['changes'][1]['state'] = 'done'
        folded = m['fold'](base, done_add, 'v2.0.0')
        self.assertIn('viewer', ids_of(folded))
        self.assertIn(['intake', 'viewer', 'calls'], [list(r) for r in folded['relations']])
        dangling = delta_of([{'op': 'change', 'id': 'lint', 'text': 'x', 'task': task_id(3), 'state': 'done',
                              'relations': [['lint', 'viewer', 'reads']]}])
        self.assertEqual(m['validate'](base, dangling), [])
        with self.assertRaises(ValueError):
            m['fold'](base, dangling, 'v2.0.0')
        self.assertEqual(base, base_map())
        self.assertEqual(delta, delta_of())

    def test_the_view_draws_today_and_after_scopes_them_and_refuses_a_bad_delta(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, page, _ = run_view(tmp, 'full', delta_of(), base_map())
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            data = island_of(page)
            self.assertEqual(data['map'], {'today': ['intake', 'lint', 'report', 'ship', 'store'],
                                           'after': ['intake', 'lint', 'report', 'ship', 'store', 'viewer'],
                                           'changed': ['store', 'viewer'], 'stale': ['report']})
            static = static_part(page)
            for needle in ('id="architecture"', 'data-pic="today"', 'data-pic="after"', 'role="tab"', 'Showing: the whole project'):
                self.assertIn(needle, static)
            added = re.search(r'<article[^>]*data-pic="after"[^>]*data-cid="viewer"[^>]*>|<article[^>]*data-cid="viewer"[^>]*data-pic="after"[^>]*>', static)
            self.assertIsNotNone(added)
            self.assertIn('data-change="add"', added.group(0))
            stale = re.search(r'<article[^>]*data-cid="report"[^>]*>', static)
            self.assertIn('data-stale="true"', stale.group(0))
            self.assertIn(task_id(2), static)
            result, page, _ = run_view(tmp, 'scoped', delta_of(), base_map(), ['--map-scope', 'changed'])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(island_of(page)['map'], {'today': ['intake', 'report', 'store'],
                                                      'after': ['intake', 'report', 'store', 'viewer'],
                                                      'changed': ['store', 'viewer'], 'stale': ['report']})
            self.assertNotIn('data-cid="lint"', static_part(page))
            result, page, _ = run_view(tmp, 'nomap', delta_of())
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            data = island_of(page)
            self.assertIn('map', data)
            self.assertIsNone(data['map'])
            self.assertIn('data-map="none"', static_part(page))
            result, page, _ = run_view(tmp, 'plain', None)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn('id="architecture"', static_part(page))
            self.assertIsNone(island_of(page)['map'])
            for name, bad, needle in invalid_deltas():
                result, page, out = run_view(tmp, 'bad-' + re.sub(r'\W+', '-', name), bad, base_map())
                self.assertEqual(result.returncode, 1, name)
                self.assertTrue(any(line.startswith('refused: ') and needle in line for line in result.stdout.splitlines()), name)
                self.assertFalse(out.exists(), name)
            result, page, out = run_view(tmp, 'missing-base', delta_of(), base_map(), ['--map', str(Path(tmp) / 'nowhere.json')])
            self.assertEqual(result.returncode, 1)
            self.assertFalse(out.exists())

    def test_the_view_escapes_every_map_string(self):
        base = base_map()
        base['project'] = PAYLOAD
        base['groups'][0]['title'] = PAYLOAD
        base['components'][0].update(title=PAYLOAD, text='"><svg onload=alert(3)>', sources=['src/intake.py', ATTR])
        base['relations'][0][2] = PAYLOAD
        delta = delta_of()
        delta['changes'][1].update(title='</script><script>alert(4)</script>', text=PAYLOAD)
        with tempfile.TemporaryDirectory() as tmp:
            result, page, _ = run_view(tmp, 'hostile', delta, base)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            island_of(page)
            for needle in (PAYLOAD, '<svg onload', '</script><script>alert(4)', 'onmouseover="alert(2)"'):
                self.assertNotIn(needle, page)

    def test_the_spanish_page_names_live_work_en_marcha(self):
        spanish = ('# Plan — Migración\n\nEl plan describe los pasos de la migración. Cada tarea tiene una verificación. '
                   'La configuración queda lista después de la revisión.\n\n| `%s` | uno | o |\n' % req_id(1))
        with tempfile.TemporaryDirectory() as tmp:
            result, page, _ = run_view(tmp, 'es', None, plan_text=spanish, running=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            static = static_part(page)
            self.assertIn('<span class="live">En marcha</span>', static)
            self.assertNotIn('<span class="live">En curso</span>', static)
            self.assertIn('En curso', re.sub(r'<[^>]*>', ' ', static))
            result, page, _ = run_view(tmp, 'en', None, running=True)
            self.assertIn('<span class="live">Live</span>', static_part(page))


if __name__ == '__main__':
    unittest.main()
