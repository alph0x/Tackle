"""Execute the literal shipped Markdown recipe with controlled child processes."""
import hashlib
import json
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]
RECIPE = (REPO / 'references/guides/evidence-capture.md').read_text().split('```python\n', 1)[1].split('\n```', 1)[0]


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
                result = subprocess.run([sys.executable, '-c', script], cwd=root, capture_output=True, timeout=8)
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


if __name__ == '__main__':
    unittest.main()
