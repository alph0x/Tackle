"""History bounds and post-task obligations in the shipped templates and guides.

A scaffold copies the AGENTS template, so its policy line is what every new workspace carries; the board template
supplies the obligations table that row 17 reads; the retro template's recipes run against fixture histories; and
every document that states how many lint rows exist agrees with the lint spec. Text checks protect wording and
structure only: they do not show that an agent obeys the policy.
"""
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import test_template_drift as drift

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from maintaining.install_root import current_root  # noqa: E402

INSTALL = current_root(ROOT)
REF = INSTALL / 'references'
GUIDES = REF / 'guides'


def text(path):
    return Path(path).read_text(encoding='utf-8')


def one_line(value):
    return ' '.join(value.split())


class ScaffoldPolicyTests(unittest.TestCase):
    def scaffolded(self):
        temporary = tempfile.TemporaryDirectory(prefix='tackle-policy-')
        self.addCleanup(temporary.cleanup)
        workspace = Path(temporary.name) / 'docs/plans/demo'
        workspace.mkdir(parents=True)
        _, names = drift.scaffold_names()
        for name in names:
            shutil.copyfile(REF / name.replace('.md', '.tmpl.md'), workspace / name)
        return workspace

    def policy_line(self, workspace):
        lines = [line for line in text(workspace / 'AGENTS.md').splitlines() if 'History maintenance policy' in line]
        self.assertEqual(len(lines), 1, lines)
        return lines[0]

    def test_the_scaffolded_agents_file_carries_one_policy_line_naming_trigger_paths_retention_and_recovery(self):
        line = one_line(self.policy_line(self.scaffolded()))
        for phrase, why in (('over the archive threshold', 'trigger'), ('RUN session boundary', 'trigger'),
                            ('`history.md`', 'path'), ('`history-archive.md`', 'path'), ('verbatim', 'archive form'),
                            ('newest five', 'retained sessions'), ('context-lifecycle.md', 'recovery'),
                            ('STATUS never archives', 'authority')):
            self.assertIn(phrase, line, why)

    def test_the_policy_and_the_row_description_state_the_same_threshold_and_budget(self):
        line = one_line(self.policy_line(self.scaffolded()))
        row = next(l for l in text(GUIDES / 'lint-spec.md').splitlines() if l.startswith('| 13 ·')).split(' | ', 2)[0]
        for number in ('400', '120'):
            self.assertIn(number, line)
            self.assertIn(number, row)
        self.assertIn('History entry budget', row)
        self.assertIn('Log archive threshold', row)

    def test_the_policy_text_is_not_mistaken_for_the_workspace_overrides(self):
        agents = text(self.scaffolded() / 'AGENTS.md')
        self.assertEqual([line for line in agents.splitlines() if line.startswith('History entry budget:')], [])
        self.assertEqual([line for line in agents.splitlines() if line.startswith('Log archive threshold:')], [])

    def test_plan_section_10_points_at_the_workspace_policy_instead_of_restating_it(self):
        section = text(REF / 'plan.tmpl.md').split('## 10. Working context and maintenance', 1)[1].split('\n## ', 1)[0]
        flat = one_line(section)
        self.assertIn('AGENTS.md', flat)
        self.assertIn('policy', flat)
        self.assertNotIn('newest five', flat)


class BoardAndHistoryTemplateTests(unittest.TestCase):
    def test_the_board_template_adds_an_obligations_table_after_the_task_table(self):
        board = text(REF / 'task-board.tmpl.md')
        tables = re.findall(r'^\| (.*) \|\n\|[-| ]+\|$', board, re.M)
        self.assertEqual(len(tables), 2, tables)
        tasks, obligations = [[cell.strip() for cell in header.split(' | ')] for header in tables]
        self.assertEqual(tasks[0], 'Task')
        self.assertEqual(obligations[0], 'Obligation')
        for name in ('Owner', 'Trigger', 'Discharge check', 'State', 'Reference'):
            self.assertIn(name, obligations)
        self.assertNotIn('Status', obligations)
        self.assertLess(board.index('| Task |'), board.index('| Obligation |'))
        section = board.split('<a id="obligations"></a>', 1)[1]
        self.assertEqual([line for line in section.splitlines() if re.match(r'^\| O-', line)], [])
        for phrase in ('Open', 'Discharged', 'Withdrawn', 'O-NN', 'Active obligations', '**Remains**'):
            self.assertIn(phrase, section)
        self.assertIn('Schema: tackle-workspace/5', board)

    def test_the_status_column_of_the_task_table_keeps_the_position_the_readers_expect(self):
        board = text(REF / 'task-board.tmpl.md')
        header = re.search(r'^\| Task \|.*\|$', board, re.M)[0]
        self.assertEqual([cell.strip() for cell in header.strip('|').split('|')].index('Status'), 4)
        obligations = re.search(r'^\| Obligation \|.*\|$', board, re.M)[0]
        self.assertEqual([cell.strip() for cell in obligations.strip('|').split('|')].index('State'), 4)

    def test_the_history_template_asks_the_snapshot_for_every_open_id_and_states_the_entry_budget(self):
        history = text(REF / 'history.tmpl.md')
        line = next(l for l in history.splitlines() if l.startswith('- Active obligations:'))
        for phrase in ('Open', 'O-NN', 'none'):
            self.assertIn(phrase, line)
        self.assertIn('History entry budget', history)
        self.assertIn('120', history)


class RetroRecipeTests(unittest.TestCase):
    def cell(self, label):
        template = text(REF / 'retro.tmpl.md')
        return template.split('| ' + label + ' | `', 1)[1].split('`', 1)[0]

    def row(self, label):
        return next(l for l in text(REF / 'retro.tmpl.md').splitlines() if l.startswith('| ' + label + ' |')
                    or l.startswith('| **' + label + '** |'))

    def test_the_history_growth_recipe_counts_lines_per_entry_over_the_archive_then_the_history(self):
        command = self.cell('History growth')
        with tempfile.TemporaryDirectory(prefix='tackle-growth-') as temporary:
            root = Path(temporary)

            def entries(*sizes, blank_after=0):
                lines = ['# File', '']
                for number, size in enumerate(sizes):
                    lines += ['## 2026-09-%02d · session %d' % (number + 1, number + 1)] + ['- line'] * (size - 1)
                    lines += [''] * (blank_after if number != len(sizes) - 1 else 2)
                return '\n'.join(lines) + '\n'

            (root / 'history-archive.md').write_text(entries(5, 7), encoding='utf-8')
            (root / 'history.md').write_text(entries(3, 9, blank_after=4), encoding='utf-8')
            child = subprocess.run(['sh', '-c', command], cwd=root, capture_output=True, text=True, timeout=30)
            self.assertEqual((child.returncode, child.stderr), (0, ''))
            lines = child.stdout.splitlines()
            self.assertEqual([int(re.search(r'(\d+) lines', l)[1]) for l in lines], [5, 7, 3, 9], lines)
            self.assertEqual([l.split(':', 1)[0] for l in lines], ['history-archive.md'] * 2 + ['history.md'] * 2)
            (root / 'history-archive.md').unlink()
            child = subprocess.run(['sh', '-c', command], cwd=root, capture_output=True, text=True, timeout=30)
            self.assertEqual((child.returncode, child.stderr), (0, ''))
            self.assertEqual([int(re.search(r'(\d+) lines', l)[1]) for l in child.stdout.splitlines()], [3, 9])

    def test_the_new_row_renders_as_a_table_row_without_a_pipe_inside_its_code(self):
        line = self.row('History growth')
        self.assertEqual(len(re.split(r'(?<!\\)\|', line)), 5)
        for span in re.findall(r'`([^`]*)`', line):
            self.assertNotIn('|', span)

    def test_the_attempt_recipe_and_the_retro_guide_cite_the_cap_of_three_not_a_workspace_line(self):
        row = self.row('Attempts over budget')
        retro = text(GUIDES / 'retro.md')
        bullet = next(l for l in retro.splitlines() if l.startswith('- **Attempts over budget**'))
        for where, value in (('template row', row), ('guide bullet', bullet)):
            self.assertIn('three', value, where)
            self.assertNotIn('AGENTS.md', value, where)
            self.assertNotIn('Default loop budget', value, where)
        growth = next(l for l in retro.splitlines() if l.startswith('- **History growth**'))
        self.assertIn('history-archive.md', growth)
        self.assertIn('retro.tmpl.md', growth)
        self.assertIn('At most three failed correction-validation cycles per task', one_line(text(GUIDES / 'run-card.md')))


class CountAgreementTests(unittest.TestCase):
    WORDS = {17: 'seventeen'}

    def rows(self):
        return len(re.findall(r'^\| [0-9]+ ·', text(GUIDES / 'lint-spec.md'), re.M))

    def test_every_document_that_counts_the_lint_rows_agrees_with_the_spec(self):
        n = self.rows()
        self.assertEqual(n, 17)
        word = self.WORDS[n]
        expected = {
            GUIDES / 'lint-spec.md': ['Run all %d rows' % n, 'rows run (%d for this table' % n,
                                      'All %s commands still execute' % word],
            GUIDES / 'full-checks.md': ['Run all %d rows during PLAN' % n, 'all %d returned rows' % n,
                                        'omission runs all %d' % n, 'still requires all %d' % n,
                                        'rows 1 through %d' % n, 'list(range(1, %d))' % (n + 1),
                                        'row not in range(1, %d)' % (n + 1), 'len(results) == %d' % n,
                                        'all %d if impact' % n, 'all %d canonical rows' % n,
                                        'N/%d checks passed' % n, 'not %d/%d' % (n, n), 'execute all %s commands' % word],
            GUIDES / 'scaffold.md': ['all %d direct lint rows' % n],
            GUIDES / 'plan-card.md': ['the %d mechanical' % n],
            ROOT / 'MAINTAINING.md': ['rows 1–%d' % n],
            ROOT / 'README.md': ['rows 1–%d' % n, '(%d lint rows)' % n],
        }
        for path, phrases in expected.items():
            flat = one_line(text(path))
            for phrase in phrases:
                with self.subTest(path=path.name, phrase=phrase):
                    self.assertIn(phrase, flat)

    def test_no_current_document_still_counts_sixteen_rows_outside_the_historical_checklists(self):
        stale = re.compile(r'\b16 rows|rows 1–16|sixteen|N/16|range\(1, 17\)|\ball 16\b|\bthe 16\b', re.I)
        current = [GUIDES / 'lint-spec.md', GUIDES / 'full-checks.md', GUIDES / 'scaffold.md', GUIDES / 'plan-card.md',
                   ROOT / 'MAINTAINING.md', ROOT / 'README.md']
        for path in current:
            with self.subTest(path=path.name):
                self.assertEqual(stale.findall(text(path)), [])
        # The historical checklists keep their own counts; the new checklist counts none of the old.
        before, after = text(GUIDES / 'migrate.md').split('## v9.0 → v9.1 checklist', 1)
        self.assertEqual(stale.findall(after.split('<a id="schema-keyed-migration"></a>', 1)[0]), [])
        self.assertTrue(stale.findall(before))


if __name__ == '__main__':
    unittest.main()
