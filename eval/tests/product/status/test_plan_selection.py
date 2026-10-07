"""One reversible task selection is shared by every reader of the generated plan view.

The shipped recipe writes a page for a small fixture; its own controller then runs on its own markup in a
minimal DOM (plan_view_dom.js). Selecting a task from the graph, the task list, an anchor or the public API
marks the same task in the graph, the list, the inspector and the title strip, traces its prerequisites and
dependents from the board's dependencies, and clears on a second selection or Escape. Filters, the theme
choice, diagram zoom and the optional live client are covered on the same page. No browser layout,
painting or native behavior is observed.
"""
import tempfile
import unittest

from plan_view_dom import run_scenario
from test_plan_view import BOARD_HEAD, req_id, run_recipe, task_id

STATES = {1: 'Complete', 2: 'In progress', 3: 'Draft', 4: 'Draft', 5: 'Draft'}
DEPENDS = {1: [], 2: [1], 3: [2], 4: [3], 5: [2]}
TITLES = {1: 'First step', 2: 'Second step', 3: 'Third step', 4: 'Fourth step', 5: 'Side branch'}


def fixture():
    rows = ''.join('| %s | %s | `tasks/%s.md` | %s | %s | v |\n' % (
        task_id(n), TITLES[n], task_id(n), ', '.join(task_id(d) for d in DEPENDS[n]) or 'none', STATES[n]) for n in sorted(STATES))
    files = {'plan.md': '# Plan — Selection\n\nThe plan has a short chain and one side branch.\n\n| Criterion | Required behavior |\n|---|---|\n| `%s` | one |\n' % req_id(1),
             'task-board.md': BOARD_HEAD + rows, 'AGENTS.md': '# AGENTS\n\n**Methodology: Tackle 9.1.0**\n'}
    for n in STATES:
        files['tasks/%s.md' % task_id(n)] = '# Task\n\n- **Traces to**: %s\n' % req_id(1)
    return files


def render(files=None, case='selection'):
    with tempfile.TemporaryDirectory() as tmp:
        result, out = run_recipe(tmp, files or fixture(), case)
        assert result.returncode == 0, result.stdout + result.stderr
        return out.read_text(encoding='utf-8')


HELPERS = r"""
const T = (n) => ['T', String(n).padStart(2, '0')].join('-');
const ids = (env, selector, attribute) => env.all(selector).map((n) => n.getAttribute(attribute || 'data-task')).sort();
const edges = (env, kind) => env.all('.flow-svg .edge.' + kind).map((e) => e.getAttribute('data-from') + '>' + e.getAttribute('data-to')).sort();
"""


class PlanSelectionTests(unittest.TestCase):
    page = None

    @classmethod
    def setUpClass(cls):
        cls.page = render()

    def scenario(self, code, page=None):
        result = run_scenario(page or self.page, HELPERS + code)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, 'OK', result.stderr)

    def test_a_graph_selection_reaches_every_reader_and_traces_the_board_dependencies(self):
        self.scenario(r"""
const env = load();
const node = env.one('.flow-svg .node[data-task="' + T(3) + '"]');
node.click();
assert.strictEqual(env.root.getAttribute('data-selected-task'), T(3));
assert.ok(env.one('#task-' + T(3)).classList.contains('selected'));
assert.ok(env.one('.tb-cell[data-task="' + T(3) + '"]').classList.contains('on'));
assert.ok(env.one('.flow-svg').classList.contains('tracing'));
assert.deepStrictEqual(ids(env, '.flow-svg .node.sel'), [T(3)]);
assert.deepStrictEqual(ids(env, '.flow-svg .node.up'), [T(1), T(2)]);
assert.deepStrictEqual(ids(env, '.flow-svg .node.down'), [T(4)]);
assert.deepStrictEqual(edges(env, 'up'), [T(1) + '>' + T(2), T(2) + '>' + T(3)]);
assert.deepStrictEqual(edges(env, 'down'), [T(3) + '>' + T(4)]);
assert.deepStrictEqual(env.all('.task.related').map((c) => c.id).sort(), ['task-' + T(1), 'task-' + T(2), 'task-' + T(4)]);
const body = env.one('#flow-inspector .inspector-body');
assert.ok(!body.hidden && env.one('#flow-inspector .inspector-empty').hidden);
assert.ok(body.textContent.includes('Third step'));
assert.ok(body.textContent.includes(T(2)), 'the inspector lists what the task needs');
assert.ok(body.querySelector('a[href="#task-' + T(3) + '"]') || body.querySelectorAll('a').length, 'the inspector links back to the task list');
assert.ok(!env.one('#clear-trace').hidden);
node.click();
assert.strictEqual(env.root.getAttribute('data-selected-task'), null);
assert.strictEqual(env.all('.task.selected, .task.related, .tb-cell.on, .flow-svg .node.sel, .flow-svg .node.up, .flow-svg .edge.up').length, 0);
assert.ok(!env.one('.flow-svg').classList.contains('tracing'));
assert.ok(env.one('#flow-inspector .inspector-body').hidden && !env.one('#flow-inspector .inspector-empty').hidden);
assert.ok(env.one('#clear-trace').hidden);
node.key('Enter');
assert.strictEqual(env.root.getAttribute('data-selected-task'), T(3), 'a focused node answers Enter');
env.one('#clear-trace').click();
assert.strictEqual(env.root.getAttribute('data-selected-task'), null);
""")

    def test_the_task_list_opens_details_traces_one_direction_and_escape_clears(self):
        self.scenario(r"""
const env = load();
const head = env.one('#task-' + T(2) + ' .task-head');
head.click();
assert.ok(env.one('#task-' + T(2)).classList.contains('open'));
assert.strictEqual(head.getAttribute('aria-expanded'), 'true');
assert.strictEqual(env.root.getAttribute('data-selected-task'), T(2));
env.one('#task-' + T(2) + ' [data-trace="down"]').click();
assert.deepStrictEqual(ids(env, '.flow-svg .node.down'), [T(3), T(4), T(5)]);
assert.deepStrictEqual(ids(env, '.flow-svg .node.up'), []);
env.one('#task-' + T(2) + ' [data-trace="up"]').click();
assert.deepStrictEqual(ids(env, '.flow-svg .node.up'), [T(1)]);
assert.deepStrictEqual(ids(env, '.flow-svg .node.down'), []);
env.one('#task-' + T(4)).key('Escape');
assert.strictEqual(env.root.getAttribute('data-selected-task'), null);
head.click();
assert.ok(!env.one('#task-' + T(2)).classList.contains('open'));
""")

    def test_anchors_and_the_public_api_select_a_task_and_undo_a_filter_that_hides_it(self):
        self.scenario(r"""
let env = load({ hash: '#task-' + T(4) });
assert.strictEqual(env.root.getAttribute('data-selected-task'), T(4));
assert.ok(env.one('#task-' + T(4)).classList.contains('open'));
env = load();
const complete = env.all('[data-filter]').find((b) => b.getAttribute('data-filter') === 'Complete');
complete.click();
assert.strictEqual(complete.getAttribute('aria-pressed'), 'true');
assert.deepStrictEqual(env.all('.task').filter((c) => !c.hidden).map((c) => c.id), ['task-' + T(1)]);
assert.deepStrictEqual(ids(env, '.flow-svg .node.filtered'), [T(2), T(3), T(4), T(5)]);
assert.ok(env.one('.empty-filter').hidden);
env.location.hash = '#task-' + T(4) + '';
env.window.fire('hashchange');
assert.strictEqual(env.one('[data-filter="all"]').getAttribute('aria-pressed'), 'true');
assert.ok(!env.one('#task-' + T(4)).hidden);
assert.strictEqual(env.root.getAttribute('data-selected-task'), T(4));
env.window.TacklePlanView.select(T(5), 'both');
env.window.TacklePlanView.select(T(5), 'both');
assert.strictEqual(env.root.getAttribute('data-selected-task'), T(5), 'the restore API keeps an existing selection');
env.window.fire('resize');
assert.strictEqual(env.root.getAttribute('data-selected-task'), T(5), 'a resize keeps the selection');
""")

    def test_the_theme_choice_toggles_persists_and_survives_blocked_storage(self):
        self.scenario(r"""
let env = load();
env.one('#theme').click();
assert.strictEqual(env.root.getAttribute('data-theme'), 'dark');
assert.strictEqual(env.store['tackle-plan-view-theme'], 'dark');
env.one('#theme').click();
assert.strictEqual(env.root.getAttribute('data-theme'), 'light');
env = load({ media: { '(prefers-color-scheme: dark)': true } });
env.one('#theme').click();
assert.strictEqual(env.root.getAttribute('data-theme'), 'light', 'the first toggle leaves the system dark theme');
env = load({ storage: 'throws' });
env.one('#theme').click();
assert.strictEqual(env.root.getAttribute('data-theme'), 'dark');
assert.ok(env.root.classList.contains('js') && !env.root.classList.contains('no-js'));
""")

    def test_diagrams_start_readable_fit_on_request_and_follow_resizes_until_the_reader_zooms(self):
        self.scenario(r"""
const svg0 = load().one('.flow-svg');
const natural = Number(svg0.getAttribute('width'));
assert.ok(natural > 300);
const env = load({ sizes: [['.gscroll', natural / 2]] });
const svg = env.one('.flow-svg');
const level = env.one('#graph .zoom-level');
const scaleOf = () => Number(svg.getAttribute('width')) / natural;
assert.ok(Math.abs(scaleOf() - 0.72) < 0.01, 'a wide picture keeps a readable minimum scale: ' + scaleOf());
assert.strictEqual(level.textContent, '72%');
env.one('#graph [data-zoom="fit"]').click();
assert.ok(Math.abs(scaleOf() - (natural / 2 - 2) / natural) < 0.01, 'fit shows the whole width');
env.one('#graph [data-zoom="in"]').click();
const zoomed = scaleOf();
env.one('.gscroll').clientWidth = natural * 3;
env.window.fire('resize');
assert.ok(Math.abs(scaleOf() - zoomed) < 0.001, 'a chosen zoom survives a resize');
const fresh = load({ sizes: [['.gscroll', natural * 3]] });
assert.strictEqual(Number(fresh.one('.flow-svg').getAttribute('width')), natural, 'a roomy panel shows the natural size');
fresh.one('.gscroll').clientWidth = natural * 0.9;
fresh.window.fire('resize');
assert.ok(Math.abs(Number(fresh.one('.flow-svg').getAttribute('width')) / natural - (natural * 0.9 - 2) / natural) < 0.01);
""")

    def test_the_live_client_reports_freshness_reloads_on_a_new_revision_and_pauses_while_printing(self):
        self.scenario(r"""
const file = load({ extra: ['client'] });
assert.ok(/^Snapshot generated: \d{4}-\d{2}-\d{2}/.test(file.one('#plan-freshness').textContent), 'file mode names the snapshot');
const env = load();
const freshness = env.one('#plan-freshness');
const meta = env.document.createElement('meta');
meta.setAttribute('name', 'tackle-live-revision');
meta.setAttribute('content', 'revision-a');
env.document.documentElement.querySelector('head').appendChild(meta);
env.location.protocol = 'http:';
env.location.hostname = '127.0.0.1';
env.location.href = 'http://127.0.0.1:8787/';
let revision = 'revision-a', healthy = true, fetches = 0, reloads = 0, poll = null;
env.location.reload = () => { reloads += 1; };
env.window.fetch = () => { fetches += 1; return Promise.resolve({ ok: healthy, headers: { get: (k) => k === 'X-Tackle-Live' ? (healthy ? '1' : '0') : revision } }); };
env.window.setInterval = (fn) => { poll = fn; };
vm.runInContext(env.scripts.client, env.context);
await settle();
assert.ok(/Live source connected/.test(freshness.textContent));
assert.strictEqual(reloads, 0);
env.root.setAttribute('data-print-scope', 'both');
const before = fetches;
poll();
await settle();
assert.strictEqual(fetches, before, 'no refresh while printing');
env.root.removeAttribute('data-print-scope');
healthy = false;
poll();
await settle();
assert.ok(/Connection lost.*snapshot/.test(freshness.textContent));
healthy = true;
revision = 'revision-b';
poll();
await settle();
assert.strictEqual(reloads, 1);
""")

    def test_a_requirement_selects_and_clears_like_a_task_and_marks_the_tasks_that_cover_it(self):
        self.scenario(r"""
const R = (n) => ['R', String(n).padStart(2, '0')].join('');
const env = load();
const card = env.one('#requirement-' + R(1));
const toggle = card.querySelector('.req-toggle');
toggle.click();
assert.ok(card.classList.contains('selected'));
assert.strictEqual(toggle.getAttribute('aria-pressed'), 'true');
assert.strictEqual(env.root.getAttribute('data-selected-requirement'), R(1));
assert.deepStrictEqual(ids(env, '.flow-svg .node.covering'), [T(1), T(2), T(3), T(4), T(5)]);
assert.deepStrictEqual(env.all('.task.covering').map((c) => c.id).sort(), [1, 2, 3, 4, 5].map((n) => 'task-' + T(n)));
assert.ok(env.one('.flow-svg').classList.contains('tracing'));
assert.ok(!env.one('#clear-trace').hidden);
const inspector = env.one('#flow-inspector .inspector-body');
assert.ok(!inspector.hidden && inspector.textContent.includes(R(1)), 'the inspector names the selected requirement');
toggle.click();
assert.ok(!card.classList.contains('selected'), 'a second selection clears the requirement');
assert.ok(env.one('#flow-inspector .inspector-body').hidden);
assert.strictEqual(toggle.getAttribute('aria-pressed'), 'false');
assert.strictEqual(env.all('.node.covering, .task.covering, .requirement-card.selected').length, 0);
card.querySelector('.req-purpose').click();
assert.ok(card.classList.contains('selected'), 'the card body selects too');
env.one('.flow-svg .node[data-task="' + T(2) + '"]').click();
assert.ok(!card.classList.contains('selected'), 'a task selection replaces the requirement selection');
assert.strictEqual(env.root.getAttribute('data-selected-task'), T(2));
const chip = env.one('#task-' + T(2) + ' a[href="#requirement-' + R(1) + '"]');
chip.click();
assert.ok(card.classList.contains('selected'), 'a requirement link selects the requirement');
assert.strictEqual(env.root.getAttribute('data-selected-task'), null);
assert.strictEqual(env.location.hash, '#requirement-' + R(1));
chip.click();
assert.ok(card.classList.contains('selected'), 'following the link again keeps the selection');
card.key('Escape');
assert.ok(!card.classList.contains('selected'));
assert.strictEqual(env.location.hash, '', 'clearing the requirement clears its anchor');
const anchored = load({ hash: '#requirement-' + R(1) });
assert.ok(anchored.one('#requirement-' + R(1)).classList.contains('selected'), 'an anchor selects the requirement on load');
""")

    def test_pinch_and_ctrl_wheel_zoom_around_the_pointer_and_the_header_stacks_instead_of_clipping(self):
        self.scenario(r"""
const env = load({ sizes: [['.gscroll', 600]] });
const canvas = env.one('.gscroll');
const svg = env.one('.flow-svg');
const natural = Number(load().one('.flow-svg').getAttribute('width'));
const before = Number(svg.getAttribute('width')) / natural;
canvas.scrollLeft = 120;
canvas.scrollTop = 40;
const px = 300, py = 200;
const anchor = [(canvas.scrollLeft + px) / before, (canvas.scrollTop + py) / before];
const event = canvas.dispatch('wheel', { ctrlKey: true, deltaY: -40, clientX: px, clientY: py });
assert.ok(event.defaultPrevented, 'a pinch never zooms the whole page');
const after = Number(svg.getAttribute('width')) / natural;
assert.ok(after > before * 1.3, 'a pinch out zooms in: ' + before + ' -> ' + after);
assert.ok(Math.abs((canvas.scrollLeft + px) / after - anchor[0]) < 1.5 && Math.abs((canvas.scrollTop + py) / after - anchor[1]) < 1.5,
  'the point under the pointer stays in place');
const plain = canvas.dispatch('wheel', { deltaY: 30, clientX: px, clientY: py });
assert.ok(!plain.defaultPrevented, 'a two-finger scroll stays a native pan');
canvas.dispatch('gesturestart', { scale: 1 });
canvas.dispatch('gesturechange', { scale: 0.5, clientX: px, clientY: py });
assert.ok(Number(svg.getAttribute('width')) / natural < after * 0.6, 'a Safari pinch in zooms out');
const header = env.one('.topbar'), nav = env.one('.nav');
nav.scrollWidth = 900;
nav.clientWidth = 500;
env.window.fire('resize');
assert.ok(header.classList.contains('stacked'), 'an index that does not fit takes its own row');
nav.scrollWidth = 400;
env.window.fire('resize');
assert.ok(!header.classList.contains('stacked'), 'an index that fits stays on one row');
""")


if __name__ == '__main__':
    unittest.main()
