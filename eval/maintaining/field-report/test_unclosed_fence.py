"""The field-report tool reports an unclosed fenced example as "n/a", never a truncated count.

A board whose illustrative fenced example never closes is refused by the same strict read the
schema-keyed migration recipes use, reused here as this stand-alone tool's own local copy. Detection
itself only ever takes that strict path while resolving a Schema-less `board.md` against the legacy
pre-3 shape; a `task-board.md` with a current `Schema:` line is read leniently for its own bucket, as
before. Loaded the way the sibling field-report suite loads the tool: the CLI end to end through
`subprocess`, and the pure functions directly for a unit-level check.
"""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / 'maintaining' / 'field_report.py'

OPEN_FENCE = '```\nan example that never closes its fence\n'


def run_cli(args):
    return subprocess.run([sys.executable, str(SCRIPT)] + [str(a) for a in args],
                          capture_output=True, text=True)


def broken_board_text():
    # A real header, delimiter and first row, readable on their own; the fence then opens and never
    # closes, with a second row after it that a version reading only up to the break would never see.
    return ('# Board\n\n| Point | Status |\n|---|---|\n| P-1 | Draft |\n' + OPEN_FENCE +
            '| P-2 | Draft |\n')


def broken_task_board_text():
    return ('# Task board\n\nSchema: tackle-workspace/4\n\n'
            '| Task | Status |\n|---|---|\n| T-1 | Draft |\n' + OPEN_FENCE +
            '| T-2 | Draft |\n')


class FieldReportUnitTests(unittest.TestCase):
    """Direct calls into the tool's own module, mirroring how the sibling census hygiene tests load
    census.py the same way."""

    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('fence_fixture_field_report', SCRIPT)
        cls.field_report = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.field_report)

    def test_count_tasks_raises_on_an_unclosed_fence(self):
        with self.assertRaisesRegex(ValueError, '^unclosed fenced example$'):
            self.field_report.count_tasks(broken_task_board_text())

    def test_detect_bucket_returns_unknown_alone_and_beside_a_valid_four(self):
        valid_four = ('# Task board\n\nSchema: tackle-workspace/4\n\n'
                     '| Task | Status |\n|---|---|\n| T-1 | Draft |\n')
        self.assertEqual(self.field_report.detect_bucket({'board.md': broken_board_text()}),
                         ('unknown', None))
        self.assertEqual(
            self.field_report.detect_bucket({'board.md': broken_board_text(), 'task-board.md': valid_four}),
            ('unknown', None))


class FieldReportEndToEndTests(unittest.TestCase):
    """The real CLI, over a temporary --plans workspace whose task-board.md holds the break."""

    def test_report_says_n_a_never_a_truncated_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            plans = Path(tmp) / 'plans'
            workspace = plans / 'fence-workspace'
            workspace.mkdir(parents=True)
            (workspace / 'task-board.md').write_text(broken_task_board_text(), encoding='utf-8')
            out = Path(tmp) / 'out'
            out.mkdir()
            json_path, md_path = out / 'r.json', out / 'r.md'
            child = run_cli(['--plans', plans, '--repo', ROOT, '--since', 'HEAD', '--until', 'HEAD',
                             '--json', json_path, '--markdown', md_path])
            self.assertEqual(child.returncode, 0, child.stderr)
            data = json.loads(json_path.read_text(encoding='utf-8'))
        ws = data['workspaces']['fence-workspace']
        expected_source = str(workspace / 'task-board.md')
        self.assertEqual(ws['tasks'], {'value': 'n/a', 'source': expected_source, 'unmapped': []})


if __name__ == '__main__':
    unittest.main()
