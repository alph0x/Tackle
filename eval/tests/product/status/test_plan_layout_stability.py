"""No action on the plan view moves its controls: action messages and transient controls stay out of the control rows.

The DOM stub (plan_view_dom.js) has no layout, so this suite is a static guard plus behavior checks. The guard
reads the stylesheet of a page the shipped script builds: every action status (`role="status"`) and every control
an action shows or adds inside the flex rows of a diagram's tools is positioned out of flow, and the selected
title-strip cell does not move. An empty status region is never display:none or visibility:hidden, so a
screen reader that watches it announces the text the action writes into it. A mutation that puts the Mermaid status back into the row fails the guard. The
behavior checks run the page's own controller in the stub: the download leaves no link in the row, a zoom keeps
the canvas box, a filter keeps the task list's height until All. Real-browser boxes are measured by the plan's
own layout check in headless Chrome, not here.
"""
import re
import unittest

from plan_view_dom import run_scenario
from test_plan_mermaid import board_files, page_for

ROW_CONTAINERS = ('mermaid-tools', 'canvas-tools')


def stylesheet(page):
    return re.search(r'<style>(.*?)</style>', page, re.S).group(1)


def declarations(css, selector):
    """Every declaration block whose selector list names the selector exactly (any media), joined."""
    found = []
    for match in re.finditer(r'([^{}]+)\{([^{}]*)\}', css):
        selectors = [part.strip() for part in match.group(1).split(',')]
        if selector in selectors:
            found.append(match.group(2))
    return ';'.join(found)


def out_of_flow(css, selector):
    return bool(re.search(r'(^|;)\s*position:\s*(absolute|fixed)', declarations(css, selector)))


def row_statuses(page):
    """The class of each status element the page places inside a diagram's control row, with its container."""
    found = []
    for container in ROW_CONTAINERS:
        for row in re.finditer(r'<div class="%s"[^>]*>(.*?)</div>' % container, page, re.S):
            found += [(container, klass) for klass in re.findall(r'<p class="([\w-]+)" role="status"', row.group(1))]
    return found


def reflow_problems(page):
    """The ways an action can reflow a control row, judged from the stylesheet; empty when none."""
    css, problems = stylesheet(page), []
    statuses = row_statuses(page)
    if not statuses:
        problems.append('no status element found inside a control row')
    for container, klass in statuses:
        if not out_of_flow(css, '.' + klass):
            problems.append('.%s sits in the flow of .%s' % (klass, container))
        if not re.search(r'position:\s*relative', declarations(css, '.' + container)):
            problems.append('.%s does not anchor its out-of-flow status' % container)
    if not out_of_flow(css, '.mermaid-text'):
        problems.append('the copy fallback .mermaid-text joins the control row')
    if 'id="clear-trace"' in page and not out_of_flow(css, '#clear-trace'):
        problems.append('#clear-trace joins the canvas tools when a trace shows it')
    if re.search(r'transform', declarations(css, '.tb-cell.on')):
        problems.append('the selected title-strip cell moves')
    return problems


def hidden_empty_statuses(page):
    """Each status class in a control row whose rules (plain or :empty) hide the live region with display:none or
    visibility:hidden. The static-copy notice is a separate, deliberately hidden notice outside the control rows."""
    css, found = stylesheet(page), []
    for klass in dict.fromkeys(klass for _, klass in row_statuses(page)):
        rules = declarations(css, '.' + klass) + ';' + declarations(css, '.%s:empty' % klass)
        if re.search(r'display:\s*none|visibility:\s*hidden', rules):
            found.append('.' + klass)
    return found


class LayoutStabilityGuardTests(unittest.TestCase):
    page = None

    @classmethod
    def setUpClass(cls):
        cls.page = page_for(board_files(), 'layout-guard')

    def test_no_action_status_or_transient_control_can_reflow_its_control_row(self):
        self.assertIn(('mermaid-tools', 'mermaid-status'), row_statuses(self.page))
        self.assertEqual(reflow_problems(self.page), [])

    def test_the_mermaid_status_stays_in_its_group_for_the_controller(self):
        group = re.search(r'<div class="mermaid-tools"[^>]*>(.*?)</div>', self.page, re.S).group(1)
        self.assertTrue(group.endswith('<p class="mermaid-status" role="status"></p>'))

    def test_the_guard_fails_when_the_status_returns_to_the_row(self):
        css = stylesheet(self.page)
        rule = re.search(r'\.mermaid-status\{[^}]*\}', css).group(0)
        self.assertIn('position:absolute;', rule)
        mutated = self.page.replace(rule, rule.replace('position:absolute;', ''), 1)
        self.assertIn('.mermaid-status sits in the flow of .mermaid-tools', reflow_problems(mutated))
        lifted = self.page.replace('.tb-cell:hover{transform:translateY(-3px)}', '.tb-cell:hover,.tb-cell.on{transform:translateY(-3px)}', 1)
        self.assertNotEqual(lifted, self.page)
        self.assertIn('the selected title-strip cell moves', reflow_problems(lifted))

    def test_an_empty_status_region_stays_rendered_for_assistive_technology(self):
        css = stylesheet(self.page)
        self.assertEqual(hidden_empty_statuses(self.page), [])
        self.assertTrue(any(klass == 'mermaid-status' for _, klass in row_statuses(self.page)))
        for hiding in ('display:none', 'visibility:hidden'):
            rule = '.mermaid-status:empty{padding:0}'
            self.assertIn(rule, css)
            mutated = self.page.replace(rule, '.mermaid-status:empty{%s}' % hiding, 1)
            self.assertEqual(hidden_empty_statuses(mutated), ['.mermaid-status'], hiding)

    def test_the_inspector_has_reserved_room_on_wide_screens(self):
        css = stylesheet(self.page)
        self.assertRegex(css, r'@media \(min-width:761px\)\{\.inspector\{height:[\d.]+rem;overflow-y:auto\}\}')


class LayoutStabilityBehaviorTests(unittest.TestCase):
    page = None

    @classmethod
    def setUpClass(cls):
        cls.page = page_for(board_files(), 'layout-behavior')

    def scenario(self, code):
        result = run_scenario(self.page, code)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, 'OK', result.stderr)

    def test_the_download_leaves_no_link_in_the_control_row(self):
        self.scenario(r"""
const env = load();
const anchors = [];
const make = env.document.createElement;
env.document.createElement = (tag) => { const el = make(tag); if (tag === 'a') { anchors.push(el); } return el; };
env.window.Blob = function (parts) { this.parts = parts; };
env.window.URL = { createObjectURL: () => 'blob:x', revokeObjectURL() {} };
const button = env.one('[data-mermaid-download="plan-view-mermaid-tasks"]');
const group = button.parentNode;
const before = group.childNodes.length;
button.click();
await settle();
assert.strictEqual(anchors.length, 1, 'the download made its link');
assert.strictEqual(anchors[0].parentNode, null, 'the link left the row');
assert.strictEqual(group.childNodes.length, before);
""")

    def test_a_zoom_keeps_the_canvas_box(self):
        self.scenario(r"""
const env = load();
const canvas = env.one('.gscroll');
canvas.clientWidth = 900;
canvas.clientHeight = 480;
assert.strictEqual(canvas.style.height || '', '', 'the canvas is unlocked before any zoom');
env.one('[data-zoom="in"]').click();
await settle();
assert.strictEqual(canvas.style.height, '480px', 'the first zoom holds the canvas height');
canvas.clientHeight = 700;
env.one('[data-zoom="fit"]').click();
await settle();
assert.strictEqual(canvas.style.height, '480px', 'later zooms keep the held height');
""")

    def test_a_filter_keeps_the_task_list_height_until_all(self):
        self.scenario(r"""
const env = load();
const list = env.one('.tasks');
list.clientHeight = 900;
env.one('[data-filter="Draft"]').click();
await settle();
assert.strictEqual(list.style.minHeight, '900px', 'the filtered list keeps its height');
list.clientHeight = 300;
env.one('[data-filter="Complete"]').click();
await settle();
assert.strictEqual(list.style.minHeight, '900px', 'another filter keeps the first height');
env.one('[data-filter="all"]').click();
await settle();
assert.strictEqual(list.style.minHeight, '', 'All releases the list');
""")


if __name__ == '__main__':
    unittest.main()
