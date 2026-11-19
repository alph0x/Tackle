"""Lint rows 18 and 19 and the row 2 live-owner extension, through the shipped scripts/lint.py, on the complete
`pass-full` fixture workspace. Each planted defect prints exactly its diagnostic on its row, and rows 1-17 stay
silent on it (the control arm: the pre-feature rows do not see the defect). Legacy briefs and decisions, which
declare no `**Detail**:` and no `**Owner**:` line, stay silent on the new checks.
"""
from pathlib import Path
import re
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import test_lint_rows as base  # noqa: E402


def ident(kind, number):
    """A synthetic fixture id of the pass-full workspace, built so no source line spells one."""
    return '{}-{:02d}'.format(kind, number)


TA, TB, TZ = ident('T', 1), ident('T', 2), ident('T', 9)
DA, DB, DC, DD = (ident('D', n) for n in (1, 2, 3, 4))
CL = 'C' + '01'
RA, RB = 'R' + '01', 'R' + '02'
LEDGER_T01 = '- **Produces**:\n  - `demo/output` — the demo line\n- **Consumes**: none\n'
LEDGER_T02 = '- **Produces**: none\n- **Consumes**:\n  - `demo/output` from %s\n' % TA
EMPTY = '- **Produces**: none\n- **Consumes**: none\n'


def row(task, what, depends, verification, status):
    return '| %s | %s | tasks/%s.md | %s | %s | %s |' % (task, what, task, depends, verification, status)


ROW1 = row(TA, 'Standard work', 'none', 'reports/%s-report.md' % TA, 'Complete')
ROW2 = row(TB, 'Experiment', TA, 'pending', 'Draft')


def set_ledger(text, detail, ledger):
    """Give a generated brief a detail level and a ledger in place of its Interface fields."""
    text = re.sub(r'^- \*\*Detail\*\*: .*$', '- **Detail**: ' + detail, text, count=1, flags=re.M)
    text = re.sub(r'^- \*\*Consumes\*\*: .*\n(?:  - .*\n)*', '', text, count=1, flags=re.M)
    text = re.sub(r'^- \*\*Produces\*\*: .*\n(?:  - .*\n)*', ledger, text, count=1, flags=re.M)
    return text


def decision(number, owner=None, clauses=None, supersedes='none'):
    line = ''
    if owner or clauses:
        line = '\n' + ' · '.join((['**Owner**: ' + owner] if owner else []) + (['**Clauses**: ' + clauses] if clauses else []))
    return ('## %s · Owned · ✅ active · 2026-10-20, session 1\n\n**Decision**: x\n**Supersedes**: %s · **From**: —%s'
            % (ident('D', number), supersedes, line))


class Workspace:
    def __init__(self, case):
        self.temp = tempfile.TemporaryDirectory(prefix='tackle-ledger-rows-')
        case.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'root'
        self.root.mkdir()
        base.materialize(self.root, 'pass-full')
        self.ws = self.root / 'docs/plans/demo'

    def read(self, name):
        return (self.ws / name).read_text(encoding='utf-8')

    def write(self, name, text):
        (self.ws / name).write_text(text, encoding='utf-8')

    def sub(self, name, old, new):
        text = self.read(name)
        assert text.count(old) == 1, (name, old)
        self.write(name, text.replace(old, new))

    def brief(self, task):
        return 'tasks/%s.md' % task

    def adopt(self, first='full', second='full', ledger01=LEDGER_T01, ledger02=LEDGER_T02):
        self.write(self.brief(TA), set_ledger(self.read(self.brief(TA)), first, ledger01))
        self.write(self.brief(TB), set_ledger(self.read(self.brief(TB)), second, ledger02))

    def cite(self, task, decision_id):
        self.sub(self.brief(task), '- **Traces to**:', '- **Traces to**: %s;' % decision_id)

    def decide(self, entry):
        self.write('decisions.md', self.read('decisions.md').rstrip('\n') + '\n\n' + entry + '\n')

    def rows(self):
        out = {}
        for number in base.published_row_ids():
            verdict, child = base.run_row(number, self.root, None)
            out[number] = (verdict, [line for line in child.stdout.decode().splitlines() if line])
        return out


class LedgerAndOwnershipRows(unittest.TestCase):
    def assert_only(self, ws, number, lines):
        result = ws.rows()
        failing = {n for n, (verdict, _) in result.items() if verdict != 'PASS'}
        self.assertEqual(failing, {number} if lines else set(), result)
        self.assertEqual(result[number][1], lines)

    def test_clean_adoption_passes_every_row(self):
        ws = Workspace(self)
        ws.adopt()
        self.assert_only(ws, 18, [])

    def test_row_18_accepts_inline_and_block_producers(self):
        for producer in (
            '- **Produces**:\n  - `demo/output` — the demo line\n',
            '- **Produces**: `demo/output` — the demo line\n',
            '- **Produces**: `demo/output` — **Purpose**: demo line\n',
        ):
            with self.subTest(producer=producer):
                ws = Workspace(self)
                ws.adopt(ledger01=producer + '- **Consumes**: none\n')
                self.assert_only(ws, 18, [])

    def test_example_fence_cannot_supply_producer(self):
        example = (
            '````markdown\n'
            '```sh\n'
            '- **Produces**:\n'
            '  - `demo/output` — example only\n'
            '```\n'
            '````\n'
        )
        missing = ['missing producer: demo/output in %s' % TB]
        cases = [
            ('example only', EMPTY + example, 'FAIL', missing),
            ('no example or producer', EMPTY, 'FAIL', missing),
        ]
        for form, producer in (
            ('inline', '- **Produces**: `demo/output` — the demo line\n'),
            ('block', '- **Produces**:\n  - `demo/output` — the demo line\n'),
        ):
            ledger = producer + '- **Consumes**: none\n'
            cases.extend([
                (form + ' before example', ledger + example, 'PASS', []),
                (form + ' after example', example + ledger, 'PASS', []),
            ])

        for name, ledger, expected_verdict, expected_lines in cases:
            with self.subTest(case=name):
                ws = Workspace(self)
                ws.adopt(ledger01=ledger)
                verdict, child = base.run_row(18, ws.root, None)
                lines = [line for line in child.stdout.decode().splitlines() if line]
                self.assertEqual(verdict, expected_verdict)
                self.assertEqual(lines, expected_lines)

        real_inline = '- **Produces**: `demo/output` — the demo line\n- **Consumes**: none\n'
        real_block = '- **Produces**:\n  - `demo/output` — the demo line\n- **Consumes**: none\n'
        fake_block = '- **Produces**:\n  - `demo/output` — example only\n'
        commented = '<!--\n' + fake_block + '-->\n'
        consumer = '- **Produces**: none\n- **Consumes**:\n  - `demo/output` from %s\n' % TA
        tail_consumer = consumer + '  - `demo/tail` from %s\n' % TA
        tail_producer = real_inline + '- **Produces**: `demo/tail` — hidden\n'
        missing_tail = ['missing producer: demo/tail in %s' % TB]
        malformed = ['malformed consume: plan in %s' % TB]
        citation_prefix = consumer + '  - `plan` exists `plan.md'
        cases = [
            ('backtick equal close', EMPTY + '```\n' + fake_block + '```\n' + real_inline, consumer, []),
            ('backtick longer close', EMPTY + '```\n' + fake_block + '````\n' + real_inline, consumer, []),
            ('backtick shorter close', EMPTY + '````\n```\n' + fake_block + '````\n', consumer, missing),
            ('mismatched close', EMPTY + '```\n~~~\n' + fake_block + '```\n', consumer, missing),
            ('tilde nested example', EMPTY + '~~~~markdown\n~~~sh\n' + fake_block + '~~~\n~~~~\n', consumer, missing),
            ('tilde equal close', EMPTY + '~~~\n' + fake_block + '~~~\n' + real_inline, consumer, []),
            ('tilde longer close', EMPTY + '~~~\n' + fake_block + '~~~~\n' + real_inline, consumer, []),
            ('tilde mismatched close', EMPTY + '~~~\n```\n' + fake_block + '~~~\n', consumer, missing),
            ('closing text stays fenced', EMPTY + '```\n``` text\n' + fake_block + '```\n', consumer, missing),
            ('closing whitespace', EMPTY + '```\n' + fake_block + '``` \t\n' + real_inline, consumer, []),
            ('commented producer', EMPTY + commented, consumer, missing),
            ('comment token inside example', EMPTY + '```\n<!--\n```\n' + real_inline, consumer, []),
            ('comment token in fence metadata', EMPTY + '```markdown <!--\n' + fake_block + '```\n' + real_inline, consumer, []),
            ('backticks after comment terminator', EMPTY + '<!--\n-->```\n' + real_inline, consumer, []),
            ('tildes after comment terminator', EMPTY + '<!--\n-->~~~\n' + real_inline, consumer, []),
            ('adjacent examples', EMPTY + '```\nexample\n```\n~~~\n' + fake_block + '~~~\n', consumer, missing),
            ('unclosed fence', EMPTY + '```\n' + fake_block, consumer, missing),
            ('unclosed comment', EMPTY + '<!--\n' + fake_block, consumer, missing),
            ('inline before comment', real_inline + commented, consumer, []),
            ('inline after comment', commented + real_inline, consumer, []),
            ('block before comment', real_block + commented, consumer, []),
            ('block after comment', commented + real_block, consumer, []),
            ('quoted opener', real_block, citation_prefix + ':1 — "<!--"`\n', []),
            ('quoted single tick then opener', real_block, citation_prefix + ':1 — "a ` <!--"`\n', []),
            ('quoted repeated tick then opener', real_block, citation_prefix + ':1 — "a ```` <!--"`\n', []),
            ('quoted terminator', real_block, citation_prefix + ':1 — "-->"`\n', []),
            ('quoted opener then terminator', real_block, citation_prefix + ':1 — "<!-- x -->"`\n', []),
            ('quoted terminator then opener', real_block, citation_prefix + ':1 — "--> x <!--"`\n', []),
            ('revision and range quote', real_block, citation_prefix + '@abc1234:1-2 — "a ` <!--"`\n', []),
            ('empty quote', real_block, citation_prefix + ':1 — ""`\n', malformed),
            ('two citations on one line', real_block, citation_prefix + ':1 — "first"` - `plan` exists `plan.md:1 — "second"`\n', malformed),
            ('citation then unclosed outside comment', real_block, citation_prefix + ':1 — "first"` <!--\n', malformed),
            ('citation inside true fence', real_block, consumer + '```\n  - `plan` exists `plan.md:1 — "a ` <!--"`\n```\n', []),
            ('citation inside comment', real_block, consumer + '<!--\n  - `plan` exists `plan.md:1 — "a ` <!--"`\n-->\n', []),
            ('unclosed fence after producer', real_inline + '```\n- **Produces**: `demo/tail` — hidden\n', tail_consumer, missing_tail),
            ('unclosed comment after producer', real_inline + '<!--\n- **Produces**: `demo/tail` — hidden\n', tail_consumer, missing_tail),
            ('commented consumes field', real_block, '- **Produces**: none\n<!--\n- **Consumes**:\n  - `plan` exists `plan.md:1 — "a ` <!--"`\n-->\n', ['missing ledger: %s' % TB]),
        ]
        for marker, label in (('<!--', 'opener'), ('-->', 'terminator')):
            inline = '- **Produces**: `demo/%s` — literal symbol\n- **Consumes**: none\n- **Produces**: `demo/output` — actual following field\n' % marker
            block = '- **Produces**:\n  - `demo/%s` — literal symbol\n  - `demo/output` — actual following subitem\n- **Consumes**: none\n' % marker
            valid = '- **Produces**: none\n- **Consumes**:\n  - `demo/%s` from %s\n  - `demo/output` from %s\n' % (marker, TA, TA)
            wrong = '- **Produces**: none\n- **Consumes**:\n  - `demo/%s` from %s\n  - `demo/output` from %s\n' % (marker, TZ, TA)
            cases.extend([
                ('inline producer ' + label + ' valid owner', inline, valid, []),
                ('block consume ' + label + ' wrong owner', block, wrong,
                 ['wrong producer: demo/%s in %s names %s, produced by %s' % (marker, TB, TZ, TA)]),
            ])
        cases.append((
            'symbol span then real outside comment',
            '- **Produces**:\n  - `demo/<!--` — literal symbol <!--\n- **Produces**:\n  - `demo/fake` — commented only\n-->\n- **Produces**: `demo/output` — actual following field\n- **Consumes**: none\n',
            '- **Produces**: none\n- **Consumes**:\n  - `demo/output` from %s\n  - `demo/fake` from %s\n' % (TA, TA),
            ['missing producer: demo/fake in %s' % TB],
        ))
        for name, ledger01, ledger02, expected_lines in cases:
            with self.subTest(case=name):
                ws = Workspace(self)
                ws.adopt(ledger01=ledger01, ledger02=ledger02)
                verdict, child = base.run_row(18, ws.root, None)
                lines = [line for line in child.stdout.decode().splitlines() if line]
                self.assertEqual(verdict, 'FAIL' if expected_lines else 'PASS')
                self.assertEqual(lines, expected_lines)

    def test_legacy_briefs_and_decisions_are_silent(self):
        ws = Workspace(self)
        for task in (TA, TB):
            ws.write(ws.brief(task), re.sub(r'^- \*\*Detail\*\*: .*\n', '', ws.read(ws.brief(task)), flags=re.M))
        ws.decide(decision(3, supersedes=DB))
        self.assert_only(ws, 18, [])

    def test_row_18_reports_each_planted_ledger_defect(self):
        consume = '- **Produces**: none\n- **Consumes**:\n  - `%s` %s\n'
        cases = [
            (dict(second='someday'), None, ['invalid detail: %s someday' % TB]),
            (dict(ledger02='- **Errors**: none.\n'), None, ['missing ledger: %s' % TB]),
            (dict(ledger02='- **Produces**:\n  - `demo/output`\n- **Consumes**: none\n'), None,
             ['double producer: demo/output by %s %s' % (TA, TB)]),
            (dict(ledger02=consume % ('demo/missing', 'from ' + TA)), None, ['missing producer: demo/missing in %s' % TB]),
            (dict(ledger02=consume % ('demo/output', 'from ' + TZ)), None,
             ['wrong producer: demo/output in %s names %s, produced by %s' % (TB, TZ, TA)]),
            (dict(ledger02=consume % ('demo/output', 'somewhere')), None, ['malformed consume: demo/output in %s' % TB]),
            (dict(), ('task-board.md', ROW2, row(TB, 'Experiment', 'none', 'pending', 'Draft')),
             ['consumer without dependency: demo/output in %s on %s' % (TB, TA)]),
            (dict(second='interface'), ('task-board.md', ROW2, row(TB, 'Experiment', TA, 'ready: plan.md', 'Ready to run')),
             ['interface brief ready: %s' % TB]),
        ]
        for adopt, edit, lines in cases:
            with self.subTest(lines=lines):
                ws = Workspace(self)
                ws.adopt(**adopt)
                if edit:
                    ws.sub(*edit)
                self.assert_only(ws, 18, lines)

    def test_row_18_accepts_pinned_and_unpinned_exists_sources(self):
        for source in ('exists `plan.md:1 — "# "`', 'exists `plan.md@abc1234:1 — "# "`'):
            with self.subTest(source=source):
                ws = Workspace(self)
                ws.adopt(ledger02=LEDGER_T02 + '  - `plan` ' + source + '\n')
                self.assert_only(ws, 18, [])

    def test_row_19_reports_each_planted_ownership_defect(self):
        cases = [
            (decision(3, owner=TZ), ['unknown owner: %s %s' % (DC, TZ)]),
            (decision(3, owner=TB, clauses=CL), ['owner brief missing %s: %s' % (DC, TB), 'clause not compiled: %s %s %s' % (DC, CL, TB)]),
            (decision(3, owner=TA, supersedes=DB), ['stale supersede: %s supersedes %s (in force: %s)' % (DC, DB, DA)]),
        ]
        for entry, lines in cases:
            with self.subTest(lines=lines):
                ws = Workspace(self)
                ws.adopt()
                ws.cite(TA, DC)
                ws.decide(entry)
                self.assert_only(ws, 19, lines)

    def test_row_19_reports_a_seal_race_between_unordered_open_owners(self):
        ws = Workspace(self)
        ws.adopt(ledger02=EMPTY)
        ws.sub('task-board.md', ROW2, row(TB, 'Experiment', 'none', 'pending', 'Draft'))
        ws.sub('task-board.md', ROW1, row(TA, 'Standard work', 'none', 'pending', 'Draft'))
        compiled = ws.read(ws.brief(TA)).split('### Shared clauses (compiled)', 1)[1].split('### Interface', 1)[0]
        ws.write(ws.brief(TB), ws.read(ws.brief(TB)) + compiled)
        ws.cite(TA, DC)
        ws.cite(TB, DD)
        ws.decide(decision(3, owner=TA, clauses=CL))
        ws.decide(decision(4, owner=TB, clauses=CL))
        result = ws.rows()
        self.assertEqual(result[19][1], ['seal race: %s %s %s' % (CL, TA, TB)], result[19])
        self.assertEqual({n for n, (verdict, _) in result.items() if verdict != 'PASS'}, {19}, result)

    def test_row_2_reports_dependencies_and_requirements_left_to_skipped_tasks(self):
        ws = Workspace(self)
        ws.adopt()
        ws.sub('task-board.md', ROW1, row(TA, 'Standard work', 'none', 'reports/%s-report.md' % TA, 'Skipped'))
        self.assert_only(ws, 2, ['dependency on skipped: %s on %s' % (TB, TA)])

        ws = Workspace(self)
        ws.adopt()
        ws.sub('plan.md', '| Task | Responsibility |\n|---|---|\n| %s | Standard work |\n| %s | Experiment |' % (TA, TB),
               '| Task | Responsibility | Traces to |\n|---|---|---|\n| %s | Standard work | `%s` |\n| %s | Experiment | `%s` |' % (TA, RA, TB, RB))
        ws.sub('task-board.md', ROW2, row(TB, 'Experiment', TA, 'pending', 'Skipped'))
        self.assert_only(ws, 2, ['dead requirement owner: %s' % RB])

    def test_row_2_counts_only_unfenced_requirement_definitions(self):
        definition = '### REQ-FIXTURE-4101 · Sentinel requirement\n\nTask: T-4101\nState: open\n\nScenario: example\n'
        examples = ('Mention REQ-FIXTURE-4101 here.\n\n'
                    '```\n### REQ-FIXTURE-4101 · Example\n```\n'
                    '````markdown\n```sh\n### REQ-FIXTURE-4101 · Nested example\n```\n````\n'
                    '~~~~markdown\n<!--\n~~~\n### REQ-FIXTURE-4101 · Nested example\n~~~~~\n'
                    '<!--\n### REQ-FIXTURE-4101 · Comment\n-->\n')
        for content, expected in (
            (definition + examples, []),
            (definition + examples + definition, ['duplicate requirement definition: REQ-FIXTURE-4101']),
        ):
            with self.subTest(expected=expected):
                ws = Workspace(self)
                ws.write('requirements-delta.md', content)
                verdict, child = base.run_row(2, ws.root, None)
                self.assertEqual(child.stdout.decode().splitlines(), expected)
                self.assertEqual(verdict, 'FAIL' if expected else 'PASS')


if __name__ == '__main__':
    unittest.main()
