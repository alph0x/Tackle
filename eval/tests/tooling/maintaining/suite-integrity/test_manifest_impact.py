"""Manifest impact selection through the real runner and native child suites."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

import test_discovery as discovery

ROOT, runner = discovery.ROOT, discovery.runner


class ManifestImpactTests(unittest.TestCase):
    def setUp(self):
        discovery.DiscoveryTests.setUp(self)
        self.root = Path(self.temporary.name)
        self.fixture_number = 0
        self.invocation_number = 0

    def fixture(self, *, broken_config=True, failing_control=False):
        self.fixture_number += 1
        self.case_root = self.root / f'case-{self.fixture_number}'
        self.case_root.mkdir()
        suites = {
            'eval/family_a': {
                'test_a.py': "import unittest\nfrom pathlib import Path\nclass A(unittest.TestCase):\n def test_config(self): self.assertEqual('stable', Path('eval/shared/a.json').read_text().strip())\n",
                'test_a_extra.py': "import unittest\nclass AExtra(unittest.TestCase):\n def test_extra(self): self.assertEqual(2 + 2, 4)\n"},
            'eval/family_b': {
                'loader.py': "import json\nfrom pathlib import Path\ndef load(): return json.loads(Path('eval/shared/data.json').read_text()), json.loads(Path('eval/shared/config.json').read_text())\n",
                'adapter.py': "def expected(data, config): return data['actual'] == config['expected']\n",
                'test_b.py': "import unittest\nfrom loader import load\nfrom adapter import expected\nclass B(unittest.TestCase):\n def test_indirect_config_consumer(self): self.assertTrue(expected(*load()))\n"},
            'eval/family_c': {
                'test_c.py': "import unittest\nfrom pathlib import Path\nclass C(unittest.TestCase):\n def test_control(self):\n  Path('control-executed').touch()\n  self.assertEqual(2 + 2, 5)\n" if failing_control else "import unittest\nfrom pathlib import Path\nclass C(unittest.TestCase):\n def test_control(self):\n  Path('control-executed').touch()\n  self.assertEqual(2 + 2, 4)\n"},
            'eval/family_g': {
                'test_guard.py': "import unittest\nclass G(unittest.TestCase):\n def test_guard(self): self.assertTrue(True)\n"},
        }
        for directory, files in suites.items():
            path = self.case_root / directory
            path.mkdir(parents=True)
            for filename, source in files.items():
                (path / filename).write_text(source)
        shared = self.case_root / 'eval/shared'
        shared.mkdir(parents=True)
        (shared / 'a.json').write_text('stable\n')
        (shared / 'data.json').write_text('{"actual": "ok"}\n')
        (shared / 'config.json').write_text(json.dumps({'expected': 'wrong' if broken_config else 'ok'}) + '\n')
        manifest = {'version': 1, 'excluded_directories': ['eval/scenarios', 'eval/scratch', 'eval/runs'],
                    'suites': [
                        {'path': 'eval/family_a', 'files': ['test_a.py', 'test_a_extra.py'], 'tests': 2, 'source': 'eval/a', 'category': 'tooling', 'purpose': 'direct A'},
                        {'path': 'eval/family_b', 'files': ['test_b.py'], 'tests': 1, 'source': 'eval/b', 'category': 'tooling', 'purpose': 'indirect B'},
                        {'path': 'eval/family_c', 'files': ['test_c.py'], 'tests': 1, 'source': 'eval/c', 'category': 'tooling', 'purpose': 'control C'},
                        {'path': 'eval/family_g', 'files': ['test_guard.py'], 'tests': 1, 'source': 'eval/g', 'category': 'tooling', 'purpose': 'discovery G'}]}
        (self.case_root / 'eval/suite-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        mapping = {'version': 1, 'families': [suite['path'] for suite in manifest['suites']],
                   'rules': [{'patterns': ['eval/shared/config.json'], 'families': ['eval/family_a', 'eval/family_b'], 'exclude': [], 'reason': 'shared configuration consumers'},
                             {'patterns': ['eval/shared/data.json', 'eval/family_b/loader.py', 'eval/family_b/adapter.py'], 'families': ['eval/family_b'], 'exclude': [], 'reason': 'indirect data and loader consumers'}],
                   'global_patterns': ['eval/suite-manifest.json', 'eval/run_suites.py'],
                   'ignored_patterns': ['docs/plans/**'], 'test_source_regressions': ['eval/family_g']}
        (self.case_root / 'eval/check-selection.json').write_text(json.dumps(mapping, indent=2) + '\n')
        baseline = json.loads(json.dumps(manifest))
        baseline['suites'][0]['files'] = ['test_a.py']
        baseline['suites'][0]['tests'] = 1
        (self.case_root / 'baseline.json').write_text(json.dumps(baseline, indent=2) + '\n')
        return manifest, baseline

    def invoke(self, changed, *, phase='development', baseline=True, dry_run=False, digest_override=None,
               default_full=False, output_name='run'):
        digest = digest_override or hashlib.sha256((self.case_root / 'baseline.json').read_bytes()).hexdigest()
        output = self.case_root / output_name
        argv = [sys.executable, str(ROOT / 'eval/run_suites.py'), '--root', str(self.case_root),
                '--manifest', str(self.case_root / 'eval/suite-manifest.json')]
        if baseline:
            argv += ['--manifest-baseline', str(self.case_root / 'baseline.json'),
                     '--manifest-baseline-sha256', digest]
        if not default_full:
            for path in changed:
                argv += ['--changed', path]
        if phase != 'development':
            argv += ['--phase', phase]
        if dry_run:
            argv.append('--dry-run')
        argv += ['--output', str(output)]
        child = subprocess.run(argv, cwd=ROOT, capture_output=True)
        output.mkdir(parents=True, exist_ok=True)
        (output / 'cli-stdout.txt').write_bytes(child.stdout)
        (output / 'cli-stderr.txt').write_bytes(child.stderr)
        (output / 'command.json').write_text(json.dumps({'argv': argv, 'cwd': str(ROOT),
                                  'exit_code': child.returncode}, indent=2) + '\n')
        report_path = output / 'results.json'
        report = json.loads(report_path.read_text()) if report_path.exists() else None
        record_root = os.environ.get('TACKLE_T06_RECORD_DIR')
        if record_root:
            self.invocation_number += 1
            method = self.id().rsplit('.', 1)[-1]
            archive = Path(record_root) / 'fixtures' / method / f'cli-{self.invocation_number:03d}'
            archive.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(output, archive)
        return child, report, output

    def validate_fixture(self, *, invalid=False):
        child, report, _ = self.invoke([], baseline=False, dry_run=True, default_full=True,
                                       output_name='fixture-discovery')
        if invalid:
            self.assertEqual(child.returncode, 2, child.stderr.decode(errors='replace'))
            self.assertIsNotNone(report)
            self.assertFalse(report['passed'])
        else:
            self.assertEqual(child.returncode, 0, child.stderr.decode(errors='replace'))
            self.assertIsNotNone(report)
            self.assertIsNone(report['passed'])
            self.assertEqual(report['tests'], 0)

    def test_manifest_delta_cli_preserves_indirect_consumers_and_valid_isolation(self):
        for broken, expected_exit, expected_b_passed in [(True, 1, False), (False, 0, True)]:
            with self.subTest(broken_config=broken):
                self.fixture(broken_config=broken, failing_control=True)
                self.validate_fixture()
                child, result, output = self.invoke(['eval/suite-manifest.json', 'eval/family_a/test_a_extra.py', 'eval/shared/config.json'])
                self.assertEqual(child.returncode, expected_exit, child.stderr.decode(errors='replace'))
                self.assertIsNotNone(result)
                self.assertEqual(result['selection']['selected'], ['eval/family_a', 'eval/family_b', 'eval/family_g'])
                self.assertEqual(result['registered_tests'], 5)
                self.assertEqual(result['tests'], 4)
                self.assertFalse(result['complete'])
                self.assertEqual(result['passed'], expected_b_passed)
                self.assertFalse((self.case_root / 'control-executed').exists())
                records = {item['path']: item for item in result['suites']}
                self.assertTrue(records['eval/family_a']['passed'])
                self.assertTrue(records['eval/family_g']['passed'])
                self.assertEqual(records['eval/family_b']['passed'], not broken)
                if broken:
                    self.assertNotEqual(records['eval/family_b']['exit'], 0)
                    self.assertTrue((output / records['eval/family_b']['stderr']).is_file())

    def test_manifest_delta_cli_keeps_discovery_and_global_fallbacks(self):
        def run_case(name, edit=None, *, changed=None, phase='development', baseline=True, dry=False,
                     code=None, selected=None, tests=None, complete=None, passed='unchecked', invalid=False):
            with self.subTest(case=name):
                self.fixture(broken_config=False)
                manifest = json.loads((self.case_root / 'eval/suite-manifest.json').read_text())
                if edit:
                    edit(manifest)
                    (self.case_root / 'eval/suite-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
                self.validate_fixture(invalid=invalid)
                child, result, output = self.invoke(changed if changed is not None else ['eval/suite-manifest.json'],
                                                   phase=phase, baseline=baseline, dry_run=dry)
                self.assertEqual(child.returncode, code, child.stderr.decode(errors='replace'))
                self.assertIsNotNone(result)
                if selected is not None:
                    self.assertEqual(result['selection']['selected'], selected)
                if tests is not None:
                    self.assertEqual(result['tests'], tests)
                if complete is not None:
                    self.assertEqual(result['complete'], complete)
                if passed != 'unchecked':
                    self.assertIs(result['passed'], passed)
                return result, output

        a_g = ['eval/family_a', 'eval/family_g']
        all_families = ['eval/family_a', 'eval/family_b', 'eval/family_c', 'eval/family_g']
        # Native expected-count mismatch is selected and remains a failure.
        def wrong_expected_count(m):
            m['suites'][0].update(tests=3)
            baseline = json.loads((self.case_root / 'baseline.json').read_text())
            baseline['suites'][0].update(files=['test_a.py', 'test_a_extra.py'], tests=2)
            (self.case_root / 'baseline.json').write_text(json.dumps(baseline, indent=2) + '\n')
        run_case('count-only mismatch', wrong_expected_count, code=1,
                 selected=a_g, passed=False)
        # Add, remove and rename within one registered family stay local, including both rename paths.
        run_case('add path', changed=['eval/suite-manifest.json', 'eval/family_a/test_a_extra.py'],
                 code=0, selected=a_g, tests=3, complete=False, passed=True)

        def remove_a(m):
            old = self.case_root / 'eval/family_a/test_a_extra.py'
            old.unlink()
            m['suites'][0].update(files=['test_a.py'], tests=1)
            baseline = json.loads((self.case_root / 'baseline.json').read_text())
            baseline['suites'][0].update(files=['test_a.py', 'test_a_extra.py'], tests=2)
            (self.case_root / 'baseline.json').write_text(json.dumps(baseline, indent=2) + '\n')
        run_case('remove path', remove_a, changed=['eval/suite-manifest.json', 'eval/family_a/test_a_extra.py'],
                 code=0, selected=a_g, tests=2, complete=False, passed=True)

        def rename_a(m):
            old = self.case_root / 'eval/family_a/test_a_extra.py'
            old.rename(self.case_root / 'eval/family_a/test_a_renamed.py')
            m['suites'][0]['files'] = ['test_a.py', 'test_a_renamed.py']
            baseline = json.loads((self.case_root / 'baseline.json').read_text())
            baseline['suites'][0].update(files=['test_a.py', 'test_a_extra.py'], tests=2)
            (self.case_root / 'baseline.json').write_text(json.dumps(baseline, indent=2) + '\n')
        run_case('rename both paths', rename_a, changed=['eval/suite-manifest.json', 'eval/family_a/test_a_extra.py',
                 'eval/family_a/test_a_renamed.py'], code=0, selected=a_g, tests=3, complete=False, passed=True)

        # Full current discovery rejects inventory and baseline integrity defects before children.
        def add_unregistered(m):
            (self.case_root / 'eval/family_c/test_unregistered.py').write_text('')
        run_case('unregistered C file', add_unregistered, code=2, passed=False, invalid=True)
        run_case('duplicate registration', lambda m: m['suites'].append(dict(m['suites'][0])), code=2, passed=False, invalid=True)
        run_case('missing registration', lambda m: m['suites'][0].update(files=['missing.py']), code=2, passed=False, invalid=True)
        for label, contents, supplied_hash in [('malformed baseline', b'{', None),
                                               ('bad baseline hash', b'{"version":1}', '0' * 64)]:
            with self.subTest(case=label):
                self.fixture(broken_config=False)
                self.validate_fixture()
                (self.case_root / 'baseline.json').write_bytes(contents)
                child, result, _ = self.invoke(['eval/suite-manifest.json'], digest_override=supplied_hash)
                self.assertEqual(child.returncode, 2)
                self.assertIsNotNone(result)
                self.assertFalse(result['passed'])
        with self.subTest(case='boolean baseline count'):
            self.fixture(broken_config=False)
            self.validate_fixture()
            baseline = json.loads((self.case_root / 'baseline.json').read_text())
            baseline['suites'][0]['tests'] = True
            (self.case_root / 'baseline.json').write_text(json.dumps(baseline, indent=2) + '\n')
            child, result, _ = self.invoke(['eval/suite-manifest.json'])
            self.assertEqual(child.returncode, 2)
            self.assertIsNotNone(result)
            self.assertFalse(result['passed'])

        # Manifest semantics outside file/count deltas and unknown/global effects stay full.
        def family_membership(m):
            baseline = json.loads((self.case_root / 'baseline.json').read_text())
            baseline['suites'].append({'path': 'eval/family_old', 'files': ['test_old.py'], 'tests': 1,
                                       'source': 'eval/old', 'category': 'tooling', 'purpose': 'old family'})
            (self.case_root / 'baseline.json').write_text(json.dumps(baseline, indent=2) + '\n')
        run_case('family membership change', family_membership, code=0, selected=all_families, complete=True, passed=True)
        run_case('source change', lambda m: m['suites'][0].update(source='eval/elsewhere'), code=0,
                 selected=all_families, complete=True, passed=True)
        run_case('unknown field change', lambda m: m['suites'][0].update(extra='changed'), code=0,
                 selected=all_families, complete=True, passed=True)

        def row_boolean_number(m):
            m['suites'][0]['extra'] = 1
            baseline = json.loads((self.case_root / 'baseline.json').read_text())
            baseline['suites'][0]['extra'] = True
            (self.case_root / 'baseline.json').write_text(json.dumps(baseline, indent=2) + '\n')
        run_case('row metadata boolean differs from number', row_boolean_number, code=0,
                 selected=all_families, complete=True, passed=True)

        def nested_top_boolean_number(m):
            m['extra'] = {'policy': {'enabled': 1}}
            baseline = json.loads((self.case_root / 'baseline.json').read_text())
            baseline['extra'] = {'policy': {'enabled': True}}
            (self.case_root / 'baseline.json').write_text(json.dumps(baseline, indent=2) + '\n')
        run_case('nested top-level metadata boolean differs from number', nested_top_boolean_number, code=0,
                 selected=all_families, complete=True, passed=True)

        def reordered_metadata_keys(m):
            m['suites'][0]['extra'] = {'flag': 1, 'other': 'same'}
            baseline = json.loads((self.case_root / 'baseline.json').read_text())
            baseline['suites'][0]['extra'] = {'other': 'same', 'flag': 1}
            (self.case_root / 'baseline.json').write_text(json.dumps(baseline, indent=2) + '\n')
        run_case('equivalent metadata with reordered object keys', reordered_metadata_keys, code=0,
                 selected=a_g, tests=3, complete=False, passed=True)

        run_case('exclusion change', lambda m: m.update(excluded_directories=['eval/scenarios', 'eval/scratch', 'eval/runs', 'eval/family_z/fixtures']), code=0,
                 selected=all_families, complete=True, passed=True)

        for label, reverse_files in [('identical manifest', False), ('file reorder only', True)]:
            with self.subTest(case=label):
                self.fixture(broken_config=False)
                current = json.loads((self.case_root / 'eval/suite-manifest.json').read_text())
                baseline = json.loads(json.dumps(current))
                if reverse_files:
                    baseline['suites'][0]['files'].reverse()
                (self.case_root / 'baseline.json').write_text(json.dumps(baseline, indent=2) + '\n')
                self.validate_fixture()
                child, result, _ = self.invoke(['eval/suite-manifest.json'])
                self.assertEqual(child.returncode, 0, child.stderr.decode(errors='replace'))
                self.assertEqual(result['selection']['selected'], ['eval/family_g'])
                self.assertEqual(result['registered_tests'], 5)
                self.assertEqual(result['tests'], 1)
                self.assertFalse(result['complete'])
                self.assertTrue(result['passed'])
        run_case('baseline absent', baseline=False, code=0, selected=all_families, complete=True, passed=True)
        run_case('unknown nonmanifest path', changed=['eval/suite-manifest.json', 'unknown/source.py'], code=0,
                 selected=all_families, complete=True, passed=True)
        run_case('other global path', changed=['eval/suite-manifest.json', 'eval/run_suites.py'], code=0,
                 selected=all_families, complete=True, passed=True)
        for phase in ('integration', 'release'):
            run_case(phase + ' phase', phase=phase, code=0, selected=all_families,
                     complete=True, passed=True)

        self.fixture(broken_config=False)
        self.validate_fixture()
        child, result, _ = self.invoke([], baseline=False, default_full=True)
        self.assertEqual(child.returncode, 0)
        self.assertEqual(result['selection']['selected'], all_families)
        self.assertTrue(result['complete'])

        run_case('dry run', dry=True, code=0, selected=a_g, tests=0, complete=False, passed=None)
        output = self.case_root / 'run'
        result_path = output / 'results.json'
        result = json.loads(result_path.read_text()) if result_path.exists() else None
        if result is not None:
            self.assertEqual(result['suites'], [])
            self.assertFalse((self.case_root / 'control-executed').exists())
            self.assertFalse((output / 'family_a.stdout').exists())
            self.assertFalse((output / 'family_b.stderr').exists())

    def test_real_manifest_consumers_remain_selected(self):
        manifest = json.loads((ROOT / 'eval/suite-manifest.json').read_text())
        baseline = json.loads(json.dumps(manifest))
        row = next(suite for suite in baseline['suites']
                   if suite['path'] == 'eval/tests/tooling/maintaining/suite-integrity')
        row['tests'] += 1
        plan = runner.plan(ROOT, manifest, changed=['eval/suite-manifest.json'], manifest_baseline=baseline)
        self.assertEqual(set(plan['selected']), {'eval/tests/tooling/maintaining/suite-integrity',
                         'eval/tests/product/templates', 'eval/tests/tooling/behavior/judges/planning'})
        self.assertFalse(plan['complete'])


if __name__ == '__main__':
    unittest.main()
