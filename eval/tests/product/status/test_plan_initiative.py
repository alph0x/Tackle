"""The initiative view joins a workspace and its declared siblings (one hop) into one page, or refuses; members stay read-only.

Each case builds a three-member fixture through the shipped script with --initiative: the root alpha, its sibling api
at folder beta and its sibling gamma, which declares the root as core. Tasks are keyed <key>:T-NN with four digits.
The checks read the page, its data island, its drawn edges, its refusal lines, its --check digests and its layout.
"""
import hashlib
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import test_plan_layout_stability as layout
from plan_view_dom import run_scenario
from test_plan_siblings import AGENTS_HEAD, HEAD, PLAN, BRIEF, island, run, stage_labels, write_files
from test_plan_view import TEMPLATE, script_source, write_script
from test_plan_layout_stability import hidden_empty_statuses, reflow_problems

PAGE = 'initiative-view.html'
MEMBER_IDS = ('T-0001', 'T-0002', 'T-0007', 'T-0008', 'T-0009')
EDGE = re.compile(r'<path class="edge (?:met|open)" data-from="([^"]*)" data-to="([^"]*)"')
KEYED = re.compile(r'[a-z0-9-]+:T-\d{4}')
HELPERS = r"""
const ids = (env, selector) => env.all(selector).map((n) => n.getAttribute('data-task')).sort();
const edges = (env, kind) => env.all('.flow-svg .edge.' + kind).map((e) => e.getAttribute('data-from') + '>' + e.getAttribute('data-to')).sort();
"""


def row(ident, title, deps, status):
    return '| %s | %s | `tasks/%s.md` | %s | %s | v |\n' % (ident, title, ident, deps, status)


def board(*rows, schema=True):
    text = HEAD if schema else HEAD.replace('Schema: tackle-workspace/5\n\n', '')
    return text + ''.join(rows)


def declares(*pairs):
    """An AGENTS.md whose Sibling workspaces table declares each (slug, folder) pair in order."""
    return AGENTS_HEAD + '## Sibling workspaces\n\n| Sibling | Path | Relation |\n|---|---|---|\n' + ''.join(
        '| %s | docs/plans/%s | %s |\n' % (slug, folder, slug) for slug, folder in pairs)


def member(folder, task_board, agents):
    files = {'%s/task-board.md' % folder: task_board, '%s/AGENTS.md' % folder: agents, '%s/plan.md' % folder: PLAN}
    for ident in MEMBER_IDS:
        files['%s/tasks/%s.md' % (folder, ident)] = BRIEF % ident
    return files


def default_files():
    files = {}
    files.update(member('alpha', board(row('T-0001', 'First step', 'none', 'Complete'),
                                       row('T-0002', 'Second step', 'T-0007 [api]', 'Draft')),
                        declares(('api', 'beta'), ('gamma', 'gamma'))))
    files.update(member('beta', board(row('T-0007', 'Ship the client', 'none', 'In progress'),
                                      row('T-0008', 'Ship the server', 'none', 'Complete'),
                                      row('T-0009', 'Ship the docs', 'none', 'Draft')), AGENTS_HEAD))
    files.update(member('gamma', board(row('T-0001', 'Gamma step', 'T-0002 [core]', 'Draft')),
                        declares(('core', 'alpha'))))
    return files


def plans_of(tmp):
    return Path(tmp) / 'repo' / 'docs/plans'


def make(tmp, changes=None):
    """Write the fixture under the repository root; a change of None removes that file. Returns the root folder."""
    files = default_files()
    for name, text in (changes or {}).items():
        if text is None:
            files.pop(name, None)
        else:
            files[name] = text
    write_files(plans_of(tmp), files)
    return plans_of(tmp) / 'alpha'


def build(tmp, changes=None, options=()):
    root = make(tmp, changes)
    return run(tmp, root, options=('--initiative', *options), output=Path(tmp) / PAGE)


def scratch_script(tmp, source=None):
    folder = Path(tmp) / 'bin'
    folder.mkdir(exist_ok=True)
    return write_script(folder / 'plan_view.py', source=source)


def refused(result):
    return [line for line in result.stdout.splitlines() if line.startswith('refused: ')]


def assert_edges(page, expected):
    """The drawn edges must equal the expected (from, to) pairs, and every endpoint must carry its member key."""
    found = EDGE.findall(page)
    for pair in found:
        for end in pair:
            if not KEYED.fullmatch(end):
                raise AssertionError('unkeyed edge endpoint %s' % end)
    if sorted(found) != sorted(expected):
        raise AssertionError('edges %r, expected %r' % (found, expected))


def tree_state(folder):
    return {str(path.relative_to(folder)): (hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime_ns)
            for path in sorted(folder.rglob('*')) if path.is_file()}


def stale_after_edit(script, tmp, rel, suffix):
    """Build with the script, append the suffix to a member file, then check: the stale line, which must exit 1."""
    root = plans_of(tmp) / 'alpha'
    output = Path(tmp) / PAGE
    make(tmp)
    built = subprocess.run([sys.executable, '-I', str(script), '--template', str(TEMPLATE), '--initiative', str(root), str(output)],
                           capture_output=True, text=True, timeout=60)
    assert built.returncode == 0, built.stdout + built.stderr
    check = ['--initiative', '--check']
    current = subprocess.run([sys.executable, '-I', str(script), '--template', str(TEMPLATE), *check, str(root), str(output)],
                             capture_output=True, text=True, timeout=60)
    assert current.returncode == 0 and 'view current' in current.stdout, current.stdout + current.stderr
    member_file = plans_of(tmp) / rel
    member_file.write_text(member_file.read_text(encoding='utf-8') + suffix, encoding='utf-8')
    stale = subprocess.run([sys.executable, '-I', str(script), '--template', str(TEMPLATE), *check, str(root), str(output)],
                           capture_output=True, text=True, timeout=60)
    assert stale.returncode == 1, stale.stdout + stale.stderr
    return stale.stdout.strip()


class InitiativeViewTests(unittest.TestCase):
    def setUp(self):
        self.labels = stage_labels()

    def test_initiative_builds_members_and_edges(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, out = build(tmp)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            page = out.read_text(encoding='utf-8')
            tasks = {t['id']: t for t in island(page)['tasks']}
            self.assertEqual({key: t['status'] for key, t in tasks.items()}, {
                'alpha:T-0001': 'Complete', 'alpha:T-0002': 'Draft', 'api:T-0007': 'In progress',
                'api:T-0008': 'Complete', 'api:T-0009': 'Draft', 'gamma:T-0001': 'Draft'})
            self.assertEqual(tasks['alpha:T-0002']['deps'], ['api:T-0007'])
            self.assertEqual(tasks['gamma:T-0001']['deps'], ['alpha:T-0002'])
            assert_edges(page, [('api:T-0007', 'alpha:T-0002'), ('alpha:T-0002', 'gamma:T-0001')])
            progress = re.findall(r'<span class="sibling-plan" data-sibling="([^"]+)"><span class="sibling-slug">([^<]+)</span>'
                                  r'(?:<span class="sibling-relation">([^<]*)</span>)?<span class="sibling-progress">([^<]+)</span></span>', page)
            self.assertEqual(progress[:3], [
                ('alpha', 'alpha', '', self.labels['sibling_progress'].format(done=1, total=2)),
                ('api', 'api', 'api', self.labels['sibling_progress'].format(done=1, total=3)),
                ('gamma', 'gamma', 'gamma', self.labels['sibling_progress'].format(done=0, total=1))])
            self.assertNotIn('outside the initiative', result.stderr)

    def test_initiative_edges_name_both_ends(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, out = build(tmp)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            page = out.read_text(encoding='utf-8')
            expected = [('api:T-0007', 'alpha:T-0002'), ('alpha:T-0002', 'gamma:T-0001')]
            assert_edges(page, expected)
            variant = page.replace('data-from="api:T-0007" data-to="alpha:T-0002"',
                                   'data-from="x:api:T-0007" data-to="alpha:T-0002"', 1)
            with self.assertRaises(AssertionError):
                assert_edges(variant, expected)

    def test_initiative_slug_differs_from_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, out = build(tmp)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            page = out.read_text(encoding='utf-8')
            self.assertIn(('alpha:T-0002', 'gamma:T-0001'), EDGE.findall(page))
            self.assertFalse([task for task in island(page)['tasks'] if task['id'].startswith('core:')])
            self.assertNotIn('data-from="core:', page)
            self.assertNotIn('outside the initiative', result.stderr)

    def test_initiative_keys_by_slug(self):
        changes = {'alpha/task-board.md': board(row('T-0001', 'First step', 'none', 'Complete'),
                                                row('T-0002', 'Second step', 'none', 'Draft')),
                   'beta/task-board.md': board(row('T-0001', 'Beta first', 'none', 'Draft')),
                   'beta/AGENTS.md': AGENTS_HEAD}
        with tempfile.TemporaryDirectory() as tmp:
            result, out = build(tmp, changes)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            ids = [task['id'] for task in island(out.read_text(encoding='utf-8'))['tasks']]
            self.assertIn('alpha:T-0001', ids)
            self.assertIn('api:T-0001', ids)
            self.assertEqual(len(ids), len(set(ids)))

    def test_initiative_reports_outside_sibling(self):
        changes = {'beta/AGENTS.md': declares(('delta', 'delta')),
                   **member('delta', board(row('T-0001', 'Delta', 'none', 'Complete')), AGENTS_HEAD)}
        with tempfile.TemporaryDirectory() as tmp:
            result, out = build(tmp, changes)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(result.stderr.count('outside the initiative: delta'), 1, result.stderr)
            self.assertFalse([task for task in island(out.read_text(encoding='utf-8'))['tasks'] if task['id'].startswith('delta:')])

    def test_initiative_dep_on_outside_workspace(self):
        changes = {'beta/AGENTS.md': declares(('delta', 'delta')),
                   'beta/task-board.md': board(row('T-0007', 'Ship the client', 'none', 'In progress'),
                                               row('T-0008', 'Ship the server', 'T-0001 [delta]', 'Complete'),
                                               row('T-0009', 'Ship the docs', 'none', 'Draft')),
                   **member('delta', board(row('T-0001', 'Delta', 'none', 'Complete')), AGENTS_HEAD)}
        with tempfile.TemporaryDirectory() as tmp:
            result, out = build(tmp, changes)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            page = out.read_text(encoding='utf-8')
            self.assertIn('data-from="x:delta:T-0001" data-to="api:T-0008"', page)
            self.assertNotIn('data-task="x:', page)
            node = re.search(r'<g class="xnode [^"]*"[^>]*aria-label="delta · T-0001 · Delta · Complete"[^>]*>', page)
            self.assertIsNotNone(node, 'the outside node is missing its board status')
            self.assertNotIn('tabindex', node.group(0))
            self.assertEqual(result.stderr.count('outside the initiative: delta'), 1, result.stderr)

    def test_initiative_member_undeclared_slug(self):
        changes = {'beta/task-board.md': board(row('T-0007', 'Ship the client', 'none', 'In progress'),
                                               row('T-0008', 'Ship the server', 'none', 'Complete'),
                                               row('T-0009', 'Ship the docs', 'T-0001 [zeta]', 'Draft'))}
        with tempfile.TemporaryDirectory() as tmp:
            result, out = build(tmp, changes)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn('refused: task api:T-0009 depends on T-0001 [zeta], but no sibling named zeta is declared',
                          result.stdout)
            self.assertFalse(out.exists())

    def test_initiative_refuses_missing_board_once(self):
        cases = {
            'one member': {},
            'two members': {'beta/task-board.md': board(row('T-0007', 'Ship the client', 'T-0001 [gamma]', 'In progress'),
                                                       row('T-0008', 'Ship the server', 'none', 'Complete'),
                                                       row('T-0009', 'Ship the docs', 'none', 'Draft'), schema=False),
                            'gamma/AGENTS.md': declares(('api', 'beta'))},
        }
        base = {'alpha/task-board.md': board(row('T-0001', 'First step', 'T-0001 [gamma]', 'Draft'),
                                             row('T-0002', 'Second step', 'T-0001 [gamma], T-0007 [api]', 'Draft')),
                'beta/AGENTS.md': declares(('gamma', 'gamma')),
                'beta/task-board.md': board(row('T-0007', 'Ship the client', 'T-0001 [gamma]', 'In progress'),
                                            row('T-0008', 'Ship the server', 'none', 'Complete'),
                                            row('T-0009', 'Ship the docs', 'none', 'Draft')),
                'gamma/task-board.md': board(row('T-0001', 'Gamma step', 'none', 'Draft'), schema=False)}
        for label, extra in cases.items():
            with self.subTest(case=label), tempfile.TemporaryDirectory() as tmp:
                result, out = build(tmp, {**base, **extra})
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                lines = refused(result)
                self.assertEqual(len([line for line in lines if re.match(r'refused: sibling gamma has no tackle-workspace/5', line)]), 1, lines)
                self.assertFalse([line for line in lines if 'no sibling named' in line], lines)
                if label == 'two members':
                    self.assertEqual(len([line for line in lines if line.startswith(
                        'refused: sibling api has no tackle-workspace/5 task-board.md at docs/plans/beta')]), 1, lines)
                self.assertFalse(out.exists())

    def test_initiative_refuses_root_without_board(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, out = build(tmp, {'alpha/task-board.md': board(row('T-0001', 'First step', 'none', 'Complete'), schema=False)})
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn('refused: sibling alpha has no tackle-workspace/5 task-board.md at docs/plans/alpha', result.stdout)
            self.assertNotIn('refused: task-board.md is missing or empty', result.stdout)
            self.assertFalse(out.exists())

    def test_initiative_member_problems_carry_the_key_prefix(self):
        cases = {
            'status': ({'beta/task-board.md': board(row('T-0007', 'Ship the client', 'none', 'Bogus'),
                                                    row('T-0008', 'Ship the server', 'none', 'Complete'),
                                                    row('T-0009', 'Ship the docs', 'none', 'Draft'))},
                       'refused: api: task T-0007 has status Bogus, outside the board states'),
            'missing brief': ({'beta/tasks/T-0007.md': None},
                              'refused: api: missing brief tasks/T-0007.md for task T-0007'),
            'unknown dependency': ({'beta/task-board.md': board(row('T-0007', 'Ship the client', 'none', 'In progress'),
                                                                row('T-0008', 'Ship the server', 'none', 'Complete'),
                                                                row('T-0009', 'Ship the docs', 'T-0099', 'Draft'))},
                                   'refused: api: task T-0009 depends on unknown task T-0099'),
            'duplicate id': ({'beta/task-board.md': board(row('T-0007', 'Ship the client', 'none', 'In progress'),
                                                          row('T-0008', 'Ship the server', 'none', 'Complete'),
                                                          row('T-0009', 'Ship the docs', 'none', 'Draft'),
                                                          row('T-0009', 'Ship the docs again', 'none', 'Draft'))},
                              'refused: api: duplicate task id T-0009'),
            'root status': ({'alpha/task-board.md': board(row('T-0001', 'First step', 'none', 'Complete'),
                                                          row('T-0002', 'Second step', 'T-0007 [api]', 'Bogus'))},
                            'refused: alpha: task T-0002 has status Bogus, outside the board states'),
        }
        for label, (changes, line) in cases.items():
            with self.subTest(case=label), tempfile.TemporaryDirectory() as tmp:
                result, out = build(tmp, changes)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(line, refused(result))
                self.assertFalse(out.exists())

    def test_initiative_refuses_absent_member_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, out = build(tmp, {'alpha/AGENTS.md': declares(('api', 'beta'), ('gamma', 'gamma'), ('omega', 'omega'))})
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn('refused: sibling omega has no tackle-workspace/5 task-board.md at docs/plans/omega', result.stdout)
            self.assertFalse(out.exists())

    def test_initiative_refuses_cross_cycle(self):
        changes = {'alpha/task-board.md': board(row('T-0001', 'First step', 'T-0007 [api]', 'Draft'),
                                                row('T-0002', 'Second step', 'none', 'Complete')),
                   'beta/AGENTS.md': declares(('core', 'alpha')),
                   'beta/task-board.md': board(row('T-0007', 'Ship the client', 'T-0001 [core]', 'In progress'),
                                               row('T-0008', 'Ship the server', 'none', 'Complete'),
                                               row('T-0009', 'Ship the docs', 'none', 'Draft'))}
        with tempfile.TemporaryDirectory() as tmp:
            result, out = build(tmp, changes)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            match = [re.fullmatch(r'refused: cycle across workspaces: (\S+) -> (\S+) -> \1', line) for line in refused(result)]
            found = [m for m in match if m]
            self.assertEqual(len(found), 1, result.stdout)
            self.assertEqual({found[0].group(1), found[0].group(2)}, {'alpha:T-0001', 'api:T-0007'})
            self.assertFalse(out.exists())

    def test_initiative_refuses_three_member_cycle(self):
        changes = {'alpha/task-board.md': board(row('T-0001', 'First step', 'T-0007 [api]', 'Draft'),
                                                row('T-0002', 'Second step', 'none', 'Complete')),
                   'beta/AGENTS.md': declares(('gamma', 'gamma')),
                   'beta/task-board.md': board(row('T-0007', 'Ship the client', 'T-0001 [gamma]', 'In progress'),
                                               row('T-0008', 'Ship the server', 'none', 'Complete'),
                                               row('T-0009', 'Ship the docs', 'none', 'Draft')),
                   'gamma/task-board.md': board(row('T-0001', 'Gamma step', 'T-0001 [core]', 'Draft'))}
        with tempfile.TemporaryDirectory() as tmp:
            result, out = build(tmp, changes)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            found = [re.fullmatch(r'refused: cycle across workspaces: (\S+) -> (\S+) -> (\S+) -> \1', line) for line in refused(result)]
            found = [m for m in found if m]
            self.assertEqual(len(found), 1, result.stdout)
            cycle = list(found[0].groups())
            rotations = [['alpha:T-0001', 'api:T-0007', 'gamma:T-0001'][i:] + ['alpha:T-0001', 'api:T-0007', 'gamma:T-0001'][:i]
                         for i in range(3)]
            self.assertIn(cycle, rotations)
            self.assertFalse(out.exists())

    def test_initiative_local_cycle_inside_a_sibling(self):
        changes = {'beta/task-board.md': board(row('T-0007', 'Ship the client', 'T-0008', 'In progress'),
                                               row('T-0008', 'Ship the server', 'T-0007', 'Complete'),
                                               row('T-0009', 'Ship the docs', 'none', 'Draft'))}
        with tempfile.TemporaryDirectory() as tmp:
            result, out = build(tmp, changes)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn('refused: the dependencies form a cycle', result.stdout)
            self.assertNotIn('cycle across workspaces', result.stdout)
            self.assertFalse(out.exists())

    def test_initiative_check_stale_after_member_edit(self):
        edits = (('api:', 'beta/task-board.md', '\n| T-0010 | Extra | `tasks/T-0010.md` | none | Draft | v |\n'),
                 ('api:', 'beta/AGENTS.md', '\n<!-- edited -->\n'),
                 ('api:', 'beta/tasks/T-0007.md', '\nEdited.\n'),
                 ('gamma:', 'gamma/plan.md', '\nEdited.\n'),
                 ('gamma:', 'gamma/tasks/T-0001.md', '\nEdited.\n'),
                 ('alpha:', 'alpha/plan.md', '\nEdited.\n'))
        for key, rel, suffix in edits:
            with self.subTest(member=key, file=rel), tempfile.TemporaryDirectory() as tmp:
                line = stale_after_edit(scratch_script(tmp, script_source()), tmp, rel, suffix)
                self.assertTrue(line.startswith('view stale: '), line)
                self.assertIn(key, line)

    def test_initiative_stale_check_rejects_root_only_digest(self):
        variant = script_source().replace('inputs.update(member_digests(members))', 'pass', 1)
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(AssertionError):
                stale_after_edit(scratch_script(tmp, variant), tmp, 'beta/task-board.md', '\n| T-0010 | Extra | `tasks/T-0010.md` | none | Draft | v |\n')

    def test_initiative_leaves_members_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            before = {name: tree_state(plans_of(tmp) / name) for name in ('alpha', 'beta', 'gamma')}
            result, out = run(tmp, plans_of(tmp) / 'alpha', options=('--initiative',), output=Path(tmp) / PAGE)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            result, _ = run(tmp, plans_of(tmp) / 'alpha', options=('--initiative', '--check'), output=Path(tmp) / PAGE)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            after = {name: tree_state(plans_of(tmp) / name) for name in ('alpha', 'beta', 'gamma')}
            self.assertEqual(after, before)

    def test_initiative_rejects_page_and_map(self):
        for extra in (('--page', 'x.html'), ('--map', 'm.json')):
            with self.subTest(option=extra[0]), tempfile.TemporaryDirectory() as tmp:
                make(tmp)
                result, out = run(tmp, plans_of(tmp) / 'alpha', options=('--initiative', *extra), output=Path(tmp) / PAGE)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn('usage', result.stderr)
                self.assertFalse(out.exists())

    def test_initiative_selecting_a_member_task_traces_across_members(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, out = build(tmp)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            page = out.read_text(encoding='utf-8')
        result = run_scenario(page, HELPERS + r"""
const env = load();
env.window.TacklePlanView.select('api:T-0007', 'both');
assert.ok(env.one('.flow-svg').classList.contains('tracing'));
assert.ok(edges(env, 'down').includes('api:T-0007>alpha:T-0002'), edges(env, 'down').join(' '));
assert.ok(ids(env, '.flow-svg .node.down').includes('alpha:T-0002'));
""")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, 'OK', result.stderr)

    def test_initiative_layout_stable(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, out = build(tmp)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            page = out.read_text(encoding='utf-8')
        self.assertEqual(reflow_problems(page), [])
        self.assertEqual(hidden_empty_statuses(page), [])

        class InitiativeLayout(layout.LayoutStabilityBehaviorTests):
            @classmethod
            def setUpClass(cls):
                cls.page = page

        suite = unittest.TestSuite([InitiativeLayout(name) for name in (
            'test_a_zoom_keeps_the_canvas_box', 'test_a_filter_keeps_the_task_list_height_until_all')])
        outcome = unittest.TestResult()
        suite.run(outcome)
        self.assertEqual(outcome.failures + outcome.errors, [])
        self.assertEqual(outcome.testsRun, 2)


if __name__ == '__main__':
    unittest.main()
