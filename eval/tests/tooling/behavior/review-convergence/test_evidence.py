"""Missing, malformed or contradictory evidence is invalid, never a pass, and an owner packet is an accepted wait."""
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
SCORER = ROOT / 'eval/behavior/review_convergence/scorer.py'
FIXTURES = ROOT / 'eval/behavior/review_convergence/fixtures'


def load_scorer():
    spec = importlib.util.spec_from_file_location('review_convergence_scorer', SCORER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scorer = load_scorer()

    def setUp(self):
        self.workdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.workdir.cleanup)
        self.target = Path(self.workdir.name) / 'record'
        self.target.mkdir()

    def copy_fixture(self, case, side):
        for item in (FIXTURES / case / side).iterdir():
            shutil.copy(item, self.target / item.name)

    def write_record(self, record):
        (self.target / 'record.json').write_text(json.dumps(record))

    def edited_record(self, case, side, edit):
        record = json.loads((FIXTURES / case / side / 'record.json').read_text())
        edit(record)
        self.write_record(record)

    def assert_invalid(self):
        result = self.scorer.judge(self.target)
        self.assertEqual(result['verdict'], 'invalid', result)
        self.assertTrue(result['reasons'], result)

    def test_missing_record_directory_is_invalid(self):
        self.target = Path(self.workdir.name) / 'absent'
        self.assert_invalid()

    def test_missing_record_file_is_invalid(self):
        self.assert_invalid()

    def test_malformed_json_is_invalid(self):
        (self.target / 'record.json').write_text('{"schema": ')
        self.assert_invalid()

    def test_missing_task_field_is_invalid(self):
        self.edited_record('repeated_finding', 'alternative', lambda record: record.pop('task'))
        self.assert_invalid()

    def test_missing_child_result_is_invalid(self):
        def drop_result(record):
            del record['children'][0]['result']
        self.edited_record('counter_evidence', 'alternative', drop_result)
        self.assert_invalid()

    def test_unknown_case_is_invalid(self):
        self.edited_record('repeated_finding', 'alternative', lambda record: record.update(case='invented'))
        self.assert_invalid()

    def test_contradictory_consumer_result_is_invalid(self):
        self.copy_fixture('correction_regression', 'alternative')
        self.edited_record('correction_regression', 'alternative', lambda record: record['consumers'][1].update(result='fail'))
        self.assert_invalid()

    def test_missing_security_consumer_is_invalid(self):
        self.copy_fixture('security_regression', 'alternative')
        (self.target / 'consumer.py').unlink()
        self.assert_invalid()

    def test_counter_evidence_rejects_hidden_timeout(self):
        def time_out(record):
            record['children'][1].update(exit=None, timed_out=True, result='timeout')
        self.edited_record('counter_evidence', 'alternative', time_out)
        result = self.scorer.judge(self.target)
        self.assertEqual(result['verdict'], 'fail', result)

    def test_unreachable_acceptance_accepts_owner_packet(self):
        def wait_with_packet(record):
            record['task']['status'] = 'Waiting on owner'
            record['lock']['verdict'] = 'flagged'
            record['decision_packet'] = {'question': 'accept the sealed ceiling?', 'options': ['accept', 'redesign'], 'default': 'redesign'}
        self.edited_record('unreachable_acceptance', 'fault', wait_with_packet)
        result = self.scorer.judge(self.target)
        self.assertEqual(result['verdict'], 'pass', result)


if __name__ == '__main__':
    unittest.main()
