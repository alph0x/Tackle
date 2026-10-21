"""Lint row 14's closed-record checks, through the shipped scripts/lint.py, on the complete `pass-full` fixture
workspace. Each planted defect prints exactly its diagnostic on row 14, and every other row stays silent on it
(the control arm). A workspace stamped before 10.2.0, or not stamped, needs no brief hash.
"""
import hashlib
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import test_lint_rows as base  # noqa: E402


def ident(kind, number):
    """A synthetic fixture id of the pass-full workspace, built so no source line spells one."""
    return '{}-{:02d}'.format(kind, number)


TA, TB = ident('T', 1), ident('T', 2)
DA, DB = ident('D', 1), ident('D', 2)
RECEIPT = '**Remains**: none\n'


class Workspace:
    def __init__(self, case):
        self.temp = tempfile.TemporaryDirectory(prefix='tackle-closed-row-')
        case.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'root'
        self.root.mkdir()
        base.materialize(self.root, 'pass-full')
        self.ws = self.root / 'docs/plans/demo'

    def read(self, name):
        return (self.ws / name).read_text(encoding='utf-8')

    def write(self, name, text):
        (self.ws / name).write_text(text, encoding='utf-8')

    def brief_sha(self, task=TA):
        return hashlib.sha256((self.ws / 'tasks/{}.md'.format(task)).read_bytes()).hexdigest()

    def report_line(self, line, task=TA):
        name = 'reports/{}-report.md'.format(task)
        text = self.read(name)
        assert text.count(RECEIPT) == 1, text
        self.write(name, text.replace(RECEIPT, line + '\n' + RECEIPT))

    def append_report(self, line, task=TA):
        name = 'reports/{}-report.md'.format(task)
        self.write(name, self.read(name) + line + '\n')

    def stamp(self, version):
        self.write('AGENTS.md', '# Agents\n\n**Methodology: Tackle {}**\n'.format(version))

    def change_brief(self, task=TA):
        name = 'tasks/{}.md'.format(task)
        self.write(name, self.read(name) + '\nAn edit after closure.\n')

    def rows(self, env=None):
        out = {}
        with mock.patch.dict(os.environ, env or {}):
            for number in range(1, 20):
                verdict, child = base.run_row(number, self.root, None)
                out[number] = (verdict, [line for line in child.stdout.decode().splitlines() if line])
        return out


class ClosedRecordRow(unittest.TestCase):
    def assert_only_14(self, ws, lines, env=None):
        result = ws.rows(env)
        failing = {n for n, (verdict, _) in result.items() if verdict != 'PASS'}
        self.assertEqual(failing, {14} if lines else set(), result)
        self.assertEqual(result[14][1], lines)

    def test_recorded_hash_of_the_unchanged_brief_passes(self):
        ws = Workspace(self)
        ws.stamp('10.2.0')
        ws.report_line('**Brief sha256**: ' + ws.brief_sha())
        self.assert_only_14(ws, [])

    def test_unstamped_and_older_workspaces_need_no_hash(self):
        for version in (None, '10.1.0', '9.9.9'):
            with self.subTest(version=version):
                ws = Workspace(self)
                if version:
                    ws.stamp(version)
                self.assert_only_14(ws, [])

    def test_missing_hash_on_a_new_stamp_is_reported(self):
        for version in ('10.2.0', '10.10.1', '11.0.0'):
            with self.subTest(version=version):
                ws = Workspace(self)
                ws.stamp(version)
                self.assert_only_14(ws, ['missing brief hash: ' + TA])

    def test_a_hash_inside_fenced_code_does_not_count(self):
        ws = Workspace(self)
        ws.stamp('10.2.0')
        ws.report_line('```text\n**Brief sha256**: ' + ws.brief_sha() + '\n```')
        self.assert_only_14(ws, ['missing brief hash: ' + TA])

    def test_changed_brief_is_reported(self):
        ws = Workspace(self)
        ws.report_line('**Brief sha256**: ' + ws.brief_sha())
        ws.change_brief()
        self.assert_only_14(ws, ['closed brief changed: ' + TA])

    def test_malformed_hash_is_reported(self):
        for value in ('A' * 64, 'a' * 63):
            with self.subTest(value=value):
                ws = Workspace(self)
                ws.report_line('**Brief sha256**: ' + value)
                self.assert_only_14(ws, ['malformed brief hash: ' + TA])

    def test_erratum_with_an_active_decision_governs(self):
        ws = Workspace(self)
        ws.report_line('**Brief sha256**: ' + ws.brief_sha())
        ws.change_brief()
        ws.append_report('**Brief erratum**: {} · sha256 {}'.format(DA, ws.brief_sha()))
        self.assert_only_14(ws, [])
        ws.change_brief()
        self.assert_only_14(ws, ['closed brief changed: ' + TA])

    def test_erratum_naming_an_inactive_decision_is_reported(self):
        for decision in (DB, ident('D', 9)):
            with self.subTest(decision=decision):
                ws = Workspace(self)
                ws.report_line('**Brief sha256**: ' + ws.brief_sha())
                ws.change_brief()
                ws.append_report('**Brief erratum**: {} · sha256 {}'.format(decision, ws.brief_sha()))
                self.assert_only_14(ws, ['erratum without decision: {} {}'.format(TA, decision)])

    def test_open_tasks_are_not_closed_records(self):
        ws = Workspace(self)
        ws.change_brief(TB)
        self.assert_only_14(ws, [])

    def test_no_sha256_tool_fails_the_row(self):
        ws = Workspace(self)
        ws.report_line('**Brief sha256**: ' + ws.brief_sha())
        bin_dir = Path(ws.temp.name) / 'nosha'
        bin_dir.mkdir()
        for tool in ('sh', 'awk', 'sed', 'grep', 'mktemp', 'rm', 'cat', 'tr', 'od', 'date', 'find', 'ls', 'wc', 'head', 'cut'):
            found = shutil.which(tool)
            if found:
                (bin_dir / tool).symlink_to(found)
        with mock.patch.dict(os.environ, {'PATH': str(bin_dir)}):
            verdict, child = base.run_row(14, ws.root, None)
        self.assertNotEqual(verdict, 'PASS')
        self.assertEqual([line for line in child.stdout.decode().splitlines() if line], ['row14: no sha256 tool'])


if __name__ == '__main__':
    unittest.main()
