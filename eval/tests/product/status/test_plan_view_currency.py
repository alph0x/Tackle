"""The plan view records what it was built from, a read-only check names the inputs that changed since, and the page
lists what waits on the owner.

Guarantee: the shipped recipe writes one sha256 per page input into a JSON meta element, and `--check` with the
build's arguments prints `view current` (exit 0) or `view stale: <inputs>` (exit 1) without writing anything; bad
arguments exit 2. The page's Waiting on you section lists open questions from `questions.md`, tasks Waiting on owner
or Blocked with their Verification cell, and Open board obligations with owner and trigger.
Failure it catches: a digest that misses an input, a check that compares only an overall value or always says
current, a check that writes, and a waiting section that drops or invents items.
Consumer: the coordinator's rebuild rule and the PLAN handoff in the plan-view and PLAN card guides.
The agent's timing of these runs is outside this oracle.
"""
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_plan_view as base  # noqa: E402

REFERENCES = base.TEMPLATE.parent
WORKSPACE_INPUTS = ('task-board.md', 'plan.md', 'decisions.md', 'questions.md', 'history.md', 'resource-usage.md',
                    'AGENTS.md', 'readiness.md', 'map-delta.json', 'view/summary.json', 'summary.json',
                    'view/export-summary.json', 'export-summary.json')
ROLES = ('template', 'plan-view recipe', 'architecture-map recipe', 'map base')


def write_files(workspace, files):
    for name, text in files.items():
        path = workspace / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')


def script_in(root):
    script = Path(root) / 'plan-view-recipe.py'
    if not script.exists():
        script.write_text(base.recipe_source(), encoding='utf-8')
    return script


def call(root, args):
    return subprocess.run([sys.executable, '-I', str(script_in(root))] + [str(a) for a in args],
                          capture_output=True, text=True, timeout=60)


def snapshot(root):
    return {p: p.read_bytes() for p in Path(root).rglob('*') if p.is_file()}


def digest_meta(page):
    found = re.search(r'<meta name="tackle-input-digest" content="([^"]*)">', page)
    return json.loads(html.unescape(found.group(1))) if found else None


def stale_names(stdout):
    line = next((l for l in stdout.splitlines() if l.startswith('view stale: ')), None)
    return None if line is None else [name.strip() for name in line[len('view stale: '):].split(',')]


class Fixture:
    """One workspace three levels below a fake repository root, with its own copy of the template and recipes."""

    def __init__(self, tmp, files=None, template=None):
        self.root = Path(tmp)
        self.repo = self.root / 'repo'
        self.ws = self.repo / 'docs' / 'plans' / 'demo'
        self.page = self.ws / 'plan-view.html'
        write_files(self.ws, files if files is not None else base.workspace_files())
        self.template = template or base.TEMPLATE
        self.default_base = self.repo / '.tackle' / 'map' / 'architecture.json'

    def args(self, extra=()):
        return ['--template', self.template] + list(extra) + [self.ws, self.page]

    def build(self, extra=()):
        result = call(self.root, self.args(extra))
        assert result.returncode == 0, result.stdout + result.stderr
        return self.page.read_text(encoding='utf-8')

    def check(self, extra=()):
        before = snapshot(self.root)
        result = call(self.root, ['--check'] + self.args(extra))
        assert snapshot(self.root) == before, '--check wrote, changed or removed a file'
        return result


def copied_references(tmp):
    """The template beside a recipes/ folder holding both recipes, so a test can edit each one."""
    folder = Path(tmp) / 'skill'
    (folder / 'recipes').mkdir(parents=True)
    shutil.copy(base.TEMPLATE, folder / base.TEMPLATE.name)
    for name in ('plan-view.md', 'architecture-map.md'):
        shutil.copy(REFERENCES / 'recipes' / name, folder / 'recipes' / name)
    return folder / base.TEMPLATE.name


class InputDigestTests(unittest.TestCase):
    def test_a_fresh_build_records_every_input_and_checks_current(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(tmp)
            page = fixture.build()
            meta = digest_meta(page)
            self.assertIsNotNone(meta, 'the page has no input digest meta')
            names = list(meta['inputs'])
            self.assertEqual(names, sorted(names), 'entries are not sorted by name')
            for name in WORKSPACE_INPUTS + ROLES + tuple('tasks/%s.md' % base.task_id(n) for n in (1, 2, 3)):
                self.assertIn(name, meta['inputs'])
            for name in ('questions.md', 'readiness.md', 'map-delta.json', 'view/summary.json', 'summary.json', 'map base'):
                self.assertEqual(meta['inputs'][name], 'absent', name)
            self.assertRegex(meta['inputs']['plan.md'], r'^[0-9a-f]{64}$')
            self.assertRegex(meta['digest'], r'^[0-9a-f]{64}$')
            self.assertEqual((meta['map'], meta['map_scope']), ('default', 'all'))
            head = page.split('<body', 1)[0]
            for local in {str(Path(tmp)), str(Path(tmp).resolve())}:
                self.assertNotIn(local, head, 'the digest meta holds a local path')
            result = fixture.check()
            self.assertEqual((result.returncode, result.stdout.strip()), (0, 'view current'), result.stderr)

    def test_each_changed_workspace_input_is_named_stale_and_restoring_it_is_current(self):
        edits = {name: 'x\n' for name in WORKSPACE_INPUTS}
        edits['task-board.md'] = '| T-04 | Fourth | `tasks/T-04.md` | none | Draft | v |\n'
        edits['tasks/T-02.md'] = 'edited\n'
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(tmp)
            fixture.build()
            for name, extra in edits.items():
                path = fixture.ws / name
                old = path.read_bytes() if path.exists() else None
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((old or b'') + extra.encode('utf-8'))
                result = fixture.check()
                self.assertEqual(result.returncode, 1, (name, result.stdout, result.stderr))
                names = stale_names(result.stdout)
                expected = [name, 'tasks/T-04.md'] if name == 'task-board.md' else [name]
                self.assertEqual(sorted(names or []), sorted(expected), (name, result.stdout))
                if old is None:
                    path.unlink()
                else:
                    path.write_bytes(old)
                result = fixture.check()
                self.assertEqual((result.returncode, result.stdout.strip()), (0, 'view current'), name)

    def test_a_line_ending_rewrite_counts_as_a_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(tmp)
            fixture.build()
            plan = fixture.ws / 'plan.md'
            plan.write_bytes(plan.read_bytes().replace(b'\n', b'\r\n'))
            result = fixture.check()
            self.assertEqual((result.returncode, stale_names(result.stdout)), (1, ['plan.md']))

    def test_the_template_and_each_recipe_beside_it_are_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            template = copied_references(tmp)
            fixture = Fixture(tmp, template=template)
            fixture.build()
            self.assertEqual(fixture.check().returncode, 0)
            for role, path in (('template', template), ('plan-view recipe', template.parent / 'recipes' / 'plan-view.md'),
                               ('architecture-map recipe', template.parent / 'recipes' / 'architecture-map.md')):
                old = path.read_bytes()
                path.write_bytes(old + b'\n')
                result = fixture.check()
                self.assertEqual((result.returncode, stale_names(result.stdout)), (1, [role]), role)
                path.unlink()
                result = fixture.check()
                # A missing template is a usage error, as in the build; a missing recipe is recorded absent.
                expected = (2, None) if role == 'template' else (1, [role])
                self.assertEqual((result.returncode, stale_names(result.stdout)), expected, role + ' removed')
                path.write_bytes(old)
                self.assertEqual(fixture.check().returncode, 0, role)

    def test_a_missing_recipe_beside_the_template_is_recorded_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            template = copied_references(tmp)
            (template.parent / 'recipes' / 'architecture-map.md').unlink()
            fixture = Fixture(tmp, template=template)
            meta = digest_meta(fixture.build())
            self.assertEqual(meta['inputs']['architecture-map recipe'], 'absent')
            self.assertEqual(fixture.check().returncode, 0)

    def test_the_default_map_base_appearing_after_a_build_without_map_is_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(tmp)
            fixture.build()
            fixture.default_base.parent.mkdir(parents=True)
            fixture.default_base.write_text('{}', encoding='utf-8')
            result = fixture.check()
            self.assertEqual((result.returncode, stale_names(result.stdout)), (1, ['map base']))

    def test_an_explicit_map_base_and_the_map_options_are_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(tmp)
            explicit = Path(tmp) / 'elsewhere' / 'architecture.json'
            options = ['--map', explicit, '--map-scope', 'changed']
            meta = digest_meta(fixture.build(options))
            self.assertEqual((meta['map'], meta['map_scope'], meta['inputs']['map base']), ('given', 'changed', 'absent'))
            self.assertEqual(fixture.check(options).returncode, 0)
            explicit.parent.mkdir(parents=True)
            explicit.write_text('{}', encoding='utf-8')
            result = fixture.check(options)
            self.assertEqual((result.returncode, stale_names(result.stdout)), (1, ['map base']))
            explicit.unlink()
            result = fixture.check(['--map', explicit, '--map-scope', 'all'])
            self.assertEqual((result.returncode, stale_names(result.stdout)), (1, ['--map-scope']))
            result = fixture.check(['--map-scope', 'changed'])
            self.assertEqual((result.returncode, stale_names(result.stdout)), (1, ['--map']))

    def test_a_page_built_before_input_digests_is_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(tmp)
            page = fixture.build()
            fixture.page.write_text(re.sub(r'<meta name="tackle-input-digest" content="[^"]*">', '', page), encoding='utf-8')
            result = fixture.check()
            self.assertEqual(result.returncode, 1)
            self.assertTrue(result.stdout.startswith('view stale: '), result.stdout)

    def test_bad_arguments_exit_2_and_write_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(tmp)
            fixture.build()
            for args in (['--check'], ['--check', '--template', fixture.template, fixture.ws],
                         ['--check', fixture.ws, fixture.page],
                         ['--check', '--template', fixture.template, fixture.ws, fixture.ws / 'missing.html'],
                         ['--check', '--template', fixture.template, fixture.ws / 'missing', fixture.page],
                         ['--check', '--template', Path(tmp) / 'missing.md', fixture.ws, fixture.page],
                         ['--check', '--template', fixture.template, '--map-scope', 'some', fixture.ws, fixture.page]):
                before = snapshot(tmp)
                result = call(tmp, args)
                self.assertEqual(result.returncode, 2, (args, result.stdout, result.stderr))
                self.assertEqual(snapshot(tmp), before)

    def test_a_check_against_a_page_outside_the_workspace_leaves_both_folders_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(tmp)
            fixture.page = Path(tmp) / 'out' / 'view.html'
            fixture.page.parent.mkdir()
            fixture.build()
            self.assertEqual(fixture.check().returncode, 0)
            (fixture.ws / 'decisions.md').write_text('changed\n', encoding='utf-8')
            result = fixture.check()
            self.assertEqual((result.returncode, stale_names(result.stdout)), (1, ['decisions.md']))
            self.assertEqual(sorted(p.name for p in fixture.page.parent.iterdir()), ['view.html', 'view.stamp.js'])

    def test_an_escaped_brief_name_survives_the_meta(self):
        rows = base.plain_rows(brief_a='`tasks/a"b.md`')
        files = base.small_files('# Plan — demo\n\n| Criterion | Behavior |\n|---|---|\n| `R01` | one |\n', rows)
        files['tasks/a"b.md'] = '# Task\n\n- **Traces to**: R01\n'
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(tmp, files)
            page = fixture.build()
            self.assertIn('tasks/a"b.md', digest_meta(page)['inputs'])
            self.assertEqual(fixture.check().returncode, 0)


QUESTIONS = (
    '# Open questions\n\nSingle source.\n\n---\n\n'
    '## Q-01 · Pick the route · 🔴 open\n\nWhich route?\n\n**Determines**: the release\nroute for T-03.\n**Decides**: owner.\n\n'
    '## Q-02 · Cache · or not · 🟡 open non-blocking\n\nText.\n\n**Determines**: cache policy.\n\n'
    '## Q-03 · Unknown state · pendiente\n\nText.\n\n**Determines**: nothing yet.\n\n'
    '## Q-04 · Resolved one · 🟢 resolved → D-01\n\n**Determines**: closed-marker-a.\n\n'
    '## Q-05 · Ticked one · ✅ resolved\n\n**Determines**: closed-marker-b.\n\n'
    '## Q-06 · No field · ⚠️ provisional — awaiting user confirmation\n\nText.\n')
OBLIGATIONS = ('\n## Obligations\n\n| Obligation | What | Owner | Trigger | State | Discharge check | Reference |\n'
               '|---|---|---|---|---|---|---|\n| O-01 | Rotate the key | ops-team | before release | Open | key age | n/a |\n'
               '| O-02 | Old duty | someone | never | Discharged | done | D-01 |\n')


def waiting_files(questions=QUESTIONS, obligations=OBLIGATIONS, plan=None):
    files = base.workspace_files()
    files['task-board.md'] = files['task-board.md'].replace(
        '| Draft | v |', '| Waiting on owner | needs the route answer |').replace(
        '| In progress | v |', '| Blocked | blocked by vendor |') + obligations
    if questions is not None:
        files['questions.md'] = questions
    if plan is not None:
        files['plan.md'] = plan
    return files


def waiting_section(page):
    main = re.search(r'<main\b.*?</main>', page, re.S).group(0)
    found = re.search(r'<section class="sec waiting" id="waiting">.*?</section>', main, re.S)
    return found.group(0) if found else None


class WaitingSectionTests(unittest.TestCase):
    def test_open_questions_waiting_tasks_and_open_obligations_are_listed(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = Fixture(tmp, waiting_files()).build()
            section = waiting_section(page)
            self.assertIsNotNone(section, 'no waiting section inside <main>')
            self.assertIn('Waiting on you', section)
            for needle in ('Q-01', 'Pick the route', 'the release route for T-03', 'Q-02', 'Cache · or not', 'cache policy',
                           'Q-03', 'Unknown state', 'Q-06', 'No field', 'T-03', 'needs the route answer', 'T-02',
                           'blocked by vendor', 'O-01', 'Rotate the key', 'ops-team', 'before release'):
                self.assertIn(html.escape(needle, quote=False), section, needle)
            for absent in ('Q-04', 'Q-05', 'closed-marker', 'O-02', 'Old duty', 'Decides', 'T-01'):
                self.assertNotIn(absent, section, absent)
            self.assertIn('href="#waiting"', re.search(r'<nav\b.*?</nav>', page, re.S).group(0))
            reports = re.search(r'<div class="print-reports">.*', page, re.S).group(0)
            self.assertNotIn('id="waiting"', reports)

    def test_nothing_open_shows_one_line(self):
        files = base.workspace_files()
        files['questions.md'] = '# Open questions\n\n## Q-01 · Done · 🟢 resolved → D-01\n'
        with tempfile.TemporaryDirectory() as tmp:
            section = waiting_section(Fixture(tmp, files).build())
            self.assertIsNotNone(section)
            self.assertIn('Nothing waits on you.', section)
            self.assertNotIn('<li', section)

    def test_a_focused_plan_shows_its_open_questions_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            files = {'plan.md': base.lite_plan(), 'questions.md': QUESTIONS}
            section = waiting_section(Fixture(tmp, files).build())
            self.assertIn('Pick the route', section)
            self.assertNotIn('O-01', section)

    def test_a_spanish_plan_gets_spanish_labels(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = Fixture(tmp, waiting_files(plan=base.SPANISH_PLAN + '\n| Criterion | Behavior |\n|---|---|\n| `R01` | one |\n')).build()
            section = waiting_section(page)
            self.assertIn('Esperando por ti', section)
            self.assertIn('Determina', section)
            self.assertNotIn('Waiting on you', section)
            files = waiting_files(questions='# Preguntas\n', obligations='', plan=base.SPANISH_PLAN)
            files['task-board.md'] = base.workspace_files()['task-board.md']
            self.assertIn('Nada espera por ti.', waiting_section(Fixture(Path(tmp) / 'b', files).build()))

    def test_workspace_text_in_the_section_is_escaped(self):
        payloads = base.PAYLOADS
        questions = '## Q-01 · %s · open\n\n**Determines**: %s\n' % (payloads[0], payloads[2])
        obligations = OBLIGATIONS.replace('ops-team', payloads[1])
        with tempfile.TemporaryDirectory() as tmp:
            page = Fixture(tmp, waiting_files(questions=questions, obligations=obligations)).build()
            for payload in payloads:
                self.assertNotIn(payload, page)
            self.assertIn(html.escape(payloads[0], quote=False), waiting_section(page))


if __name__ == '__main__':
    unittest.main()
