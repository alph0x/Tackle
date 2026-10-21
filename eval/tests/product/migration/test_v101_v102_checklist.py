"""The 10.1 to 10.2 adoption path in references/guides/migrate.md: the checklist heading satisfies the migrate-chain
gate for stamp 10.2.0, its steps name the artifacts they apply and end with the stamp, and a workspace shaped like
10.1 adopts the closed-record hash and the open-brief fields step by step. The steps are applied mechanically
(the hash with the shipped `sha256sum` or `shasum -a 256` command the first step names) and judged by the shipped
lint rows, never by a copy of their logic.
"""
from pathlib import Path
import re
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


def ident(kind, number):
    """A synthetic fixture id of the pass-full workspace, built so no source line spells one."""
    return '{}-{:02d}'.format(kind, number)


TA, TB, DA = ident('T', 1), ident('T', 2), ident('D', 1)
RECEIPT = '**Remains**: none\n'
STEP_FIVE_LINE = '- **Detail**: full\n'


def steps_of(text):
    return text.split(TITLE, 1)[1].split('\n## ', 1)[0].split('\n<a id=', 1)[0]


def numbered(text):
    return re.findall(r'^\d+\. .*(?:\n(?!\d+\. ).*)*', steps_of(text), re.M)


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
        lines = self.text.splitlines()
        self.assertEqual(lines.count(TITLE), 1)
        self.assertEqual(lines[lines.index(TITLE) - 1], ANCHOR)
        self.assertLess(self.text.index('## v10.0 → v10.1 checklist'), self.text.index(TITLE))
        self.assertLess(self.text.index(TITLE), self.text.index('<a id="schema-keyed-migration"></a>'))

    def test_the_migrate_chain_gate_accepts_a_10_2_0_stamp_only_with_this_exact_heading(self):
        loader = runpy.run_path(str(ROOT / 'eval/validation-integrity/acceptance.py'))['canonical_gates']
        command = loader((ROOT / 'MAINTAINING.md').read_text(encoding='utf-8'))[3]
        shipped = ANCHOR + '\n' + TITLE + steps_of(self.text)
        for guide, wanted in ((shipped, True), (shipped.replace(TITLE, '## v10.0 → v10.2 checklist'), False),
                              (shipped.replace(TITLE, '## v10.1 → v10.2  checklist'), False)):
            with tempfile.TemporaryDirectory(prefix='tackle-gate-four-') as temporary:
                root = Path(temporary)
                (root / 'skills/tackle/references/guides').mkdir(parents=True)
                (root / 'maintaining').mkdir()
                (root / 'skills/tackle/SKILL.md').write_text('# Tackle\n\n**Tackle 10.2.0** — fixture stamp\n', encoding='utf-8')
                (root / 'skills/tackle/references/guides/migrate.md').write_text(guide, encoding='utf-8')
                shutil.copyfile(ROOT / 'maintaining/migrations.md', root / 'maintaining/migrations.md')
                child = subprocess.run(['sh', '-c', command], cwd=root, capture_output=True, text=True)
                self.assertEqual(child.stderr, '')
                if wanted:
                    self.assertEqual((child.returncode, child.stdout), (0, ''))
                else:
                    self.assertIn('missing migrate checklist → v10.2', child.stdout)

    def test_the_steps_name_each_adopted_artifact_and_end_with_the_stamp(self):
        steps = ' '.join(steps_of(self.text).split())
        for phrase in ('`sha256sum <brief>`', '`shasum -a 256 <brief>`', '`**Brief sha256**:', '`**Brief erratum**:',
                       '`- **Detail**: full`', '`- **Detail**: interface`', '`**Produces**`', '`**Consumes**`',
                       '`**Owner**:', '**Clauses**:', '19 of 19', '`tackle-workspace/5`', 'Skipped'):
            self.assertIn(phrase, steps)
        items = numbered(self.text)
        self.assertGreaterEqual(len(items), 9)
        self.assertIn('Methodology: Tackle 10.2.0', items[-1])
        baseline = next(i for i, item in enumerate(items) if 'sha256sum' in item)
        self.assertLess(baseline, len(items) - 1)

    def test_step_three_states_the_position_and_that_it_is_the_only_closed_record_change(self):
        three = step(self.text, 3)
        for phrase in ("right before the report's `Final status:` line, or right before its `**Remains**:` line when it has none",
                       "only change adoption makes to a closed task's records", 'outside code fences'):
            self.assertIn(phrase, three)

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
        self.assertLess(last.index('Methodology: Tackle 10.2.0'), last.index('19 of 19'))
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
        line = span_with(step(text, 3), 'Brief sha256').replace('<64 lowercase hex digits>', brief_hash(self.ws / 'tasks/{}.md'.format(TA)))
        name = 'reports/{}-report.md'.format(TA)
        if final_status:
            self.edit(name, lambda report: report.replace(RECEIPT, 'Final status: Complete. Next owner: the coordinator.\n' + RECEIPT))
        self.edit(name, lambda report: place(report, line))
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
