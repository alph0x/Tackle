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
        for number in range(1, 20):
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


if __name__ == '__main__':
    unittest.main()
