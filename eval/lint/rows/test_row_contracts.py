"""Rows 6, 11 and 16 on current workspaces: history chronology, a usage row for each Complete task, and the
lifecycle validity of `resource-usage.md`, including a pre-v2 table that a migration carried there.

Each test copies the row's command from `references/guides/lint-spec.md`, substitutes the slug, and runs it with
`sh` from a disposable root.
"""
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
LINT = (ROOT / 'references/guides/lint-spec.md').read_text()
BOARD = ('Schema: tackle-workspace/5\n\n| Task | What | Brief | Depends on | Status | Verification |\n'
         '|---|---|---|---|---|---|\n| T-A | Work | tasks/T-A.md | none | Complete | reports/T-A-report.md |\n')
HEADER = ('| Run ID | Event | Task | Role | Harness | Tier | Model | Effort | At | Outcome | Attempts | Rework | '
          'Verification | Source |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n')
CARRIED = ('| Point | Role | Tier | Model | Effort | Tokens in | Tokens out | Session |\n|---|---|---|---|---|---|---|---|\n'
           '| T-A | Driver | standard | model | high | n/a | n/a | old-session |\n')


def event(kind='start', *, run='run-1', task='T-A', role='Driver', attempts='n/a', rework='n/a'):
    return (f'| {run} | {kind} | {task} | {role} | harness | standard | model | n/a | n/a | observed | {attempts} | '
            f'{rework} | n/a | fixture |\n')


def literal_row(number):
    line = next(line for line in LINT.splitlines() if line.startswith(f'| {number} ·'))
    return line.split(' | `', 1)[1].rsplit('` |', 1)[0]


def run_row(number, files):
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        workspace = root / 'docs/plans/demo'
        workspace.mkdir(parents=True)
        for name, text in files.items():
            (workspace / name).parent.mkdir(parents=True, exist_ok=True)
            (workspace / name).write_text(text)
        return subprocess.run(['sh', '-c', literal_row(number).replace('<slug>', 'demo')], cwd=root,
                              capture_output=True, text=True, timeout=10)


class ChronologyRowTests(unittest.TestCase):
    def test_ordered_history_passes_and_reversed_or_newer_archive_or_missing_history_fails(self):
        valid = run_row(6, {'history.md': '## 2026-01-01 — start\n\n## 2026-01-02 — finish\n',
                            'history-archive.md': '## 2025-12-31 — archived\n'})
        invalid = run_row(6, {'history.md': '## 2026-01-02 — finish\n\n## 2026-01-01 — start\n',
                              'history-archive.md': '## 2026-01-01 — archived\n'})
        cross = run_row(6, {'history.md': '## 2026-01-01 — start\n\n## 2026-01-02 — finish\n',
                            'history-archive.md': '## 2026-01-03 — archived too late\n'})
        self.assertEqual((valid.returncode, valid.stdout), (0, ''))
        self.assertNotEqual(invalid.returncode, 0)
        self.assertIn('row6: out of order', invalid.stdout)
        self.assertNotEqual(cross.returncode, 0)
        self.assertIn('row6: archive newer than log oldest', cross.stdout)
        missing = run_row(6, {})
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn('row6: missing history.md', missing.stdout)


class UsageRowTests(unittest.TestCase):
    def test_a_complete_task_needs_a_usage_row_and_a_workspace_without_a_ledger_skips(self):
        ledger = '| Run ID | Event | Task | Role |\n|---|---|---|---|\n'
        valid = run_row(11, {'task-board.md': BOARD, 'resource-usage.md': ledger + '| run-1 | finish | T-A | Driver |\n'})
        self.assertEqual((valid.returncode, valid.stdout), (0, ''))
        skipped = run_row(11, {'task-board.md': BOARD})
        self.assertEqual((skipped.returncode, skipped.stdout), (0, ''))
        missing = run_row(11, {'task-board.md': BOARD, 'resource-usage.md': ledger + '| run | T-Z |\n'})
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn('row11: done task without usage row: T-A', missing.stdout)
        boardless = run_row(11, {'resource-usage.md': ledger + '| run | T-A |\n'})
        self.assertNotEqual(boardless.returncode, 0)
        self.assertIn('migrate first', boardless.stdout)


class LifecycleRowTests(unittest.TestCase):
    def check(self, body):
        return run_row(16, {'resource-usage.md': body})

    def assert_valid(self, body):
        result = self.check(body)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '', ''))

    def assert_invalid(self, body, diagnostic):
        result = self.check(body)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stderr, '')
        self.assertIn(diagnostic, result.stdout)
        return result

    def test_valid_invalid_and_malformed_ledgers_and_a_missing_one(self):
        self.assert_valid(HEADER + '# prose with no data row is valid and ignored\n'
                          + event(attempts='0', rework='0') + event('finish', attempts='1', rework='0')
                          + event(run='run-2', task='T-B', attempts='0', rework='0')
                          + event('observe-incomplete', run='run-2', task='T-B', attempts='0', rework='0'))
        invalid = self.assert_invalid(HEADER + event('finish', attempts='-1', rework='0')
                                      + event(task='T-B', attempts='0', rework='0')
                                      + event(attempts='0', rework='0'), 'terminal before start')
        self.assertIn('row16: line 3:', invalid.stdout)
        self.assertIn('Task/Role changed', invalid.stdout)
        malformed = self.assert_invalid(HEADER + event('checkpoint', run='run-unknown')
                                        + event(run='') + event(run='run-missing-task', task='')
                                        + event(run='run-missing-role', role='')
                                        + event(run='run-missing-count', attempts='')
                                        + '| truncated | start | T-A |\n', 'unknown Event')
        for message in ['missing Run ID', 'missing Task', 'missing Role',
                        'missing, invalid, or negative Attempts/Rework', 'malformed data row']:
            self.assertIn(message, malformed.stdout)
        missing = run_row(16, {})
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn('row16: missing resource-usage.md', missing.stdout)

    def test_a_carried_table_then_v2_keeps_unknowns_and_an_interrupted_run(self):
        self.assert_valid(CARRIED + '\nSchema: tackle-observability/2\n' + HEADER + event() + event('observe-incomplete'))

    def test_empty_negative_and_nonnumeric_counts_fail(self):
        for count in ('', '-1', 'unknown', '1.5', '1x'):
            for field in ('attempts', 'rework'):
                with self.subTest(count=count, field=field):
                    self.assert_invalid(HEADER + event(**{field: count}), 'Attempts/Rework')

    def test_an_orphan_terminal_after_a_carried_table_fails(self):
        self.assert_invalid(CARRIED + HEADER + event('finish'), 'terminal before start')

    def test_a_late_start_does_not_repair_history(self):
        self.assert_invalid(HEADER + event('finish') + event(), 'terminal before start')

    def test_duplicates_and_a_task_or_role_change_fail(self):
        for body, message in ((event() + event(), 'duplicate start'),
                              (event() + event('finish') + event('observe-incomplete'), 'duplicate terminal'),
                              (event() + event('finish', role='Checker'), 'Task/Role changed')):
            with self.subTest(message=message):
                self.assert_invalid(HEADER + body, message)

    def test_a_pre_v2_header_after_v2_cannot_hide_bad_events(self):
        result = self.assert_invalid(HEADER + event() + CARRIED + event('finish', run='orphan'), 'terminal before start')
        self.assertIn('legacy header after v2', result.stdout)

    def test_truncated_and_unknown_events_fail(self):
        self.assert_invalid(CARRIED + HEADER + '| run-x | start | T-A |\n', 'malformed data row')
        self.assert_invalid(HEADER + event('checkpoint'), 'unknown Event')


if __name__ == '__main__':
    unittest.main()
