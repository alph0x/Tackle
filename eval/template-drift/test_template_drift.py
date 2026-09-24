"""A workspace scaffolded, compiled and migrated from the shipped templates and guides is current and lint-clean.

Every case derives its input from the shipped documents (templates, scaffold.md, migrate.md,
terminology.md, verify.md) and judges lint rows through full-checks.md's canonical recipes.
"""
import hashlib
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
REF = ROOT / 'references'
SLUG = 'demo'
NAMESPACE = {'__name__': 'template_drift_test'}
for _block in re.findall(r'```python\n(.*?)\n```', (REF / 'guides/full-checks.md').read_text(), re.S):
    if 'def canonical_rows' in _block:
        exec(_block, NAMESPACE)
RECIPE = {'__name__': 'template_drift_recipe'}
exec((REF / 'guides/decompose-and-lint.md').read_text().split('```python\n')[1].split('\n```')[0], RECIPE)
LEGACY_GLYPHS = ('\U0001F534', '\U0001F7E1', '⏸', '\U0001F7E2', '⚪')


def skill_stamp():
    return re.search(r'^\*\*Tackle (\d+\.\d+\.\d+)\*\*', (ROOT / 'SKILL.md').read_text(), re.M)[1]


def stale_stamps(texts):
    wanted = skill_stamp()
    return sorted({(name, found) for name, text in texts.items()
                   for found in re.findall(r'Tackle (\d+\.\d+\.\d+)', text) if found != wanted})


def scaffold_names():
    block = re.search(r'```sh\n(ws=docs/plans/<initiative>.*?)\n```', (REF / 'guides/scaffold.md').read_text(), re.S)[1]
    return block, re.search(r'for name in ([^;]+); do', block)[1].split()


def fill(text):
    text = text.replace('{{YYYY-MM-DD}}', '2026-09-24')
    return re.sub(r'\{\{.*?\}\}', 'x', text, flags=re.S)


def compiled_brief(identity='T-01', clause=None):
    text = (REF / 'task.tmpl.md').read_text().replace('T-0N', identity).replace('t-0n', identity.lower())
    if clause:
        cid, digest = clause
        text = (text.replace('{{clause id}}', cid).replace('{{revision}}', 'rev 1 (D-01)')
                .replace('{{hash of the exact clause bytes}}', digest))
    else:
        text = re.sub(r'- \*\*\{\{clause id\}\}.*?\}\}\.\n', '', text, count=1, flags=re.S)
    lines = []
    for line in text.split('\n'):
        if line.startswith('- **Effort**:'):
            line = '- **Effort**: high'
        elif line.startswith('- **Type**:'):
            line = '- **Type**: standard.'
        elif line.startswith('- **Depends on**:'):
            line = '- **Depends on**: none.'
        elif line.startswith(('- **Rounds**:', '- **Metric**:', '- **Threshold**:')):
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
    source = (REF / 'guides/lint-spec.md').read_bytes()
    rows = NAMESPACE['canonical_rows'](source, hashlib.sha256(source).hexdigest(), SLUG)
    verdicts = {}
    for number in range(1, 17):
        child = subprocess.run(['sh', '-c', rows[number]['command'].decode()], cwd=root, capture_output=True, timeout=60)
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
    text = (REF / 'guides/migrate.md').read_text()
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

    def test_checklist_migrates_a_legacy_workspace_to_a_clean_v4_workspace(self):
        shutil.copytree(HERE / 'fixtures/legacy-p', self.root, dirs_exist_ok=True)
        pairs = re.findall(r'`([^`]+)` → `([^`]+)`', checklist())
        self.assertTrue(pairs, 'the checklist names no old → new artifact map')
        for old, new in pairs:
            if (self.ws / old.rstrip('/')).exists():
                (self.ws / old.rstrip('/')).rename(self.ws / new.rstrip('/'))
        states = state_map()
        for path in sorted(self.ws.rglob('*')):
            if path.is_file() and re.search(r'P-\d+', path.name):
                path = path.rename(path.with_name(re.sub(r'P-(\d+)', r'T-\1', path.name)))
            if path.is_file() and path.suffix == '.md':
                text = path.read_text()
                for old, new in pairs:
                    text = text.replace(old, new)
                text = re.sub(r'P-(\d+)', r'T-\1', text)
                path.write_text(text)
        board = self.ws / 'task-board.md'
        lines = board.read_text().split('\n')
        out = []
        for line in lines:
            cells = line.split(' | ')
            if line.startswith('| Point |') or line.startswith('| Task |'):
                line = ' | '.join(cells[:-1] + ['Verification']) + ' |'
            elif re.match(r'^\| T-\d+ \|', line):
                state = states[cells[4].strip()]
                ref = 'reports/' + cells[0][2:].strip() + '-report.md' if state in ('Complete', 'Blocked') else 'pending'
                line = ' | '.join(cells[:4] + [state, ref]) + ' |'
            out.append(line)
        text = '\n'.join(out)
        self.assertIn('Schema: tackle-workspace/4', checklist())
        board.write_text(re.sub(r'\n\n\|', '\n\nSchema: tackle-workspace/4\n\n|', text, count=1))
        for number, (verdict, out_text, err) in lint(self.root).items():
            with self.subTest(row=number):
                self.assertEqual(verdict, 'PASS', (out_text, err))

    def test_agents_file_map_is_aligned_and_complete(self):
        block = (REF / 'AGENTS.tmpl.md').read_text().split('## File map', 1)[1].split('```')[1]
        entries = [l for l in block.splitlines() if '←' in l]
        self.assertEqual(len({l.index('←') for l in entries}), 1, entries)
        names = {re.search(r'[├└]── (\S+)', l)[1] for l in entries}
        self.assertEqual(names, set(scaffold_names()[1]) | {'tasks/'})

    def test_task_consistency_recipe_accepts_t_and_p_identities(self):
        for identity in ('T-01', 'P-01'):
            with self.subTest(identity=identity):
                task = dict(id=identity, requirements=['R01'], outcome='Preserve parsed output',
                            write_scope=['result.json'], inputs={'spec': 'revision-1'},
                            acceptance_check='python3 check.py', regression_check='python3 regression.py',
                            record='records/check', produces={}, consumes=[],
                            cases=[dict(requirement='R01', input='', expected=[], check='empty-array round trip')],
                            semantic_review='passed', boundary_fixtures='passed')
                result = RECIPE['prepare_tasks'](['R01'], [task], [identity], {},
                                                 dict(contract='c1', source='s1', configuration='cfg1', dependencies='d1',
                                                      selectors=['input.json'], runtime='Python 3'),
                                                 [dict(owner='coordinator', check='consumer round trip', record='records/delivery')])
                self.assertEqual(result['states'][identity], 'Ready to run')

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
        fixtures = ROOT / 'eval/fixtures/usage-observability'
        golden = {'coverage-zero.md': ['tokens 0/N (0%)', 'duration 1/2 (50%)'],
                  'coverage-partial.md': ['tokens 1/2 (50%)', 'duration 2/2 (100%)']}
        guide_recipe = re.search(r'Run `(.*?)` from a fixture workspace', (REF / 'guides/retro.md').read_text())[1]
        for name, expected in golden.items():
            shutil.copyfile(fixtures / name, self.root / 'resource-usage.md')
            for label, cmd in (('template', command('**Lifecycle coverage**')), ('guide', guide_recipe)):
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


if __name__ == '__main__':
    unittest.main()
