"""Small execution-level regressions for canonical identity and saved scripts."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))
from maintaining.install_root import current_root  # noqa: E402
INSTALL = current_root(ROOT)

CAPTURE = (INSTALL/'scripts/capture.py').read_text()
LINT = (INSTALL/'scripts/lint_runner.py').read_text()
SOURCE = (INSTALL/'scripts/lint.py').read_bytes()
SHA = hashlib.sha256(SOURCE).hexdigest()
_spec = importlib.util.spec_from_file_location('documented_lint', INSTALL/'scripts/lint_runner.py')
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
NS = vars(_module)


class IsolatedVeracity(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name, data in [('capture.py', CAPTURE.encode()), ('lint_runner.py', LINT.encode()), ('lint.py', SOURCE)]:
            (self.root/name).write_bytes(data)
        self.workspace = self.root/'docs/plans/demo'
        (self.workspace/'tasks').mkdir(parents=True)
        (self.workspace/'tasks/T-A.md').write_text('- **Effort**: low\n')
        (self.workspace/'plan.md').write_text('T-A\n')
        (self.workspace/'task-board.md').write_text(
            'Schema: tackle-workspace/5\n\n'
            '| Task | What | Brief | Depends on | Status | Verification |\n'
            '|---|---|---|---|---|---|\n'
            '| T-A | Work | tasks/T-A.md | none | Draft | pending |\n')

    def captured(self, row=12, command=None):
        canonical = NS['canonical_rows'](SOURCE, SHA, 'demo')[row]['command']
        (self.root/'row.sh').write_bytes(canonical if command is None else command)
        spec = dict(argv=['sh', 'row.sh'], selectors=[dict(glob='docs/plans/demo/tasks/*.md', required=True)],
                    artifacts=[], destination='evidence', timeout_seconds=2)
        (self.root/'check.json').write_text(json.dumps(spec))
        run = subprocess.run([sys.executable, 'capture.py', 'check.json'], cwd=self.root, capture_output=True, timeout=5)
        out = Path(run.stdout.decode().strip()).parent
        return out, json.loads((out/'result.json').read_text())

    def verdict(self, row, out, record):
        return NS['captured_lint_verdict'](SOURCE, SHA, 'demo', row, 'row.sh', record, out)

    def test_real_canonical_row_is_accepted(self):
        out, record = self.captured()
        self.assertEqual(self.verdict(12, out, record), 'PASS')

    def test_recorded_noncanonical_success_is_rejected(self):
        out, record = self.captured(command=b'true')
        self.assertEqual(record['child_exit'], 0)
        self.assertEqual(self.verdict(12, out, record), 'ERROR')

    def test_observed_row4_quote_mutation_is_rejected(self):
        command = NS['canonical_rows'](SOURCE, SHA, 'demo')[4]['command']
        mutated = command.replace(b'[^\"]+\"/', b'[^\"]+/')
        self.assertNotEqual(command, mutated)
        out, record = self.captured(4, mutated)
        self.assertEqual(self.verdict(4, out, record), 'ERROR')

    def test_stdout_findings_exit_zero_fail(self):
        (self.workspace/'tasks/T-A.md').write_text('- **Effort**: impossible\n')
        out, record = self.captured()
        self.assertEqual(record['child_exit'], 0)
        self.assertEqual(self.verdict(12, out, record), 'FAIL')

    def test_row12_pattern_mutation_is_rejected(self):
        command = NS['canonical_rows'](SOURCE, SHA, 'demo')[12]['command']
        mutated = command.replace(b'Effort\\*\\*', b'Effort\\*')
        self.assertNotEqual(command, mutated)
        out, record = self.captured(12, mutated)
        self.assertEqual(self.verdict(12, out, record), 'ERROR')

    def test_missing_script_fingerprint_cannot_be_rescued_by_transcript(self):
        out, record = self.captured()
        del record['inputs_before']['row.sh']
        self.assertEqual(self.verdict(12, out, record), 'ERROR')

    def test_forged_mapping_or_missing_blob_rejected(self):
        out, record = self.captured(command=b'true')
        digest = hashlib.sha256(NS['canonical_rows'](SOURCE, SHA, 'demo')[12]['command']).hexdigest()
        record['inputs_before']['row.sh'] = digest
        record['inputs_after']['row.sh'] = digest
        self.assertEqual(self.verdict(12, out, record), 'ERROR')

    def test_tampered_stream_is_not_pass(self):
        out, record = self.captured()
        (out/'stdout.bin').write_bytes(b'hidden finding')
        self.assertEqual(self.verdict(12, out, record), 'ERROR')

    def test_saved_product_script_is_automatic_and_history_survives(self):
        (self.root/'row.sh').write_text('printf first')
        out1, r1 = self.captured(command=b'printf first')
        old = {str(p.relative_to(out1)): p.read_bytes() for p in out1.rglob('*') if p.is_file()}
        out2, r2 = self.captured(command=b'printf second')
        for out, record, data in [(out1, r1, b'printf first'), (out2, r2, b'printf second')]:
            self.assertEqual((out/'blobs'/record['inputs_before']['row.sh']).read_bytes(), data)
            self.assertIn('capture.py', record['inputs_before'])
            self.assertIn('check.json', record['inputs_before'])
        self.assertEqual(old, {str(p.relative_to(out1)): p.read_bytes() for p in out1.rglob('*') if p.is_file()})

    def test_connected_path_uses_literal_rows_and_honest_subset_score(self):
        self.run_connected_subset()

    def test_connected_path_rejects_changed_capture_helper(self):
        config = dict(slug='demo', rows=[12],
                      capture_script='capture.py',
                      selectors=[dict(glob='docs/plans/demo/**/*.md', required=True)],
                      workspace='docs/plans/demo', timeout_seconds=2)
        (self.root/'lint.json').write_text(json.dumps(config))
        (self.root/'capture.py').write_text(CAPTURE + '\nprint("changed")\n')
        run = subprocess.run([sys.executable, 'lint_runner.py', 'lint.json'], cwd=self.root, capture_output=True, timeout=10)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn(b'capture script revision changed', run.stderr)
        self.assertFalse((self.workspace/'evidence').exists())

    def run_connected_subset(self):
        (self.workspace/'tasks/T-A.md').write_text('- **Effort**: impossible\n')
        config = dict(slug='demo', rows=[5,12,15],
                      capture_script='capture.py',
                      selectors=[dict(glob='docs/plans/demo/**/*.md',required=True)],
                      destination='lint-evidence', timeout_seconds=2)
        (self.workspace/'AGENTS.md').write_text('Reference staleness window: 14\n')
        (self.root/'lint.json').write_text(json.dumps(config))
        run = subprocess.run([sys.executable, 'lint_runner.py', 'lint.json'], cwd=self.root, capture_output=True, timeout=10)
        self.assertEqual(run.returncode, 1, run.stderr)
        summary = json.loads(Path(run.stdout.decode().strip()).read_text())
        self.assertEqual((summary['passed'],summary['total'],summary['complete']), (2,3,False))
        self.assertEqual(summary['rows']['12']['verdict'], 'FAIL')
        for key, result in summary['rows'].items():
            self.assertEqual(result['source_sha256'], SHA)
            record = json.loads((self.root/result['observation']/'result.json').read_text())
            self.assertEqual((self.root/result['observation']/'blobs'/record['inputs_before'][record['argv'][1]]).read_bytes(),
                             NS['canonical_rows'](SOURCE,SHA,'demo')[int(key)]['command'])


class LintSourcePin(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.root = self.base/'project'
        self.root.mkdir()
        for name, data in [('capture.py', CAPTURE.encode()), ('lint_runner.py', LINT.encode()), ('lint.py', SOURCE)]:
            (self.root/name).write_bytes(data)
        (self.root/'docs/plans/demo/tasks').mkdir(parents=True)
        (self.root/'docs/plans/demo/tasks/T-A.md').write_text('- **Effort**: low\n')
        self.outside = self.base/'outside'
        self.outside.mkdir()
        (self.outside/'keep.txt').write_text('outside')
        (self.outside/'capture.py').write_bytes(CAPTURE.encode())
        self.outside_before = self.snapshot(self.outside)

    def snapshot(self, path):
        return {str(p.relative_to(path)): p.read_bytes() for p in path.rglob('*') if p.is_file()}

    def config(self, **changes):
        config = dict(slug='demo', rows=[12], selectors=[dict(glob='docs/plans/demo/**/*.md', required=True)],
                      workspace='docs/plans/demo', timeout_seconds=2)
        config.update(changes)
        return config

    def run_runner(self, config, argv_path='lint.json', config_file=None):
        (config_file or self.root/'lint.json').write_text(json.dumps(config))
        return subprocess.run([sys.executable, 'lint_runner.py', argv_path], cwd=self.root,
                              capture_output=True, timeout=10)

    def assert_nothing_written(self):
        self.assertEqual(list(self.root.rglob('evidence')), [])
        self.assertEqual(list(self.root.rglob('verification-records')), [])
        self.assertEqual(list(self.root.rglob('lint-*')), [])

    def test_mutated_lint_beside_runner_copy_is_refused_before_writes(self):
        for name, data in [('trailing newline', SOURCE + b'\n'), ('changed row', SOURCE + b'# drift\n')]:
            with self.subTest(mutation=name):
                (self.root/'lint.py').write_bytes(data)
                run = self.run_runner(self.config())
                self.assertNotEqual(run.returncode, 0)
                self.assertIn(b'ValueError: lint source revision changed', run.stderr)
                self.assert_nothing_written()
                (self.root/'lint.py').write_bytes(SOURCE)

    def test_source_keys_are_refused_before_any_read_or_write(self):
        (self.outside/'source.py').write_bytes(SOURCE)
        cases = [
            dict(source='lint.py'),
            dict(source_sha256=SHA),
            dict(source='lint.py', source_sha256=SHA),
            dict(source=str(self.outside/'source.py'), source_sha256=SHA),
            dict(source='../x', source_sha256=SHA),
        ]
        for extra in cases:
            with self.subTest(keys=sorted(extra)):
                run = self.run_runner(self.config(**extra))
                self.assertNotEqual(run.returncode, 0)
                self.assertIn(b'ValueError', run.stderr)
                self.assertIn(b'the lint source is the pinned lint.py beside the runner', run.stderr)
                self.assertNotIn(b'FileNotFoundError', run.stderr)
                self.assert_nothing_written()
                self.assertEqual(self.snapshot(self.outside), self.outside_before | {'source.py': SOURCE})

    def test_confined_keys_refuse_escapes_before_writes(self):
        (self.root/'link').symlink_to(self.outside, target_is_directory=True)
        (self.root/'cap-link.py').symlink_to(self.outside/'capture.py')
        (self.root/'cfg-link.json').symlink_to(self.outside/'lint.json')
        (self.outside/'lint.json').write_text(json.dumps(self.config()))
        before = self.snapshot(self.outside)
        for value in ['../outside', str(self.outside), 'link']:
            with self.subTest(key='workspace', value=value):
                run = self.run_runner(self.config(workspace=value))
                self.assertNotEqual(run.returncode, 0)
                self.assertIn(b'ValueError', run.stderr)
                self.assert_nothing_written()
                self.assertEqual(self.snapshot(self.outside), before)
            with self.subTest(key='destination', value=value):
                config = self.config(destination=value)
                config.pop('workspace')
                run = self.run_runner(config)
                self.assertNotEqual(run.returncode, 0)
                self.assertIn(b'ValueError', run.stderr)
                self.assert_nothing_written()
                self.assertEqual(self.snapshot(self.outside), before)
        for value in ['../outside/capture.py', str(self.outside/'capture.py'), 'cap-link.py']:
            with self.subTest(key='capture_script', value=value):
                run = self.run_runner(self.config(capture_script=value))
                self.assertNotEqual(run.returncode, 0)
                self.assertIn(b'ValueError', run.stderr)
                self.assert_nothing_written()
                self.assertEqual(self.snapshot(self.outside), before)
        for argv_path in ['../outside/lint.json', str(self.outside/'lint.json'), 'cfg-link.json']:
            with self.subTest(config_path=argv_path):
                run = self.run_runner(self.config(), argv_path=argv_path)
                self.assertNotEqual(run.returncode, 0)
                self.assertIn(b'ValueError', run.stderr)
                self.assert_nothing_written()
                self.assertEqual(self.snapshot(self.outside), before)

    def test_trusted_lint_pin_matches_the_shipped_lint_bytes(self):
        match = re.search(r"trusted_lint_sha256 = '([0-9a-f]{64})'", LINT)
        self.assertIsNotNone(match)
        self.assertEqual(hashlib.sha256(SOURCE).hexdigest(), match.group(1))


if __name__ == '__main__':
    unittest.main()
