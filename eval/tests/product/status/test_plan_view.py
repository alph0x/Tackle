"""The shipped plan-view recipe writes a faithful, escaped, offline view of a workspace, or refuses.

The test extracts the recipe from `references/recipes/plan-view.md`, runs it as a child process with the
shipped template, and checks the page and its data island against the workspace it built. Ids are built
at run time. The interactive behavior (click, trace, filter) is outside this oracle.
"""
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
RECIPE = REPO / 'skills/tackle/references/recipes/plan-view.md'
TEMPLATE = REPO / 'skills/tackle/references/plan-view.template.md'
STATES = ('Draft, Ready to run, In progress, Checking, Complete, Blocked, Interrupted, Skipped, '
          'Unverifiable, Waiting on owner')
PAYLOADS = ('<img src=x onerror=alert(1)>', '"><svg onload=alert(2)>', '</script><script>alert(3)</script>',
            '<b onmouseover=alert(4)>four</b>', 'R&D')
ATTR = 'x" onmouseover="alert(5)'


def task_id(n):
    return 'T-%02d' % n


def req_id(n):
    return 'R%02d' % n


def decision_id(n):
    return 'D-%02d' % n


def recipe_source():
    parts = RECIPE.read_text(encoding='utf-8').split('```python\n')
    assert len(parts) == 2, 'the recipe must hold exactly one fenced python block'
    return parts[1].split('\n```')[0] + '\n'


def usage_row(run, event, scope, role):
    return '| %s | %s | %s | %s | h | standard | m | n/a | 2026-10-03T10:00:00Z | o | n/a | n/a | n/a | s |\n' % (
        run, event, scope, role)


def workspace_files(deps_of_last=None):
    first_task, second_task, third_task = task_id(1), task_id(2), task_id(3)
    req_a, req_b, req_c, req_d = (req_id(n) for n in (1, 2, 3, 4))
    dec_a, dec_b = decision_id(1), decision_id(2)
    deps_of_last = deps_of_last if deps_of_last is not None else '%s, %s' % (first_task, second_task)
    rows = [(first_task, 'First ' + ATTR, 'none', 'Complete'),
            (second_task, 'Second ' + PAYLOADS[0], first_task, 'In progress'),
            (third_task, 'Third', deps_of_last, 'Draft')]
    board = ('# Task board\n\nStates: %s.\n\n| Task | What | Brief | Depends on | Status | Verification |\n|---|---|---|---|---|---|\n'
             % STATES + ''.join('| %s | %s | `tasks/%s.md` | %s | %s | v |\n' % (i, w, i, d, s) for i, w, d, s in rows))
    plan = ('# Action plan — demo\n\n## 2. Expected result\n\nThe plan says what ships and how each need is checked.\n\n'
            '| Criterion | Required behavior |\n|---|---|\n| `%s` | one |\n| `%s` | %s |\n| `%s` | three |\n| `%s` | four |\n'
            % (req_a, req_b, PAYLOADS[3], req_c, req_d))
    briefs = {first_task: req_a, second_task: req_b, third_task: '%s–%s' % (req_b, req_c)}
    files = {'task-board.md': board, 'plan.md': plan,
             'decisions.md': '# Decisions\n\n## %s · Scope · ✅ active · 2026-10-01\n\nText.\n\n## %s · Route %s · ✅ active · 2026-10-02\n\nText.\n'
                             % (dec_a, dec_b, PAYLOADS[1]),
             'history.md': '# History\n\n### State snapshot\n- old-marker\n\n## later\n\n### State snapshot\n- newest-marker %s %s\n'
                           % (PAYLOADS[2], PAYLOADS[4]),
             'AGENTS.md': '# AGENTS\n\n**Methodology: Tackle 9.1.0**\n',
             'resource-usage.md': '# Usage\n\n| Run ID | Event | Task | Role | Harness | Tier | Model | Effort | At | Outcome | Attempts | Rework | Verification | Source |\n'
                                  '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n'
                                  + usage_row('run/a', 'start', first_task, 'executor') + usage_row('run/a', 'finish', first_task, 'executor')
                                  + usage_row('run/b', 'start', second_task, 'executor')}
    for task, traces in briefs.items():
        files['tasks/%s.md' % task] = '# Task\n\n- **Traces to**: %s\n- **Goal**: demo.\n' % traces
    return files


def run_recipe(tmp, files, case):
    workspace = Path(tmp) / case
    for name, text in files.items():
        path = workspace / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
    script = Path(tmp) / (case + '-recipe.py')
    script.write_text(recipe_source(), encoding='utf-8')
    out = workspace / 'plan-view.html'
    result = subprocess.run([sys.executable, '-I', str(script), '--template', str(TEMPLATE), str(workspace), str(out)],
                            capture_output=True, text=True, timeout=60)
    return result, out


class PlanViewTests(unittest.TestCase):
    def test_the_shipped_recipe_writes_a_faithful_view_of_a_fixture_workspace(self):
        first_task, second_task, third_task = task_id(1), task_id(2), task_id(3)
        with tempfile.TemporaryDirectory() as tmp:
            result, out = run_recipe(tmp, workspace_files(), 'coordinated')
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            page = out.read_text(encoding='utf-8')
            island = re.search(r'<script type="application/json" id="plan-view-data">(.*?)</script>', page, re.S).group(1)
            self.assertIsNone(re.search(r'[<>&]', island), 'the island holds a raw <, > or &')
            data = json.loads(island)
            self.assertEqual(data['schema'], 'tackle-plan-view/1')
            self.assertIs(data['focused'], False)
            self.assertEqual({t['id']: (t['status'], sorted(t['deps'])) for t in data['tasks']},
                             {first_task: ('Complete', []), second_task: ('In progress', [first_task]), third_task: ('Draft', [first_task, second_task])})
            self.assertEqual({k: sorted(v) for k, v in data['requirements'].items()},
                             {req_id(1): [first_task], req_id(2): [second_task, third_task], req_id(3): [third_task], req_id(4): []})
            self.assertEqual(sorted(data['decisions']), [decision_id(1), decision_id(2)])
            self.assertIn('newest-marker', data['snapshot'])
            self.assertNotIn('old-marker', data['snapshot'])
            self.assertEqual([(w['scope'], w['role']) for w in data['working']], [(second_task, 'executor')])
            for payload in PAYLOADS + (ATTR,):
                self.assertNotIn(payload, page)
            self.assertNotIn('onmouseover="', page)
            static = re.sub(r'<script\b.*?</script>', '', page, flags=re.S)
            for task, up, down in ((first_task, '', '%s %s' % (second_task, third_task)), (second_task, first_task, third_task), (third_task, '%s %s' % (first_task, second_task), '')):
                node = re.search(r'<[a-z]+\b[^>]*\bid="task-%s"[^>]*>' % task, static).group(0)
                self.assertIn('data-upstream="%s"' % up, node)
                self.assertIn('data-downstream="%s"' % down, node)
                self.assertEqual('data-live="true"' in node, task == second_task)
            for status in ('Complete', 'In progress', 'Draft'):
                self.assertIn('data-filter="%s"' % status, static)
            for needle in ('<details', decision_id(1), decision_id(2), 'newest-marker', 'id="working-now"',
                           'prefers-color-scheme: dark', '<html lang="en"'):
                self.assertIn(needle, static)
            footer = re.search(r'<footer\b.*?</footer>', static, re.S).group(0)
            self.assertIn('Made with Tackle 9.1.0', footer)
            self.assertIn('href="https://github.com/alph0x/Tackle"', footer)
            self.assertIn('target="_blank"', footer)
            self.assertRegex(footer, r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}')
            self.assertNotRegex(page, r'<script\b[^>]*\bsrc=')

    def test_the_shipped_recipe_refuses_inconsistent_sources_and_writes_nothing(self):
        unknown = task_id(9)
        with tempfile.TemporaryDirectory() as tmp:
            result, out = run_recipe(tmp, workspace_files(deps_of_last=unknown), 'unknown-dependency')
            self.assertEqual(result.returncode, 1)
            self.assertTrue(any(line.startswith('refused: ') and unknown in line for line in result.stdout.splitlines()))
            self.assertFalse(out.exists())
            files = workspace_files()
            files['task-board.md'] = files['task-board.md'].replace('| Draft |', '| Done |')
            result, out = run_recipe(tmp, files, 'bad-status')
            self.assertEqual(result.returncode, 1)
            self.assertIn('Done', result.stdout)
            self.assertFalse(out.exists())


BOARD_HEAD = ('# Board\n\nStates: %s.\n\n| Task | What | Brief | Depends on | Status | Verification |\n|---|---|---|---|---|---|\n' % STATES)


def small_files(plan, rows, extra_board=''):
    first, second = task_id(1), task_id(2)
    files = {'plan.md': plan, 'task-board.md': BOARD_HEAD + ''.join(rows) + extra_board}
    for task in (first, second):
        files['tasks/%s.md' % task] = '# Task\n\n- **Traces to**: %s\n' % req_id(1)
    return files


def plain_rows(title_a='a', brief_a=None):
    first, second = task_id(1), task_id(2)
    brief_a = brief_a or '`tasks/%s.md`' % first
    return ['| %s | %s | %s | none | Draft | v |\n' % (first, title_a, brief_a),
            '| %s | b | `tasks/%s.md` | %s | Draft | v |\n' % (second, second, first)]


def lite_plan():
    a, b = req_id(1), req_id(2)
    return ('Gate: Lite\n# Fix the parser\n\n- Purpose / requirements: %s the parser accepts quoted commas; %s it rejects a bare quote.\n'
            '- Cases → checks: %s → `pytest -k quoted`; %s → `pytest -k bare`.\n- Validation: pytest tests/test_parser.py\n- State: Ready\n' % (a, b, a, b))


def page_of(tmp, files, case):
    result, out = run_recipe(tmp, files, case)
    return result, (out.read_text(encoding='utf-8') if out.exists() else '')


class PlanViewFindingsTests(unittest.TestCase):
    def test_a_focused_plan_in_the_lite_template_shape_shows_its_requirements_and_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, page = page_of(tmp, {'plan.md': lite_plan(), 'history.md': '# History\n'}, 'lite')
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            data = json.loads(re.search(r'id="plan-view-data">(.*?)</script>', page, re.S).group(1))
            self.assertIs(data['focused'], True)
            self.assertEqual(sorted(data['requirements']), [req_id(1), req_id(2)])
            self.assertIn('<title>Fix the parser</title>', page)
            self.assertNotIn('Gate: Lite', re.sub(r'<script\b.*?</script>', '', page, flags=re.S))
            self.assertIn('pytest -k quoted', page)
            self.assertIn('the parser accepts quoted commas', page)
            result, page = page_of(tmp, {'plan.md': 'Gate: Lite\n# Empty\n\n- Purpose / requirements: nothing named\n'}, 'lite-empty')
            self.assertEqual(result.returncode, 1)
            self.assertTrue(any('Focused' in line for line in result.stdout.splitlines() if line.startswith('refused: ')))

    def test_the_page_language_follows_positive_evidence_and_defaults_to_english(self):
        plans = {
            'fr': ('# Plan — Réécriture\n\nLe plan décrit les étapes. Chaque tâche a une vérification. Le système est prêt après la révision.\n', 'en'),
            'pt': ('# Plano — Migração\n\nO plano descreve as etapas da migração. Cada tarefa tem uma verificação. A configuração está pronta após a revisão.\n', 'en'),
            'de': ('# Plan — Umbau\n\nDer Plan beschreibt die Schritte. Jede Aufgabe hat eine Prüfung. Das System ist nach der Prüfung bereit.\n', 'en'),
            'es': ('# Plan — Migración\n\nEl plan describe los pasos de la migración. Cada tarea tiene una verificación. La configuración queda lista después de la revisión.\n', 'es'),
            'en': ('# Plan — Migration\n\nThe plan describes the steps of the migration. Each task has a check.\n', 'en')}
        with tempfile.TemporaryDirectory() as tmp:
            for code, (plan, expected) in plans.items():
                result, page = page_of(tmp, small_files(plan, plain_rows()), 'lang-' + code)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('<html lang="%s"' % expected, page, code)

    def test_only_the_task_table_is_read_as_tasks_and_cells_keep_escaped_pipes(self):
        plan = '# Plan — demo\n\n| Criterion | Behavior |\n|---|---|\n| `%s` | one |\n' % req_id(1)
        notes = '\n## Notes\n\n| Task | Note |\n|---|---|\n| %s | waits for review |\n' % task_id(1)
        with tempfile.TemporaryDirectory() as tmp:
            result, page = page_of(tmp, small_files(plan, plain_rows('parse a \\| b'), notes), 'second-table')
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('parse a | b', page)
            result, page = page_of(tmp, small_files(plan, plain_rows(brief_a='[brief](tasks/%s.md)' % task_id(1))), 'link-brief')
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            result, page = page_of(tmp, small_files(plan, plain_rows(brief_a='`../outside.md`')), 'outside-brief')
            self.assertEqual(result.returncode, 1)
            self.assertIn('outside the workspace', result.stdout)


if __name__ == '__main__':
    unittest.main()
