"""Archived adoption obligations retain their native row consumers.

The current release gate checks catalog provenance; historical workspace inputs remain unchanged."""
import hashlib
import importlib.util
import re
import json
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from maintaining.install_root import current_root  # noqa: E402

INSTALL = current_root(ROOT)
REFERENCES = INSTALL / 'references'
MIGRATE = REFERENCES / 'guides/migrate.md'
ARCHIVE = ROOT / 'maintaining/migrations.md'
SPEC = (REFERENCES.parent / 'scripts/lint.py').read_bytes()
FIXTURE = ROOT / 'eval/lint/rows/fixtures/pass-obligations'
SLUG = 'demo'
WS = 'docs/plans/' + SLUG


def lint_recipe():
    """The shipped canonical_rows and lint_verdict, imported from scripts/lint_runner.py."""
    spec = importlib.util.spec_from_file_location('migration_lint_recipe', REFERENCES.parent / 'scripts/lint_runner.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return vars(module)


RECIPE = lint_recipe()
ROWS = RECIPE['canonical_rows'](SPEC, hashlib.sha256(SPEC).hexdigest(), SLUG)
SCRIPTS = REFERENCES.parent / 'scripts/migrate'
MIGRATION_FIXTURES = ROOT / 'eval/migration/fixtures'
MIGRATION_README = ROOT / 'eval/migration/README.md'
TITLE = '## v9.0 → v9.1 checklist'
ANCHOR = '<a id="v90--v91-checklist"></a>'


def checklist(text):
    return text.split(TITLE, 1)[1].split('\n## ', 1)[0].split('\n<a id=', 1)[0]


def one_line(value):
    return ' '.join(value.split())


def load_script(path):
    """Import a migration script by file path and return its names. `schema` is the one module every
    step imports; each step is loaded fresh under its own name."""
    if path.stem == 'schema':
        sys.path.insert(0, str(path.parent))
        import schema
        return vars(schema)
    spec = importlib.util.spec_from_file_location('migration_readme_' + path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return vars(module)


def load_files(directory):
    return {str(p.relative_to(directory)).replace('\\', '/'): p.read_bytes() for p in directory.rglob('*') if p.is_file()}


def lint_files(files):
    """{row: verdict} for a migrated workspace mapping, judged by the shipped rows and verdict."""
    with tempfile.TemporaryDirectory(prefix='tackle-migrated-lint-') as temporary:
        for relative, data in files.items():
            if not relative.startswith('legacy-'):
                target = Path(temporary) / 'docs/plans' / SLUG / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
        verdicts = {}
        for number in sorted(ROWS):
            child = subprocess.run(['sh', '-c', ROWS[number]['command'].decode()], cwd=temporary, capture_output=True, timeout=60)
            record = dict(child_exit=child.returncode, timeout=False, launch_error=None, signal=None,
                          inputs_stable=True, artifacts_present=True)
            verdicts[number] = RECIPE['lint_verdict'](number, record, child.stdout, child.stderr)
        return verdicts


def gate_four():
    loader = runpy.run_path(str(ROOT / 'eval/validation-integrity/acceptance.py'))['canonical_gates']
    return loader((ROOT / 'MAINTAINING.md').read_text(encoding='utf-8'))[3]


class ChecklistTests(unittest.TestCase):
    def setUp(self):
        self.text = ARCHIVE.read_text(encoding='utf-8')

    def test_the_heading_is_exact_unique_and_anchored_between_its_neighbors_in_the_archive(self):
        lines = self.text.splitlines()
        self.assertEqual(lines.count(TITLE), 1)
        at = lines.index(TITLE)
        self.assertEqual(lines[at - 1], ANCHOR)
        self.assertLess(self.text.index('## v9.1.0 → v9.1.1 checklist'), self.text.index(TITLE))
        self.assertLess(self.text.index(TITLE), self.text.index('## v9.0.0 → v9.0.1 checklist'))
        self.assertNotIn(TITLE, MIGRATE.read_text(encoding='utf-8'))

    def test_the_migrate_chain_gate_accepts_a_9_1_0_stamp_only_with_this_exact_heading(self):
        """The historical identity remains mandatory in the current installed catalog gate."""
        command = gate_four()
        expected_heading = TITLE.removeprefix('## ')
        cases = (('original', expected_heading, True),
                 ('equivalent-json', expected_heading, True),
                 ('catalog-identity', 'v9.0.1 → v9.1 checklist', False),
                 ('catalog-identity', 'v9.0 → v9.1  checklist', False),
                 ('current-target', expected_heading, False),
                 ('retained-identity', 'v9.0.1 → v9.1 checklist', False),
                 ('retained-identity', 'v9.0 → v9.1  checklist', False))
        for mutation, heading, wanted in cases:
            with self.subTest(mutation=mutation, heading=heading):
                with tempfile.TemporaryDirectory(prefix='tackle-gate-four-') as temporary:
                    root = Path(temporary)
                    shutil.copytree(INSTALL, root / 'skills/tackle')
                    (root / 'maintaining').mkdir()
                    for name in ('check_migration_catalog.py', 'migrations.md'):
                        shutil.copyfile(ROOT / 'maintaining' / name, root / 'maintaining' / name)
                    target = root / 'skills/tackle/references/guides/migration-catalog.json'
                    catalog = json.loads(target.read_bytes())
                    self.assertEqual(catalog['target_methodology'], '10.2.0')
                    groups = [group for group in catalog['provenance']['groups']
                              if group['source'] == 'H' and group['heading'] == expected_heading]
                    self.assertEqual(len(groups), 1)
                    if mutation == 'catalog-identity':
                        groups[0]['heading'] = heading
                    elif mutation == 'current-target':
                        catalog['target_methodology'] = '9.1.0'
                    elif mutation == 'retained-identity':
                        retained = root / 'maintaining/migrations.md'
                        original = retained.read_text(encoding='utf-8')
                        lines = original.splitlines(keepends=True)
                        matches = [index for index, line in enumerate(lines)
                                   if line.rstrip('\r\n') == TITLE]
                        self.assertEqual(len(matches), 1)
                        index = matches[0]
                        lines[index] = lines[index].replace(TITLE, '## ' + heading, 1)
                        retained.write_text(''.join(lines), encoding='utf-8')
                    if mutation != 'original':
                        target.write_text(json.dumps(catalog, ensure_ascii=False,
                                                     sort_keys=True, indent=2) + '\n', encoding='utf-8')
                    child = subprocess.run(['sh', '-c', command], cwd=root, capture_output=True, timeout=30)
                    if wanted:
                        self.assertEqual((child.returncode, child.stdout, child.stderr), (0, b'', b''))
                    else:
                        self.assertNotEqual(child.returncode, 0)
                        self.assertTrue(child.stdout or child.stderr)

    def test_the_checklist_names_the_artifacts_the_adoption_applies_and_ends_with_the_stamp_bump(self):
        steps = checklist(self.text)
        for phrase in ('rows 1–17', '`**Remains**: none`', 'task-board.tmpl.md', 'Active obligations', 'AGENTS.tmpl.md',
                       'History entry budget', 'Methodology:', '9.1.0'):
            self.assertIn(phrase, steps)
        numbered = re.findall(r'^\d+\. .*(?:\n(?!\d+\. ).*)*', steps, re.M)
        self.assertTrue(numbered)
        self.assertIn('Methodology:', numbered[-1])
        self.assertIn('9.1.0', numbered[-1])

    def test_step_5_says_when_the_archive_applies_and_what_to_do_when_it_does_not(self):
        numbered = re.findall(r'^\d+\. .*(?:\n(?!\d+\. ).*)*', checklist(self.text), re.M)
        step = one_line(numbered[4])
        for phrase in ('over the archive threshold', 'older than the newest five', 'does not apply',
                       '`History entry budget: N`', 'blocks nothing by itself'):
            self.assertIn(phrase, step)
        self.assertLess(step.index('older than the newest five'), step.index('does not apply'))
        self.assertLess(step.index('does not apply'), step.index('`History entry budget: N`'))

    def test_earlier_checklists_keep_their_sixteen_row_counts(self):
        # The archive lists the newest checklist first, so the earlier ones follow this one.
        earlier = self.text.split(TITLE, 1)[1].split('\n## ', 1)[1]
        self.assertIn('Run rows 1–16 and the installed capability/recovery consumer', earlier)
        self.assertIn('(`lint: N/16`)', earlier)
        self.assertNotIn('rows 1–17', earlier)


class AdoptionTests(unittest.TestCase):
    def workspace(self):
        temporary = tempfile.TemporaryDirectory(prefix='tackle-adoption-')
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name) / 'root'
        shutil.copytree(FIXTURE, root)
        return root

    def run_rows(self, root):
        """{row: (verdict, output lines)} for rows 1 through 17 under the system AWK."""
        results = {}
        for number in sorted(ROWS):
            child = subprocess.run(['sh', '-c', ROWS[number]['command'].decode()], cwd=root, capture_output=True, timeout=30)
            record = dict(child_exit=child.returncode, timeout=False, launch_error=None, signal=None,
                          inputs_stable=True, artifacts_present=True)
            results[number] = (RECIPE['lint_verdict'](number, record, child.stdout, child.stderr),
                               child.stdout.decode().splitlines())
        return results

    def nine_zero_one(self):
        root = self.workspace()
        board = (root / WS / 'task-board.md').read_text(encoding='utf-8')
        (root / WS / 'task-board.md').write_text(board.split('<a id="obligations"></a>')[0], encoding='utf-8')
        (root / WS / 'reports/T-A-report.md').write_text('# T-A report\n\nReviewer: demo.\n', encoding='utf-8')
        history = (root / WS / 'history.md').read_text(encoding='utf-8')
        (root / WS / 'history.md').write_text(history.replace('- Active obligations: O-01\n', '- Active obligations: none outside the board.\n'),
                                              encoding='utf-8')
        return root

    def test_a_9_0_1_workspace_fails_only_row_17_and_the_checklist_steps_make_it_pass_every_row(self):
        root = self.nine_zero_one()
        before = self.run_rows(root)
        self.assertEqual(sorted(before), list(range(1, 20)))
        self.assertEqual({number for number, (verdict, _) in before.items() if verdict != 'PASS'}, {17}, before)
        self.assertEqual(len(before[17][1]), 1, before[17])
        self.assertIn('T-A', before[17][1][0])
        steps = checklist(ARCHIVE.read_text(encoding='utf-8'))

        # Step: add the receipt to each Complete task's report.
        self.assertIn('**Remains**: none', steps)
        report = root / WS / 'reports/T-A-report.md'
        report.write_text(report.read_text(encoding='utf-8') + '\n**Remains**: none\n', encoding='utf-8')
        # Step: copy the obligations section of the board template below the task table.
        template = (REFERENCES / 'task-board.tmpl.md').read_text(encoding='utf-8')
        self.assertIn('<a id="obligations"></a>', template)
        section = '<a id="obligations"></a>' + template.split('<a id="obligations"></a>', 1)[1]
        board = root / WS / 'task-board.md'
        board.write_text(board.read_text(encoding='utf-8').rstrip('\n') + '\n\n' + section, encoding='utf-8')
        # Step: copy the default policy line of the AGENTS template.
        policy = next(line for line in (REFERENCES / 'AGENTS.tmpl.md').read_text(encoding='utf-8').splitlines()
                      if 'History maintenance policy' in line)
        agents = root / WS / 'AGENTS.md'
        agents.write_text(agents.read_text(encoding='utf-8') + '\n' + policy + '\n', encoding='utf-8')

        after = self.run_rows(root)
        self.assertEqual({number: verdict for number, (verdict, _) in after.items()}, {number: 'PASS' for number in range(1, 20)}, after)
        self.assertTrue(all(lines == [] for _, lines in after.values()), after)

    def test_an_open_obligation_is_carried_into_the_table_the_snapshot_and_the_receipt(self):
        root = self.nine_zero_one()
        older = (root / WS / 'history.md').read_text(encoding='utf-8')
        # Step 3 addresses Complete tasks only: a Draft task's report keeps no receipt and row 17 does not ask for one.
        (root / WS / 'reports/T-B-report.md').write_text('# T-B report\n\nNot started.\n', encoding='utf-8')
        # Step 3: the Complete task left an obligation behind, so its receipt names it.
        report = root / WS / 'reports/T-A-report.md'
        report.write_text(report.read_text(encoding='utf-8') + '\n**Remains**: O-01\n', encoding='utf-8')
        # Step 4: the obligations section of the board template, with the obligation recorded Open.
        template = (REFERENCES / 'task-board.tmpl.md').read_text(encoding='utf-8')
        section = '<a id="obligations"></a>' + template.split('<a id="obligations"></a>', 1)[1]
        delimiter = '|---|---|---|---|---|---|---|\n'
        self.assertEqual(section.count(delimiter), 1)
        row = '| O-01 | Rotate the sample credential | owner | before the release | Open | the rotation record exists | |\n'
        board = root / WS / 'task-board.md'
        board.write_text(board.read_text(encoding='utf-8').rstrip('\n') + '\n\n' + section.replace(delimiter, delimiter + row),
                         encoding='utf-8')
        # Step 5: the default policy line.
        policy = next(line for line in (REFERENCES / 'AGENTS.tmpl.md').read_text(encoding='utf-8').splitlines()
                      if 'History maintenance policy' in line)
        agents = root / WS / 'AGENTS.md'
        agents.write_text(agents.read_text(encoding='utf-8') + '\n' + policy + '\n', encoding='utf-8')

        # Until a new entry's snapshot names the obligation, row 17 reports it and nothing else fails.
        waiting = self.run_rows(root)
        self.assertEqual({number for number, (verdict, _) in waiting.items() if verdict != 'PASS'}, {17}, waiting)
        self.assertIn('O-01', ' '.join(waiting[17][1]))
        # Step 4: append an entry whose State snapshot names it; the older snapshot is never edited.
        history = root / WS / 'history.md'
        history.write_text(older + '\n## 2026-09-25 · session 3\n\n- Adopted the checklist; O-01 stays open.\n\n'
                           '### State snapshot (record current state when appending; never edit an older snapshot)\n'
                           '- Task state: T-A Complete; T-B Draft.\n- Active obligations: O-01\n', encoding='utf-8')
        after = self.run_rows(root)
        self.assertEqual({number: verdict for number, (verdict, _) in after.items()}, {number: 'PASS' for number in range(1, 20)}, after)
        self.assertTrue(all(lines == [] for _, lines in after.values()), after)
        self.assertTrue(history.read_text(encoding='utf-8').startswith(older))


class MigrationFixtureTargetTests(unittest.TestCase):
    def test_the_readme_states_what_the_two_named_lint_integration_targets_pass(self):
        schema = load_script(SCRIPTS / 'schema.py')
        steps = [load_script(SCRIPTS / name) for name in ('step_pre3_to_3.py', 'step_3_to_4.py', 'step_4_to_5.py')]
        context = {'date': '2026-09-25', 'run_id': 'migration-readme-check', 'methodology': 'Tackle 9.0.0'}
        chained = load_files(MIGRATION_FIXTURES / 'pre3-to-3/before')
        for step in steps:
            chained, _ = step['transform'](chained, context)
        single, _ = steps[2]['transform'](load_files(MIGRATION_FIXTURES / '4-to-5/before'), context)
        readme = MIGRATION_README.read_text(encoding='utf-8').splitlines()
        for name, files in (('pre3-to-3', chained), ('4-to-5', single)):
            self.assertEqual(schema['schema_of'](files), '5', name)
            verdicts = lint_files(files)
            passing = [number for number, verdict in verdicts.items() if verdict == 'PASS']
            failing = sorted(set(verdicts) - set(passing))
            row = next(line for line in readme if line.startswith('| `fixtures/%s/before/`' % name))
            stated = re.search(r'passes (\d+) of the (\d+) rows; rows ([\d, and]+) report', row)
            self.assertIsNotNone(stated, row)
            self.assertEqual((int(stated[1]), int(stated[2])), (len(passing), len(verdicts)), name)
            self.assertEqual(sorted(int(number) for number in re.findall(r'\d+', stated[3])), failing, name)


if __name__ == '__main__':
    unittest.main()
