"""Execute the shipped evidence script with controlled child processes."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))
from maintaining.install_root import current_root  # noqa: E402
INSTALL = current_root(REPO)

RECIPE = (INSTALL / 'scripts/evidence_capture.py').read_text()

CAPTURE_AUDITOR = r'''
import json
import os
import runpy
import sys

script = sys.argv[1]
sys.argv = [script, 'spec.json']
events = []
mutations = {'os.mkdir', 'os.remove', 'os.rmdir', 'os.rename', 'os.replace',
             'os.link', 'os.symlink', 'os.chmod', 'os.chown', 'os.truncate'}

def audit(event, args):
    if event == 'open':
        mode, flags = args[1:3]
        if ((isinstance(mode, str) and any(c in mode for c in 'wax+'))
                or (isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR
                    | os.O_CREAT | os.O_TRUNC | os.O_APPEND))):
            events.append([event, str(args[0]), str(mode), flags])
    elif event in mutations or event in ('subprocess.Popen', 'os.system',
                                          'os.posix_spawn', 'os.spawn',
                                          'os.exec', 'os.fork'):
        events.append([event, *[str(a) for a in args]])

sys.addaudithook(audit)
try:
    runpy.run_path(script, run_name='__main__')
finally:
    print('BOUNDARY_EVENTS=' + json.dumps(events), file=sys.stderr)
'''


def snapshot(root):
    entries = {}
    for path in root.rglob('*'):
        name = str(path.relative_to(root))
        if path.is_symlink():
            entries[name] = ('symlink', os.readlink(path))
        elif path.is_dir():
            entries[name] = ('directory',)
        else:
            entries[name] = ('file', path.read_bytes())
    return entries


class CaptureTests(unittest.TestCase):
    def observe(self, child, *, artifacts=(), timeout=3, missing_input=False, repeat=False):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'child.py').write_text(child)
            (root / 'SPEC.md').write_text('fixed contract\n')
            if not missing_input:
                (root / 'test_module.py').write_text('protected\n')
            argv = [sys.executable, 'child.py']
            script = RECIPE.replace('argv = ["python3", "-m", "unittest", "discover", "-v"]', 'argv = ' + repr(argv))
            script = script.replace('inputs = ["module.py", "test_module.py", "SPEC.md"]', 'inputs = ["child.py", "test_module.py", "SPEC.md"]')
            script = script.replace('artifacts = []', 'artifacts = ' + repr(list(artifacts)))
            script = script.replace('timeout_seconds = 30', 'timeout_seconds = ' + repr(timeout))
            observations = []
            for _ in range(2 if repeat else 1):
                result = subprocess.run([sys.executable, '-c', script, str(root)], cwd=root, capture_output=True, timeout=8)
                dirs = sorted((root / 'evidence').glob('validation-*')) if (root / 'evidence').exists() else []
                events = {d.name: {f.name: f.read_bytes() for f in d.iterdir()} for d in dirs}
                observations.append((result, events))
            return observations, argv

    def test_binary_capture_exact_command_clock_and_fingerprints(self):
        runs, argv = self.observe("import os\nos.write(1,b'\\xff\\n')\nos.write(2,b'error\\x00')\n")
        run, events = runs[0]
        self.assertEqual(run.returncode, 0)
        files = next(iter(events.values()))
        record = json.loads(files['result.json'])
        self.assertEqual(record['argv'], argv)
        self.assertEqual(files['stdout.bin'], b'\xff\n')
        self.assertEqual(files['stderr.bin'], b'error\x00')
        self.assertEqual(record['inputs_before']['SPEC.md'], hashlib.sha256(b'fixed contract\n').hexdigest())
        self.assertEqual(record['inputs_after'], record['inputs_before'])
        self.assertLessEqual(record['start'], record['end'])
        self.assertEqual((record['actor'], record['model'], record['effort']), ('n/a',) * 3)

    def test_printed_pass_does_not_hide_child_failure(self):
        runs, _ = self.observe("print('PASS'); raise SystemExit(7)")
        run, events = runs[0]
        files = next(iter(events.values()))
        self.assertEqual(run.returncode, 1)
        self.assertEqual(json.loads(files['result.json'])['child_exit'], 7)
        self.assertEqual(files['stdout.bin'], b'PASS\n')

    def test_timeout_preserves_partial_output_without_success(self):
        runs, _ = self.observe("import time\nprint('partial',flush=True)\ntime.sleep(10)", timeout=0.15)
        run, events = runs[0]
        files = next(iter(events.values()))
        record = json.loads(files['result.json'])
        self.assertEqual(run.returncode, 1)
        self.assertTrue(record['timeout'])
        self.assertIsNone(record['child_exit'])
        self.assertFalse(record['accepted'])
        self.assertEqual(files['stdout.bin'], b'partial\n')

    def test_changed_input_is_not_current_evidence(self):
        runs, _ = self.observe("from pathlib import Path\nPath('test_module.py').write_text('weakened')")
        run, events = runs[0]
        record = json.loads(next(iter(events.values()))['result.json'])
        self.assertEqual(run.returncode, 1)
        self.assertEqual(record['child_exit'], 0)
        self.assertFalse(record['inputs_stable'])
        self.assertNotEqual(record['inputs_before'], record['inputs_after'])

    def test_missing_artifact_rejects_successful_child(self):
        runs, _ = self.observe('pass', artifacts=['absent.zip'])
        run, events = runs[0]
        record = json.loads(next(iter(events.values()))['result.json'])
        self.assertEqual(run.returncode, 1)
        self.assertIn('artifact_error', record)
        self.assertTrue(record['inputs_stable'])
        self.assertFalse(record['artifacts_present'])
        self.assertFalse(record['accepted'])

    @unittest.skipIf(sys.platform == 'win32', 'POSIX signal observation')
    def test_signal_is_observed_separately(self):
        runs, _ = self.observe('import os,signal\nos.kill(os.getpid(), signal.SIGTERM)')
        run, events = runs[0]
        record = json.loads(next(iter(events.values()))['result.json'])
        self.assertEqual(run.returncode, 1)
        self.assertEqual(record['child_exit'], -signal.SIGTERM)
        self.assertEqual(record['signal'], signal.SIGTERM)

    def test_missing_declared_input_fails_before_inference_or_success(self):
        runs, _ = self.observe("print('must not run')", missing_input=True)
        run, events = runs[0]
        self.assertNotEqual(run.returncode, 0)
        self.assertNotIn(b'must not run', run.stdout)
        self.assertEqual(events, {})

    def test_repeated_capture_keeps_old_raw_bytes(self):
        runs, _ = self.observe("from pathlib import Path\nPath('output.bin').write_bytes(b'actual')", artifacts=['output.bin'], repeat=True)
        self.assertEqual([r.returncode for r, _ in runs], [0, 0])
        first, second = runs[0][1], runs[1][1]
        self.assertEqual(len(first), 1)
        self.assertEqual(len(second), 2)
        key = next(iter(first))
        self.assertEqual(first[key], second[key])
        self.assertEqual(json.loads(first[key]['result.json'])['artifacts']['output.bin'], hashlib.sha256(b'actual').hexdigest())

    def assert_rejected_before_effect(self, root, script, name):
        before = snapshot(root)
        result = subprocess.run(
            [sys.executable, '-I', '-B', '-c', CAPTURE_AUDITOR, str(script)],
            cwd=root, capture_output=True, text=True, timeout=30)
        markers = [line for line in result.stderr.splitlines()
                   if line.startswith('BOUNDARY_EVENTS=')]
        self.assertEqual(len(markers), 1, result.stderr)
        events = json.loads(markers[0].split('=', 1)[1])
        self.assertNotEqual(result.returncode, 0, name)
        self.assertEqual(events, [], name)
        self.assertEqual(snapshot(root), before, name)

    def test_native_capture_rejects_invalid_inputs_before_effect(self):
        command = [sys.executable, '-I', '-B', '-c',
                   "from pathlib import Path; Path('launch-sentinel').write_text('ran')"]
        cases = [
            ('timeout-zero', 0, command),
            ('timeout-negative', -1, command),
            ('timeout-text', 'nonnumeric', command),
            ('timeout-nan', float('nan'), command),
            ('timeout-inf', float('inf'), command),
            ('timeout-neg-inf', -float('inf'), command),
            ('timeout-false', False, command),
            ('timeout-true', True, command),
            ('timeout-null', None, command),
            ('timeout-list', [], command),
            ('argv-empty', 2, []),
            ('argv-nonstring-member', 2, [sys.executable, 4]),
            ('argv-string', 2, 'not-a-list'),
            ('argv-null', 2, None),
            ('argv-number', 2, 3),
            ('argv-bool', 2, True),
            ('argv-object', 2, {}),
            ('argv-bool-member', 2, [sys.executable, False]),
        ]
        for name, timeout, argv in cases:
            with self.subTest(case=name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                spec = {'argv': argv, 'selectors': [], 'artifacts': [],
                        'destination': 'store', 'timeout_seconds': timeout}
                (root / 'spec.json').write_text(json.dumps(spec))
                self.assert_rejected_before_effect(
                    root, INSTALL / 'scripts/capture.py', name)
                self.assertFalse((root / 'launch-sentinel').exists(), name)

    def test_native_capture_accepts_valid_input_and_records_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            command = [sys.executable, '-I', '-B', '-c',
                       "import sys; print('native stdout'); print('native stderr', file=sys.stderr)"]
            spec = {'argv': command, 'selectors': [], 'artifacts': [],
                    'destination': 'store', 'timeout_seconds': 3}
            (root / 'spec.json').write_text(json.dumps(spec))
            result = subprocess.run(
                [sys.executable, '-I', '-B', str(INSTALL / 'scripts/capture.py'),
                 'spec.json'],
                cwd=root, capture_output=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            records = list((root / 'store').glob('observation-*/result.json'))
            self.assertEqual(len(records), 1)
            record = json.loads(records[0].read_text())
            self.assertEqual(record['argv'], command)
            self.assertEqual(record['child_exit'], 0)
            self.assertTrue(record['accepted'])
            self.assertEqual((records[0].parent / 'stdout.bin').read_bytes(), b'native stdout\n')
            self.assertEqual((records[0].parent / 'stderr.bin').read_bytes(), b'native stderr\n')

    def test_native_runner_rejects_invalid_timeouts_before_effect(self):
        cases = [
            ('zero', 0),
            ('negative', -1),
            ('text', 'nonnumeric'),
            ('nan', float('nan')),
            ('inf', float('inf')),
            ('neg-inf', -float('inf')),
            ('false', False),
            ('true', True),
            ('null', None),
            ('list', []),
        ]
        for name, timeout in cases:
            with self.subTest(case=name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                shutil.copytree(REPO / 'eval/lint/rows/fixtures/pass-full', root, dirs_exist_ok=True)
                config = {
                    'slug': 'demo',
                    'workspace': 'docs/plans/demo',
                    'selectors': [{'glob': 'docs/plans/demo/*.md', 'required': True}],
                    'rows': [1],
                    'timeout_seconds': timeout,
                }
                (root / 'spec.json').write_text(json.dumps(config))
                self.assert_rejected_before_effect(
                    root, INSTALL / 'scripts/lint_runner.py', name)

    def test_native_runner_accepts_valid_timeout_and_records_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(REPO / 'eval/lint/rows/fixtures/pass-full', root, dirs_exist_ok=True)
            config = {
                'slug': 'demo',
                'workspace': 'docs/plans/demo',
                'selectors': [{'glob': 'docs/plans/demo/*.md', 'required': True}],
                'rows': [1],
                'timeout_seconds': 2,
            }
            (root / 'spec.json').write_text(json.dumps(config))
            result = subprocess.run(
                [sys.executable, '-I', '-B', str(INSTALL / 'scripts/lint_runner.py'),
                 'spec.json'],
                cwd=root, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads((root / Path(result.stdout.strip())).read_text())
            self.assertEqual(summary['total'], 1)
            self.assertEqual(summary['passed'], 1)
            self.assertEqual(summary['rows']['1']['verdict'], 'PASS')


if __name__ == '__main__':
    unittest.main()
