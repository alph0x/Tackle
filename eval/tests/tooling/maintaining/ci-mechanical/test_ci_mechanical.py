"""Execute the named workflow block against isolated synthetic repositories."""
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
SCRIPT = ROOT / 'maintaining/ci_mechanical.py'

class MechanicalChecks(unittest.TestCase):
    def run_fixture(self, workflow, files=None):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ci = root / '.github/workflows/ci.yml'
            ci.parent.mkdir(parents=True)
            ci.write_text(workflow)
            for name, content in (files or {}).items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
            return subprocess.run(['python3', '-I', '-B', str(SCRIPT), '--repo', str(root)], capture_output=True, text=True)

    def test_named_block_runs_and_names_first_failure(self):
        workflow = 'steps:\n  - name: Run the documented mechanical release checks\n    run: |\n      set -eu\n      grep -q wanted eval/README.md\n      exit 7\n  - name: Other\n    run: exit 9\n'
        failure = self.run_fixture(workflow, {'eval/README.md': 'missing'})
        self.assertNotEqual(failure.returncode, 0)
        self.assertIn('eval/README.md', failure.stdout + failure.stderr)
        success = self.run_fixture(workflow.replace('      exit 7\n', ''), {'eval/README.md': 'wanted'})
        self.assertEqual(success.returncode, 0, success.stderr)

        prefix = 'steps:\n  - name: Run the documented mechanical release checks\n    run: |\n'
        cases = [
            ('continued command', 'printf "%s\\n" \\\n  expected\n', 0),
            ('successful exit', 'exit 0\n', 0),
            ('failing exit', 'printf "before\\n"\nexit 7\n', 7),
            ('shell state', 'value=retained\nprintf "%s\\n" "$value"\n', 0),
            ('stderr', 'printf "message\\n" >&2\n', 0),
        ]
        for name, body, status in cases:
            with self.subTest(name=name):
                direct = subprocess.run(['sh', '-c', 'set -eu\n' + body],
                                        capture_output=True, text=True)
                synthetic = prefix + ''.join('      ' + line + '\n' for line in body.splitlines())
                result = self.run_fixture(synthetic)
                self.assertEqual(direct.returncode, status)
                self.assertEqual(result.returncode, status)
                self.assertEqual(result.stdout, direct.stdout)
                if status:
                    self.assertEqual(result.stderr, direct.stderr +
                                     'ci_mechanical: failed (exit 7) at: exit 7\n')
                else:
                    self.assertEqual(result.stderr, direct.stderr)

    def test_missing_step_fails(self):
        self.assertNotEqual(self.run_fixture('steps:\n  - name: Other\n    run: echo ok\n').returncode, 0)
