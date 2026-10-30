"""Current catalog instructions retain baseline, erratum, next-wave and native lint guarantees.

Historical source identities are provenance; runtime route order comes from the catalog."""
from pathlib import Path
import re
import json
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'eval/tests/product/lint/rows'))
from maintaining.install_root import current_root  # noqa: E402
import test_lint_rows as base  # noqa: E402

INSTALL = current_root(ROOT)
MIGRATE = INSTALL / 'references/guides/migrate.md'
TITLE = '## v10.1 → v10.2 checklist'
ANCHOR = '<a id="v101--v102-checklist"></a>'


def skill_stamp():
    return re.search(r'^\*\*Tackle ([^*]+)\*\*', (ROOT / 'skills/tackle/SKILL.md').read_text(), re.M).group(1)


def ident(kind, number):
    """A synthetic fixture id of the pass-full workspace, built so no source line spells one."""
    return '{}-{:02d}'.format(kind, number)


TA, TB, DA = ident('T', 1), ident('T', 2), ident('D', 1)
RECEIPT = '**Remains**: none\n'
STEP_FIVE_LINE = '- **Detail**: full\n'


def catalog_value():
    return json.loads((INSTALL / 'references/guides/migration-catalog.json').read_bytes())


def item_identity(number):
    return json.dumps(['G', TITLE.removeprefix('## '), number], ensure_ascii=False, separators=(',', ':'))


def numbered(text):
    # Test-only provenance projection. Runtime order is the catalog rule/requires order below.
    rules = catalog_value()['rules']
    result = []
    for number in range(1, 12):
        wanted = item_identity(number)
        matches = [i['text'] for rule in rules for i in rule['instructions'] if wanted in i['sources']]
        if len(matches) != 1:
            raise AssertionError('one current instruction must retain this source obligation: ' + wanted)
        result.append(str(number) + '. ' + matches[0])
    return result


def steps_of(text):
    return '\n'.join(numbered(text))


def brief_hash(path):
    """Step 2's command: `sha256sum`, or `shasum -a 256` where it is absent."""
    command = ['sha256sum', str(path)] if shutil.which('sha256sum') else ['shasum', '-a', '256', str(path)]
    return subprocess.run(command, capture_output=True, text=True, check=True).stdout.split()[0]


def step(text, number):
    return ' '.join(numbered(text)[number - 1].split())


def code_spans(value):
    return re.findall(r'`([^`]+)`', value)


def span_with(value, needle):
    return next(s for s in code_spans(value) if needle in s)


def place(report, line):
    """Step 3's position: right before the last `Final status:` line, else right before the last receipt."""
    lines = report.split('\n')
    finals = [i for i, l in enumerate(lines) if l.startswith('Final status:')]
    receipts = [i for i, l in enumerate(lines) if l.startswith('**Remains**:')]
    lines.insert((finals or receipts)[-1], line)
    return '\n'.join(lines)


class ChecklistText(unittest.TestCase):
    def setUp(self):
        self.text = MIGRATE.read_text(encoding='utf-8')

    def test_the_heading_is_exact_unique_and_anchored_after_the_previous_checklist(self):
        self.assertNotIn(TITLE, self.text)
        self.assertIn('migration-catalog.json', self.text)
        catalog = catalog_value()
        groups = [g for g in catalog['provenance']['groups'] if g['source'] == 'G']
        self.assertEqual(sum(g['heading'] == TITLE.removeprefix('## ') for g in groups), 1)
        self.assertLess([g['heading'] for g in groups].index('v10.0 → v10.1 checklist'),
                        [g['heading'] for g in groups].index(TITLE.removeprefix('## ')))
        self.assertLess(self.text.index('<a id="compact-migration"></a>'),
                        self.text.index('<a id="schema-keyed-migration"></a>'))

    def test_the_migrate_chain_gate_accepts_a_10_2_0_stamp_only_with_this_exact_heading(self):
        """The historical identity remains mandatory in the current installed catalog gate."""
        loader = runpy.run_path(str(ROOT / 'eval/validation-integrity/acceptance.py'))['canonical_gates']
        command = loader((ROOT / 'MAINTAINING.md').read_text(encoding='utf-8'))[3]
        expected_heading = TITLE.removeprefix('## ')
        cases = (('original', expected_heading, True),
                 ('equivalent-json', expected_heading, True),
                 ('catalog-identity', 'v10.0 → v10.2 checklist', False),
                 ('catalog-identity', 'v10.1 → v10.2  checklist', False),
                 ('current-target', expected_heading, False),
                 ('retained-identity', 'v10.0 → v10.2 checklist', False),
                 ('retained-identity', 'v10.1 → v10.2  checklist', False))
        for mutation, heading, wanted in cases:
            with self.subTest(mutation=mutation, heading=heading):
                with tempfile.TemporaryDirectory(prefix='tackle-gate-four-') as temporary:
                    root = Path(temporary)
                    shutil.copytree(INSTALL, root / 'skills/tackle')
                    (root / 'maintaining').mkdir()
                    for name in ('check_migration_catalog.py', 'migrations.md'):
                        shutil.copyfile(ROOT / 'maintaining' / name, root / 'maintaining' / name)
                    target = root / 'skills/tackle/references/guides/migration-catalog.json'
                    catalog = json.loads(target.read_bytes())
                    self.assertEqual(catalog['target_methodology'], skill_stamp())
                    groups = [group for group in catalog['provenance']['groups']
                              if group['source'] == 'G' and group['heading'] == expected_heading]
                    self.assertEqual(len(groups), 1)
                    if mutation == 'catalog-identity':
                        groups[0]['heading'] = heading
                    elif mutation == 'current-target':
                        catalog['target_methodology'] = '10.1.0'
                    elif mutation == 'retained-identity':
                        retained = root / 'maintaining/migrations.md'
                        original = retained.read_text(encoding='utf-8')
                        lines = original.splitlines(keepends=True)
                        matches = [index for index, line in enumerate(lines)
                                   if line.rstrip('\r\n') == TITLE]
                        self.assertEqual(len(matches), 1)
                        index = matches[0]
                        lines[index] = lines[index].replace(TITLE, '## ' + heading, 1)
                        retained.write_text(''.join(lines), encoding='utf-8')
                    if mutation != 'original':
                        target.write_text(json.dumps(catalog, ensure_ascii=False,
                                                     sort_keys=True, indent=2) + '\n', encoding='utf-8')
                    child = subprocess.run(['sh', '-c', command], cwd=root, capture_output=True, timeout=30)
                    if wanted:
                        self.assertEqual((child.returncode, child.stdout, child.stderr), (0, b'', b''))
                    else:
                        self.assertNotEqual(child.returncode, 0)
                        self.assertTrue(child.stdout or child.stderr)

    def test_the_steps_name_each_adopted_artifact_and_end_with_the_stamp(self):
        steps = ' '.join(steps_of(self.text).split())
        for phrase in ('`sha256sum <brief>`', '`shasum -a 256 <brief>`', '`**Brief sha256**:', '`**Brief erratum**:',
                       '`- **Detail**: full`', '`- **Detail**: interface`', '`**Produces**`', '`**Consumes**`',
                       '`**Owner**:', '**Clauses**:', '19 of 19', '`tackle-workspace/5`', 'Skipped'):
            self.assertIn(phrase, steps)
        items = numbered(self.text)
        self.assertGreaterEqual(len(items), 9)
        self.assertIn('Methodology: Tackle ' + catalog_value()['target_methodology'], items[-1])
        baseline = next(i for i, item in enumerate(items) if 'sha256sum' in item)
        self.assertLess(baseline, len(items) - 1)

    def test_step_three_states_the_position_the_history_line_and_the_order(self):
        three = step(self.text, 3)
        for phrase in ("right before the report's `Final status:` line, or right before its `**Remains**:` line when it has none",
                       "only changes adoption makes to a closed task's records", 'outside code fences',
                       '`Brief sha256 T-NN: <the same hash>`', 'to the end of `history.md`',
                       'History only grows: never edit an older entry.',
                       'Do both before any other edit to a closed brief.'):
            self.assertIn(phrase, three)

    def test_the_hash_is_taken_and_recorded_before_any_brief_is_edited_and_the_stamp_is_last(self):
        rules = catalog_value()['rules']
        order = [r['id'] for r in rules]
        self.assertEqual(order, 'I P S A R B M E J H N Q W O V Z'.split())
        for i, rule in enumerate(rules):
            self.assertEqual(rule['requires'], [] if i == 0 else [order[i - 1]])
        self.assertLess(order.index('R'), order.index('B'))
        self.assertLess(order.index('R'), order.index('Z'))
        self.assertLess(order.index('V'), order.index('Z'))
        for phrase in ('sha256sum', '**Brief sha256**:', 'before any other edit'):
            self.assertIn(phrase, ' '.join(i['text'] for r in rules if r['id'] == 'R' for i in r['instructions']))

    def test_step_four_authorizes_an_erratum_by_an_active_decision_after_step_three(self):
        four = step(self.text, 4)
        for phrase in ('After recording the baseline, a closed brief changes only by erratum.', 'An active decision authorizes the edit',
                       'append `**Brief erratum**: D-NN · sha256 <hash after the edit>` to its report'):
            self.assertIn(phrase, four)

    def test_steps_five_and_six_edit_an_in_progress_or_checking_brief_only_at_its_task_boundary(self):
        five, six = step(self.text, 5), step(self.text, 6)
        self.assertIn("Edit the brief of an In progress or Checking task only at that task's boundary, never during an attempt.", five)
        self.assertIn('The task-boundary rule applies here too.', six)

    def test_step_six_states_the_source_rules_and_the_single_producer(self):
        six = step(self.text, 6)
        for phrase in ('Every consumed name gets one source: `from T-NN`, `from T-NN [sibling]` or `exists` with an anchored citation.',
                       'A `from T-NN` task must be an ancestor through `Depends on`.',
                       "A `[sibling]` source must also appear in the brief's own `Depends on` cell.",
                       'A name has one producing brief; row 18 fails a name that two briefs produce.',
                       'An interface brief needs no ledger.'):
            self.assertIn(phrase, six)
        self.assertNotIn('descendant', six)

    def test_step_seven_names_the_successor_of_a_superseded_decision(self):
        seven = step(self.text, 7)
        self.assertIn('When a decision with these lines supersedes an earlier one, the earlier heading names it, '
                      'as `⤴ superseded by D-NN`. Row 19 fails a heading that names another, and a still-active predecessor is no finding.', seven)
        self.assertIn("The owner's brief must cite the decision id and, at `full` detail, carry each named clause compiled.", seven)

    def test_step_eight_expects_19_silent_rows_and_repairs_a_closed_brief_only_by_erratum(self):
        self.assertIn('expect 19 of 19 rows silent. Repair a finding from another row as its own guide states, '
                      'and a closed brief only by erratum.', step(self.text, 8))

    def test_step_nine_states_what_keeps_working_and_the_two_row_two_repairs(self):
        nine = step(self.text, 9)
        for phrase in ('Rows 18 and 19 skip legacy briefs and decisions, and row 14 asks for the hash only after the 10.2.0 stamp.',
                       'Repair the first by depending on the successor, and the second by naming the Skipped task on '
                       "an open successor's `**Lineage**:` line."):
            self.assertIn(phrase, nine)
        self.assertNotIn('depending on the Skipped task', nine)
        self.assertNotIn("the successor's `**Lineage**", nine.replace("an open successor's", ''))

    def test_step_ten_states_the_round_cap_and_its_override_and_the_validator_decision(self):
        ten = step(self.text, 10)
        self.assertIn('capped at three rounds unless `AGENTS.md` sets `Verify round cap: N`', ten)
        self.assertIn('An `Acceptance validator:` line in `AGENTS.md` needs a decision recording the owner\'s request.', ten)

    def test_the_stamp_waits_for_every_complete_task(self):
        last = step(self.text, len(numbered(self.text)))
        self.assertIn('only after the baseline covers every Complete task', last)
        self.assertIn('From now on row 14 requires that line in each Complete report.', last)

    def test_step_five_states_the_detail_rule(self):
        five = step(self.text, 5)
        self.assertIn('Use `full` for the [next wave](verify.md#milestone-readiness) and for any brief whose row is '
                      'Ready to run, In progress or Checking. Use `interface` for the rest.', five)
        self.assertNotRegex(five, r'`interface` for [^.]*Ready to run')

    def test_the_ownership_line_format_allows_either_part(self):
        seven = step(self.text, 7)
        self.assertIn('`**Owner**: T-NN · **Clauses**: C-xx` after `**Supersedes**`', seven)
        self.assertIn('either part may be omitted', seven)

    def test_the_last_step_stamps_then_lints_again(self):
        last = step(self.text, len(numbered(self.text)))
        self.assertLess(last.index('Methodology: Tackle ' + catalog_value()['target_methodology']), last.index('19 of 19'))
        self.assertIn('again', last)

    def test_each_step_is_a_short_sentence_group_without_workspace_ids(self):
        for item in numbered(self.text):
            for sentence in re.split(r'(?<=[.;])\s+(?=[A-Z`*])', re.sub(r'^\d+\.\s+', '', item)):
                self.assertLessEqual(len(sentence.split()), 30, sentence)
        self.assertFalse(re.search(r'(?<![A-Za-z0-9_])[TDQ]-[0-9]{1,3}(?![A-Za-z0-9_])', steps_of(self.text)))


class Adoption(unittest.TestCase):
    """A workspace shaped like 10.1 (a closed task, an open one, an active decision) stepping through the checklist."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='tackle-adopt-102-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / 'root'
        self.root.mkdir()
        base.materialize(self.root, 'pass-full')
        self.ws = self.root / 'docs/plans/demo'
        self.stamp('10.1.0')
        # A 10.1 brief has neither a Detail line nor a ledger.
        self.edit('tasks/{}.md'.format(TB), lambda text: text.replace(STEP_FIVE_LINE, ''))
        self.edit('tasks/{}.md'.format(TB), lambda text: re.sub(r'- \*\*(Consumes|Produces)\*\*: none\n', '', text))
        self.edit('tasks/{}.md'.format(TA), lambda text: text.replace(STEP_FIVE_LINE, ''))

    def edit(self, name, change):
        path = self.ws / name
        path.write_text(change(path.read_text(encoding='utf-8')), encoding='utf-8')

    def stamp(self, version):
        (self.ws / 'AGENTS.md').write_text('# Agents\n\n**Methodology: Tackle {}**\n'.format(version), encoding='utf-8')

    def rows(self):
        out = {}
        for number in range(1, 20):
            verdict, child = base.run_row(number, self.root, None)
            out[number] = (verdict, [line for line in child.stdout.decode().splitlines() if line])
        return out

    def only(self, expected):
        """Assert that exactly the named rows print exactly the named lines."""
        result = self.rows()
        got = {number: lines for number, (_, lines) in result.items() if lines}
        self.assertEqual(got, expected, result)
        self.assertEqual({n for n, (verdict, _) in result.items() if verdict != 'PASS'}, set(expected), result)

    def baseline(self, final_status=False):
        """Step 3, from the checklist's own line, at the position step 3 states."""
        text = MIGRATE.read_text(encoding='utf-8')
        line = span_with(step(text, 3), '**Brief sha256**').replace('<64 lowercase hex digits>', brief_hash(self.ws / 'tasks/{}.md'.format(TA)))
        name = 'reports/{}-report.md'.format(TA)
        if final_status:
            self.edit(name, lambda report: report.replace(RECEIPT, 'Final status: Complete. Next owner: the coordinator.\n' + RECEIPT))
        self.edit(name, lambda report: place(report, line))
        return line

    def history_line(self):
        """Step 3's second line, from the checklist's own text, appended to the end of history.md."""
        text = MIGRATE.read_text(encoding='utf-8')
        line = span_with(step(text, 3), 'Brief sha256 T-NN').replace('T-NN', TA).replace('<the same hash>', brief_hash(self.ws / 'tasks/{}.md'.format(TA)))
        self.edit('history.md', lambda history: history.rstrip('\n') + '\n' + line + '\n')
        return line

    def test_a_workspace_that_adopts_nothing_passes_every_row(self):
        self.only({})

    def test_the_new_stamp_before_the_baseline_is_refused_and_the_baseline_then_passes(self):
        self.stamp('10.2.0')
        self.only({14: ['missing brief hash: ' + TA]})
        self.baseline()
        self.only({})

    def test_the_hash_line_lands_right_before_the_final_status_line_or_the_receipt(self):
        for final in (False, True):
            with self.subTest(final_status=final):
                self.setUp()
                line = self.baseline(final)
                lines = (self.ws / 'reports/{}-report.md'.format(TA)).read_text(encoding='utf-8').split('\n')
                target = 'Final status:' if final else '**Remains**:'
                at = next(i for i, l in enumerate(lines) if l.startswith(target))
                self.assertEqual(lines[at - 1], line)
                self.stamp('10.2.0')
                self.only({})

    def test_a_closed_brief_changes_only_by_erratum(self):
        self.baseline()
        self.edit('tasks/{}.md'.format(TA), lambda text: text + '\nAn edit after closure.\n')
        self.only({14: ['closed brief changed: ' + TA]})
        template = span_with(step(MIGRATE.read_text(encoding='utf-8'), 4), 'Brief erratum')
        line = template.replace('D-NN', DA).replace('<hash after the edit>', brief_hash(self.ws / 'tasks/{}.md'.format(TA))) + '\n'
        self.edit('reports/{}-report.md'.format(TA), lambda text: text + line)
        self.only({})

    def test_open_briefs_adopt_the_detail_line_and_the_ledger(self):
        brief = 'tasks/{}.md'.format(TB)
        add_detail = lambda value: (lambda text: text.replace('- **Traces to**: x.\n', '- **Traces to**: x.\n- **Detail**: ' + value + '\n'))
        self.edit(brief, add_detail('interface'))
        self.only({})
        self.edit(brief, lambda text: text.replace('- **Detail**: interface', '- **Detail**: full'))
        self.only({18: ['missing ledger: ' + TB]})
        self.edit(brief, lambda text: text.replace('- **Errors**:', '- **Consumes**: none\n- **Produces**: none\n- **Errors**:', 1))
        self.only({})

    def test_an_interface_brief_never_stands_on_a_ready_to_run_row(self):
        self.edit('tasks/{}.md'.format(TB), lambda text: text.replace('- **Traces to**: x.\n', '- **Traces to**: x.\n- **Detail**: interface\n'))
        self.edit('task-board.md', lambda text: re.sub(r'(\| %s \|.*\|) Draft \|' % TB, r'\1 Ready to run |', text))
        result = self.rows()
        self.assertIn('interface brief ready: ' + TB, result[18][1], result)

    def test_both_step_three_lines_pass_and_a_baseline_rewritten_after_an_edit_is_caught(self):
        self.baseline()
        self.history_line()
        self.stamp('10.2.0')
        self.only({})
        self.edit('tasks/{}.md'.format(TA), lambda text: text + '\nAn edit after closure.\n')
        report = 'reports/{}-report.md'.format(TA)
        new_hash = brief_hash(self.ws / 'tasks/{}.md'.format(TA))
        self.edit(report, lambda text: re.sub(r'(\*\*Brief sha256\*\*: )[0-9a-f]{64}', lambda m: m.group(1) + new_hash, text))
        self.only({14: ['rewritten brief hash: ' + TA]})

    def test_the_history_line_alone_never_replaces_the_report_line(self):
        self.history_line()
        self.stamp('10.2.0')
        self.only({14: ['rewritten brief hash: ' + TA]})
        self.baseline()
        self.only({})

    def test_a_closed_brief_edit_with_both_lines_still_needs_the_erratum(self):
        self.baseline()
        self.history_line()
        self.edit('tasks/{}.md'.format(TA), lambda text: text + '\nAn edit after closure.\n')
        self.only({14: ['closed brief changed: ' + TA]})
        template = span_with(step(MIGRATE.read_text(encoding='utf-8'), 4), 'Brief erratum')
        line = template.replace('D-NN', DA).replace('<hash after the edit>', brief_hash(self.ws / 'tasks/{}.md'.format(TA))) + '\n'
        self.edit('reports/{}-report.md'.format(TA), lambda text: text + line)
        self.only({})

    def test_the_earlier_heading_must_name_the_decision_that_supersedes_it(self):
        later, earlier, other = ident('D', 3), ident('D', 4), ident('D', 5)
        self.edit('tasks/{}.md'.format(TB), lambda text: text + '\nThis task applies {}.\n'.format(later))
        self.edit('decisions.md', lambda text: text
                  + '\n## {} \u00b7 Earlier \u00b7 \u2934 superseded by {} \u00b7 2026-09-22, session 1\n\n**Decision**: earlier.\n'.format(earlier, other)
                  + '\n## {} \u00b7 New \u00b7 \u2705 active \u00b7 2026-09-25, session 1\n\n**Decision**: new.\n**Supersedes**: {}\n**Owner**: {}\n'.format(later, earlier, TB))
        self.only({19: ['stale supersede: {} supersedes {} (in force: {})'.format(later, earlier, other)]})
        self.edit('decisions.md', lambda text: text.replace('superseded by ' + other, 'superseded by ' + later, 1))
        self.only({})

    def test_a_still_active_predecessor_is_no_finding(self):
        later, earlier = ident('D', 3), ident('D', 4)
        self.edit('tasks/{}.md'.format(TB), lambda text: text + '\nThis task applies {}.\n'.format(later))
        self.edit('decisions.md', lambda text: text
                  + '\n## {} \u00b7 Earlier \u00b7 \u2705 active \u00b7 2026-09-22, session 1\n\n**Decision**: earlier.\n'.format(earlier)
                  + '\n## {} \u00b7 New \u00b7 \u2705 active \u00b7 2026-09-25, session 1\n\n**Decision**: new.\n**Supersedes**: {}\n**Owner**: {}\n'.format(later, earlier, TB))
        self.only({})

    def decide(self, line):
        self.edit('tasks/{}.md'.format(TB), lambda text: text + '\nThis task applies {}.\n'.format(DA))
        self.edit('decisions.md', lambda text: text.replace('**Decision**: demo.\n', '**Decision**: demo.\n**Supersedes**: none\n' + line + '\n', 1))

    def test_the_decision_ownership_line_is_adopted_only_where_written(self):
        template = span_with(step(MIGRATE.read_text(encoding='utf-8'), 7), 'Owner')
        self.assertEqual(template, '**Owner**: T-NN · **Clauses**: C-xx')
        # The checklist's own format, then each part alone (an interface owner brief is not yet checked for clauses).
        self.edit('tasks/{}.md'.format(TB), lambda text: text.replace('- **Traces to**: x.\n', '- **Traces to**: x.\n- **Detail**: interface\n'))
        self.decide(template.replace('T-NN', TB).replace('C-xx', 'C' + '01'))
        self.only({})
        self.setUp()
        self.decide('**Owner**: ' + TB)
        self.only({})
        self.setUp()
        self.decide('**Owner**: ' + ident('T', 9))
        self.only({19: ['unknown owner: {} {}'.format(DA, ident('T', 9))]})


if __name__ == '__main__':
    unittest.main()
