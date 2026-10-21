"""Closed-record hardening, through the shipped scripts/lint.py on the complete `pass-full` fixture workspace:
row 7 skips a seal inside a closed brief and still fails the same seal in an open brief; row 14 catches a baseline
rewritten after closure by comparing it with the first `Brief sha256 <task>: <hash>` line of history (archive first,
fenced lines ignored), accepts only the exact erratum form, and stays silent without a history line. Each planted
defect fails only its row (the control arm is every other row). Every workspace-shaped id is built at runtime.
"""
import hashlib
import os
from pathlib import Path
import re
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
DA, DB, DC = ident('D', 1), ident('D', 2), ident('D', 9)
RECEIPT = '**Remains**: none\n'
SUPERSEDED_SEAL = '\n<!-- SEALED: {} -->\n'.format(DB)    # DB is a superseded decision in the fixture
MISSING_SEAL = '\n<!-- SEALED: {} -->\n'.format(DC)       # DC has no heading in the fixture
MIDDLE_DOT = '·'


class Workspace:
    def __init__(self, case):
        self.temp = tempfile.TemporaryDirectory(prefix='tackle-closed-hardening-')
        case.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'root'
        self.root.mkdir()
        base.materialize(self.root, 'pass-full')
        self.ws = self.root / 'docs/plans/demo'

    def read(self, name):
        return (self.ws / name).read_text(encoding='utf-8')

    def write(self, name, text):
        (self.ws / name).write_text(text, encoding='utf-8')

    def append(self, name, text):
        self.write(name, self.read(name) + text)

    def brief_sha(self, task=TA):
        return hashlib.sha256((self.ws / 'tasks/{}.md'.format(task)).read_bytes()).hexdigest()

    def report_line(self, line, task=TA):
        name = 'reports/{}-report.md'.format(task)
        text = self.read(name)
        assert text.count(RECEIPT) == 1, text
        self.write(name, text.replace(RECEIPT, line + '\n' + RECEIPT))

    def baseline(self, history=True, task=TA):
        """Closure's two lines: the report's baseline and history's protected copy."""
        digest = self.brief_sha(task)
        self.report_line('**Brief sha256**: ' + digest, task)
        if history:
            self.append('history.md', 'Brief sha256 {}: {}\n'.format(task, digest))
        return digest

    def edit_brief(self, task=TA):
        self.append('tasks/{}.md'.format(task), '\nAn edit after closure.\n')

    def rewrite_baseline(self, task=TA):
        """The attack: edit the closed brief, then make the report's baseline match the edit."""
        self.edit_brief(task)
        name = 'reports/{}-report.md'.format(task)
        digest = self.brief_sha(task)
        self.write(name, re.sub(r'(\*\*Brief sha256\*\*: )[0-9a-f]{64}', lambda m: m.group(1) + digest, self.read(name)))

    def set_status(self, status, task=TA):
        board = self.read('task-board.md')
        self.write('task-board.md', re.sub(r'(\| %s \|.*\| )Complete( \|)' % task, lambda m: m.group(1) + status + m.group(2), board))

    def stamp(self, version):
        self.write('AGENTS.md', '# Agents\n\n**Methodology: Tackle {}**\n'.format(version))

    def rows(self):
        out = {}
        for number in range(1, 20):
            verdict, child = base.run_row(number, self.root, None)
            out[number] = (verdict, [line for line in child.stdout.decode().splitlines() if line])
        return out


class Rows(unittest.TestCase):
    def only(self, ws, row, lines):
        """Exactly `row` fails and prints exactly `lines`; with no lines every row is silent."""
        result = ws.rows()
        failing = {n for n, (verdict, _) in result.items() if verdict != 'PASS'}
        self.assertEqual(failing, {row} if lines else set(), result)
        if lines:
            self.assertEqual(result[row][1], lines)
        self.assertEqual({n: l for n, (_, l) in result.items() if l and n != row}, {}, result)


class ClosedSealExemption(Rows):
    def test_a_superseded_or_missing_seal_in_a_closed_brief_is_silent(self):
        for seal in (SUPERSEDED_SEAL, MISSING_SEAL):
            for status in ('Complete', 'Skipped', 'Unverifiable'):
                with self.subTest(seal=seal.strip(), status=status):
                    ws = Workspace(self)
                    ws.set_status(status)
                    ws.append('tasks/{}.md'.format(TA), seal)
                    if status == 'Complete':
                        self.only(ws, 7, [])
                    else:   # row 2 reports the open task that depends on the Skipped or Unverifiable one; row 7 stays silent
                        result = ws.rows()
                        self.assertEqual(result[7][1], [])
                        self.assertLessEqual({n for n, (v, _) in result.items() if v != 'PASS'}, {2}, result)

    def test_the_same_seal_in_an_open_brief_still_fails(self):
        for seal, line in ((SUPERSEDED_SEAL, 'superseded seal: ' + DB), (MISSING_SEAL, 'missing seal: ' + DC)):
            with self.subTest(seal=seal.strip()):
                ws = Workspace(self)
                ws.append('tasks/{}.md'.format(TB), seal)
                self.only(ws, 7, [line])

    def test_open_statuses_do_not_exempt_a_brief(self):
        for status in ('Draft', 'Ready to run', 'In progress', 'Checking', 'Blocked'):
            with self.subTest(status=status):
                ws = Workspace(self)
                ws.set_status('Draft')
                ws.append('tasks/{}.md'.format(TA), SUPERSEDED_SEAL)
                ws.write('task-board.md', re.sub(r'(\| %s \|.*\| )Draft( \|)' % TA, lambda m: m.group(1) + status + m.group(2), ws.read('task-board.md')))
                self.assertEqual(ws.rows()[7][1], ['superseded seal: ' + DB])

    def test_closed_and_open_briefs_together_report_only_the_open_one(self):
        ws = Workspace(self)
        ws.append('tasks/{}.md'.format(TA), SUPERSEDED_SEAL)
        ws.append('tasks/{}.md'.format(TB), MISSING_SEAL)
        self.only(ws, 7, ['missing seal: ' + DC])

    def test_the_design_contract_is_never_exempt(self):
        ws = Workspace(self)
        ws.append('design-contract.md', MISSING_SEAL)
        self.only(ws, 7, ['missing seal: ' + DC])

    def test_a_brief_the_board_does_not_name_is_read_as_open(self):
        ws = Workspace(self)
        ws.write('task-board.md', re.sub(r'\| %s \|[^\n]*\n' % TA, '', ws.read('task-board.md')))
        ws.append('tasks/{}.md'.format(TA), SUPERSEDED_SEAL)
        self.assertEqual(ws.rows()[7][1], ['superseded seal: ' + DB])

    def test_a_brief_named_by_a_closed_row_and_an_open_row_stays_checked(self):
        for status in ('Draft', 'In progress'):
            with self.subTest(status=status):
                ws = Workspace(self)
                board = ws.read('task-board.md')
                ws.write('task-board.md', re.sub(r'(\| %s \| [^|]*\| )tasks/%s.md' % (TB, TB), lambda m: m.group(1) + 'tasks/{}.md'.format(TA), board))
                ws.append('tasks/{}.md'.format(TA), SUPERSEDED_SEAL)
                self.assertIn('tasks/{}.md'.format(TA), ws.read('task-board.md').split(TB)[1])
                self.assertEqual(ws.rows()[7][1], ['superseded seal: ' + DB])

    def test_a_lite_plan_is_still_checked_beside_closed_briefs(self):
        ws = Workspace(self)
        ws.write('plan.md', 'Gate: Lite\n\n<!-- SEALED: {} -->\n'.format(DC))
        ws.append('tasks/{}.md'.format(TA), SUPERSEDED_SEAL)
        result = ws.rows()
        self.assertEqual(result[7][1], ['missing seal: ' + DC])


class ProtectedBaseline(Rows):
    def test_an_unchanged_baseline_with_its_history_line_is_silent(self):
        ws = Workspace(self)
        ws.baseline()
        ws.stamp('10.2.0')
        self.only(ws, 14, [])

    def test_a_baseline_rewritten_to_match_an_edited_brief_fails(self):
        ws = Workspace(self)
        ws.baseline()
        ws.rewrite_baseline()
        self.only(ws, 14, ['rewritten brief hash: ' + TA])

    def test_without_the_history_line_the_same_rewrite_is_silent(self):
        ws = Workspace(self)
        ws.baseline(history=False)
        ws.rewrite_baseline()
        self.only(ws, 14, [])

    def test_an_edit_that_leaves_the_baseline_is_changed_not_rewritten(self):
        ws = Workspace(self)
        ws.baseline()
        ws.edit_brief()
        self.only(ws, 14, ['closed brief changed: ' + TA])

    def test_an_edit_with_a_rewritten_baseline_and_an_unauthorized_erratum_prints_both_in_order(self):
        ws = Workspace(self)
        ws.baseline()
        ws.rewrite_baseline()
        ws.edit_brief()
        ws.append('reports/{}-report.md'.format(TA), '**Brief erratum**: {} {} sha256 {}\n'.format(DC, MIDDLE_DOT, ws.brief_sha()))
        self.assertEqual(ws.rows()[14][1], ['rewritten brief hash: ' + TA, 'erratum without decision: {} {}'.format(TA, DC)])

    def test_a_valid_erratum_chain_beside_an_untouched_baseline_is_silent(self):
        ws = Workspace(self)
        ws.baseline()
        ws.edit_brief()
        ws.append('reports/{}-report.md'.format(TA), '**Brief erratum**: {} {} sha256 {}\n'.format(DA, MIDDLE_DOT, ws.brief_sha()))
        self.only(ws, 14, [])

    def test_history_in_the_archive_alone_protects_the_baseline(self):
        ws = Workspace(self)
        digest = ws.baseline(history=False)
        ws.write('history-archive.md', '# Archive\n\n## 2026-09-22 session 1\n\n- Closed.\nBrief sha256 {}: {}\n'.format(TA, digest))
        self.only(ws, 14, [])
        ws.rewrite_baseline()
        self.only(ws, 14, ['rewritten brief hash: ' + TA])

    def test_history_lines_inside_fenced_code_are_ignored(self):
        ws = Workspace(self)
        digest = ws.baseline(history=False)
        ws.append('history.md', '\n```text\nBrief sha256 {}: {}\n```\n'.format(TA, digest))
        ws.rewrite_baseline()
        self.only(ws, 14, [])

    def test_the_first_history_value_counts_so_a_later_line_cannot_bless_a_rewrite(self):
        ws = Workspace(self)
        ws.baseline()
        ws.rewrite_baseline()
        ws.append('history.md', 'Brief sha256 {}: {}\n'.format(TA, ws.brief_sha()))
        self.only(ws, 14, ['rewritten brief hash: ' + TA])

    def test_the_bullet_prefixes_of_the_history_line_are_read(self):
        for prefix in ('- ', '* '):
            with self.subTest(prefix=prefix):
                ws = Workspace(self)
                digest = ws.baseline(history=False)
                ws.append('history.md', '{}Brief sha256 {}: {}\n'.format(prefix, TA, digest))
                ws.rewrite_baseline()
                self.only(ws, 14, ['rewritten brief hash: ' + TA])

    def test_a_malformed_or_crlf_history_value_is_a_malformed_hash(self):
        digest = Workspace(self).brief_sha()
        for value in (digest[:63], digest.upper(), digest + ' ok', digest + '\r'):
            with self.subTest(value=value):
                ws = Workspace(self)
                ws.baseline(history=False)
                ws.append('history.md', 'Brief sha256 {}: {}\n'.format(TA, value))
                self.only(ws, 14, ['malformed brief hash: ' + TA])

    def test_history_lines_of_another_task_do_not_count(self):
        ws = Workspace(self)
        ws.baseline(history=False)
        ws.append('history.md', 'Brief sha256 {}: {}\n'.format(TB, 'a' * 64))
        ws.rewrite_baseline()
        self.only(ws, 14, [])

    def delete_baseline(self, ws):
        name = 'reports/{}-report.md'.format(TA)
        ws.write(name, re.sub(r'\*\*Brief sha256\*\*: [0-9a-f]{64}\n\n?', '', ws.read(name)))

    def test_a_deleted_baseline_is_a_removed_baseline_whatever_the_stamp(self):
        for version in (None, '10.1.0', '10.2.0'):
            with self.subTest(version=version):
                ws = Workspace(self)
                ws.baseline()
                self.delete_baseline(ws)
                if version:
                    ws.stamp(version)
                self.only(ws, 14, ['rewritten brief hash: ' + TA])

    def test_a_baseline_moved_into_a_fence_is_a_removed_baseline(self):
        ws = Workspace(self)
        digest = ws.baseline()
        self.delete_baseline(ws)
        ws.append('reports/{}-report.md'.format(TA), '\n```text\n**Brief sha256**: {}\n```\n'.format(digest))
        self.only(ws, 14, ['rewritten brief hash: ' + TA])

    def test_a_removed_baseline_still_compares_the_brief_with_the_history_value(self):
        ws = Workspace(self)
        ws.baseline()
        self.delete_baseline(ws)
        ws.edit_brief()
        self.only(ws, 14, ['closed brief changed: ' + TA, 'rewritten brief hash: ' + TA])

    def test_a_removed_baseline_with_a_valid_erratum_chain_is_only_rewritten(self):
        ws = Workspace(self)
        ws.baseline()
        self.delete_baseline(ws)
        ws.edit_brief()
        ws.append('reports/{}-report.md'.format(TA), '**Brief erratum**: {} {} sha256 {}\n'.format(DA, MIDDLE_DOT, ws.brief_sha()))
        self.only(ws, 14, ['rewritten brief hash: ' + TA])

    def test_a_report_without_a_baseline_and_without_a_history_value_is_missing(self):
        ws = Workspace(self)
        ws.stamp('10.2.0')
        self.only(ws, 14, ['missing brief hash: ' + TA])
        ws.append('history.md', 'Brief sha256 {}: {}\n'.format(TB, 'a' * 64))
        self.only(ws, 14, ['missing brief hash: ' + TA])

    def test_a_wrong_first_history_value_is_repaired_by_the_baseline_and_an_erratum(self):
        ws = Workspace(self)
        wrong = 'a' * 64
        ws.report_line('**Brief sha256**: ' + wrong)
        ws.append('history.md', 'Brief sha256 {}: {}\n'.format(TA, wrong))
        self.only(ws, 14, ['closed brief changed: ' + TA])
        ws.append('reports/{}-report.md'.format(TA), '**Brief erratum**: {} {} sha256 {}\n'.format(DA, MIDDLE_DOT, ws.brief_sha()))
        self.only(ws, 14, [])
        # a baseline that does not match the wrong history value is still a rewrite
        name = 'reports/{}-report.md'.format(TA)
        ws.write(name, ws.read(name).replace(wrong, ws.brief_sha()))
        self.only(ws, 14, ['rewritten brief hash: ' + TA])


class StrictErratum(Rows):
    def erratum_case(self, text, lines):
        ws = Workspace(self)
        ws.baseline()
        ws.edit_brief()
        ws.append('reports/{}-report.md'.format(TA), text.format(DA, MIDDLE_DOT, ws.brief_sha()) + '\n')
        self.only(ws, 14, lines)

    def test_the_exact_form_is_accepted_with_any_blanks_between_fields(self):
        self.erratum_case('**Brief erratum**: {0} {1} sha256 {2}', [])
        self.erratum_case('**Brief erratum**:   {0}   {1}  sha256    {2}', [])

    def test_every_other_form_is_a_malformed_hash(self):
        bad = ('**Brief erratum**: {0} sha256 {2}',                       # no separator
               '**Brief erratum**: {0} - sha256 {2}',                     # ascii hyphen
               '**Brief erratum**: {0} . sha256 {2}',                     # ascii dot
               '**Brief erratum**: {0} {1} {1} sha256 {2}',               # two dots
               '**Brief erratum**: see {0} {1} sha256 {2}',               # words before
               '**Brief erratum**: {0} {1} sha256 {2} ok',                # words after
               '**Brief erratum**: {0} {1} sha1 {2}',                     # wrong keyword
               '**Brief erratum**: {0} {1} sha256 {2}`',                  # stray backtick
               '**Brief erratum**: {0} {1} sha256 {2}\r')                 # CRLF line
        for text in bad:
            with self.subTest(line=text):
                self.erratum_case(text, ['malformed brief hash: ' + TA])

    def test_a_malformed_erratum_inside_fenced_code_is_ignored(self):
        ws = Workspace(self)
        ws.baseline()
        ws.edit_brief()
        digest = ws.brief_sha()
        ws.append('reports/{}-report.md'.format(TA), '**Brief erratum**: {} {} sha256 {}\n\n```text\n**Brief erratum**: {} sha256 {}\n```\n'.format(DA, MIDDLE_DOT, digest, DA, digest))
        self.only(ws, 14, [])

    def test_a_crlf_baseline_line_is_a_malformed_hash(self):
        ws = Workspace(self)
        ws.report_line('**Brief sha256**: ' + ws.brief_sha() + '\r')
        self.only(ws, 14, ['malformed brief hash: ' + TA])


if __name__ == '__main__':
    unittest.main()
