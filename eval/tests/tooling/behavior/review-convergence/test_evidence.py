"""Missing, malformed, unknown or contradictory evidence is invalid, never a pass.

Records that would otherwise pass are edited in a temporary copy, so each test changes one thing.
"""
import hashlib
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
SCORER = ROOT / 'eval/behavior/review_convergence/scorer.py'
CATALOG = ROOT / 'eval/behavior/review_convergence/cases.json'
FIXTURES = ROOT / 'eval/behavior/review_convergence/fixtures'


def load_scorer():
    spec = importlib.util.spec_from_file_location('review_convergence_scorer', SCORER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scorer = load_scorer()
        cls.catalog = json.loads(CATALOG.read_text(encoding='utf-8'))

    def setUp(self):
        self.workdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.workdir.cleanup)
        self.target = Path(self.workdir.name) / 'record'
        self.target.mkdir()

    def copy_fixture(self, case, variant):
        for item in (FIXTURES / case / variant).iterdir():
            if item.is_file():
                shutil.copy(item, self.target / item.name)

    def write_record(self, record):
        (self.target / 'record.json').write_text(json.dumps(record))

    def edited(self, case, variant, edit):
        self.copy_fixture(case, variant)
        record = json.loads((self.target / 'record.json').read_text())
        edit(record)
        self.write_record(record)

    def assert_verdict(self, verdict):
        result = self.scorer.judge(self.target)
        self.assertEqual(result['verdict'], verdict, result)
        self.assertTrue(result['reasons'], result)
        return result

    def assert_invalid(self):
        return self.assert_verdict('invalid')

    def test_missing_record_directory_is_invalid(self):
        self.target = Path(self.workdir.name) / 'absent'
        self.assert_invalid()

    def test_missing_record_file_is_invalid(self):
        self.assert_invalid()

    def test_malformed_json_is_invalid(self):
        (self.target / 'record.json').write_text('{"schema": ')
        self.assert_invalid()

    def test_missing_task_revision_is_invalid(self):
        self.edited('repeated_finding', 'v05', lambda record: record['task'].pop('revision'))
        self.assert_invalid()

    def test_missing_transcript_reference_is_invalid(self):
        self.edited('repeated_finding', 'v05', lambda record: record.pop('transcript_sha256'))
        self.assert_invalid()

    def test_transcript_reference_must_be_a_sha256_digest_or_null(self):
        for value in ('ABC', 'g' * 64, 12):
            with self.subTest(value=value):
                self.edited('repeated_finding', 'v05', lambda record, item=value: record.update(transcript_sha256=item))
                self.assert_invalid()

    def test_unknown_case_is_invalid(self):
        self.edited('repeated_finding', 'v05', lambda record: record.update(case='invented'))
        self.assert_invalid()

    def test_unknown_status_is_invalid(self):
        for status in ('Done', 'Closed', 'complete', 'Accepted '):
            with self.subTest(status=status):
                self.edited('repeated_finding', 'v05', lambda record, value=status: record['task'].update(status=value))
                self.assert_invalid()

    def test_accepted_statuses_reject_open_blocking(self):
        for status in self.catalog['shared']['accepted']:
            with self.subTest(status=status):
                self.edited('repeated_finding', 'v07', lambda record, value=status: record['task'].update(status=value))
                result = self.scorer.judge(self.target)
                self.assertEqual(result['verdict'], 'fail', result)
                self.assertTrue(any('open blocking' in reason for reason in result['reasons']), result)

    def test_unknown_finding_kind_is_invalid(self):
        self.edited('repeated_finding', 'v05', lambda record: record['findings'][0].update(kind='nit'))
        self.assert_invalid()

    def test_unknown_event_kind_is_invalid(self):
        self.edited('repeated_finding', 'v05', lambda record: record['events'][0].update(kind='guess'))
        self.assert_invalid()

    def test_round_citing_unknown_event_is_invalid(self):
        self.edited('repeated_finding', 'v05', lambda record: record['rounds'][0].update(source_event_ids=['event-missing']))
        self.assert_invalid()

    def test_round_without_source_events_is_invalid(self):
        self.edited('repeated_finding', 'v05', lambda record: record['rounds'][0].pop('source_event_ids'))
        self.assert_invalid()

    def test_new_evidence_must_resolve_to_an_evidence_event(self):
        self.edited('repeated_finding', 'v05', lambda record: record['findings'][1].update(new_evidence=['event-alpha']))
        self.assert_invalid()

    def test_unknown_review_verdict_is_invalid(self):
        self.edited('repeated_finding', 'v05', lambda record: record['rounds'][1].update(verdict='MAYBE'))
        self.assert_invalid()

    def test_missing_child_result_is_invalid(self):
        self.edited('counter_evidence', 'v06', lambda record: record['events'][2].pop('result'))
        self.assert_invalid()

    def test_missing_child_result_row_is_invalid(self):
        self.edited('counter_evidence', 'v06', lambda record: record.update(events=[event for event in record['events'] if event.get('name') != 'lock-check']))
        self.assert_invalid()

    def test_boolean_child_exit_is_invalid(self):
        self.edited('counter_evidence', 'v06', lambda record: record['events'][2].update(exit=False))
        self.assert_invalid()

    def test_counter_without_source_events_is_invalid(self):
        self.edited('counter_evidence', 'v06', lambda record: record['counter'].pop('source_event_ids'))
        self.assert_invalid()

    def test_forged_reset_in_segments_still_fails(self):
        def reset(record):
            record['counter']['cycles_spent'] = 0
            record['segments'][0]['cycles'] = 0
        self.edited('counter_evidence', 'v06', reset)
        result = self.scorer.judge(self.target)
        self.assertEqual(result['verdict'], 'fail', result)
        self.assertEqual(len(result['reasons']), 2, result)

    def test_boolean_phase_exit_is_invalid(self):
        self.edited('unrun_phases', 'v05', lambda record: record['events'][2].update(exit=False))
        self.assert_invalid()

    def test_unknown_review_decision_in_phases_is_invalid(self):
        self.edited('unrun_phases', 'v05', lambda record: record['events'][3].update(verdict='PASS'))
        self.assert_invalid()

    def test_contradictory_consumer_result_is_invalid(self):
        self.edited('correction_regression', 'v01', lambda record: record['consumer_results'][1].update(result='pass'))
        self.assert_invalid()

    def test_missing_consumer_result_is_invalid(self):
        self.edited('correction_regression', 'v04', lambda record: record['consumer_results'].pop())
        self.assert_invalid()

    def test_unknown_consumer_result_is_invalid(self):
        self.edited('correction_regression', 'v04', lambda record: record['consumer_results'][0].update(result='partial'))
        self.assert_invalid()

    def test_record_cannot_override_the_frozen_sensitive_keys(self):
        self.edited('sensitive_markdown', 'v01', lambda record: record.update(sensitive_keys=[]))
        result = self.scorer.judge(self.target)
        self.assertEqual(result['verdict'], 'fail', result)

    def test_consumer_name_must_be_a_bare_file_name(self):
        for name in ('../consumer.py', 'nested/consumer.py'):
            with self.subTest(name=name):
                self.edited('security_regression', 'v04', lambda record, value=name: record.update(consumer=value))
                self.assert_invalid()

    def test_consumer_bytes_must_match_the_pinned_digest(self):
        self.edited('security_regression', 'v04', lambda record: None)
        (self.target / 'consumer.py').write_text('def confine(path, root):\n    return True\n')
        self.assert_invalid()

    def test_changed_file_digest_must_match_the_executed_consumer(self):
        def other_digest(record):
            record['changed_files'][0]['sha256'] = '0' * 64
        self.edited('security_regression', 'v04', other_digest)
        self.assert_invalid()

    def test_consumer_that_raises_is_invalid(self):
        self.edited('security_regression', 'v04', lambda record: None)
        source = 'raise RuntimeError("unavailable")\n'
        (self.target / 'consumer.py').write_text(source)
        self.write_pinned_record(source)
        self.assert_invalid()

    def test_consumer_returning_a_non_boolean_is_invalid(self):
        self.edited('security_regression', 'v04', lambda record: None)
        source = 'def confine(path, root):\n    return 1\n'
        (self.target / 'consumer.py').write_text(source)
        self.write_pinned_record(source)
        self.assert_invalid()

    def write_pinned_record(self, source):
        record = json.loads((self.target / 'record.json').read_text())
        pinned = hashlib.sha256(source.encode('utf-8')).hexdigest()
        record['consumer_sha256'] = pinned
        record['changed_files'][0]['sha256'] = pinned
        self.write_record(record)

    def test_missing_consumer_file_is_invalid(self):
        self.copy_fixture('security_regression', 'v04')
        (self.target / 'consumer.py').unlink()
        self.assert_invalid()

    def test_security_flag_contradicting_the_frozen_standard_is_invalid(self):
        self.edited('security_regression', 'v04', lambda record: record['changed_files'][0].update(security=False))
        self.assert_invalid()

    def test_score_target_contradicting_the_frozen_threshold_is_invalid(self):
        self.edited('unreachable_acceptance', 'v01', lambda record: record['gate'].update(threshold=0.5))
        self.assert_invalid()

    def test_missing_decision_packet_key_is_invalid(self):
        self.edited('unreachable_acceptance', 'v02', lambda record: record.pop('decision_packet'))
        self.assert_invalid()

    def test_malformed_decision_packet_is_invalid(self):
        self.edited('unreachable_acceptance', 'v06', lambda record: record.update(decision_packet={'question': 'q'}))
        self.assert_invalid()

    def test_unknown_request_kind_is_invalid(self):
        self.edited('unbounded_preparation', 'v06', lambda record: record['requests'][0].update(kind='expansion'))
        self.assert_invalid()

    def test_unknown_request_decision_is_invalid(self):
        self.edited('unbounded_preparation', 'v06', lambda record: record['requests'][0].update(decision='pending'))
        self.assert_invalid()

    def test_accepted_extension_without_size_is_invalid(self):
        self.edited('unbounded_preparation', 'v06', lambda record: record['requests'][0].pop('to_size'))
        self.assert_invalid()


if __name__ == '__main__':
    unittest.main()
