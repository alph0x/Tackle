"""Suite index consistency and selection through native runner fixtures."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[5]
INDEX = 'eval/tests/README.md'
MANIFEST = 'eval/suite-manifest.json'
CONSUMER = 'eval/tests/tooling/maintaining/suite-integrity'
RULES = 'eval/tests/tooling/rules'


def assert_suite_index(index, manifest):
    """Assert that table rows represent each registered suite once."""
    expected = {s['path'].removeprefix('eval/tests/'): s['category'] for s in manifest['suites']}
    assert len(expected) == len(manifest['suites']), 'duplicate registry family'
    lines = index.splitlines()
    header = '| Category | Suite | Guarantees |'
    assert lines.count(header) == 1, 'missing or duplicate suite table'
    start = lines.index(header)
    assert re.fullmatch(r'\|\s*:?-+:?\s*\|\s*:?-+:?\s*\|\s*:?-+:?\s*\|', lines[start + 1]), 'invalid table separator'
    seen = set()
    for line in lines[start + 2:]:
        if not line.startswith('|'):
            break
        cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
        assert len(cells) == 3, 'invalid suite row'
        category, link, description = cells
        match = re.fullmatch(r'\[([^\]]+)\]\(([^)]+)\)', link)
        assert match, 'invalid suite link'
        name, target = match.groups()
        assert name in expected, 'unknown suite: ' + name
        assert name not in seen, 'duplicate suite: ' + name
        assert category == expected[name], 'wrong category: ' + name
        assert target == name + '/', 'wrong target: ' + name
        assert description.strip(), 'empty description: ' + name
        seen.add(name)
    assert seen == set(expected), 'missing suites: ' + repr(set(expected) - seen)


def read_index(root):
    assert_suite_index((root / INDEX).read_text(), json.loads((root / MANIFEST).read_text()))


class SuiteIndexTests(unittest.TestCase):
    def test_real_index(self):
        read_index(ROOT)

    def test_faults_and_valid_alternatives_use_same_consumer(self):
        manifest = {'suites': [{'path': 'eval/tests/product/alpha', 'category': 'product'},
                               {'path': 'eval/tests/tooling/beta', 'category': 'tooling'}]}
        prefix = '| Category | Suite | Guarantees |\n|---|---|---|\n'
        a = '| product | [product/alpha](product/alpha/) | Alpha behavior. |\n'
        b = '| tooling | [tooling/beta](tooling/beta/) | Beta behavior. |\n'
        for text in [prefix + a, prefix + a + a + b,
                     prefix + a.replace('product |', 'tooling |', 1) + b,
                     prefix + a.replace('(product/alpha/)', '(product/wrong/)') + b,
                     prefix + a.replace('Alpha behavior.', '  ') + b]:
            with self.subTest(index=text), self.assertRaises(AssertionError):
                assert_suite_index(text, manifest)
        assert_suite_index('Introductory prose.\n\n' + prefix + b + a.replace('Alpha behavior.', 'Another useful explanation.') + '\nMore prose.\n', manifest)

    def test_actual_runner_index_selection_and_consumer(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            consumer = CONSUMER
            control = 'eval/tests/product/control'
            rules_family = RULES
            for family in (consumer, control, rules_family):
                (root / family).mkdir(parents=True)
            # Import this exact consumer in the runner's native child, not a second oracle.
            (root / consumer / 'test_consumer.py').write_text(
                'import importlib.util, unittest\nfrom pathlib import Path\n'
                + 'spec = importlib.util.spec_from_file_location("index_consumer", ' + repr(str(Path(__file__).resolve())) + ')\n'
                + 'module = importlib.util.module_from_spec(spec)\nspec.loader.exec_module(module)\n'
                + 'class Consumer(unittest.TestCase):\n def test_index(self): module.read_index(Path.cwd())\n')
            (root / consumer / 'test_extra.py').write_text('import unittest\nclass Extra(unittest.TestCase):\n def test_extra(self): self.assertTrue(True)\n')
            (root / control / 'test_control.py').write_text('import unittest\nfrom pathlib import Path\nclass Control(unittest.TestCase):\n def test_control(self):\n  Path("control-executed").touch()\n  self.fail("planted unrelated failure")\n')
            (root / rules_family / 'test_rules.py').write_text(
                'import sys, unittest\nfrom pathlib import Path\nfrom unittest.mock import patch\n'
                + 'sys.path.insert(0, ' + repr(str(ROOT / 'eval/rules')) + ')\n'
                + 'import committed_text as scanner\n'
                + 'class Rules(unittest.TestCase):\n def test_added_index_row(self):\n'
                + '  row = Path("eval/tests/README.md").read_text().splitlines()[2]\n'
                + '  diff = "--- a/eval/tests/README.md\\n+++ b/eval/tests/README.md\\n@@ -3,0 +3,1 @@\\n+" + row + "\\n"\n'
                + '  with patch.object(scanner, "_git_diff", return_value=diff):\n'
                + '   findings = scanner.scan_committed_text(' + repr(str(ROOT)) + ', scanner._PREFLIGHT_BASE, "synthetic")\n'
                + '  self.assertEqual(findings, [], scanner.format_findings(findings))\n')
            families = [(consumer, ['test_consumer.py', 'test_extra.py'], 2, 'tooling'),
                        (control, ['test_control.py'], 1, 'product'), (rules_family, ['test_rules.py'], 1, 'tooling')]
            manifest = {'version': 1, 'excluded_directories': ['eval/scenarios', 'eval/scratch', 'eval/runs'],
                        'suites': [dict(path=p, files=f, tests=n, source=p, category=c, purpose='fixture behavior') for p, f, n, c in families]}
            (root / MANIFEST).write_text(json.dumps(manifest))
            baseline = json.loads(json.dumps(manifest))
            baseline['suites'][0]['files'] = ['test_consumer.py']
            baseline['suites'][0]['tests'] = 1
            baseline_path = root / 'baseline.json'
            baseline_path.write_text(json.dumps(baseline))
            mapping = json.loads((ROOT / 'eval/check-selection.json').read_text())
            index_rules = [r for r in mapping['rules'] if INDEX in r['patterns']]
            self.assertEqual(len(index_rules), 1)
            self.assertEqual(index_rules[0]['families'], [CONSUMER, RULES])
            manifest_rules = [r for r in mapping['rules'] if MANIFEST in r['patterns']]
            self.assertEqual(len(manifest_rules), 1)
            self.assertIn(CONSUMER, manifest_rules[0]['families'])
            projected_manifest = dict(manifest_rules[0], families=[CONSUMER])
            fixed = {'version': 1, 'families': [p for p, _, _, _ in families],
                     'rules': [index_rules[0], projected_manifest], 'global_patterns': mapping['global_patterns'],
                     'ignored_patterns': mapping['ignored_patterns'], 'test_source_regressions': mapping['test_source_regressions']}
            old = dict(fixed, rules=[projected_manifest])
            table = '| Category | Suite | Guarantees |\n|---|---|---|\n' + ''.join(
                '| {} | [{}]({}/) | Fixture behavior. |\n'.format(c, p.removeprefix('eval/tests/'), p.removeprefix('eval/tests/')) for p, _, _, c in families)
            index = root / INDEX
            index.write_text(table)
            archive = Path(os.environ['T11_FIXTURE_RECORDS']) if 'T11_FIXTURE_RECORDS' in os.environ else None

            def invoke(name, rules, changed, *, baseline_on=False):
                (root / 'eval/check-selection.json').write_text(json.dumps(rules))
                output = root / name
                argv = [sys.executable, '-I', '-B', str(ROOT / 'eval/run_suites.py'), '--root', str(root), '--manifest', str(root / MANIFEST)]
                for path in changed:
                    argv += ['--changed', path]
                if baseline_on:
                    argv += ['--manifest-baseline', str(baseline_path), '--manifest-baseline-sha256', hashlib.sha256(baseline_path.read_bytes()).hexdigest()]
                argv += ['--output', str(output)]
                start = datetime.datetime.now(datetime.timezone.utc).isoformat()
                try:
                    child = subprocess.run(argv, cwd=ROOT, capture_output=True, timeout=120)
                    timed_out = False
                except subprocess.TimeoutExpired as error:
                    child = subprocess.CompletedProcess(argv, None, error.stdout or b'', error.stderr or b'')
                    timed_out = True
                finish = datetime.datetime.now(datetime.timezone.utc).isoformat()
                (output / 'cli.stdout').write_bytes(child.stdout)
                (output / 'cli.stderr').write_bytes(child.stderr)
                (output / 'command.json').write_text(json.dumps({'argv': argv, 'cwd': str(ROOT), 'start': start, 'finish': finish, 'exit': child.returncode, 'timeout': timed_out, 'signal': -child.returncode if child.returncode is not None and child.returncode < 0 else None, 'streams': {'stdout': hashlib.sha256(child.stdout).hexdigest(), 'stderr': hashlib.sha256(child.stderr).hexdigest()}, 'mapping': rules}, indent=2))
                if archive:
                    archive.mkdir(parents=True, exist_ok=True)
                    shutil.copytree(output, archive / name)
                return child, json.loads((output / 'results.json').read_text())

            child, report = invoke('old', old, [INDEX])
            self.assertEqual(child.returncode, 1)
            self.assertTrue(report['complete'])
            self.assertEqual(report['selection']['unknown_paths'], [INDEX])
            self.assertTrue((root / 'control-executed').exists())
            (root / 'control-executed').unlink()
            child, report = invoke('fixed', fixed, [INDEX])
            self.assertEqual(child.returncode, 0, child.stderr.decode())
            self.assertEqual(report['selection']['selected'], [consumer, rules_family])
            self.assertTrue(report['passed'])
            self.assertFalse((root / 'control-executed').exists())
            index.write_text(table.replace('Fixture behavior.', '', 1))
            child, report = invoke('malformed', fixed, [INDEX])
            self.assertEqual(child.returncode, 1)
            self.assertFalse(report['suites'][0]['passed'])
            self.assertFalse((root / 'control-executed').exists())
            index.write_text(table.replace('Fixture behavior.', 'Prepared T-' + str(123) + '.', 1))
            read_index(root)  # The leaking description remains a valid index.
            child, report = invoke('leak', fixed, [INDEX])
            self.assertEqual(child.returncode, 1)
            self.assertEqual(report['selection']['selected'], [consumer, rules_family])
            self.assertTrue(report['suites'][0]['passed'])
            self.assertFalse(report['suites'][1]['passed'])
            self.assertIn(b'workspace-id', (root / 'leak' / 'cli.stdout').read_bytes() + (root / 'leak' / 'cli.stderr').read_bytes() + b''.join(p.read_bytes() for p in (root / 'leak').rglob('*') if p.is_file()))
            self.assertFalse((root / 'control-executed').exists())
            index.write_text(table.replace('Fixture behavior.', 'Alternative descriptive prose.'))
            child, report = invoke('qualified', fixed, [INDEX, MANIFEST, consumer + '/test_extra.py'], baseline_on=True)
            self.assertEqual(child.returncode, 0, child.stderr.decode())
            self.assertEqual(report['selection']['manifest_impact']['status'], 'qualified')
            self.assertEqual(report['selection']['selected'], [consumer, rules_family])
            self.assertTrue(report['passed'])
            self.assertFalse((root / 'control-executed').exists())


if __name__ == '__main__':
    unittest.main()
