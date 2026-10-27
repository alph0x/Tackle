import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest


RECIPE = (Path(__file__).resolve().parents[5] / 'skills/tackle/scripts/evidence_capture.py').read_text()
DEFAULT = ['python3', '-m', 'unittest', 'discover', '-v']
PASS = "import unittest\nclass Sample(unittest.TestCase):\n def test_pass(self): pass\n"


class DefaultObservationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.workspace = self.root / 'workspace'
        self.workspace.mkdir()
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.log = self.root / 'wrapper.json'
        executable = shlex.quote(sys.executable)
        log = shlex.quote(str(self.log))
        wrapper = self.bin / 'python3'
        wrapper.write_text('#!/bin/sh\n' + executable + ' -I -c '
                           + shlex.quote('import json,sys; open(sys.argv[1], "w").write(json.dumps({"args": sys.argv[2:], "version": sys.version}))')
                           + ' ' + log + ' "$@"\nexec ' + executable + ' "$@"\n')
        wrapper.chmod(0o755)
        for name in ('module.py', 'test_module.py', 'SPEC.md'):
            (self.root / name).write_text('')

    def observe(self, *, recipe=RECIPE, env=None):
        script = self.root / 'recipe.py'
        script.write_text(recipe)
        child_env = os.environ.copy()
        child_env['PATH'] = str(self.bin) + os.pathsep + child_env.get('PATH', '')
        child_env.update(env or {})
        result = subprocess.run([sys.executable, '-I', str(script), str(self.workspace)],
                                cwd=self.root, env=child_env, capture_output=True, timeout=20)
        out = next((self.workspace / 'evidence').glob('validation-*'))
        record = json.loads((out / 'result.json').read_text())
        receipt = (out / 'receipt.md').read_text()
        payload = receipt.split('```json\n', 1)[1].split('\n```', 1)[0]
        self.assertEqual(json.loads(payload), record)
        return result, record

    def passing(self):
        (self.root / 'test_pass.py').write_text(PASS)

    def test_empty_suite(self):
        result, record = self.observe()
        self.assertEqual(result.returncode, 1)
        self.assertFalse(record['accepted'])

    def test_passing_suite(self):
        self.passing()
        result, record = self.observe()
        self.assertEqual(result.returncode, 0)
        self.assertTrue(record['accepted'])

    def test_mixed_suite(self):
        for name in ('a', 'z'):
            (self.root / ('test_' + name + '.py')).write_text(
                'import unittest\nfrom pathlib import Path\nclass Sample(unittest.TestCase):\n'
                + ' def test_pass(self): Path(' + repr(name) + ').write_text("seen")\n')
        (self.root / 'test_fail.py').write_text(
            'import unittest\nclass Sample(unittest.TestCase):\n def test_fail(self): self.fail()\n')
        result, record = self.observe()
        self.assertEqual(result.returncode, 1)
        self.assertFalse(record['accepted'])
        self.assertTrue((self.root / 'a').is_file())
        self.assertTrue((self.root / 'z').is_file())

    def test_printed_summary_spoofing(self):
        (self.root / 'test_module.py').write_text('print("Ran 3 tests\\nOK")\n')
        result, record = self.observe()
        self.assertEqual(result.returncode, 1)
        self.assertFalse(record['accepted'])

    def test_input_changed(self):
        (self.root / 'test_change.py').write_text(
            'import unittest\nfrom pathlib import Path\nclass Sample(unittest.TestCase):\n'
            ' def test_change(self): Path("module.py").write_text("changed")\n')
        result, record = self.observe()
        self.assertEqual(result.returncode, 1)
        self.assertFalse(record['accepted'])
        self.assertFalse(record['inputs_stable'])

    def test_artifact_missing(self):
        self.passing()
        result, record = self.observe(recipe=RECIPE.replace('artifacts = []', 'artifacts = ["missing"]'))
        self.assertEqual(result.returncode, 1)
        self.assertFalse(record['accepted'])
        self.assertFalse(record['artifacts_present'])

    def test_timeout(self):
        (self.root / 'test_sleep.py').write_text(
            'import unittest, time\nclass Sample(unittest.TestCase):\n def test_sleep(self): time.sleep(10)\n')
        result, record = self.observe(recipe=RECIPE.replace('timeout_seconds = 30', 'timeout_seconds = 2'))
        self.assertEqual(result.returncode, 1)
        self.assertFalse(record['accepted'])
        self.assertTrue(record['timeout'])

    def test_hostile_startup(self):
        self.passing()
        hostile = self.root / 'hostile'
        hostile.mkdir()
        marker = self.root / 'marker'
        (hostile / 'sitecustomize.py').write_text('from pathlib import Path\nPath(' + repr(str(marker)) + ').write_text("seen")\n')
        result, record = self.observe(env={'PYTHONPATH': str(hostile)})
        self.assertEqual(result.returncode, 0)
        self.assertTrue(record['accepted'])
        self.assertFalse(marker.exists())

    def test_honest_receipt(self):
        self.passing()
        result, record = self.observe()
        log = json.loads(self.log.read_text())
        self.assertEqual(result.returncode, 0)
        self.assertTrue(record['accepted'])
        self.assertEqual(record['argv'][0], 'python3')
        self.assertEqual(record['argv'][1:], log['args'])
        self.assertIn('-I', record['argv'])
        self.assertEqual(record['configured_argv'], DEFAULT)

    def test_child_runtime(self):
        self.passing()
        result, record = self.observe()
        self.assertEqual(result.returncode, 0)
        self.assertTrue(record['accepted'])
        self.assertEqual(json.loads(self.log.read_text())['version'], sys.version)

    def test_custom_command_unchanged(self):
        (self.root / 'child.py').write_text('pass\n')
        configured = [sys.executable, 'child.py']
        recipe = RECIPE.replace('argv = ["python3", "-m", "unittest", "discover", "-v"]', 'argv = ' + repr(configured))
        result, record = self.observe(recipe=recipe)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(record['accepted'])
        self.assertEqual(record['argv'], configured)
        self.assertNotIn('configured_argv', record)

    def test_configuration_lines(self):
        for line in ('argv = ["python3", "-m", "unittest", "discover", "-v"]',
                     'inputs = ["module.py", "test_module.py", "SPEC.md"]',
                     'artifacts = []', 'timeout_seconds = 30'):
            self.assertEqual(RECIPE.count(line), 1)


if __name__ == '__main__':
    unittest.main()
