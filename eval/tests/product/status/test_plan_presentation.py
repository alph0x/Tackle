"""Actual shipped recipe retains optional narrative and complete canonical detail.

The consumer is the generated static Full/Lite document. These assertions do not
measure native UI interaction or aesthetic acceptance.
"""
import html
import json
import re
import tempfile
import unittest
from html.parser import HTMLParser

from eval.tests.product.status.test_plan_view import decision_id, lite_plan, req_id, run_recipe, task_id, workspace_files


def island(page):
    return json.loads(re.search(r'id="plan-view-data">(.*?)</script>', page, re.S).group(1))


class SectionVisibility(HTMLParser):
    """Semantic reachability permits any source-backed section placement."""
    def __init__(self, page):
        super().__init__()
        self.stack, self.sections = [], {}
        self.feed(page)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id') in ('requirements', 'decisions'):
            self.sections[attrs['id']] = not any(name == 'details' and 'open' not in values
                                                for name, values in self.stack)
        if tag not in ('meta', 'link', 'input', 'img', 'br', 'hr', 'area', 'base', 'col', 'embed', 'param', 'source', 'track', 'wbr'):
            self.stack.append((tag, attrs))

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        for n in range(len(self.stack) - 1, -1, -1):
            if self.stack[n][0] == tag:
                del self.stack[n:]
                break


def narrative():
    return dict(title='Narrative title', kicker='Narrative kicker', objective='Narrative objective',
                outcomes=[dict(title='Outcome %d' % n, text='Explanation %d' % n) for n in range(8)],
                tasks={task_id(1): 'First task purpose', task_id(2): 'Second task purpose', task_id(3): 'Third task purpose'},
                milestones={'M%d' % 1: 'Foundation milestone', 'M%d' % 2: 'Repair milestone', 'M%d' % 3: 'Release milestone', '+': 'Added milestone'},
                now='Current narrative context', next=['Next narrative step'], you=['Owner narrative context'],
                decisions=[dict(date='2026-10-01', text='Curated decision explanation')],
                progress=100, tasks_status={task_id(2): 'Complete'}, dependencies={})


class PlanPresentationTests(unittest.TestCase):
    def render(self, files, name):
        with tempfile.TemporaryDirectory() as tmp:
            result, output = run_recipe(tmp, files, name)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            return output.read_text(encoding='utf-8')

    def test_curated_explanations_reach_static_page_without_changing_board_facts(self):
        files = workspace_files()
        summary = narrative()
        files['view/summary.json'] = json.dumps(summary)
        page = self.render(files, 'curated')
        self.assertEqual(len(re.findall(r'class="outcome-card"', page)), 8)
        for text in [summary['title'], summary['kicker'], summary['objective'], summary['now'], *summary['next'],
                     *summary['you'], *summary['tasks'].values(), *summary['milestones'].values(),
                     summary['decisions'][0]['text']]:
            self.assertIn(text, html.unescape(page))
        data = island(page)
        self.assertEqual({t['id']: t['status'] for t in data['tasks']},
                         {task_id(1): 'Complete', task_id(2): 'In progress', task_id(3): 'Draft'})
        self.assertEqual(next(t for t in data['tasks'] if t['id'] == task_id(3))['deps'], [task_id(1), task_id(2)])
        overview = page.split('id="overview"', 1)[1].split('</section>', 1)[0]
        self.assertIn('Explanation 7', overview)
        self.assertNotIn('<details', overview)
        reports = page.split('id="print-report-plan"', 1)[1]
        self.assertIn('Explanation 7', reports)

    def test_complete_requirement_columns_and_both_decision_id_forms_survive(self):
        files = workspace_files()
        files['plan.md'] += ('\n| Criterion | Required behavior | Observable output/effect | Boundary cases | Valid alternatives |\n'
                             '|---|---|---|---|---|\n| `%s` | Complete behavior | Visible effect | Empty input boundary | Alternative implementation |\n' % req_id(1))
        numeric = 'D%d' % 27
        files['decisions.md'] += '\n## %s — Numeric decision\n\nUnique numeric body with **bold detail**.\n\n### Rationale\n\nNested rationale retained.\n\n## Unrelated section\n\nOutside decision body.\n' % numeric
        page = self.render(files, 'complete')
        for text in ('Complete behavior', 'Visible effect', 'Empty input boundary', 'Alternative implementation',
                     'Unique numeric body', 'Nested rationale retained'):
            self.assertIn(text, html.unescape(page))
        self.assertEqual(island(page)['decisions'], [decision_id(1), decision_id(2), numeric])
        record = page.split('id="decision-record-%s"' % numeric, 1)[1].split('</article>', 1)[0]
        self.assertIn('Unknown', record)
        self.assertIn('Nested rationale retained', record)
        self.assertNotIn('Outside decision body', record)
        self.assertIn('id="requirements"', page)
        self.assertIn('id="decisions"', page)
        self.assertEqual(SectionVisibility(page).sections, {'requirements': True, 'decisions': True})

    def test_optional_summary_absence_preserves_full_and_truthful_lite_views(self):
        full = self.render(workspace_files(), 'without-summary')
        self.assertEqual(len(island(full)['tasks']), 3)
        self.assertIn('id="requirement-%s"' % req_id(1), full)
        self.assertIn('id="decision-record-%s"' % decision_id(1), full)
        lite = self.render({'plan.md': lite_plan()}, 'focused-without-summary')
        self.assertTrue(island(lite)['focused'])
        self.assertEqual(island(lite)['tasks'], [])
        self.assertIn('id="requirement-%s"' % req_id(1), lite)
        self.assertIn('id="requirement-%s"' % req_id(2), lite)
        self.assertNotIn('class="outcome-card"', lite)
        self.assertNotIn('id="task-T-', lite)

    def test_untrusted_summary_is_escaped_and_invalid_optional_shape_has_a_valid_fallback(self):
        files = workspace_files()
        payload = '</script><script>alert("narrative")</script><img src=x onerror=alert(1)>'
        summary = narrative()
        summary['objective'] = payload
        summary['outcomes'][0]['text'] = payload
        summary['tasks'][task_id(1)] = payload
        summary['decisions'][0]['text'] = payload
        files['summary.json'] = json.dumps(summary)
        page = self.render(files, 'escaped')
        self.assertNotIn(payload, page)
        self.assertIn(html.escape(payload, quote=True), page)
        self.assertEqual(len(island(page)['tasks']), 3)
        files['summary.json'] = json.dumps({'outcomes': 'wrong type', 'tasks': [], 'next': None, 'you': 1, 'decisions': [None]})
        fallback = self.render(files, 'invalid-optional')
        self.assertEqual(len(island(fallback)['tasks']), 3)
        self.assertIn('id="requirements"', fallback)
        self.assertNotIn('class="outcome-card"', fallback)


if __name__ == '__main__':
    unittest.main()
