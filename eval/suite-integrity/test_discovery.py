"""Exercise discovery and child outcomes using disposable real test suites."""
import importlib.util
import json
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('suite_runner', ROOT / 'eval/run_suites.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.directory = self.root / 'eval/example'
        self.directory.mkdir(parents=True)
        self.test = self.directory / 'test_example.py'
        self.test.write_text('import unittest\nclass Example(unittest.TestCase):\n    def test_real(self):\n        self.assertEqual(2 + 2, 4)\n')
        self.manifest = {'version': 1, 'excluded_directories': ['eval/scenarios', 'eval/example/fixtures'], 'suites': [
            {'path': 'eval/example', 'files': ['test_example.py'], 'tests': 1}]}

    def execute(self):
        return runner.run(self.root, self.manifest, self.root / 'output')

    def test_real_nonempty_suite_passes_and_retains_streams(self):
        result = self.execute()
        self.assertTrue(result['passed'])
        self.assertEqual(result['tests'], 1)
        record = result['suites'][0]
        self.assertEqual(record['exit'], 0)
        self.assertIn('test_real', (self.root / 'output' / record['stderr']).read_text())
        self.assertIn('python', result)

    def test_planted_regression_is_not_green(self):
        self.test.write_text(self.test.read_text().replace('2 + 2, 4', '2 + 2, 5'))
        self.assertFalse(self.execute()['passed'])

    def test_zero_discovered_tests_is_not_green(self):
        self.test.write_text('"""No tests."""\n')
        result = self.execute()
        self.assertFalse(result['passed'])
        self.assertEqual(result['suites'][0]['tests'], 0)

    def test_unintended_method_subset_is_not_green(self):
        self.manifest['suites'][0]['tests'] = 2
        self.assertFalse(self.execute()['passed'])

    def test_missing_registered_file_rejects(self):
        self.test.unlink()
        with self.assertRaises(ValueError):
            self.execute()

    def test_unregistered_file_rejects(self):
        (self.directory / 'test_new.py').write_text('')
        with self.assertRaises(ValueError):
            self.execute()

    def test_unregistered_family_rejects(self):
        other = self.root / 'eval/new_family'
        other.mkdir()
        (other / 'test_new.py').write_text('')
        with self.assertRaises(ValueError):
            self.execute()

    def test_missing_family_rejects(self):
        self.manifest['suites'][0]['path'] = 'eval/absent'
        with self.assertRaises(ValueError):
            self.execute()

    def test_explicit_synthetic_fixture_exclusion(self):
        fixtures = self.directory / 'fixtures'
        fixtures.mkdir()
        (fixtures / 'test_deliberately_broken.py').write_text('raise AssertionError()')
        self.assertTrue(self.execute()['passed'])

    def test_path_traversal_and_duplicate_registry_reject(self):
        self.manifest['suites'].append(dict(self.manifest['suites'][0]))
        with self.assertRaises(ValueError):
            self.execute()
        self.manifest['suites'] = [{'path': '../outside', 'files': ['test_example.py'], 'tests': 1}]
        with self.assertRaises(ValueError):
            self.execute()

    def test_registry_itself_cannot_exclude_a_real_suite(self):
        self.manifest['excluded_directories'].append('eval/example')
        with self.assertRaises(ValueError):
            self.execute()

    def test_import_error_fails(self):
        self.test.write_text('raise ImportError("planted")\n')
        self.assertFalse(self.execute()['passed'])

    def test_skipped_required_test_is_not_green(self):
        self.test.write_text(self.test.read_text().replace('    def test_real', '    @unittest.skip("planted omission")\n    def test_real'))
        self.assertFalse(self.execute()['passed'])

    def test_cli_retains_discovery_rejection(self):
        self.test.unlink()
        manifest = self.root / 'manifest.json'
        manifest.write_text(json.dumps(self.manifest))
        output = self.root / 'output'
        child = subprocess.run([sys.executable, str(ROOT / 'eval/run_suites.py'),
                                '--root', str(self.root), '--manifest', str(manifest),
                                '--output', str(output)], capture_output=True)
        self.assertEqual(child.returncode, 2)
        self.assertFalse(json.loads((output / 'results.json').read_text())['passed'])
        self.assertEqual((output / 'discovery.stderr').read_bytes(), child.stderr)


if __name__ == '__main__':
    unittest.main()
