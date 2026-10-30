"""Generated evidence must be accepted by the shipped lint consumer."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
SCRIPT = ROOT / 'maintaining/record_rows.py'
sys.path.insert(0, str(ROOT / 'eval/tests/product/lint/rows'))
import test_lint_rows as base

class RecordRows(unittest.TestCase):
    def invoke(self, brief, attempts, extra):
        args = ['python3', '-I', '-B', str(SCRIPT), '--brief', str(brief), '--task', 'T' + '-' + '01', '--run-id', 'run-1', '--attempts', str(attempts)] + extra
        return subprocess.run(args, capture_output=True, text=True)

    def test_generated_workspace_passes_lint_rows(self):
        for attempts, extra in ((0, ['--observed-absence', 'no corrections observed']), (1, ['--failure', 'missing marker', '--correction', 'add marker', '--validation-command', 'check', '--result', 'exit 1']), (2, ['--correction-event', json.dumps({'failure': 'missing marker', 'correction': 'add marker', 'validation_command': 'check', 'result': 'exit 1'}), '--correction-event', json.dumps({'failure': 'missing second marker', 'correction': 'add second marker', 'validation_command': 'check again', 'result': 'exit 1'})])):
            with self.subTest(attempts=attempts):
                self.check_workspace(attempts, extra)

    def check_workspace(self, attempts, extra):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            base.materialize(root, 'pass-full')
            shutil.copytree(ROOT / 'skills/tackle/scripts', root / 'skills/tackle/scripts')
            ws = root / 'docs/plans/demo'
            result = self.invoke(ws / ('tasks/T' + '-' + '01.md'), attempts, extra)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(result.stdout)
            (ws / 'resource-usage.md').write_text(data['resource_usage'])
            (ws / 'history.md').write_text((ws / 'history.md').read_text() + '\n' + data['event'])
            report = ws / ('reports/T' + '-' + '01-report.md')
            report.write_text(report.read_text().replace('**Remains**: none', data['closure_receipt']))
            for row in (10, 14, 16, 17):
                child = subprocess.run(['python3', '-I', '-B', 'skills/tackle/scripts/lint.py', '--row', str(row), 'demo'], cwd=root, capture_output=True, text=True)
                self.assertEqual(child.returncode, 0, (row, child.stdout, child.stderr))

    def test_evidence_is_required(self):
        with tempfile.TemporaryDirectory() as temp:
            brief = Path(temp) / 'brief.md'
            brief.write_text('brief')
            self.assertNotEqual(self.invoke(brief, 0, []).returncode, 0)
            self.assertNotEqual(self.invoke(brief, 1, []).returncode, 0)
