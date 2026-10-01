"""Proposal: drive row 16 and the shipped retro recipe with lifecycle evidence fixtures."""
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
ROWS = ROOT / 'eval/tests/product/lint/rows'
LESSONS = ROOT / 'eval/tests/product/lessons'
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROWS))
sys.path.insert(0, str(LESSONS))

# These sibling test modules own the real command extraction and disposable-workspace
# execution helpers. Import as module aliases so unittest does not rediscover their cases.
import test_row_contracts as row_contracts  # noqa: E402
import test_coverage_table as retro_consumer  # noqa: E402


ROW_HEADER = row_contracts.HEADER
CARRIED_POINT = row_contracts.CARRIED
V2_SCHEMA = 'Schema: tackle-observability/2\n'
REVIEW_RUN = '2026-09-20-s1/T-A/Reviewer/01'
DRIVER_RUN = '2026-09-20-s1/T-A/Driver/01'
START_AT = '2026-09-20T10:00:00Z'
FINISH_AT = '2026-09-20T10:04:00Z'

def role_event(kind, *, run_id=REVIEW_RUN, task='T-A', role='Reviewer', at='n/a',
               outcome='running', attempts='n/a', rework='n/a', verification='n/a',
               source='synthetic'):
    cells = [run_id, kind, task, role, 'generic', 'standard', 'n/a', 'n/a', at,
             outcome, attempts, rework, verification, source]
    return '| ' + ' | '.join(cells) + ' |\n'


def ledger_pair(*, run_id=REVIEW_RUN, start_at='n/a', finish_at='n/a',
                outcome='success', attempts='n/a', rework='n/a',
                verification='n/a', source='synthetic'):
    return (V2_SCHEMA + ROW_HEADER
            + role_event('start', run_id=run_id, at=start_at, outcome='running')
            + role_event('finish', run_id=run_id, at=finish_at, outcome=outcome,
                         attempts=attempts, rework=rework, verification=verification,
                         source=source))


def trace_record(event_id='cycle-alpha', *, run_id=DRIVER_RUN, task='T-A', role='Driver',
                 kind='correction-validation', failure_id='fault-alpha',
                 observed='checker exited 1 where the corrected output was expected',
                 correction='added the missing output guard',
                 command='python3 check.py', result='exit 1; expected valid output, observed diagnostic',
                 cycle_count='1', authorization='n/a'):
    return ('Task: ' + task + '\n'
            'Event ID: ' + event_id + '\n'
            'Run ID: ' + run_id + '\n'
            'Role: ' + role + '\n'
            'Kind: ' + kind + '\n'
            'Failure ID: ' + failure_id + '\n'
            'Observed failure: ' + observed + '\n'
            'Correction: ' + correction + '\n'
            'Validation command: ' + command + '\n'
            'Result: ' + result + '\n'
            'Cycle count: ' + cycle_count + '\n'
            'Authorization: ' + authorization + '\n')


def history(records):
    body = ['# Synthetic append-only task history\n']
    for anchor, entries in records:
        body.extend(['\n### ' + anchor + '\n\n'])
        body.extend(entries)
    return ''.join(body)


def run_retro(ledger_text):
    with tempfile.TemporaryDirectory(prefix='tackle-lifecycle-proposal-') as scratch:
        lifecycle = Path(scratch) / 'resource-usage.md'
        lifecycle.write_text(ledger_text, encoding='utf-8')
        command = retro_consumer.extract_fixture_recipe_command()
        return retro_consumer.run_in_workspace(command, lifecycle, sidecar_path=None)


class LifecycleSemanticsTests(unittest.TestCase):
    def assert_valid_row(self, files):
        result = row_contracts.run_row(16, files)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '', ''))

    def assert_rejected_row(self, files, run_id=REVIEW_RUN, field=None):
        result = row_contracts.run_row(16, files)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertEqual(result.stderr, '')
        self.assertIn('row16:', result.stdout)
        self.assertIn(run_id, result.stdout)
        if field is not None:
            self.assertIn(field, result.stdout)

    def test_reviewer_success_can_report_a_blocked_product(self):
        ledger = ledger_pair(start_at=START_AT, finish_at=FINISH_AT, outcome='success',
                             verification='Product acceptance is BLOCKED pending independent evidence.')
        self.assert_valid_row({'resource-usage.md': ledger})
        child = run_retro(ledger)
        self.assertEqual((child.returncode, child.stderr), (0, ''))
        self.assertEqual(child.stdout.splitlines(),
                         ['tokens 0/N (0%)', 'duration 1/1 (100%)'])

    def test_declared_role_outcomes_are_accepted(self):
        for outcome in ('success', 'failed', 'blocked', 'aborted'):
            with self.subTest(outcome=outcome):
                ledger = (V2_SCHEMA + ROW_HEADER
                          + role_event('start', outcome='running')
                          + role_event('finish', outcome=outcome))
                self.assert_valid_row({'resource-usage.md': ledger})

        invalid = (
            ('start marked success',
             V2_SCHEMA + ROW_HEADER + role_event('start', outcome='success')
             + role_event('finish', outcome='success')),
            ('finish marked complete',
             V2_SCHEMA + ROW_HEADER + role_event('start', outcome='running')
             + role_event('finish', outcome='complete')),
            ('finish left in progress',
             V2_SCHEMA + ROW_HEADER + role_event('start', outcome='running')
             + role_event('finish', outcome='running')),
            ('product prose in role outcome',
             V2_SCHEMA + ROW_HEADER + role_event('start', outcome='running')
             + role_event('finish', outcome='product BLOCKED awaiting evidence')),
            ('incomplete observation has product status',
             V2_SCHEMA + ROW_HEADER + role_event('start', outcome='running')
             + role_event('observe-incomplete', outcome='blocked')),
        )
        for label, ledger in invalid:
            with self.subTest(invalid_outcome=label):
                self.assert_rejected_row({'resource-usage.md': ledger})

    def test_unknowns_survive_a_carried_point_header_without_a_sidecar(self):
        ledger = (CARRIED_POINT + '\nSchema: tackle-observability/2\n' + ROW_HEADER
                  + role_event('start', at='n/a', outcome='running', attempts='n/a', rework='n/a')
                  + role_event('observe-incomplete', at='n/a', outcome='incomplete',
                               attempts='n/a', rework='n/a', source='coordinator-observed'))
        self.assert_valid_row({'resource-usage.md': ledger})
        child = run_retro(ledger)
        self.assertEqual((child.returncode, child.stderr), (0, ''))
        self.assertEqual(child.stdout.splitlines(),
                         ['tokens 0/N (0%)', 'duration 0/N (0%)'])

    def test_linked_task_correction_cycles_accept_relative_and_stable_references(self):
        entry = trace_record()
        evidence = history([('Cycle alpha', [entry])])
        alternate = ('# Synthetic external correction receipt\n\n### Event cycle-alpha\n\n'
                     'Task ID: T-A\n'
                     'Fault: fault-alpha\n'
                     'Observed: checker returned a diagnostic instead of the required output\n'
                     'Repair: added the missing output guard\n'
                     'Check: python3 check.py; exit 1\n'
                     'Counted cycle: 1\n')
        references = (
            ('relative history path and anchor', 'history.md#cycle-alpha', 'n/a',
             {'history.md': evidence}),
            ('external receipt with an equivalent stable event id',
             'evidence/correction-receipt.md#event-cycle-alpha', 'cycle-alpha',
             {'evidence/correction-receipt.md': alternate}),
        )
        for label, source, verification, record_files in references:
            with self.subTest(reference=label):
                ledger = ledger_pair(attempts='1', source=source, verification=verification)
                self.assert_valid_row({'resource-usage.md': ledger, **record_files})

        markdown_link = ledger_pair(
            attempts='1', verification='cycle-alpha',
            source='[receipt](evidence/correction-receipt.md#event-cycle-alpha)')
        self.assert_valid_row({'resource-usage.md': markdown_link,
                               'evidence/correction-receipt.md':
                                   alternate.replace('Counted cycle: 1\n', '')})
        verification_only = ledger_pair(
            attempts='1', source='n/a',
            verification='evidence/correction-receipt.md#event-cycle-alpha')
        self.assert_valid_row({'resource-usage.md': verification_only,
                               'evidence/correction-receipt.md': alternate})

        stable_only = ledger_pair(attempts='1', source='n/a', verification='cycle-alpha')
        self.assert_valid_row({'resource-usage.md': stable_only, 'history.md': evidence})

        two_cycles = history([
            ('Cycle alpha', [trace_record()]),
            ('Cycle beta', [trace_record(
                event_id='cycle-beta', run_id='2026-09-20-s1/T-A/Driver/02',
                failure_id='fault-beta',
                observed='the second corrected output still omitted its required marker',
                correction='added the second output marker',
                result='exit 1; expected both markers, observed only the first',
            )]),
        ])
        self.assert_valid_row({
            'resource-usage.md': ledger_pair(attempts='2', source='history.md'),
            'history.md': two_cycles,
        })
        # An earlier count remains supported when the append-only trace gains a later cycle.
        self.assert_valid_row({
            'resource-usage.md': ledger_pair(attempts='1', source='history.md'),
            'history.md': two_cycles,
        })
        same_fault_two_repairs = history([
            ('Cycle alpha', [trace_record()]),
            ('Cycle beta', [trace_record(event_id='cycle-beta', failure_id='fault-alpha',
                                        correction='a second distinct repair of the same fault',
                                        command='python3 verify_second_repair.py',
                                        result='exit 1; second repair still failed validation')]),
        ])
        self.assert_valid_row({'resource-usage.md': ledger_pair(attempts='2', source='history.md'),
                               'history.md': same_fault_two_repairs})

    def test_attempt_counts_reject_missing_wrong_and_keyword_only_evidence(self):
        valid_entry = trace_record()
        cases = (
            ('missing reference', 'synthetic', history([('Cycle alpha', [valid_entry])])),
            ('missing target', 'history.md#cycle-missing', history([('Cycle alpha', [valid_entry])])),
            ('wrong task', 'history.md#cycle-alpha',
             history([('Cycle alpha', [trace_record(task='T-B')])])),
            ('keyword-only text', 'history.md#cycle-alpha',
             '# Synthetic append-only task history\n\n### Cycle alpha\n\nattempt 1 failed\n'),
        )
        for label, source, evidence in cases:
            with self.subTest(case=label):
                ledger = ledger_pair(attempts='1', source=source)
                self.assert_rejected_row({'resource-usage.md': ledger, 'history.md': evidence},
                                         field='Attempts')

        # A linked external receipt cannot turn its own claim into proof of a cycle.
        claim_only = ('# Synthetic external correction receipt\n\n'
                      '### Event cycle-alpha\n\n'
                      'Task ID: T-A\n'
                      'Counted cycle: 1\n')
        receipt_path = 'evidence/claim-only.md'
        ledger = ledger_pair(attempts='1',
                             source=receipt_path + '#event-cycle-alpha',
                             verification='cycle-alpha')
        self.assert_rejected_row({'resource-usage.md': ledger, receipt_path: claim_only},
                                 field='Attempts')
        command_only = trace_record(command='echo failed', result='success; exit 0')
        self.assert_rejected_row({
            'resource-usage.md': ledger_pair(attempts='1', source='history.md#cycle-alpha'),
            'history.md': history([('Cycle alpha', [command_only])]),
        }, field='Attempts')
        for padded in ('01', '00'):
            self.assert_rejected_row({'resource-usage.md': ledger_pair(attempts=padded,
                                                                        source='synthetic')},
                                     field='Attempts')

    def test_initial_validation_dispatch_and_repeated_fault_tests_do_not_count(self):
        initial = trace_record(event_id='initial-alpha', kind='initial-validation', cycle_count='0')
        dispatch = trace_record(event_id='dispatch-alpha', kind='dispatch', cycle_count='0')
        cases = (
            ('initial validation', history([('Cycle initial-alpha', [initial])]), '1'),
            ('routine dispatch', history([('Cycle dispatch-alpha', [dispatch])]), '1'),
            ('retest of the same implementation fault',
             history([('Correction trace fault-alpha', [
                 trace_record(),
                 trace_record(event_id='retest-alpha', kind='repeated-test', cycle_count='0'),
             ])]), '2'),
            ('initial validation with a false cycle claim',
             history([('Cycle initial-alpha', [trace_record(
                 event_id='initial-alpha', kind='initial-validation', cycle_count='1')])]), '1'),
            ('routine dispatch with a false cycle claim',
             history([('Cycle dispatch-alpha', [trace_record(
                 event_id='dispatch-alpha', kind='dispatch', cycle_count='1')])]), '1'),
            ('retest of the same fault with a false cycle claim',
             history([('Correction trace fault-alpha', [
                 trace_record(),
                 trace_record(event_id='retest-alpha', kind='repeated-test', cycle_count='1'),
             ])]), '2'),
            ('duplicate correction event ID cannot count twice',
             history([('Cycle alpha', [trace_record(), trace_record()])]), '2'),
        )
        for label, evidence, attempts in cases:
            with self.subTest(case=label):
                ledger = ledger_pair(attempts=attempts, source='history.md')
                self.assert_rejected_row({'resource-usage.md': ledger, 'history.md': evidence},
                                         field='Attempts')

    def test_declared_capability_escalation_counts_once_on_first_validation(self):
        brief = '# Task T-A\n\n- **Escalation**: declared\n'
        escalation = trace_record(
            event_id='capability-alpha', kind='declared-capability-escalation', failure_id='n/a',
            observed='the first validation found the requested capability unavailable',
            correction='one declared capability escalation', command='python3 check.py',
            result='unsupported capability observed; one authorized escalation recorded',
            cycle_count='1', authorization='tasks/T-A.md')
        receipt = '# Synthetic external capability receipt\n\n### Event capability-alpha\n\n' + escalation
        receipt_path = 'evidence/capability-escalation-alpha.md'
        ledger = ledger_pair(attempts='1', source=receipt_path + '#event-capability-alpha')
        self.assert_valid_row({'resource-usage.md': ledger, receipt_path: receipt,
                               'tasks/T-A.md': brief})

        counted_twice = ledger_pair(attempts='2', source=receipt_path + '#event-capability-alpha')
        self.assert_rejected_row({'resource-usage.md': counted_twice, receipt_path: receipt,
                                  'tasks/T-A.md': brief}, field='Attempts')
        wrong_brief = '# Task T-B\n\n- **Escalation**: declared\n'
        self.assert_rejected_row({'resource-usage.md': ledger, receipt_path: receipt,
                                  'tasks/T-A.md': wrong_brief}, field='Attempts')
        for misleading in (
            '# Task T-A\n\nThis prose says Escalation: declared.\n',
            '# Task T-A\n\n```markdown\n- **Escalation**: declared\n```\n',
        ):
            self.assert_rejected_row({'resource-usage.md': ledger, receipt_path: receipt,
                                      'tasks/T-A.md': misleading}, field='Attempts')
        named_brief = '# Task T-A — observer\n\n- **Escalation**: declared\n'
        named_receipt = receipt.replace('tasks/T-A.md', 'tasks/T-A-observer.md')
        self.assert_valid_row({'resource-usage.md': ledger, receipt_path: named_receipt,
                               'tasks/T-A-observer.md': named_brief})

        correction = trace_record(event_id='cycle-alpha')
        distinct = history([('Cycle alpha', [correction]),
                            ('Event capability-alpha', [escalation])])
        self.assert_valid_row({'resource-usage.md': ledger_pair(attempts='2', source='history.md'),
                               'history.md': distinct, 'tasks/T-A.md': brief})
        split_references = ledger_pair(
            attempts='2', source='evidence/correction.md#event-cycle-alpha',
            verification=receipt_path + '#event-capability-alpha')
        self.assert_valid_row({'resource-usage.md': split_references,
                               'evidence/correction.md': history([('Event cycle-alpha', [correction])]),
                               receipt_path: receipt, 'tasks/T-A.md': brief})
        duplicate_id = history([('Cycle alpha', [correction]),
                                ('Event cycle-alpha', [escalation.replace(
                                    'Event ID: capability-alpha', 'Event ID: cycle-alpha')])])
        self.assert_rejected_row({'resource-usage.md': ledger_pair(attempts='2', source='history.md'),
                                  'history.md': duplicate_id, 'tasks/T-A.md': brief},
                                 field='Attempts')

    def test_n_a_or_unknown_role_clock_is_never_measured(self):
        for at in ('n/a', 'unknown'):
            with self.subTest(at=at):
                ledger = ledger_pair(start_at=START_AT, finish_at=at, outcome='success',
                                     source='synthetic')
                if at == 'n/a':
                    self.assert_valid_row({'resource-usage.md': ledger})
                child = run_retro(ledger)
                self.assertEqual((child.returncode, child.stderr), (0, ''))
                self.assertEqual(child.stdout.splitlines(),
                                 ['tokens 0/N (0%)', 'duration 0/N (0%)'])


if __name__ == '__main__':
    unittest.main()
