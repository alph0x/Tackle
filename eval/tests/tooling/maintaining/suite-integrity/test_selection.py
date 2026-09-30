"""Selection boundaries using the existing discovery fixture and native children."""
import json
from pathlib import Path
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

    def test_real_map_retains_reviewed_consumers(self):
        manifest = json.loads((ROOT / 'eval/suite-manifest.json').read_text())
        families = {s['source']: s['path'] for s in manifest['suites']}
        cases = {
            'eval/protocol-v2/check.py': ['eval/protocol-v2', 'eval/behavior/harness',
                'eval/behavior/judges/planning', 'eval/behavior/judges/resume', 'eval/records',
                'eval/install/inventory', 'eval/cohorts/2026-09-candidate', 'eval/cohorts/2026-09-resume',
                'eval/cohorts/2026-09-second-candidate', 'eval/cohorts/2026-09-third-candidate'],
            'eval/support/lint.py': ['eval/lint/rows', 'eval/lint/task-contracts', 'eval/lint/task-identity',
                'eval/maintaining/suite-integrity', 'eval/run/execution', 'eval/templates', 'eval/validation-integrity'],
            'skills/tackle/references/task.tmpl.md': ['eval/lint/task-identity', 'eval/lint/rows',
                'eval/templates', 'eval/rules', 'eval/install/inventory', 'eval/install/reading-budget']}
        for path, expected in cases.items():
            with self.subTest(path=path):
                plan = runner.plan(ROOT, manifest, changed=[path])
                self.assertEqual(set(plan['selected']), {families[f] for f in expected})
                self.assertEqual(plan['planned_tests'], sum(s['tests'] for s in manifest['suites']
                    if s['path'] in plan['selected']))
