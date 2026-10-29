"""History bounds and post-task obligations in the shipped templates and guides.

A scaffold copies the AGENTS template, so its policy line is what every new workspace carries; the board template
supplies the obligations table that row 17 reads; the retro template's recipes run against fixture histories; and
every document that states how many lint rows exist agrees with the lint spec. Text checks protect wording and
structure only: they do not show that an agent obeys the policy.
"""
import importlib.util
import json
import re
import json
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


STATUS_LISTING = 'List every `Open` obligation (`O-NN`) with its owner and trigger.'
NEXT_REPORT = 'When no task is Ready, Next reports the open obligations (id, owner, trigger) rather than nothing.'


def status_bullets(guide):
    """{label: one-line text} of the bullets under `## Queries` in status.md."""
    section = guide.split('## Queries', 1)[1].split('\n## ', 1)[0]
    found = {}
    for chunk in re.split(r'\n(?=- \*\*)', section):
        match = re.match(r'- \*\*([A-Za-z]+)\*\*', chunk)
        if match:
            found[match[1]] = one_line(chunk)
    return found


def status_problems(guide):
    """What the STATUS bullet of the post-task obligations contract finds missing in a status guide."""
    bullets = status_bullets(guide)
    problems = []
    if STATUS_LISTING not in bullets.get('Status', ''):
        problems.append('the Status bullet does not list the Open obligations with owner and trigger')
    if NEXT_REPORT not in bullets.get('Next', ''):
        problems.append('the Next bullet does not report the open obligations when no task is Ready')
    return problems


def plant(guide, sentence, replacement):
    """`guide` with `sentence`, however the guide wraps it, replaced."""
    pattern = r'\s+'.join(re.escape(word) for word in sentence.split())
    planted, count = re.subn(pattern, lambda match: replacement, guide)
    assert count == 1, (sentence, count)
    return planted


def load_runner():
    spec = importlib.util.spec_from_file_location('tackle_run_suites', ROOT / 'eval/run_suites.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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

    def run_metric(self, label, files):
        with tempfile.TemporaryDirectory(prefix='tackle-retro-cases-') as temporary:
            root = Path(temporary)
            for name, lines in files.items():
                (root / name).write_text('\n'.join(lines) + '\n', encoding='utf-8')
            return subprocess.run(['sh', '-c', self.cell(label)], cwd=root, capture_output=True, text=True, timeout=30)

    def echo(self, files, name, line):
        hits = [number for number, text_line in enumerate(files[name], 1) if text_line == line]
        self.assertEqual(len(hits), 1, line)
        return '%s:%d: %s' % (name, hits[0], line)

    def assert_attempts(self, files, counted, counts, over=(), unattributed=()):
        child = self.run_metric('Attempts over budget', files)
        self.assertEqual((child.returncode, child.stderr), (0, ''), child.stderr)
        out = child.stdout.splitlines()
        if not counted:
            self.assertEqual(out, ['none'])
            return
        echoes = [l for l in out if re.match(r'history(-archive)?\.md:\d+: ', l)]
        self.assertEqual(echoes, [self.echo(files, name, line) for name, line in counted], out)
        got = {m[1]: int(m[2]) for m in (re.match(r'^([PT]-[A-Za-z0-9]+) (\d+)$', l) for l in out) if m}
        self.assertEqual(got, counts, out)
        self.assertEqual({l[len('over cap: '):] for l in out if l.startswith('over cap: ')}, set(over), out)
        self.assertEqual({l for l in out if l.startswith('unattributed ')}, set(unattributed), out)

    def assert_gate(self, files, gate, sessions, undated=(), completed='1', present=(), absent=()):
        child = self.run_metric('Gate accuracy', files)
        self.assertEqual((child.returncode, child.stderr), (0, ''), child.stderr)
        out = child.stdout.splitlines()
        self.assertEqual([l for l in out if l.startswith('Gate: ') or l == 'gate n/a'], [gate], out)
        self.assertEqual([l for l in out if l.startswith('sessions ')], ['sessions %d' % sessions], out)
        self.assertEqual({l for l in out if l.startswith('undated heading: ')}, set(undated), out)
        self.assertEqual([l for l in out if l.startswith('completed ')], ['completed %s' % completed], out)
        for fragment in present:
            self.assertTrue(any(fragment in l for l in out), fragment)
        for fragment in absent:
            self.assertFalse(any(fragment in l for l in out), fragment)

    def test_a1_both_journal_forms_count_across_the_archive_then_the_history(self):
        files = {'history-archive.md': ['# History archive', '', '## 2026-10-01 · session 1',
                                        '- T-0042 attempt 1: lint failed'],
                 'history.md': ['# History', '', '## 2026-10-02 · session 2',
                                '- 2026-10-02 — T-0042 correction cycle 2: test red',
                                '- Correction cycle 3 of 3 sent to the T-0042 executor',
                                '- T-0042 correction 4 of 3: still red']}
        self.assert_attempts(files, [('history-archive.md', '- T-0042 attempt 1: lint failed'),
                                     ('history.md', '- 2026-10-02 — T-0042 correction cycle 2: test red'),
                                     ('history.md', '- Correction cycle 3 of 3 sent to the T-0042 executor'),
                                     ('history.md', '- T-0042 correction 4 of 3: still red')],
                             {'T-0042': 4}, over=['T-0042'])

    def test_a2_state_snapshot_lines_are_skipped_whatever_their_case(self):
        history = ['# History', '', '## 2026-10-02 · session 1', '- T-0042 attempt 1: x failed', '',
                   '### State snapshot', '- Active obligations: 1 of 3 for T-0042 (attempt 1: x failed)',
                   '- Blocked on: nothing.', '', '## 2026-10-03 · session 2', '- T-0042 Attempt 2: y failed']
        self.assert_attempts({'history.md': history},
                             [('history.md', '- T-0042 attempt 1: x failed'),
                              ('history.md', '- T-0042 Attempt 2: y failed')], {'T-0042': 2})

    def test_a3_only_attempt_and_cycle_lines_with_a_number_of_at_least_one_count(self):
        history = ['# History', '', '## 2026-10-05 · session 1',
                   '- T-0042 correction cycle 1 of 3: lint red → fix import; python3 -m unittest: fail',
                   '- T-0042 attempt 2: retry with a clean cache', '- T-0042 attempt : noise',
                   '- T-0042 correction cycle 0 noted']
        self.assert_attempts({'history.md': history}, [('history.md', history[3]), ('history.md', history[4])],
                             {'T-0042': 2})

    def test_a4_a_history_without_counted_lines_prints_none(self):
        self.assert_attempts({'history.md': ['# History', '', '## 2026-10-06 · session 1', '- T-0042 started']},
                             [], {})

    def test_a5_an_idless_counted_line_takes_the_ids_of_its_entry(self):
        history = ['# History', '', '## 2026-10-07 · session 1', '- T-0042 started',
                   '- correction cycle 1 of 3: lint red → fix; python3 -m unittest: pass']
        self.assert_attempts({'history.md': history}, [('history.md', history[4])], {'T-0042': 1})

    def test_a6_several_ids_are_credited_and_an_entry_without_ids_is_unattributed(self):
        history = ['# History', '', '## 2026-10-08 · session 1', '- T-0042 and T-0043 share the parser',
                   '- attempt 1: parser fix failed', '', '## 2026-10-09 · session 2', '- attempt 1: unowned failure']
        self.assert_attempts({'history.md': history}, [('history.md', history[4]), ('history.md', history[7])],
                             {'T-0042': 1, 'T-0043': 1}, unattributed=['unattributed history.md:8'])

    def test_a7_exactly_three_counted_lines_are_not_over_the_cap(self):
        history = ['# History', '', '## 2026-10-10 · session 1', '- T-0042 attempt 1: a', '- T-0042 attempt 2: b',
                   '- T-0042 correction cycle 3 of 3: c → d; make test: fail']
        self.assert_attempts({'history.md': history}, [('history.md', history[3]), ('history.md', history[4]),
                                                       ('history.md', history[5])], {'T-0042': 3})

    def test_a8_a_snapshot_ends_at_the_next_subheading_and_at_the_end_of_the_file(self):
        archive = ['## 2026-10-10 · session 1', '- T-0042 attempt 1: a failed', '### State snapshot',
                   '- Obligations: T-0042 (attempt 1: a failed)']
        history = ['# History', '- T-0042 attempt 2: b failed', '', '## 2026-10-11 · session 2', '### State snapshot',
                   '- Obligations: T-0042 (attempt 2: b failed)', '### Notes', '- T-0042 attempt 3: c failed']
        self.assert_attempts({'history-archive.md': archive, 'history.md': history},
                             [('history-archive.md', archive[1]), ('history.md', history[1]),
                              ('history.md', history[7])], {'T-0042': 3})

    def test_a9_a_task_named_twice_on_one_counted_line_is_credited_once(self):
        history = ['# History', '', '## 2026-10-12 · session 1',
                   '- T-0042 correction cycle 2: T-0042 test red',
                   '- T-0042 and T-0042 attempt 1: x',
                   '- T-0042 attempt 2: y, T-0042 again']
        self.assert_attempts({'history.md': history}, [('history.md', history[3]), ('history.md', history[4]),
                                                       ('history.md', history[5])], {'T-0042': 3})

    def test_g1_a_full_gate_below_line_one_counts_distinct_session_labels_and_dates(self):
        plan = ['# Action plan — Fixture', '', 'Gate: Full', '', '## 1. Objective']
        history = ['# History', '', '## 2026-10-18 · session 1', '- T-0042 started; the gate held',
                   '## 2026-10-18 · session 1', '- continued after a break', '## 2026-10-19 · session 2',
                   '- delegate the review', '## Session 3 — 2026-10-19', '- T-0042 Complete',
                   '## 2026-10-21 (continued)', '- x', '## 2026-10-21 (continued)', '- y']
        board = ['Schema: tackle-workspace/4', '', '| Task | What | Brief | Depends on | Verification | Status |',
                 '|---|---|---|---|---|---|', '| T-0042 | Parser work | tasks/T-0042.md | none | pending | Complete |']
        self.assert_gate({'plan.md': plan, 'history.md': history, 'task-board.md': board}, 'Gate: Full', 4,
                         undated=['undated heading: history.md:9'], present=['the gate held'], absent=['delegate'])

    def test_g2_a_lite_plan_without_a_board_reports_completed_as_not_applicable(self):
        self.assert_gate({'plan.md': ['Gate: Lite', '', '# Lite fixture'],
                          'history.md': ['# History', '', '## 2026-10-20 · session 1', '- T-0042 Complete']},
                         'Gate: Lite', 1, completed='n/a')

    def test_g3_a_plan_without_a_gate_line_prints_gate_not_applicable_and_no_delegate_match(self):
        board = ['Schema: tackle-workspace/4', '', '| Task | What | Brief | Depends on | Verification | Status |',
                 '|---|---|---|---|---|---|', '| T-0042 | Parser work | tasks/T-0042.md | none | pending | Complete |']
        self.assert_gate({'plan.md': ['# Action plan — Fixture', '', '## 1. Objective', '- delegate the investigation'],
                          'history.md': ['# History', '', '## 2026-10-22 · session 1', '- we delegate this to the reviewer'],
                          'task-board.md': board}, 'gate n/a', 1, absent=['delegate'])

    def test_g4_an_undated_archive_heading_counts_and_fenced_or_commented_headings_do_not(self):
        plan = ['# Action plan — Fixture', '', 'Gate: Full', '', '## 1. Objective']
        archive = ['# History archive', '', '## Notes', '- legacy note', '', '## 2026-10-01 · session 1', '- a']
        history = ['# History', '', '## 2026-10-02 · session 2', '```text', '## not a heading', '```', '<!--',
                   '## also not a heading', '-->', '- b']
        board = ['Schema: tackle-workspace/4', '', '| Task | What | Brief | Depends on | Verification | Status |',
                 '|---|---|---|---|---|---|', '| T-0042 | Parser work | tasks/T-0042.md | none | pending | Complete |']
        self.assert_gate({'plan.md': plan, 'history-archive.md': archive, 'history.md': history, 'task-board.md': board},
                         'Gate: Full', 2, undated=['undated heading: history-archive.md:3'])

    def test_g5_labels_shared_by_the_archive_and_the_history_count_once(self):
        board = ['Schema: tackle-workspace/4', '', '| Task | What | Brief | Depends on | Verification | Status |',
                 '|---|---|---|---|---|---|', '| T-0042 | Parser work | tasks/T-0042.md | none | pending | Complete |']
        self.assert_gate({'plan.md': ['Gate: Full', '', '## 1. Objective'], 'task-board.md': board,
                          'history-archive.md': ['## 2026-10-16 · session 1', '- a', '## 2026-10-17 · session 2', '- b'],
                          'history.md': ['## 2026-10-18 · session 2', '- c', '## 2026-10-19 · session 3', '- d']},
                         'Gate: Full', 3)


    def test_r04_the_clock_format_and_its_unmeasured_clocks_are_stated_in_each_home(self):
        clock = 'YYYY-MM-DDTHH:MM:SS[.fff](Z|±HH:MM)'
        retro_source = text(GUIDES / 'retro.md')
        fixture = re.search(r'(?ms)^### Fixture recipe\n(.*?)(?=^#{1,3} |\Z)', retro_source)
        self.assertIsNotNone(fixture, 'missing retro fixture recipe section')
        lite = text(REF / 'lite-plan.tmpl.md').splitlines()
        start = lite.index('# Resource usage')
        end = next((i for i in range(start + 1, len(lite)) if lite[i].startswith('# ')), len(lite))
        homes = {'resource-usage.tmpl.md': text(REF / 'resource-usage.tmpl.md'),
                 'lite-plan.tmpl.md # Resource usage': '\n'.join(lite[start:end]),
                 'guides/retro.md ### Fixture recipe': fixture.group(1)}
        for home, body in homes.items():
            flat = ' '.join(body.split())
            self.assertIn(clock, flat, home)
            self.assertRegex(flat, r'minute[- ]only', home)
            self.assertRegex(flat, r'space[- ]separated', home)
            self.assertRegex(flat, r'unmeasured|not measured', home)

    def test_t1_the_plan_template_puts_the_full_gate_on_line_three_and_keeps_its_title_and_first_section(self):
        lines = text(REF / 'plan.tmpl.md').splitlines()
        self.assertEqual(lines[0], '# Action plan — {{TITLE}}')
        self.assertEqual(lines[2], 'Gate: Full')
        self.assertEqual(lines[3:5], ['', '## 1. Objective'])
        self.assertEqual([l for l in lines if l.startswith('Gate: ')], ['Gate: Full'])


class StatusObligationTests(unittest.TestCase):
    def test_the_status_guide_lists_open_obligations_and_next_reports_them_when_nothing_is_ready(self):
        self.assertEqual(status_problems(text(GUIDES / 'status.md')), [])

    def test_the_check_fails_when_those_sentences_are_negated_removed_or_moved(self):
        guide = text(GUIDES / 'status.md')
        list_sentence = 'scans available workspaces and gives one line per plan.'
        planted = {
            'listing removed': plant(guide, STATUS_LISTING, ''),
            'listing negated': plant(guide, STATUS_LISTING, 'Never list an `Open` obligation with its owner and trigger.'),
            'next sentence removed': plant(guide, NEXT_REPORT, ''),
            'next sentence negated': plant(guide, NEXT_REPORT, 'When no task is Ready, Next reports nothing.'),
            'next sentence moved to the List bullet': plant(plant(guide, NEXT_REPORT, ''), list_sentence,
                                                           list_sentence + ' ' + NEXT_REPORT),
        }
        for label, variant in planted.items():
            with self.subTest(case=label):
                self.assertNotEqual(status_problems(variant), [], label)

    def test_a_status_guide_change_selects_the_family_that_checks_it(self):
        manifest = json.loads((ROOT / 'eval/suite-manifest.json').read_text(encoding='utf-8'))
        plan = load_runner().plan(ROOT, manifest, changed=['skills/tackle/references/guides/status.md'])
        self.assertIn('eval/tests/product/templates', plan['selected'])


class CountAgreementTests(unittest.TestCase):
    WORDS = {19: 'nineteen'}

    def rows(self):
        return len(re.findall(r'^\| [0-9]+ ·', text(GUIDES / 'lint-spec.md'), re.M))

    def test_every_document_that_counts_the_lint_rows_agrees_with_the_spec(self):
        n = self.rows()
        self.assertEqual(n, 19)
        word = self.WORDS[n]
        expected = {
            GUIDES / 'lint-spec.md': ['Run all %d rows' % n, 'rows run (%d for this table' % n,
                                      'All %s commands still execute' % word],
            GUIDES / 'full-checks.md': ['Run all %d rows during PLAN' % n, 'all %d returned rows' % n,
                                        'omission runs all %d' % n, 'still requires all %d' % n,
                                        'all %d if impact' % n, 'all %d canonical rows' % n,
                                        'N/%d checks passed' % n, 'not %d/%d' % (n, n), 'execute all %s commands' % word],
            INSTALL / 'scripts/lint_runner.py': ['rows 1 through %d' % n, 'list(range(1, %d))' % (n + 1),
                                                 'row not in range(1, %d)' % (n + 1), 'len(results) == %d' % n],
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
        catalog = json.loads((GUIDES / 'migration-catalog.json').read_bytes())
        instructions = '\n'.join(item['text'] for rule in catalog['rules'] for item in rule['instructions'])
        self.assertEqual(stale.findall(instructions), [])
        self.assertEqual(catalog['target_methodology'], '10.3.0')
        archive = text(ROOT / 'maintaining/migrations.md')
        old = archive.split('## v8.4 → v9.0 checklist', 1)[1].split('\n## ', 1)[0]
        self.assertTrue(stale.findall(old))
        archived = archive.split('## v9.0 → v9.1 checklist', 1)[1].split('\n## ', 1)[0]
        self.assertEqual(stale.findall(archived), [])


if __name__ == '__main__':
    unittest.main()
