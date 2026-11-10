"""Direct record writer guarantees, faults and valid alternatives.

Lifecycle: row 16 rejects missing/shared-cycle evidence and bad transitions; zero with
observed absence and distinct task-linked cycles are valid. Closure: rows 10/14/17
reject a bad receipt or missing obligation; a substantive report and none are valid.
History: row 13 rejects drift/undated entries; dated continuations preserve history.
Compiler: the literal seal command rejects stale hashes; LF and CRLF are valid.
Telemetry: field_report must not allocate session observations to roles; unavailable
metrics remain n/a. Filesystem: escapes and links must not mutate targets; a spaced
workspace and replacement of a hardlink are valid.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
SCRIPT = ROOT / 'skills/tackle/scripts/record.py'
sys.path.insert(0, str(ROOT / 'eval/tests/product/lint/rows'))
import test_lint_rows as base
sys.path.insert(0, str(ROOT))
from maintaining import field_report

TASK_ID = 'T' + '-' + '01'
OTHER_TASK_ID = 'T' + '-' + '02'
ACTIVE_DECISION = 'D' + '-' + '01'
INACTIVE_DECISION = 'D' + '-' + '02'
UNKNOWN_DECISION = 'D' + '-' + '999'
FIRST_OBLIGATION = 'O' + '-' + '01'
SECOND_OBLIGATION = 'O' + '-' + '02'
UNKNOWN_OBLIGATION = 'O' + '-' + '999'
FIRST_CLAUSE_ID = 'C' + '01'
CLAUSE_ID = 'C' + '02'
NEXT_CLAUSE_ID = 'C' + '03'
MISSING_CLAUSE_ID = 'C' + '99'
FAILURE_ID = 'f' + '1'


class RecordTool(unittest.TestCase):
    def setUp(self):
        self.new_workspace()

    def new_workspace(self):
        self.temp = tempfile.TemporaryDirectory(prefix='record-tool-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / 'configured root with spaces'
        self.root.mkdir()
        base.materialize(self.root, 'pass-full')
        shutil.copytree(ROOT / 'skills/tackle/scripts', self.root / 'skills/tackle/scripts')
        self.ws = self.root / 'docs/plans/demo'
        # Old renderer scenarios replace the ledger, not the fixture's unrelated run.
        usage = self.ws / 'resource-usage.md'
        usage.write_text('\n'.join(usage.read_text().splitlines()[:6]) + '\n')
        history = self.ws / 'history.md'
        history.write_text(history.read_text().split('### Event cycle-alpha')[0])

    def invoke(self, kind, data, spec='input.json'):
        (self.ws / spec).write_text(json.dumps({'schema': 'tackle-record/1', 'kind': kind, 'data': data}))
        return subprocess.run([sys.executable, '-I', '-B', str(SCRIPT), '--workspace', str(self.ws), '--spec', spec], capture_output=True, text=True)

    def ok(self, kind, data):
        result = self.invoke(kind, data)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['kind'], kind)
        return result

    def snapshot(self):
        return {str(p.relative_to(self.ws)): p.read_bytes() for p in self.ws.rglob('*') if p.is_file() and p.name != 'input.json'}

    def refused(self, kind, data):
        before = self.snapshot()
        result = self.invoke(kind, data)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(result.stdout, '')
        self.assertTrue(result.stderr.startswith('record: '))
        self.assertEqual(before, self.snapshot())

    def lint(self, *rows):
        for row in rows:
            verdict, child = base.run_row(row, self.root, None)
            self.assertEqual(verdict, 'PASS', (row, child.stdout, child.stderr))

    def start(self, run='run-1', role='Driver'):
        self.ok('lifecycle', {'run_id': run, 'event': 'start', 'task': TASK_ID, 'role': role})

    def event(self, event_id, failure, correction, command):
        self.ok('correction', {'event_id': event_id, 'task': TASK_ID, 'run_id': 'run-1',
                'failure_id': 'fault-' + event_id, 'observed_failure': failure,
                'correction': correction, 'validation_command': command, 'result': 'exit 1'})

    def test_reconcile_inserts_start_before_each_orphan_terminal(self):
        usage = self.ws / 'resource-usage.md'
        history = self.ws / 'history.md'
        prefix = usage.read_text()
        old_history = history.read_text()
        first = f'| orphan-run | finish | {TASK_ID} | Executor | demo | fast | model-a | high | 2026-10-01T10:00:00Z | success | n/a | n/a | n/a | n/a |\n'
        normal_start = f'| normal-run  | start | {TASK_ID} | Executor | demo | fast | model-a | high | n/a | running | n/a | n/a | n/a | n/a |\n'
        normal_finish = f'| normal-run | finish  | {TASK_ID} | Executor | demo | fast | model-a | high | n/a | success | n/a | n/a | n/a | n/a |\n'
        last = f'| missing-run | observe-incomplete | {TASK_ID} | Executor | demo | fast | model-a | high | n/a | incomplete | n/a | n/a | n/a | n/a |\n'
        usage.write_text(prefix + first + normal_start + normal_finish + last)
        verdict, child = base.run_row(16, self.root, None)
        self.assertEqual(verdict, 'FAIL', (child.stdout, child.stderr))
        self.ok('reconcile', {'run_id': 'orphan-run', 'event_id': 'recovered-first', 'observed': 'start was not recorded'})
        self.ok('reconcile', {'run_id': 'missing-run', 'event_id': 'recovered-last', 'observed': 'start | absent'})
        start_first = f'| orphan-run | start | {TASK_ID} | Executor | demo | fast | model-a | high | n/a | running | n/a | n/a | n/a | history.md#event-recovered-first |\n'
        start_last = f'| missing-run | start | {TASK_ID} | Executor | demo | fast | model-a | high | n/a | running | n/a | n/a | n/a | history.md#event-recovered-last |\n'
        self.assertEqual(usage.read_text(), prefix + start_first + first + normal_start + normal_finish + start_last + last)
        event_first = f'\n### Event recovered-first\nTask ID: {TASK_ID}\nRun ID: orphan-run\nKind: reconciled-start\nObserved: start was not recorded\n'
        event_last = f'\n### Event recovered-last\nTask ID: {TASK_ID}\nRun ID: missing-run\nKind: reconciled-start\nObserved: start | absent\n'
        self.assertEqual(history.read_text(), old_history + event_first + event_last)
        self.assertFalse((self.ws / 'resource-usage.telemetry.jsonl').exists())
        self.lint(16)

    def test_reconcile_finds_orphan_terminal_across_ledger_blocks(self):
        usage = self.ws / 'resource-usage.md'
        history = self.ws / 'history.md'
        prefix = usage.read_text()
        old_history = history.read_text()

        def row(run, event, empty=False):
            outcome = 'running' if event == 'start' else 'success'
            source = '' if empty else ' n/a '
            return (f'| {run} | {event} | {TASK_ID} | Executor | demo | fast | model-a | high | '
                    f'n/a | {outcome} | n/a | n/a | n/a |{source}|\n')

        normal_start, normal_finish = row('normal-run', 'start'), row('normal-run', 'finish')
        split_start, split_finish = row('split-run', 'start'), row('split-run', 'finish')
        empty_start, empty_finish = row('empty-split', 'start', True), row('empty-split', 'finish')
        near = row('near-orphan', 'finish', True)
        far = row('far-orphan', 'finish')
        first = normal_start + normal_finish + split_start + empty_start
        second = split_finish + near
        third = empty_finish + far
        ledger = prefix + first + '\n' + second + '\nA note between blocks.\n\n' + third
        usage.write_text(ledger)
        verdict, child = base.run_row(16, self.root, None)
        self.assertEqual(verdict, 'FAIL', (child.stdout, child.stderr))

        for run in ('split-run', 'empty-split'):
            before = self.snapshot()
            result = self.invoke('reconcile', {'run_id': run, 'event_id': 'refused-' + run,
                                                'observed': 'start exists'})
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertEqual(result.stdout, '')
            self.assertEqual(result.stderr.strip(), 'record: not an orphan terminal')
            self.assertEqual(self.snapshot(), before)

        self.ok('reconcile', {'run_id': 'far-orphan', 'event_id': 'recovered-far',
                              'observed': 'far start missing'})
        self.ok('reconcile', {'run_id': 'near-orphan', 'event_id': 'recovered-near',
                              'observed': 'near start missing'})
        start_far = row('far-orphan', 'start').replace(' n/a |\n', ' history.md#event-recovered-far |\n')
        start_near = row('near-orphan', 'start').replace(' n/a |\n', ' history.md#event-recovered-near |\n')
        self.assertEqual(usage.read_text(), ledger.replace(far, start_far + far).replace(near, start_near + near))
        events = (f'\n### Event recovered-far\nTask ID: {TASK_ID}\nRun ID: far-orphan\n'
                  'Kind: reconciled-start\nObserved: far start missing\n'
                  f'\n### Event recovered-near\nTask ID: {TASK_ID}\nRun ID: near-orphan\n'
                  'Kind: reconciled-start\nObserved: near start missing\n')
        self.assertEqual(history.read_text(), old_history + events)
        self.lint(16)

    def test_reconcile_refusals_write_nothing(self):
        usage = self.ws / 'resource-usage.md'
        history = self.ws / 'history.md'
        prefix = usage.read_text()
        terminal = f'| orphan-run | finish | {TASK_ID} | Executor | demo | fast | model-a | high | n/a | success | n/a | n/a | n/a | n/a |\n'
        start = terminal.replace(' | finish |', ' | start |').replace(' | success |', ' | running |')
        incomplete = terminal.replace(' | finish |', ' | observe-incomplete |').replace(' | success |', ' | incomplete |')
        data = {'run_id': 'orphan-run', 'event_id': 'recovered', 'observed': 'start missing'}
        cases = [
            (prefix, data),
            (prefix + start + terminal, data),
            (prefix + terminal + incomplete, data),
            (prefix + start, data),
            (prefix + terminal, dict(data, observed='')),
            (prefix + terminal, dict(data, observed='two\nlines')),
            (prefix + terminal, {'run_id': 'orphan-run', 'event_id': 'recovered'}),
            ((prefix + terminal).replace('Schema: tackle-observability/2', ''), data),
            ('# Resource usage\n\n| Task | Role |\n|---|---|\n', data),
            (prefix + terminal + '\n' + '\n'.join(prefix.splitlines()[4:6]) + '\n', data),
            (prefix + terminal + '\n'.join(prefix.splitlines()[4:6]) + '\n', data),
        ]
        for ledger, spec in cases:
            with self.subTest(ledger=ledger, spec=spec):
                usage.write_text(ledger)
                self.refused('reconcile', spec)
        usage.write_text(prefix + terminal)
        history.write_text(history.read_text() + '\n### Event recovered\nTask ID: ' + TASK_ID + '\n')
        self.refused('reconcile', data)

    def test_legacy_zero_one_two_cycles_reach_real_lint(self):
        for attempts in (0, 1, 2):
            with self.subTest(attempts=attempts):
                self.new_workspace()
                if attempts:
                    self.event('run-1-1', 'missing marker', 'add marker', 'check')
                if attempts == 2:
                    self.event('run-1-2', 'missing second marker', 'add second marker', 'check again')
                self.start('case-' + str(attempts))
                data = {'run_id': 'case-' + str(attempts), 'event': 'finish', 'task': TASK_ID,
                        'role': 'Driver', 'attempts': attempts, 'outcome': 'success'}
                if attempts == 0:
                    data['absence'] = {'event_id': 'zero-1', 'observed': 'no corrections observed'}
                else:
                    data.update(source='history.md#run-1-1', verification='history.md')
                self.ok('lifecycle', data)
                self.ok('closure', {'task': TASK_ID, 'remains': 'none'})
                self.lint(10, 14, 16, 17)

    def test_both_missing_evidence_refusals(self):
        self.start()
        for attempts in (0, 1):
            with self.subTest(attempts=attempts):
                self.refused('lifecycle', {'run_id': 'run-1', 'event': 'finish', 'task': TASK_ID,
                                          'role': 'Driver', 'attempts': attempts, 'outcome': 'success'})

    def test_transition_and_scalar_refusals(self):
        common = {'run_id': 'run-1', 'task': TASK_ID, 'role': 'Driver'}
        self.refused('lifecycle', dict(common, event='finish', outcome='success'))
        self.start()
        self.refused('lifecycle', dict(common, event='start'))
        for changes in ({'outcome': 'running'}, {'attempts': True}, {'at': '12:34'},
                        {'at': '2026-10-01 10:00:00Z'}, {'at': '2026-10-01T10:00:00'},
                        {'at': '2026-10-01 10:00:00'},
                        {'verification': 'all checks passed'}, {'source': 'history.md | injected'}):
            finish = dict(common, event='finish', outcome='success')
            finish.update(changes)
            self.refused('lifecycle', finish)
        self.ok('lifecycle', dict(common, event='finish', outcome='blocked', at='2026-10-01T10:00:00.125+05:30'))
        self.refused('lifecycle', dict(common, event='observe-incomplete'))
        self.lint(16)

    def test_correction_duplicate_and_passing_result_refused(self):
        self.event('cycle-new', 'missing marker', 'add marker', 'check')
        event = {'event_id': 'cycle-new', 'task': TASK_ID, 'run_id': 'run-1', 'failure_id': FAILURE_ID,
                 'observed_failure': 'missing marker', 'correction': 'add marker',
                 'validation_command': 'check', 'result': 'exit 1'}
        self.refused('correction', event)
        self.refused('correction', dict(event, event_id='cycle-pass', result='exit 0'))

    def test_shared_manual_evidence_and_duplicate_cannot_inflate_count(self):
        history = self.ws / 'history.md'
        manual = (f'\n### Event manual-one\nTask ID: {TASK_ID}\nFault: marker\n'
                  'Observed: missing marker\nRepair: add marker\nCheck: check; exit 1\n'
                  f'\n### Event manual-one\nTask ID: {TASK_ID}\nFault: marker\n'
                  'Observed: missing marker\nRepair: add marker\nCheck: check; exit 1\n')
        old_history = history.read_text()
        self.start()
        finish = {'run_id': 'run-1', 'event': 'finish', 'task': TASK_ID, 'role': 'Driver',
                  'outcome': 'success', 'attempts': 2, 'source': 'history.md#manual-one',
                  'verification': 'history.md'}
        history.write_text(old_history + manual.replace('check; exit 1', 'failed check'))
        self.refused('lifecycle', dict(finish, attempts=1))
        history.write_text(old_history + manual)
        self.refused('lifecycle', finish)
        history.write_text(history.read_text() + manual.replace('manual-one', 'manual-two'))
        self.ok('lifecycle', finish)
        self.lint(16)

    def test_mismatched_role_telemetry_refuses_entire_finish(self):
        self.start()
        record = {'captured_at': '2026-10-01T12:30:00Z', 'collector': 'manual', 'source': 'receipt',
                  'scope': 'role', 'scope_id': 'other', 'run_id': 'other', 'metrics': {},
                  'provenance': 'n/a'}
        self.refused('lifecycle', {'run_id': 'run-1', 'event': 'finish', 'task': TASK_ID,
                                  'role': 'Driver', 'outcome': 'success', 'telemetry': record})

    def test_closure_preserves_report_and_status(self):
        report = self.ws / f'reports/{TASK_ID}-report.md'
        board = self.ws / 'task-board.md'
        before = board.read_text()
        digest = hashlib.sha256((self.ws / f'tasks/{TASK_ID}.md').read_bytes()).hexdigest()
        self.refused('closure', {'task': TASK_ID, 'remains': 'none.'})
        self.refused('closure', {'task': TASK_ID, 'remains': [UNKNOWN_OBLIGATION]})
        self.ok('closure', {'task': TASK_ID, 'remains': 'none'})
        self.assertIn('Reviewer: demo.', report.read_text())
        self.assertIn(digest, report.read_text())
        self.assertEqual(before, board.read_text())
        self.lint(10, 14, 17)

    def test_closure_active_erratum_preserves_original_seal(self):
        self.ok('closure', {'task': TASK_ID, 'remains': 'none'})
        brief = self.ws / f'tasks/{TASK_ID}.md'
        report = self.ws / f'reports/{TASK_ID}-report.md'
        first = hashlib.sha256(brief.read_bytes()).hexdigest()
        brief.write_bytes(brief.read_bytes() + b'\nUpdated content.\n')
        self.refused('closure', {'task': TASK_ID, 'remains': 'none'})
        self.refused('closure', {'task': TASK_ID, 'remains': 'none', 'erratum': INACTIVE_DECISION})
        self.ok('closure', {'task': TASK_ID, 'remains': 'none', 'erratum': ACTIVE_DECISION})
        self.assertIn('**Brief sha256**: ' + first, report.read_text())
        self.assertIn(f'**Brief erratum**: {ACTIVE_DECISION} · sha256 ' + hashlib.sha256(brief.read_bytes()).hexdigest(), report.read_text())
        self.lint(14)

    def test_closure_erratum_active_definition_corpus(self):
        corpus = [
            ('## {} · Demo decision · active · 2026-09-24', True),
            ('## {} · Demo decision · ✅ active · 2026-09-24', True),
            ('## {} · Demo decision ·active· 2026-09-24', True),
            ('## {}\u00a0· Demo decision · active · 2026-09-24', False),
            ('## {} · Demo decision · inactive · 2026-09-24', False),
            ('## {} · Demo decision · proactive · 2026-09-24', False),
            ('## {} · Make active the cache · 2026-09-24', False),
            ('## {} · Demo decision · active · ⤴ superseded by {} · 2026-09-24', False),
            ('## {} · Demo decision · superseded by {} · active · 2026-09-24', False),
            ('## {} · Demo decision · ✅ active · superseded by the owner · 2026-09-24', False),
            ('```text\n## {} · Demo decision · active · 2026-09-24\n```', False),
            ('- {} · active', False),
            ('## {} · Demo decision · 2026-09-24', False),
        ]
        for heading, accepted in corpus:
            with self.subTest(heading=heading):
                self.new_workspace()
                self.ok('closure', {'task': TASK_ID, 'remains': 'none'})
                decisions = self.ws / 'decisions.md'
                text = decisions.read_text()
                decisions.write_text(text.replace(text.splitlines()[2], heading.format(ACTIVE_DECISION, 'D' + '-' + '03')))
                brief = self.ws / f'tasks/{TASK_ID}.md'
                brief.write_bytes(brief.read_bytes() + b'\nUpdated content.\n')
                data = {'task': TASK_ID, 'remains': 'none', 'erratum': ACTIVE_DECISION}
                before = self.snapshot()
                result = self.invoke('closure', data)
                if accepted:
                    self.assertEqual(result.returncode, 0, result.stderr)
                    report = (self.ws / f'reports/{TASK_ID}-report.md').read_text()
                    self.assertIn(f'**Brief erratum**: {ACTIVE_DECISION} · sha256 ' + hashlib.sha256(brief.read_bytes()).hexdigest(), report)
                else:
                    self.assertEqual(result.returncode, 2)
                    self.assertIn('erratum decision not active', result.stderr)
                    self.assertEqual(self.snapshot(), before)

    def test_history_retains_old_entries_and_snapshot(self):
        history = self.ws / 'history.md'
        old = history.read_bytes()
        data = {'heading': '2026-10-01 · session 3 · continuation', 'did': ['Recorded work'],
                'decisions': ['none'], 'blockers': ['none'], 'next': ['Review'],
                'state': {'task_state': 'Complete', 'in_flight': 'none', 'blocked_on': 'none',
                          'resume_from': 'Review', 'checkpoint': 'recorded'}}
        self.refused('history', dict(data, heading='Session notes'))
        self.ok('history', data)
        self.assertTrue(history.read_bytes().startswith(old))
        self.assertIn('Active obligations: none', history.read_text())
        self.refused('history', data)
        self.lint(13, 17)

    def test_open_obligation_in_snapshot_and_closure(self):
        board = self.ws / 'task-board.md'
        board.write_text(board.read_text() + '\n| Obligation | State | Reference |\n|---|---|---|\n'
                         f'| {FIRST_OBLIGATION} | Open | |\n| {SECOND_OBLIGATION} | Open | |\n')
        data = {'heading': '2026-10-02 · session 4 · continuation', 'did': ['Review'],
                'decisions': ['none'], 'blockers': ['none'], 'next': ['Continue'],
                'state': {'task_state': 'Complete', 'in_flight': 'none', 'blocked_on': 'none',
                          'resume_from': 'Continue', 'checkpoint': 'recorded'}}
        self.ok('history', data)
        self.ok('closure', {'task': TASK_ID, 'remains': [FIRST_OBLIGATION]})
        self.assertIn(f'Active obligations: {FIRST_OBLIGATION}, {SECOND_OBLIGATION}', (self.ws / 'history.md').read_text())
        self.lint(13, 17)

    def test_write_modes_respect_umask_and_drop_special_bits(self):
        telemetry = {'captured_at': '2026-10-01T12:30:00Z', 'collector': 'manual', 'source': 'receipt',
                     'scope': 'session', 'scope_id': 'session-1', 'run_id': 'n/a',
                     'metrics': {'input_tokens': 12}, 'provenance': 'observed session total'}
        for mask, expected in ((0o077, 0o600), (0o022, 0o644)):
            with self.subTest(umask=oct(mask)):
                self.new_workspace()
                sidecar = self.ws / 'resource-usage.telemetry.jsonl'
                self.assertFalse(sidecar.exists())
                (self.ws / 'input.json').write_text(json.dumps(
                    {'schema': 'tackle-record/1', 'kind': 'telemetry', 'data': telemetry}))
                result = subprocess.run(
                    [sys.executable, '-I', '-B', str(SCRIPT), '--workspace', str(self.ws), '--spec', 'input.json'],
                    capture_output=True, text=True, preexec_fn=lambda: os.umask(mask))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(sidecar.stat().st_mode & 0o7777, expected)
        for mode, expected in ((0o4644, 0o644), (0o640, 0o640)):
            with self.subTest(existing_mode=oct(mode)):
                self.new_workspace()
                usage = self.ws / 'resource-usage.md'
                before = usage.read_text()
                usage.chmod(mode)
                self.start()
                self.assertNotEqual(usage.read_text(), before)
                self.assertEqual(usage.stat().st_mode & 0o7777, expected)

    def test_telemetry_unallocated_and_invalid_metrics(self):
        data = {'captured_at': '2026-10-01T12:30:00Z', 'collector': 'manual', 'source': 'receipt',
                'scope': 'session', 'scope_id': 'session-1', 'run_id': 'n/a',
                'metrics': {'input_tokens': 12}, 'provenance': 'observed session total'}
        for value in (-1, True, float('nan')):
            self.refused('telemetry', dict(data, metrics={'input_tokens': value}))
        self.refused('telemetry', dict(data, run_id='run-1'))
        self.ok('telemetry', data)
        report = field_report.workspace_report(str(self.root / 'docs/plans'), 'demo')
        self.assertEqual(report['tokens']['value']['session']['input_tokens'], 12)
        self.assertNotIn('role', report['tokens']['value'])

    def test_compile_clause_literal_seal_and_boundaries(self):
        contract = self.ws / 'design-contract.md'
        brief = self.ws / f'tasks/{OTHER_TASK_ID}.md'
        original = brief.read_bytes()
        for newline, title in ((b'\n', b'Second clause'), (b'\r\n', b'Second clause'),
                               (b'\n', b'Literal sha256 ` prefix with **markup**')):
            with self.subTest(newline=newline, title=title):
                brief.write_bytes(original)
                contract.write_bytes(newline.join([b'## ' + CLAUSE_ID.encode() + b' \xc2\xb7 ' + title, b'', b'Nested content.', b'### Detail', b'More.', b'## ' + NEXT_CLAUSE_ID.encode() + b' \xc2\xb7 Next', b'Other.', b'']))
                for example in (b'\n```text\n', b'\n````text\n```\nExample.\n````\n',
                                b'\n~~~text\n```\nExample.\n~~~\n'):
                    brief.write_bytes(original + example)
                    self.refused('compile-clause', {'clause_id': CLAUSE_ID, 'brief': f'tasks/{OTHER_TASK_ID}.md'})
                brief.write_bytes(original)
                self.ok('compile-clause', {'clause_id': CLAUSE_ID, 'brief': f'tasks/{OTHER_TASK_ID}.md'})
                command = base.seal_command().replace('docs/plans/<slug>', 'docs/plans/demo')
                # The first fixture clause is irrelevant to this newly installed contract.
                (self.ws / f'tasks/{TASK_ID}.md').unlink(missing_ok=True)
                child = subprocess.run(['sh', '-c', command], cwd=self.root, capture_output=True, text=True)
                self.assertEqual(child.returncode, 0, (child.stdout, child.stderr))
                self.refused('compile-clause', {'clause_id': CLAUSE_ID, 'brief': f'tasks/{OTHER_TASK_ID}.md'})
        self.refused('compile-clause', {'clause_id': MISSING_CLAUSE_ID, 'brief': f'tasks/{OTHER_TASK_ID}.md'})

    def test_configured_path_escape_symlink_and_hardlink(self):
        outside = self.root.parent / 'outside'
        outside.write_bytes(b'outside unchanged')
        (self.ws / 'tasks/linked.md').symlink_to(outside)
        (self.ws / 'tasks/linked-dir').symlink_to(outside.parent, target_is_directory=True)
        self.refused('compile-clause', {'clause_id': FIRST_CLAUSE_ID, 'brief': '../outside'})
        self.refused('compile-clause', {'clause_id': FIRST_CLAUSE_ID, 'brief': 'tasks/linked.md'})
        self.refused('compile-clause', {'clause_id': FIRST_CLAUSE_ID, 'brief': 'tasks/linked-dir/outside.md'})
        link = self.root.parent / 'workspace-link'
        link.symlink_to(self.ws, target_is_directory=True)
        before = self.snapshot()
        child = subprocess.run([sys.executable, '-I', '-B', str(SCRIPT), '--workspace', str(link),
                                '--spec', 'input.json'], capture_output=True, text=True)
        self.assertEqual(child.returncode, 2, child.stderr)
        self.assertEqual(before, self.snapshot())
        report = self.ws / f'reports/{TASK_ID}-report.md'
        report.unlink()
        os.link(outside, report)
        # A substantive existing report is required, so use a hardlink to that content.
        outside.write_text(f'# {TASK_ID} report\n\nReviewer: demo.\n\n**Remains**: none\n')
        old = outside.read_bytes()
        self.ok('closure', {'task': TASK_ID, 'remains': 'none'})
        self.assertEqual(outside.read_bytes(), old)
        self.assertNotEqual(report.read_bytes(), old)

    def test_closure_preserves_fenced_examples_not_receipts(self):
        for marker in ('```', '~~~'):
            with self.subTest(marker=marker):
                self.new_workspace()
                report = self.ws / f'reports/{TASK_ID}-report.md'
                example = (marker + f'text\n**Remains**: {UNKNOWN_OBLIGATION}\n**Brief sha256**: ' + '0' * 64
                           + f'\n**Brief erratum**: {UNKNOWN_DECISION} · sha256 ' + '1' * 64 + '\n' + marker + '\n')
                report.write_text(f'# {TASK_ID} report\n\nReviewer: demo.\n\n' + example.rsplit(marker, 1)[0])
                self.refused('closure', {'task': TASK_ID, 'remains': 'none'})
                report.write_text(f'# {TASK_ID} report\n\nReviewer: demo.\n\n' + example)
                self.ok('closure', {'task': TASK_ID, 'remains': 'none'})
                self.assertIn(example, report.read_text())
                self.lint(10, 14, 17)

    def test_declared_escalation_requires_real_single_line_authorization(self):
        for declaration, accepted in (
                ('\n```text\n- **Escalation**: declared\n```\n', False),
                ('\n- **Escalation**:\ndeclared\n', False),
                ('\n- **Escalation**: declared\n', True)):
            with self.subTest(declaration=declaration):
                self.new_workspace()
                brief = self.ws / f'tasks/{TASK_ID}.md'
                brief.write_text(brief.read_text() + declaration)
                history = self.ws / 'history.md'
                history.write_text(history.read_text() + (
                    '\n### Event capability-alpha\nRun ID: run-1\nFailure ID: n/a\n'
                    f'Task ID: {TASK_ID}\nEvent ID: capability-alpha\nKind: declared-capability-escalation\n'
                    f'Authorization: tasks/{TASK_ID}.md\nObserved: first validation found the capability unavailable\n'
                    'Correction: one declared capability escalation\nValidation command: check\n'
                    'Result: unsupported capability observed; one authorized escalation recorded\n'))
                self.start()
                finish = {'run_id': 'run-1', 'event': 'finish', 'task': TASK_ID, 'role': 'Driver',
                          'outcome': 'blocked', 'attempts': 1, 'source': 'history.md#capability-alpha',
                          'verification': 'history.md'}
                if accepted:
                    self.ok('lifecycle', finish)
                    self.lint(16)
                else:
                    self.refused('lifecycle', finish)

    def test_manual_heading_whitespace_and_last_alias_match_consumer(self):
        for heading, observed, accepted in (
                ('###\tEvent manual-alias', 'Observed: marker missing', True),
                ('### Event manual-alias', 'Observed failure:\nObserved: marker missing', True),
                ('### Event manual-alias', 'Observed failure: marker missing\nObserved:', False)):
            with self.subTest(heading=heading, observed=observed):
                self.new_workspace()
                history = self.ws / 'history.md'
                history.write_text(history.read_text() + '\n' + heading
                                   + f'\nTask ID: {TASK_ID}\nFault: marker\n' + observed
                                   + '\nRepair: add marker\nCheck: check; exit 1\n')
                self.start()
                finish = {'run_id': 'run-1', 'event': 'finish', 'task': TASK_ID, 'role': 'Driver',
                          'outcome': 'blocked', 'attempts': 1, 'source': 'history.md#manual-alias',
                          'verification': 'history.md'}
                if accepted:
                    self.ok('lifecycle', finish)
                    self.lint(16)
                else:
                    self.refused('lifecycle', finish)

    def test_correction_publication_visible_to_counter_consumer(self):
        for example, accepted in (
                ('\n````text\n```\nExample.\n````\n', False),
                ('\n```text\n~~~\nExample.\n```\n', False),
                ('\n```text\nExample.\n```\n', True),
                ('\n````text\nExample.\n````\n', True),
                ('\n````text\n```sh\nExample.\n```\n````\n', True),
                ('\n~~~text\nExample.\n~~~\n', True)):
            with self.subTest(example=example):
                self.new_workspace()
                history = self.ws / 'history.md'
                history.write_text(history.read_text() + example)
                data = {'event_id': 'reader-event', 'task': TASK_ID, 'run_id': 'run-1',
                        'failure_id': 'marker', 'observed_failure': 'missing marker',
                        'correction': 'add marker', 'validation_command': 'check', 'result': 'exit 1'}
                if accepted:
                    self.ok('correction', data)
                    self.start()
                    self.ok('lifecycle', {'run_id': 'run-1', 'event': 'finish', 'task': TASK_ID,
                                         'role': 'Driver', 'outcome': 'blocked', 'attempts': 1,
                                         'source': 'history.md#reader-event', 'verification': 'history.md'})
                    self.lint(16)
                else:
                    self.refused('correction', data)
