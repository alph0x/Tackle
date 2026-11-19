"""Selection boundaries using the existing discovery fixture and native children."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

import test_discovery as discovery

ROOT, runner = discovery.ROOT, discovery.runner


class SelectionTests(unittest.TestCase):
    def setUp(self):
        discovery.DiscoveryTests.setUp(self)
        other = self.root / 'eval/other'
        other.mkdir()
        (other / 'test_other.py').write_text(self.test.read_text())
        self.manifest['suites'].append({'path': 'eval/other', 'files': ['test_other.py'], 'tests': 1})
        self.mapping = {
            'version': 1, 'families': ['eval/example', 'eval/other'],
            'rules': [{'patterns': ['src/producer.py'], 'families': ['eval/example', 'eval/other'],
                       'exclude': [], 'reason': 'producer and consumer'}],
            'global_patterns': ['eval/run_suites.py'], 'ignored_patterns': ['docs/plans/**'],
            'test_source_regressions': ['eval/example']}
        self.save_map()
        producer = self.root / 'src/producer.py'
        producer.parent.mkdir(parents=True, exist_ok=True)
        producer.write_text('# Fixture producer\n')
        (self.root / 'eval/run_suites.py').touch(exist_ok=True)
        subprocess.run(['git', 'init', '-q'], cwd=self.root, check=True)
        subprocess.run(['git', '-c', 'core.excludesFile=/dev/null', 'add', '-f', '--', '.'],
                       cwd=self.root, check=True)

    def save_map(self):
        (self.root / 'eval/check-selection.json').write_text(json.dumps(self.mapping))

    def test_selected_native_result_is_explicitly_partial(self):
        result = runner.run(self.root, self.manifest, self.root / 'output', changed=['eval/example/test_example.py'])
        self.assertTrue(result['passed'])
        self.assertFalse(result['complete'])
        self.assertEqual(result['registered_tests'], 2)
        self.assertEqual(result['tests'], 1)
        self.assertEqual([s['path'] for s in result['suites']], ['eval/example'])
        self.assertIn('test_real', (self.root / 'output' / result['suites'][0]['stderr']).read_text())

    def test_all_phases_and_unknown_paths_keep_full_registry(self):
        for changed, phase in [(None, 'development'), (['unknown.file'], 'development'),
                               (['eval/example/test_example.py'], 'integration'),
                               (['eval/example/test_example.py'], 'release')]:
            with self.subTest(changed=changed, phase=phase):
                plan = runner.plan(self.root, self.manifest, changed=changed, phase=phase)
                self.assertTrue(plan['complete'])
                self.assertEqual(plan['planned_tests'], 2)

    def test_dry_run_and_empty_slice_never_claim_execution(self):
        marker = self.root / 'child-ran'
        self.test.write_text(f'from pathlib import Path\nPath({str(marker)!r}).touch()\n' + self.test.read_text())
        for i, (changed, dry_run) in enumerate([(['eval/example/test_example.py'], True), ([], False)]):
            with self.subTest(changed=changed):
                result = runner.run(self.root, self.manifest, self.root / f'output-{i}', changed=changed, dry_run=dry_run)
                self.assertIsNone(result['passed'])
                self.assertEqual(result['tests'], 0)
                self.assertEqual(result['suites'], [])
                self.assertFalse(marker.exists())

    def test_partial_selection_validates_unselected_inventory(self):
        (self.root / 'eval/other/test_unregistered.py').write_text('')
        with self.assertRaisesRegex(ValueError, 'inventory mismatch'):
            runner.plan(self.root, self.manifest, changed=['eval/example/test_example.py'])

    def test_bad_paths_and_stale_map_are_rejected(self):
        for path in ('../outside', '/outside', 'eval\\example', 'bad\npath'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                runner.plan(self.root, self.manifest, changed=[path])
        self.mapping['families'].pop()
        self.save_map()
        with self.assertRaisesRegex(ValueError, 'families'):
            runner.plan(self.root, self.manifest, changed=['eval/example/test_example.py'])

    def test_known_cross_family_consumer_is_selected(self):
        plan = runner.plan(self.root, self.manifest, changed=['src/producer.py'])
        self.assertEqual(plan['selected'], ['eval/example', 'eval/other'])
        self.mapping['rules'][0]['families'].append('eval/missing')
        self.save_map()
        with self.assertRaisesRegex(ValueError, 'unregistered'):
            runner.plan(self.root, self.manifest, changed=['src/producer.py'])

    def test_selected_child_failure_propagates(self):
        self.test.write_text(self.test.read_text().replace('2 + 2, 4', '2 + 2, 5'))
        result = runner.run(self.root, self.manifest, self.root / 'output', changed=['eval/example/test_example.py'])
        self.assertFalse(result['passed'])
        self.assertNotEqual(result['suites'][0]['exit'], 0)

    def test_native_admission_of_sources_and_live_selection_rules(self):
        marker = self.root / 'admission-children-ran'
        children = [
            ('example', self.test),
            ('other', self.root / 'eval/other/test_other.py'),
        ]
        for name, child in children:
            original = child.read_text()
            child.write_text(
                'from pathlib import Path\n'
                f'with Path({str(marker)!r}).open("a") as marker:\n'
                f'    marker.write({name + chr(10)!r})\n'
                + original
            )
        subprocess.run(
            ['git', '-c', 'core.excludesFile=/dev/null', 'add', '-f', '--',
             'eval/example/test_example.py', 'eval/other/test_other.py'],
            cwd=self.root, check=True,
        )
        (self.root / 'empty-source').mkdir()
        (self.root / 'untracked-source.py').write_text('# Untracked fixture input\n')

        cases = [
            ('file', 'src/producer.py', None, None, 'src/producer.py', None),
            ('directory', 'src', None, None, 'src/producer.py', None),
            ('shared', 'src/producer.py', None, None, 'src/producer.py', None),
            ('missing', 'missing-source.py', None, None, 'src/producer.py', 'source'),
            ('empty', 'empty-source', None, None, 'src/producer.py', 'source'),
            ('untracked', 'untracked-source.py', None, None, 'src/producer.py', 'source'),
            ('dead-rule', 'src/producer.py', 'src/never-matches.py', None,
             'src/producer.py', 'rule'),
            ('excluded-rule', 'src/producer.py', 'src/producer.py', 'src/producer.py',
             'src/producer.py', 'rule'),
            ('ignored', 'src/producer.py', None, None, 'docs/plans/unmatched.md', None),
        ]
        for name, source, pattern, excluded, changed, failure in cases:
            with self.subTest(case=name):
                if marker.exists():
                    marker.unlink()
                manifest = json.loads(json.dumps(self.manifest))
                manifest['suites'][0]['source'] = source
                if name == 'shared':
                    manifest['suites'][1]['source'] = source
                mapping = json.loads(json.dumps(self.mapping))
                if pattern is not None:
                    mapping['rules'][0]['patterns'] = [pattern]
                if excluded is not None:
                    mapping['rules'][0]['exclude'] = [excluded]
                (self.root / 'eval/check-selection.json').write_text(json.dumps(mapping))
                manifest_path = self.root / f'admission-{name}.json'
                manifest_path.write_text(json.dumps(manifest))
                output = self.root / f'admission-output-{name}'
                completed = subprocess.run(
                    [sys.executable, '-I', '-B', str(ROOT / 'eval/run_suites.py'),
                     '--root', str(self.root), '--manifest', str(manifest_path),
                     '--output', str(output), '--changed', changed],
                    cwd=self.root, capture_output=True, text=True,
                )
                result = json.loads((output / 'results.json').read_text())
                if failure is not None:
                    self.assertEqual(completed.returncode, 2, completed.stderr)
                    self.assertFalse(result['passed'])
                    self.assertEqual(result['tests'], 0)
                    self.assertEqual(result['exit'], 2)
                    details = completed.stdout + completed.stderr + result['error']
                    if failure == 'source':
                        self.assertIn('source', details.lower())
                        self.assertIn(source, details)
                    else:
                        self.assertRegex(details.lower(), r'rule|pattern')
                        self.assertIn(pattern, details)
                    self.assertFalse(marker.exists())
                elif name == 'ignored':
                    self.assertEqual(completed.returncode, 0, completed.stderr)
                    self.assertIsNone(result['passed'])
                    self.assertEqual(result['tests'], 0)
                    self.assertEqual(result['suites'], [])
                    self.assertFalse(marker.exists())
                else:
                    self.assertEqual(completed.returncode, 0, completed.stderr)
                    self.assertTrue(result['passed'])
                    self.assertEqual(result['tests'], 2)
                    self.assertEqual(
                        {suite['path'] for suite in result['suites']},
                        {'eval/example', 'eval/other'},
                    )
                    self.assertCountEqual(marker.read_text().splitlines(), ['example', 'other'])

    def test_real_map_retains_reviewed_consumers(self):
        manifest = json.loads((ROOT / 'eval/suite-manifest.json').read_text())
        cases = {
            'eval/protocol-v2/check.py': ['eval/tests/tooling/protocol-v2', 'eval/tests/tooling/behavior/harness',
                'eval/tests/tooling/behavior/judges/planning', 'eval/tests/tooling/behavior/judges/resume',
                'eval/tests/tooling/records', 'eval/tests/product/install/inventory',
                'eval/tests/historical/verdicts/cost-and-fall-rate',
                'eval/tests/historical/verdicts/resume-comparison',
                'eval/tests/historical/verdicts/escalation-and-completeness',
                'eval/tests/historical/verdicts/no-regression'],
            'eval/support/lint.py': ['eval/tests/product/lint/rows', 'eval/tests/product/lint/task-contracts',
                'eval/tests/product/lint/task-identity', 'eval/tests/tooling/maintaining/suite-integrity',
                'eval/tests/product/run/execution', 'eval/tests/product/templates',
                'eval/tests/tooling/validation-integrity', 'eval/tests/product/run/record-tool'],
            'skills/tackle/references/task.tmpl.md': ['eval/tests/product/lint/task-identity',
                'eval/tests/product/lint/rows', 'eval/tests/product/templates', 'eval/tests/tooling/rules',
                'eval/tests/product/install/inventory', 'eval/tests/tooling/install/reading-budget',
                'eval/tests/product/run/record-tool']}
        for path, expected in cases.items():
            with self.subTest(path=path):
                plan = runner.plan(ROOT, manifest, changed=[path])
                self.assertEqual(set(plan['selected']), set(expected))
                self.assertEqual(plan['planned_tests'], sum(s['tests'] for s in manifest['suites']
                    if s['path'] in plan['selected']))
