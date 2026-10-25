"""Shipped templates and actual compact copy/adoption reach the current native lint contract.

Historical source fixtures remain inputs; the test does not implement a second structural migration."""
import hashlib
import importlib.util
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = (Path(__file__).resolve().parents[4] / 'eval/templates')
sys.path.insert(0, str(ROOT))
from maintaining.install_root import current_root  # noqa: E402
from eval.support.lint import lint_namespace, brief_base, run_lint_row  # noqa: E402

INSTALL = current_root(ROOT)
REF = INSTALL / 'references'
SLUG = 'demo'
NAMESPACE = lint_namespace()

_spec = importlib.util.spec_from_file_location('template_drift_decompose', INSTALL / 'scripts/decompose_check.py')
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
RECIPE = vars(_module)
LEGACY_GLYPHS = ('\U0001F534', '\U0001F7E1', '⏸', '\U0001F7E2', '⚪')


def skill_stamp():
    return re.search(r'^\*\*Tackle (\d+\.\d+\.\d+)\*\*', (INSTALL / 'SKILL.md').read_text(), re.M)[1]


def stale_stamps(texts):
    wanted = skill_stamp()
    return sorted({(name, found) for name, text in texts.items()
                   for found in re.findall(r'Tackle (\d+\.\d+\.\d+)', text) if found != wanted})


def scaffold_names():
    block = re.search(r'```sh\n(ws=docs/plans/<initiative>.*?)\n```', (REF / 'guides/scaffold.md').read_text(), re.S)[1]
    return block, re.search(r'for name in ([^;]+); do', block)[1].split()


def fill(text):
    text = text.replace('{{YYYY-MM-DD}}', '2026-09-24')
    text = re.sub(r'\{\{.*?\}\}', 'x', text, flags=re.S)
    # A filled brief declares full detail and an empty symbol ledger, as a clean adopter of rows 18 and 19.
    text = text.replace('- **Detail**: x\n', '- **Detail**: full\n')
    text = re.sub(r'- \*\*Consumes\*\*: x\n(?:  - .*\n)+', '- **Consumes**: none\n', text)
    return re.sub(r'- \*\*Produces\*\*: x\n(?:  - .*\n)+', '- **Produces**: none\n', text)


def compiled_brief(identity='T-01', clause=None):
    text = brief_base(identity, clause, template=(REF / 'task.tmpl.md').read_text())
    lines = []
    drop_continuation = False
    for line in text.split('\n'):
        if drop_continuation:
            drop_continuation = False
            if line.startswith('  '):
                continue
        if line.startswith('- **Effort**:'):
            line = '- **Effort**: high' + '\n- **Tier reason**: effort raised above the compiled default'
        elif line.startswith('- **Type**:'):
            line = '- **Type**: standard.'
        elif line.startswith('- **Depends on**:'):
            line = '- **Depends on**: none.'
        elif line.startswith(('- **Rounds**:', '- **Metric**:', '- **Threshold**:',
                               '- **Tier**:', '- **Tier reason**:', '- **Escalation**:')):
            drop_continuation = True
            continue
        lines.append(line)
    return fill('\n'.join(lines))


def clause_bytes(contract, cid):
    selected, found = [], False
    for line in contract.splitlines():
        if found and (line.startswith('## ') or line.startswith('<a id=')):
            break
        if not found and line.split()[:2] == ['##', cid]:
            found = True
        if found:
            selected.append(line + '\n')
    return ''.join(selected)


def lint(root):
    source = (REF.parent / 'scripts/lint.py').read_bytes()
    verdicts = {}
    for number in range(1, 20):
        child = run_lint_row(root, number, slug=SLUG, source=source, timeout=60)
        record = dict(child_exit=child.returncode, timeout=False, launch_error=None,
                      signal=(-child.returncode if child.returncode < 0 else None), inputs_stable=True, artifacts_present=True)
        verdicts[number] = (NAMESPACE['lint_verdict'](number, record, child.stdout, child.stderr),
                            child.stdout.decode(errors='replace')[:300], child.stderr.decode(errors='replace')[:300])
    return verdicts


def seal_command():
    after = (REF / 'guides/verify.md').read_text().split('<a id="seal-integrity-command"></a>', 1)[1]
    block = re.search(r'```sh\n(.*?)\n[ ]*```', after, re.S)[1]
    return '\n'.join(line[3:] if line.startswith('   ') else line for line in block.split('\n')).replace('<slug>', SLUG)


def checklist():
    """The 8.3 → 8.4 artifact map, archived with the superseded checklists in maintaining/migrations.md."""
    text = (ROOT / 'maintaining/migrations.md').read_text()
    return text.split('## v8.3 → v8.4 checklist', 1)[1].split('\n## ', 1)[0]


def state_map():
    table = (REF / 'terminology.md').read_text().split('## States and observations', 1)[1].split('\n## ', 1)[0]
    mapping = {}
    for glyph in LEGACY_GLYPHS:
        row = next(l for l in table.splitlines() if l.startswith('| `' + glyph + '`'))
        mapping[glyph] = re.match(r'(Draft|In progress|Complete|Blocked|Skipped)', row.split(' | ')[1])[1]
    return mapping


class TemplateDriftTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='tackle-template-drift-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.ws = self.root / 'docs/plans' / SLUG

    def scaffold(self):
        check, names = scaffold_names()
        self.ws.mkdir(parents=True)
        for name in names:
            shutil.copyfile(REF / name.replace('.md', '.tmpl.md'), self.ws / name)
        (self.ws / 'tasks').mkdir()
        child = subprocess.run(['sh', '-c', check.replace('<initiative>', SLUG)], cwd=self.root, capture_output=True)
        self.assertEqual((child.returncode, child.stdout, child.stderr), (0, b'', b''))
        return names

    def test_scaffold_is_current_and_free_of_leftovers(self):
        names = self.scaffold()
        texts = {name: (self.ws / name).read_text() for name in names}
        self.assertEqual(stale_stamps(texts), [])
        stale = dict(texts, **{'README.md': texts['README.md'].replace(skill_stamp(), '8.1.0')})
        self.assertEqual(stale_stamps(stale), [('README.md', '8.1.0')])
        run = (REF / 'guides/run.md').read_text()
        for flag in re.findall(r'^\*\*([a-z][a-z-]*): (?:on|off)\*\*', texts['AGENTS.md'], re.M):
            self.assertIn(flag, run, 'flag not defined by run.md: ' + flag)
        readme = texts['README.md']
        index = readme.split('## Index', 1)[1].split('\n## ', 1)[0]
        order = readme.split('## Reading order', 1)[1].split('\n## ', 1)[0]
        for name in ('task-board.md', 'resource-usage.md'):
            self.assertIn('| `' + name + '` |', index)
        self.assertTrue(any('task-board.md' in step and 'current' in step for step in order.splitlines()), order)
        extra = {name: (REF / name).read_text() for name in ('task.tmpl.md', 'questions.tmpl.md', 'design-contract.tmpl.md')}
        extra['quality-dimensions.md'] = (REF / 'guides/quality-dimensions.md').read_text()
        for name, text in {**texts, **extra}.items():
            with self.subTest(file=name):
                for leftover in ('MBTX', 'SDK', 'wave plan', '"Deferred"', 'verification-records/results'):
                    self.assertNotIn(leftover, text)
                self.assertIsNone(re.search(r'\| Write scope (auth|a hot|parallelism|persistence|UI|user-visible|error handling|retries)', text))

    def test_history_template_has_no_prefilled_result_or_legacy_glyph(self):
        text = (REF / 'history.tmpl.md').read_text()
        self.assertRegex(text, r'exit: `?\{\{[^}]+\}\}`? · timeout: `?\{\{[^}]+\}\}`? · signal: `?\{\{[^}]+\}\}`?')
        self.assertNotIn('exit: 0', text)
        for glyph in LEGACY_GLYPHS:
            self.assertNotIn(glyph, text)

    def test_compiled_brief_keeps_e2e_first_and_replay_clauses(self):
        brief = ' '.join(compiled_brief().split())
        for clause in ('Prefer E2E through the real consumer',
                       'Never add a unit test after implementing the behavior it covers',
                       'retain a replay artifact containing this command/script, accessible fixtures, expected and observed results',
                       'without overwriting the original raw record'):
            self.assertIn(clause, brief)

    def test_filled_scaffold_passes_every_lint_row(self):
        names = self.scaffold()
        for name in names:
            (self.ws / name).write_text(fill((self.ws / name).read_text()))
        board = (self.ws / 'task-board.md').read_text()
        self.assertIn('Schema: tackle-workspace/5', board)
        header = '| Task | What | Brief | Depends on | Status | Verification |\n|---|---|---|---|---|---|\n'
        self.assertIn(header, board)
        (self.ws / 'task-board.md').write_text(board.replace(header, header + '| T-01 | x | tasks/T-01-x.md | none | Draft | pending |\n'))
        (self.ws / 'tasks/T-01-x.md').write_text(compiled_brief())
        for number, (verdict, out, err) in lint(self.root).items():
            with self.subTest(row=number):
                self.assertEqual(verdict, 'PASS', (out, err))

    def test_template_contract_seals_and_detects_drift(self):
        self.assertIn('through the line before the next `## ` heading or `<a id=` line', (REF / 'task.tmpl.md').read_text())
        self.scaffold()
        contract = fill((REF / 'design-contract.tmpl.md').read_text())
        (self.ws / 'design-contract.md').write_text(contract)
        body = clause_bytes(contract, 'C02')
        self.assertTrue(body.startswith('## C02 · Interface'), body[:80])
        digest = hashlib.sha256(body.encode()).hexdigest()
        (self.ws / 'tasks/T-01-x.md').write_text(compiled_brief(clause=('C02', digest)))
        clean = subprocess.run(['sh', '-c', seal_command()], cwd=self.root, capture_output=True, timeout=60)
        self.assertEqual((clean.returncode, clean.stdout, clean.stderr), (0, b'', b''))
        edited = contract.replace(body, body + 'An unsealed addition.\n')
        (self.ws / 'design-contract.md').write_text(edited)
        drift = subprocess.run(['sh', '-c', seal_command()], cwd=self.root, capture_output=True, timeout=60)
        self.assertEqual(drift.returncode, 1)
        self.assertIn(b'seal drift: C02', drift.stdout)

    def test_checklist_migrates_an_older_workspace_to_a_clean_5_workspace(self):
        path = ROOT / 'eval/tests/product/migration/test_compact_migration.py'
        spec = importlib.util.spec_from_file_location('compact_migration_fixture', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        observer = module.CompactMigrationTests()
        with observer.lab() as lab:
            installed = observer.install(lab)
            project = lab / 'project'
            shutil.copytree(HERE / 'fixtures/legacy-p', project)
            source = project / 'docs/plans/demo'
            before = module.inventory(source)
            job = lab / 'job'
            manifest, plan, boundary = observer.plan(installed, source, job, next_wave=False)
            observer.cli(installed, 'prepare', ['--manifest', manifest, '--job', job], 0)
            module.write_json(job / 'boundary.json', boundary)
            candidate = job / 'candidate-project/docs/plans/demo'
            board = candidate / 'task-board.md'
            self.assertIn('Schema: tackle-workspace/5', board.read_text())
            baselines = []
            for line in board.read_text().split('\n'):
                cells = [cell.strip() for cell in line.split('|')[1:-1]]
                if len(cells) != 6 or not re.fullmatch(r'T-\d+', cells[0]):
                    continue
                if cells[4] not in ('Complete', 'Skipped', 'Unverifiable'):
                    brief = candidate / cells[2]
                    text = brief.read_text()
                    if '- **Tier reason**:' not in text:
                        text = re.sub(r'(- \*\*Effort\*\*: (?!low\n).*\n)',
                                      r'\1- **Tier reason**: kept its Effort through migration\n', text)
                        brief.write_text(text)
                if cells[4] == 'Complete':
                    # The public fixture's closure is known to this operator; migration never infers none.
                    report = candidate / 'reports' / (cells[0] + '-report.md')
                    content = report.read_text()
                    if '**Remains**:' not in content:
                        content += '\n**Remains**: none\n'
                    digest = hashlib.sha256((candidate / cells[2]).read_bytes()).hexdigest()
                    content = content.replace('**Remains**: none', '**Brief sha256**: ' + digest + '\n**Remains**: none')
                    report.write_text(content)
                    history = candidate / 'history.md'
                    history.write_text(history.read_text().rstrip('\n') + '\nBrief sha256 %s: %s\n' % (cells[0], digest))
                    baselines.append((cells[0], digest))
            self.assertGreaterEqual(len(baselines), 1)
            observer.final_receipt(installed, source, job, candidate, plan)
            observer.cli(installed, 'adopt', ['--job', job], 0)
            self.assertEqual(module.inventory(job / 'original-backup'), before)
            self.root, self.ws = project, source
            for task, digest in baselines:
                self.assertEqual((source / 'history.md').read_text().count('Brief sha256 %s: %s' % (task, digest)), 1)
            for number, (verdict, out_text, err) in lint(self.root).items():
                with self.subTest(row=number):
                    self.assertEqual(verdict, 'PASS', (out_text, err))

    def test_agents_file_map_is_aligned_and_complete(self):
        block = (REF / 'AGENTS.tmpl.md').read_text().split('## File map', 1)[1].split('```')[1]
        entries = [l for l in block.splitlines() if '←' in l]
        self.assertEqual(len({l.index('←') for l in entries}), 1, entries)
        names = {re.search(r'[├└]── (\S+)', l)[1] for l in entries}
        self.assertEqual(names, set(scaffold_names()[1]) | {'tasks/'})

    def test_task_consistency_recipe_accepts_t_identities_and_refuses_p(self):
        for identity in ('T-A', 'P-A'):
            with self.subTest(identity=identity):
                task = dict(id=identity, requirements=['RA'], outcome='Preserve parsed output',
                            write_scope=['result.json'], inputs={'spec': 'revision-1'},
                            acceptance_check='python3 check.py', regression_check='python3 regression.py',
                            record='records/check', produces={}, consumes=[],
                            cases=[dict(requirement='RA', input='', expected=[], check='empty-array round trip')],
                            semantic_review='passed', boundary_fixtures='passed')
                prepare = lambda: RECIPE['prepare_tasks'](['RA'], [task], [identity], {},
                                                          dict(contract='c1', source='s1', configuration='cfg1', dependencies='d1',
                                                               selectors=['input.json'], runtime='Python 3'),
                                                          [dict(owner='coordinator', check='consumer round trip', record='records/delivery')])
                if identity.startswith('T-'):
                    self.assertEqual(prepare()['states'][identity], 'Ready to run')
                else:
                    with self.assertRaisesRegex(ValueError, 'identity'):
                        prepare()

    def test_retro_metrics_render_and_print_the_documented_rows(self):
        template = (REF / 'retro.tmpl.md').read_text()
        table = template.split('## Metrics', 1)[1].split('\n## ', 1)[0]
        rows = [l for l in table.splitlines() if l.startswith('| ') and not l.startswith('| Metric') and not l.startswith('|---')]
        self.assertTrue(rows)
        for line in rows:
            with self.subTest(row=line[:30]):
                self.assertEqual(len(re.split(r'(?<!\\)\|', line)), 5)
                for span in re.findall(r'`([^`]*)`', line):
                    self.assertNotIn('|', span, 'a rendered table turns an escaped pipe into a literal one')
        def command(metric):
            return template.split('| ' + metric + ' | `', 1)[1].split('`', 1)[0]
        fixtures = ROOT / 'eval/run/usage/fixtures'
        # The corrected recipe derives Measured/Eligible from the lifecycle table (plus
        # its optional telemetry sidecar) instead of reading the fixture's own already-computed
        # ## Coverage input table back unread. Neither fixture ships a sidecar file, so both now
        # honestly report 0 measured tokens; coverage-partial.md's old golden (1/2 (50%)) merely
        # echoed its own hand-authored answer key, never a value the old recipe actually derived.
        golden = {'coverage-zero.md': ['tokens 0/N (0%)', 'duration 1/2 (50%)'],
                  'coverage-partial.md': ['tokens 0/N (0%)', 'duration 2/2 (100%)']}
        # retro.md's Fixture recipe runs the template's Lifecycle coverage row rather than a copy of it.
        self.assertIn("Run the **Lifecycle coverage** row's command of the [retro template](../retro.tmpl.md)",
                      (REF / 'guides/retro.md').read_text())
        for name, expected in golden.items():
            shutil.copyfile(fixtures / name, self.root / 'resource-usage.md')
            for label, cmd in (('template', command('**Lifecycle coverage**')),):
                with self.subTest(fixture=name, recipe=label):
                    child = subprocess.run(['sh', '-c', cmd], cwd=self.root, capture_output=True, text=True, timeout=30)
                    self.assertEqual((child.returncode, child.stderr), (0, ''))
                    self.assertEqual(child.stdout.splitlines(), expected)
            tokens = subprocess.run(['sh', '-c', command('**Exact-token coverage**')], cwd=self.root, capture_output=True, text=True)
            self.assertEqual(tokens.stdout.splitlines(), expected[:1])
        (self.root / 'AGENTS.md').write_text('Default loop budget: 3 attempts\n')
        (self.root / 'plan.md').write_text('Gate: Full, recorded at intake\n')
        (self.root / 'history.md').write_text('## 2026-09-20 · session 1\nattempt 1: first try failed\nT-01 Complete → In progress\nT-02 Blocked\n'
                                              '## 2026-09-21 · session 2\nT-01 \U0001F7E2 → \U0001F7E1\ngate held\n')
        (self.root / 'task-board.md').write_text('Schema: tackle-workspace/4\n\n| Task | What | Brief | Depends on | Verification | Status |\n'
                                                 '|---|---|---|---|---|---|\n| T-01 | Complete work | tasks/T-01.md | none | reports/T-01-report.md | Complete |\n'
                                                 '| T-02 | Draft work | tasks/T-02.md | T-01 | pending | Draft |\n')
        child = subprocess.run(['sh', '-c', command('Tasks by status')], cwd=self.root, capture_output=True, text=True)
        self.assertEqual(sorted(child.stdout.splitlines()), ['Complete 1', 'Draft 1'])
        expected = {'Attempts over budget': ['attempt 1:'], 'Blocked durations': ['## 2026-09-20', 'T-02 Blocked'],
                    'Reopened tasks': ['T-01 Complete → In progress', 'T-01 \U0001F7E2 → \U0001F7E1'],
                    'Comprehension debt': ['T-01'], 'Gate accuracy': ['gate held', 'Gate: Full']}
        for metric, fragments in expected.items():
            with self.subTest(metric=metric):
                child = subprocess.run(['sh', '-c', command(metric)], cwd=self.root, capture_output=True, text=True, timeout=30)
                self.assertEqual((child.returncode, child.stderr), (0, ''))
                for fragment in fragments:
                    self.assertIn(fragment, child.stdout)
                self.assertNotIn('T-02', child.stdout) if metric == 'Comprehension debt' else None


def load_script(name):
    """Import a script under the install by file path and return its names; `schema` is the one
    module every migration step imports."""
    path = INSTALL / name
    if path.stem == 'schema':
        sys.path.insert(0, str(path.parent))
        import schema
        return vars(schema)
    spec = importlib.util.spec_from_file_location('template_drift_' + path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return vars(module)


if __name__ == '__main__':
    unittest.main()
