"""Rows 13 and 17 through the canonical rows: the session-entry budget and the post-task obligations.

Every case copies a fixture into a disposable root, or builds a variant of one, runs the row that the shipped
extractor takes from ``lint-spec.md``, and reads the verdict with the shipped ``lint_verdict``, under every AWK
this host has. No case reads a row's text or re-implements its logic; the only independent implementation here is
the deliberately naive "keyword" checker, which exists to show that the fixtures cannot be passed by it.
"""
import re
import shutil
import tempfile
import unittest
from pathlib import Path

import test_lint_rows as base

WS = 'docs/plans/' + base.SLUG
HISTORY = WS + '/history.md'
BOARD = 'task-board.md'
REPORT = 'reports/T-A-report.md'
SNAPSHOT_HEADING = '### State snapshot (record current state when appending; never edit an older snapshot)'


def entry(heading, total):
    """An entry of exactly `total` lines, heading included, with sub-headings and a State snapshot, no trailing blank.
    A short entry (under 20 lines) is the heading and plain bullets."""
    if total < 20:
        return [heading] + ['- Recorded routine observation %d.' % (index + 1) for index in range(total - 1)]
    head = [heading, '', '### Did', '']
    tail = ['', '### Next', '', '- Continue.', '', SNAPSHOT_HEADING, '- Task state: fixture.', '- In flight: none.',
            '- Blocked on: nothing.', '- Resume from: fixture.', '- Active obligations: none']
    filler = total - len(head) - len(tail)
    assert filler > 0, total
    lines = head + ['- Recorded routine observation %d.' % (index + 1) for index in range(filler)] + tail
    assert len(lines) == total and lines[-1].strip()
    return lines


def history_text(entries, gap=1, preamble=('# History', '')):
    """Entries joined by `gap` blank lines; returns the text and each entry's 1-based heading line."""
    lines, starts = list(preamble), []
    for number, one in enumerate(entries):
        starts.append(len(lines) + 1)
        lines += one
        if number != len(entries) - 1:
            lines += [''] * gap
    return '\n'.join(lines) + '\n', starts


class Workspace(unittest.TestCase):
    def workspace(self, fixture='pass-full', fixture_base=None):
        temporary = tempfile.TemporaryDirectory(prefix='tackle-obligations-')
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name) / 'root'
        root.mkdir()
        base.materialize(root, fixture, fixture_base)
        return root

    def read(self, root, relative):
        return (root / WS / relative).read_text(encoding='utf-8')

    def write(self, root, relative, text):
        path = root / WS / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')

    def observe(self, number, root):
        """[(awk name, verdict, output lines, child)] for every AWK this host has."""
        found = []
        for name, awk in base.awk_variants():
            verdict, child = base.run_row(number, root, awk)
            found.append((name, verdict, child.stdout.decode().splitlines(), child))
        return found

    def assert_row(self, number, root, verdict, case=''):
        """The row gives `verdict` under every AWK, and returns the output lines of the system AWK."""
        found = self.observe(number, root)
        for name, got, lines, child in found:
            with self.subTest(case=case, awk=name, row=number):
                self.assertEqual(got, verdict, (child.returncode, lines[:6], child.stderr[:300]))
        outputs = {tuple(lines) for _, _, lines, _ in found}
        self.assertEqual(len(outputs), 1, 'the AWKs disagree: %r' % (outputs,))
        return found[0][2]


class EntryBudgetTests(Workspace):
    def budget_root(self, entries, gap=1, budget=None, preamble=('# History', '')):
        root = self.workspace('pass-full')
        text, starts = history_text(entries, gap, preamble)
        self.write(root, 'history.md', text)
        if budget is not None:
            self.write(root, 'AGENTS.md', '# Agents\n\nHistory entry budget: %s\n' % budget)
        return root, starts

    def test_entries_at_or_under_the_budget_print_nothing(self):
        for total in (119, 120):
            root, _ = self.budget_root([entry('## 2026-09-23 · session 1', 8), entry('## 2026-09-24 · session 2', total)])
            self.assertEqual(self.assert_row(13, root, 'PASS', 'newest at %d' % total), [])

    def test_the_newest_entry_one_line_over_is_one_warning_naming_file_line_and_numbers(self):
        root, starts = self.budget_root([entry('## 2026-09-23 · session 1', 8), entry('## 2026-09-24 · session 2', 121)])
        lines = self.assert_row(13, root, 'WARN')
        self.assertEqual(len(lines), 1, lines)
        self.assertIn(HISTORY, lines[0])
        self.assertRegex(lines[0], r'\b%d\b' % starts[1])
        self.assertIn('121 > 120', lines[0])

    def test_an_older_entry_over_the_budget_is_reported_when_the_newest_is_short(self):
        root, starts = self.budget_root([entry('## 2026-09-23 · session 1', 121), entry('## 2026-09-24 · session 2', 9)])
        lines = self.assert_row(13, root, 'WARN')
        self.assertEqual(len(lines), 1, lines)
        self.assertRegex(lines[0], r'\b%d\b' % starts[0])
        self.assertIn('121 > 120', lines[0])

    def test_every_entry_over_the_budget_gets_its_own_line_in_file_order(self):
        root, starts = self.budget_root([entry('## 2026-09-22 · session 1', 125), entry('## 2026-09-23 · session 2', 30),
                                         entry('## 2026-09-24 · session 3', 140)])
        lines = self.assert_row(13, root, 'WARN')
        self.assertEqual(len(lines), 2, lines)
        self.assertRegex(lines[0], r'\b%d\b' % starts[0])
        self.assertIn('125 > 120', lines[0])
        self.assertRegex(lines[1], r'\b%d\b' % starts[2])
        self.assertIn('140 > 120', lines[1])

    def test_the_workspace_budget_overrides_the_default_in_both_directions(self):
        root, _ = self.budget_root([entry('## 2026-09-24 · session 1', 150)], budget=200)
        self.assertEqual(self.assert_row(13, root, 'PASS', 'raised'), [])
        root, _ = self.budget_root([entry('## 2026-09-24 · session 1', 201)], budget=200)
        self.assertIn('201 > 200', self.assert_row(13, root, 'WARN', 'raised and exceeded')[0])
        root, _ = self.budget_root([entry('## 2026-09-24 · session 1', 60)], budget=50)
        self.assertIn('60 > 50', self.assert_row(13, root, 'WARN', 'lowered')[0])

    def test_only_a_line_that_starts_with_the_override_text_overrides_the_default(self):
        for text in ('# Agents\n\n- History entry budget: 500\n', '# Agents\n\nSee `History entry budget: 500` below.\n',
                     '# Agents\n\nHistory entry budget: many\n'):
            root, _ = self.budget_root([entry('## 2026-09-24 · session 1', 130)])
            self.write(root, 'AGENTS.md', text)
            self.assertIn('130 > 120', self.assert_row(13, root, 'WARN', text)[0])

    def test_trailing_blank_lines_and_other_second_level_headings_bound_the_entry(self):
        root, _ = self.budget_root([entry('## 2026-09-23 · session 1', 120), entry('## 2026-09-24 · session 2', 10)], gap=15)
        self.assertEqual(self.assert_row(13, root, 'PASS', 'blank lines after an entry'), [])
        root, _ = self.budget_root([entry('## 2026-09-24 · session 1', 100)])
        with open(root / HISTORY, 'a', encoding='utf-8') as handle:
            handle.write('\n## Notes\n\n' + '\n'.join('- note %d' % number for number in range(1, 140)) + '\n')
        self.assertEqual(self.assert_row(13, root, 'PASS', 'a later heading that is not a session'), [])
        root, _ = self.budget_root([entry('## 2026-09-24 · session 1', 120)])
        with open(root / HISTORY, 'a', encoding='utf-8') as handle:
            handle.write('\n\n\n\n')
        self.assertEqual(self.assert_row(13, root, 'PASS', 'blank lines at the end of the file'), [])

    def test_text_before_the_first_session_entry_is_not_an_entry(self):
        preamble = ['# History', ''] + ['Archive policy line %d.' % number for number in range(1, 140)] + ['']
        root, _ = self.budget_root([entry('## 2026-09-24 · session 1', 30)], preamble=preamble)
        self.assertEqual(self.assert_row(13, root, 'PASS'), [])

    def test_the_archive_threshold_line_is_unchanged(self):
        root = self.workspace('fail-13', 'pass-full')
        self.assertEqual(self.assert_row(13, root, 'WARN'), [HISTORY + ' over archive threshold (3)'])
        text, starts = history_text([entry('## 2026-09-24 · session 1', 125)])
        self.write(root, 'history.md', text)
        self.write(root, 'AGENTS.md', '# Agents\n\nLog archive threshold: 100\n')
        lines = self.assert_row(13, root, 'WARN', 'both thresholds')
        self.assertEqual(lines[0], HISTORY + ' over archive threshold (100)')
        self.assertEqual(len(lines), 2, lines)
        self.assertIn('125 > 120', lines[1])

    def test_a_missing_history_is_an_explicit_error_not_a_finding_about_size(self):
        root = self.workspace('pass-full')
        (root / HISTORY).unlink()
        for name, verdict, lines, child in self.observe(13, root):
            with self.subTest(awk=name):
                self.assertEqual(verdict, 'ERROR', (child.returncode, lines, child.stderr))
                self.assertTrue(any('history.md' in line for line in lines), lines)
                self.assertNotIn('over archive threshold', ' '.join(lines))

    def test_the_description_sends_the_fix_to_run_under_the_policy_not_to_status(self):
        row = next(line for line in base.SPEC.read_text(encoding='utf-8').splitlines() if line.startswith('| 13 ·'))
        description = row.split(' | ', 2)[0]
        self.assertIn('RUN', description)
        self.assertIn('policy', description)
        self.assertNotIn('status.md', description)


def keyword_only(root):
    """A deliberately naive row 17 that looks for the keywords anywhere: an `Open` id must appear somewhere in
    history.md, and a Complete task's report must mention remains somewhere."""
    board = (root / WS / BOARD).read_text(encoding='utf-8')
    history = (root / HISTORY).read_text(encoding='utf-8')
    found = []
    for line in board.splitlines():
        cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
        if cells and re.match(r'O-\d\d', cells[0]) and 'Open' in cells and cells[0][:4] not in history:
            found.append(cells[0])
    for line in board.splitlines():
        cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
        if len(cells) > 5 and cells[0].startswith('T-') and 'Complete' in cells:
            report = root / WS / 'reports' / (cells[0] + '-report.md')
            if not report.is_file() or 'remains' not in report.read_text(encoding='utf-8').lower():
                found.append(cells[0])
    return found


def with_cell(board, identity, column, value):
    """The obligations row of `identity` with its `column`-th cell (0 is the first) replaced."""
    out = []
    for line in board.splitlines():
        cells = line.strip().strip('|').split('|')
        if cells and cells[0].strip() == identity:
            cells[column] = ' ' + value + ' '
            line = '|' + '|'.join(cells) + '|'
        out.append(line)
    return '\n'.join(out) + '\n'


class ObligationTests(Workspace):
    def obligations(self):
        return self.workspace('pass-obligations')

    def findings(self, root, fixture_name='', verdict='FAIL'):
        return self.assert_row(17, root, verdict, fixture_name)

    def test_clean_workspaces_pass_every_row_including_row_17(self):
        for fixture, fixture_base in (('pass-obligations', None), ('pass-full', None), ('pass-full-5', None),
                                      ('pass-lite', None)):
            root = self.workspace(fixture, fixture_base)
            for number in range(1, 18):
                self.assertEqual(self.assert_row(number, root, 'PASS', fixture), [], (fixture, number))

    def test_each_planted_defect_is_reported_with_the_id_the_brief_names(self):
        cases = (('fail-17', ['O-01']), ('fail-17b', ['O-02']), ('fail-17c', ['O-01']), ('fail-17d', ['O-03']),
                 ('fail-17e', ['Done']), ('fail-17f', ['T-A']), ('fail-17g', ['T-A']),
                 ('fail-17i', ['**O-01**', 'malformed']))
        for fixture, fragments in cases:
            root = self.workspace(fixture, 'pass-obligations')
            lines = self.findings(root, fixture)
            self.assertEqual(len(lines), 1, (fixture, lines))
            for fragment in fragments:
                self.assertIn(fragment, lines[0], fixture)
        root = self.workspace('fail-17h', 'pass-obligations')
        lines = self.findings(root, 'fail-17h')
        self.assertTrue(any('O-01 (T-A)' in line and 'malformed' in line for line in lines), lines)

    def test_every_row_of_the_obligations_table_is_registered_whatever_its_first_cell(self):
        # An Open row whose first cell is not exactly an id used to be skipped when the cell did not start with
        # the id: the newest snapshot says none and the receipt says none, so nothing else could flag it.
        for first in ('**O-01**', 'o-01', '[O-01](#o-01)', '`O-01`', '_O-01_', '(O-01)', '~~O-01~~', '- O-01', '# O-01',
                      'O1', 'OB-01', '01', '', 'Obligation 1', 'O-1', 'O-001', 'O-01 (T-A)'):
            root = self.workspace('fail-17i', 'pass-obligations')
            self.write(root, BOARD, with_cell(self.read(root, BOARD), '**O-01**', 0, first))
            lines = self.findings(root, repr(first))
            self.assertEqual(len(lines), 1, (first, lines))
            self.assertIn('malformed', lines[0], first)
            self.assertIn(first, lines[0], first)

    def test_a_decorated_id_is_reported_even_when_the_table_header_is_not_named_obligation(self):
        for first in ('**O-01**', 'o-01', '[O-01](#o-01)', '`O-01`'):
            root = self.workspace('fail-17i', 'pass-obligations')
            board = self.read(root, BOARD).replace('| Obligation | What |', '| ID | What |')
            self.write(root, BOARD, with_cell(board, '**O-01**', 0, first))
            lines = self.findings(root, 'header ID, first cell ' + first)
            self.assertEqual(len(lines), 1, (first, lines))
            self.assertIn('malformed', lines[0], first)

    def test_a_decorated_id_with_a_correct_snapshot_is_still_reported_as_malformed_first(self):
        root = self.workspace('fail-17i', 'pass-obligations')
        self.write(root, 'history.md', self.read(root, 'history.md').replace('- Active obligations: none',
                                                                             '- Active obligations: O-01'))
        lines = self.findings(root, 'bold id, snapshot names it')
        self.assertIn('malformed', lines[0])
        self.assertTrue(any('O-01' in line and 'no row' in line for line in lines[1:]), lines)

    def test_only_the_obligations_table_and_o_prefixed_rows_are_registered(self):
        root = self.obligations()
        board = self.read(root, BOARD)
        # A task whose id merely contains O-01, a second table after a blank line, and rows right after a heading.
        board = board.replace('| T-B | More work |', '| T-NO-01 | Boundary | tasks/T-NO-01.md | T-A | Draft | pending |\n| T-B | More work |')
        board += '\n| Symbol | Meaning |\n|---|---|\n| x | not an obligation |\n| open | still not one |\n'
        board = board.rstrip('\n') + '\n## Notes\n| Topic | Detail |\n|---|---|\n| first | row |\n'
        self.write(root, BOARD, board)
        self.assertEqual(self.findings(root, 'other tables and a boundary id', 'PASS'), [])
        root = self.obligations()
        self.write(root, BOARD, self.read(root, BOARD).rstrip('\n') + '\n## Notes\n| x | not a row |\n')
        self.assertEqual(self.findings(root, 'a heading ends the table', 'PASS'), [])

    def test_rows_below_the_templates_comment_line_are_still_part_of_the_table(self):
        root = self.workspace('fail-17i', 'pass-obligations')
        delimiter = '|---|---|---|---|---|---|---|\n'
        board = self.read(root, BOARD)
        self.assertEqual(board.count(delimiter), 1)
        board = board.replace(delimiter, delimiter + '<!-- Add O-NN rows only when an obligation outlives its task. -->\n')
        self.write(root, BOARD, with_cell(board, '**O-01**', 0, '01'))
        lines = self.findings(root, 'a malformed first cell below the comment line')
        self.assertEqual(len(lines), 1, lines)
        self.assertIn('malformed', lines[0])

    def test_the_board_is_read_the_way_rows_2_and_3_read_it_fenced_rows_included(self):
        root = self.obligations()
        fenced = '\n```markdown\n| O-09 | example | owner | never | Open | none | |\n```\n'
        self.write(root, BOARD, self.read(root, BOARD) + fenced)
        self.assertIn('O-09', ' '.join(self.findings(root, 'a fenced example row on the board')))

    def test_the_row_17_note_states_what_the_cell_registers_and_where_fences_are_skipped(self):
        note = next(line for line in base.SPEC.read_text(encoding='utf-8').splitlines() if line.startswith('- Row 17 reads'))
        flat = ' '.join(note.split())
        for phrase in ('headed `Obligation`', '`**O-01**`', 'reported as malformed', 'Reports and `history.md`', 'rows 2 and 3'):
            self.assertIn(phrase, flat)

    def test_a_keyword_only_checker_passes_what_the_row_reports(self):
        clean = self.obligations()
        self.assertEqual(keyword_only(clean), [])
        for fixture in ('fail-17', 'fail-17c', 'fail-17g'):
            root = self.workspace(fixture, 'pass-obligations')
            with self.subTest(fixture=fixture):
                self.assertEqual(keyword_only(root), [], 'the fixture must not be catchable by keywords alone')
                self.assertTrue(self.findings(root, fixture), 'the canonical row must report it')

    def test_a_malformed_first_cell_does_not_change_what_the_status_readers_report(self):
        clean, damaged = self.obligations(), self.workspace('fail-17h', 'pass-obligations')
        for number in (3, 8, 10, 11, 12, 14):
            before = [(name, verdict, lines) for name, verdict, lines, _ in self.observe(number, clean)]
            after = [(name, verdict, lines) for name, verdict, lines, _ in self.observe(number, damaged)]
            self.assertEqual(before, after, number)
            self.assertTrue(all(verdict == 'PASS' for _, verdict, _ in after), (number, after))

    def test_ids_in_prose_elsewhere_are_not_citations(self):
        root = self.obligations()
        self.write(root, 'reports/review-notes.md', '# Review notes\n\nWe considered O-07 and O-08 and left them.\n')
        self.write(root, REPORT, self.read(root, REPORT).replace('Reviewer: demo.',
                                                                   'Reviewer: demo. Compare O-09 in passing.'))
        text = self.read(root, 'history.md')
        self.write(root, 'history.md', text.replace('- Planned the work and opened O-01.',
                                                    '- Planned the work and opened O-01, and discussed O-06.'))
        self.write(root, 'plan.md', self.read(root, 'plan.md') + '\nNote: O-05 is a later idea.\n')
        self.assertEqual(self.findings(root, 'prose elsewhere', 'PASS'), [])

    def test_the_receipt_grammar_accepts_none_and_a_list_of_existing_ids_only(self):
        accepted = ('none', 'O-01', 'O-03', 'O-01, O-03', 'O-01,O-03', '  O-01  ')
        rejected = ('None', '', 'O-1', 'O-001', 'O-01 and O-03', 'O-01 (pending)', 'none, O-01', 'T-A', 'O-01;O-03')
        for value in accepted:
            root = self.obligations()
            self.write(root, REPORT, '# T-A report\n\n**Remains**: %s\n' % value)
            self.assertEqual(self.findings(root, 'accepted %r' % value, 'PASS'), [], value)
        for value in rejected:
            root = self.obligations()
            self.write(root, REPORT, '# T-A report\n\n**Remains**: %s\n' % value)
            self.assertTrue(self.findings(root, 'rejected %r' % value), value)
        for line in ('Remains: none', '**Remains** none', '**Remains:** none', '**remains**: none',
                     'Nothing remains: none', 'The task remains open.'):
            root = self.obligations()
            self.write(root, REPORT, '# T-A report\n\n%s\n' % line)
            self.assertIn('T-A', ' '.join(self.findings(root, 'not the field: %r' % line)), line)
        root = self.obligations()
        self.write(root, REPORT, '# T-A report\n\n- **Remains**: none\n\nLater text.\n')
        self.assertEqual(self.findings(root, 'bullet', 'PASS'), [])
        root = self.obligations()
        self.write(root, REPORT, '# T-A report\n\n**Remains**: none\n\nA later receipt.\n**Remains**: O-02\n')
        self.assertIn('O-02', ' '.join(self.findings(root, 'second receipt line')))

    def test_a_receipt_or_snapshot_inside_a_code_fence_is_not_read(self):
        root = self.obligations()
        self.write(root, REPORT, '# T-A report\n\n```text\n**Remains**: none\n```\n')
        self.assertIn('T-A', ' '.join(self.findings(root, 'fenced receipt')))
        root = self.obligations()
        text = self.read(root, 'history.md')
        fenced = '\n```markdown\n' + SNAPSHOT_HEADING + '\n- Active obligations: O-01, O-03\n```\n'
        self.write(root, 'history.md', text.replace('- Active obligations: O-01\n', '- Active obligations: none\n') + fenced)
        self.assertIn('O-01', ' '.join(self.findings(root, 'fenced snapshot')))

    def test_only_the_newest_snapshot_counts_and_it_needs_the_field(self):
        root = self.obligations()
        text = self.read(root, 'history.md')
        self.write(root, 'history.md', text.replace('- Active obligations: O-01\n', ''))
        self.assertIn('O-01', ' '.join(self.findings(root, 'snapshot without the field')))
        root = self.obligations()
        self.write(root, 'history.md', text.replace(SNAPSHOT_HEADING, '### Notes'))
        self.assertIn('O-01', ' '.join(self.findings(root, 'no snapshot at all')))
        root = self.obligations()
        self.write(root, 'history.md', text.replace('- Active obligations: O-01\n', '- Active obligations: none\n')
                   + '\n### Later notes\n- Active obligations: O-01\n')
        self.assertIn('O-01', ' '.join(self.findings(root, 'the line belongs to another section')))
        root = self.obligations()
        self.write(root, 'history.md', text.replace('- Active obligations: O-01\n',
                                                    '- Active obligations: none\n- Active obligations: O-01\n'))
        self.assertIn('O-01', ' '.join(self.findings(root, 'only the first field line is the field')))
        root = self.obligations()
        self.write(root, 'history.md', text.replace('- Active obligations: O-01\n',
                                                    '- Active obligations: O-01; the prose also names O-02\n'))
        self.assertIn('O-02', ' '.join(self.findings(root, 'unknown id in the snapshot line')))
        root = self.obligations()
        self.write(root, 'history.md', text.replace('- Active obligations: O-01\n', '- Active obligations: XO-01 and O-011\n'))
        self.assertIn('O-01', ' '.join(self.findings(root, 'ids need word boundaries')))
        root = self.obligations()
        self.write(root, 'history.md', text.replace('- Active obligations: O-01\n',
                                                    '- Active obligations: O-01, O-03 (closed since)\n'))
        self.assertEqual(self.findings(root, 'a closed id may still be named', 'PASS'), [])

    def test_state_tokens_and_references_follow_the_three_state_contract(self):
        board_state, board_ref = 4, 6
        for state, reference, verdict in (('Open', '', 'PASS'), ('Discharged', 'reports/T-A-report.md', 'PASS'),
                                          ('Withdrawn', 'verification-records/x/record.md', 'PASS'),
                                          ('Discharged', 'D-' + '07', 'PASS'), ('Withdrawn', 'notes.md', 'PASS'),
                                          ('Done', 'reports/T-A-report.md', 'FAIL'), ('open', '', 'FAIL'),
                                          ('', '', 'FAIL'), ('Discharged', '', 'FAIL'), ('Withdrawn', 'n/a', 'FAIL'),
                                          ('Discharged', '-', 'FAIL'), ('Discharged', 'done', 'FAIL')):
            root = self.obligations()
            board = with_cell(with_cell(self.read(root, BOARD), 'O-03', board_state, state), 'O-03', board_ref, reference)
            self.write(root, BOARD, board)
            if state == 'Open':
                self.write(root, 'history.md', self.read(root, 'history.md').replace(
                    '- Active obligations: O-01\n', '- Active obligations: O-01, O-03\n'))
            lines = self.findings(root, '%s/%s' % (state, reference), verdict)
            if verdict == 'FAIL':
                self.assertEqual(len(lines), 1, (state, reference, lines))
                self.assertIn('O-03', lines[0])

    def test_a_duplicate_id_and_a_missing_report_are_reported(self):
        root = self.obligations()
        board = self.read(root, BOARD)
        self.write(root, BOARD, board.rstrip('\n') + '\n| O-03 | Again | owner | later | Withdrawn | never | D-' + '09 |\n')
        self.assertIn('O-03', ' '.join(self.findings(root, 'duplicate id')))
        root = self.obligations()
        (root / WS / REPORT).unlink()
        self.assertIn('T-A', ' '.join(self.findings(root, 'no report')))

    def test_an_empty_obligations_table_and_a_workspace_without_one_are_equivalent(self):
        root = self.obligations()
        text = self.read(root, BOARD)
        kept = [line for line in text.splitlines() if not line.startswith('| O-')]
        self.write(root, BOARD, '\n'.join(kept) + '\n')
        self.write(root, 'history.md', self.read(root, 'history.md').replace('- Active obligations: O-01\n',
                                                                            '- Active obligations: none\n'))
        self.write(root, REPORT, '# T-A report\n\n**Remains**: none\n')
        self.assertEqual(self.findings(root, 'header only', 'PASS'), [])
        self.write(root, BOARD, text.split('<a id="obligations"></a>')[0])
        self.assertEqual(self.findings(root, 'no table', 'PASS'), [])

    def test_lite_workspaces_skip_and_older_or_malformed_workspaces_are_refused(self):
        root = self.obligations()
        self.write(root, 'plan.md', 'Gate: Lite\n' + self.read(root, 'plan.md'))
        self.write(root, REPORT, '# T-A report\n')
        self.assertEqual(self.findings(root, 'lite skip', 'PASS'), [])
        for fixture, fixture_base in (('refuse-4', 'pass-full'), ('refuse-3', None), ('refuse-pre3', None)):
            older = self.workspace(fixture, fixture_base)
            for name, verdict, lines, child in self.observe(17, older):
                with self.subTest(fixture=fixture, awk=name):
                    self.assertEqual(verdict, 'ERROR', (lines, child.stderr))
                    self.assertTrue(any('migrate first' in line and 'references/guides/migrate.md' in line
                                        for line in lines), lines)
        crlf = self.obligations()
        (crlf / WS / BOARD).write_bytes((crlf / WS / BOARD).read_bytes().replace(b'\n', b'\r\n'))
        for name, verdict, lines, child in self.observe(17, crlf):
            with self.subTest(awk=name):
                self.assertEqual(verdict, 'ERROR')
                self.assertTrue(any('with LF line endings' in line for line in lines), lines)
        missing = self.obligations()
        (missing / HISTORY).unlink()
        for name, verdict, lines, child in self.observe(17, missing):
            with self.subTest(awk=name):
                self.assertEqual(verdict, 'ERROR', (lines, child.stderr))
                self.assertTrue(any('history.md' in line for line in lines), lines)


if __name__ == '__main__':
    unittest.main()
