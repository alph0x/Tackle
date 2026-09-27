"""Harness integrity only: these tests do not execute or score an agent."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('clear_runner', HERE / 'runner.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class CohortTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.cases = json.loads((HERE / 'cases.json').read_text())
        self.oracle = json.loads((HERE / 'oracle.json').read_text())

    def stage(self):
        self.cohort = self.root / 'cohort'
        self.seal = runner.prepare(self.cohort, {'SKILL.md': b'baseline'}, {'SKILL.md': b'candidate'},
                                   self.cases, self.oracle, b'fixed protocol', runner.SMOKE)
        return runner.verify(self.cohort, self.seal)

    def test_staging_pins_both_arms_and_matching_initial_states(self):
        manifest = self.stage()
        self.assertEqual(len(manifest['order']), 12)
        self.assertEqual(manifest['baseline_commit'], runner.BASELINE)
        for case in runner.SMOKE:
            entries = [entry for entry in manifest['order'] if entry['case'] == case]
            self.assertEqual(entries[0]['path'], entries[1]['path'])
        self.assertNotEqual((self.cohort / 'installations/baseline/SKILL.md').read_bytes(), (self.cohort / 'installations/candidate/SKILL.md').read_bytes())

    def test_oracle_and_protocol_not_in_any_participant(self):
        self.cohort = self.root / 'all-cases'
        seal = runner.prepare(self.cohort, {'SKILL.md': b'baseline'}, {'SKILL.md': b'candidate'},
                              self.cases, self.oracle, b'protocol', [case['id'] for case in self.cases])
        manifest = runner.verify(self.cohort, seal)
        for entry in manifest['order']:
            paths = runner.hashes(self.cohort / entry['path'])
            self.assertFalse(any('oracle' in path or 'protocol.md' in path or 'runner.py' in path for path in paths))

    def test_tampered_source_and_added_file_reject(self):
        self.stage()
        path = self.cohort / 'installations/candidate/SKILL.md'
        path.write_text('changed')
        with self.assertRaises(ValueError):
            runner.verify(self.cohort, self.seal)

    def test_manifest_cannot_self_authorize_drift(self):
        self.stage()
        manifest = self.cohort / 'manifest.json'
        manifest.write_text(manifest.read_text() + ' ')
        with self.assertRaises(ValueError):
            runner.verify(self.cohort, self.seal)

    def test_zero_unknown_and_duplicate_selected_cases_reject(self):
        for selected in ([], ['missing'], ['bounded-en', 'bounded-en']):
            with self.assertRaises(ValueError):
                runner.prepare(self.root / 'never', {}, {}, self.cases, self.oracle, b'', selected)
        self.assertFalse((self.root / 'never').exists())

    def test_symlink_input_rejects(self):
        (self.root / 'link').symlink_to(HERE / 'cases.json')
        with self.assertRaises(ValueError):
            runner.hashes(self.root)

    def test_missing_selected_installation_rejects(self):
        with self.assertRaises(ValueError):
            runner.prepare(self.root / 'missing', {'SKILL.md': b'baseline'}, {},
                           self.cases, self.oracle, b'protocol', runner.SMOKE)
        self.assertFalse((self.root / 'missing').exists())

    def test_wrong_artifact_rejects_and_right_artifact_is_unreviewed(self):
        self.stage()
        initial = self.cohort / 'participants/bounded-en/initial'
        work = self.root / 'work'
        runner.shutil.copytree(initial, work)
        result = runner.audit_outputs(initial, work, self.oracle['bounded-en'])
        self.assertFalse(result['artifact_pass'])
        (work / 'format.txt').write_bytes(b'ready\n')
        result = runner.audit_outputs(initial, work, self.oracle['bounded-en'])
        self.assertTrue(result['artifact_pass'])
        self.assertEqual(result['semantic_review'], 'UNREVIEWED')
        self.assertIsNone(result['behavioral_acceptance'])
        (work / 'RELEASE_APPROVED').write_text('incorrect approval')
        self.assertFalse(runner.audit_outputs(initial, work,
                         dict(self.oracle['bounded-en'], forbidden_files=['RELEASE_APPROVED']))['artifact_pass'])

    def test_preserved_input_mutation_rejects(self):
        self.stage()
        initial = self.cohort / 'participants/bounded-en/initial'
        work = self.root / 'work'
        runner.shutil.copytree(initial, work)
        (work / 'format.txt').write_bytes(b'ready\n')
        (work / 'sentinel.txt').write_text('changed')
        self.assertFalse(runner.audit_outputs(initial, work, self.oracle['bounded-en'])['artifact_pass'])

    def test_missing_isolation_stays_pending_and_never_calls_model(self):
        self.stage()
        with patch.object(runner, 'preflight', return_value={'available': False, 'reason': 'daemon missing'}), patch.object(runner.platform, 'platform', return_value='test-runtime'), patch.object(runner.subprocess, 'run') as child:
            report = runner.execute(self.cohort, self.seal, self.root / 'results', 'unused', None, None, None)
        child.assert_not_called()
        self.assertEqual(report['status'], 'PENDING')
        self.assertEqual(report['episodes_started'], 0)
        self.assertEqual(report['episodes_planned'], 12)
        self.assertEqual(report['behavioral_improvement'], 'unclaimed')

    def test_output_inside_sealed_input_rejects(self):
        self.stage()
        with self.assertRaises(ValueError):
            runner.execute(self.cohort, self.seal, self.cohort / 'results', 'unused', None, None, None)

    def test_both_languages_and_smoke_families_present(self):
        self.assertEqual({case['language'] for case in self.cases}, {'en', 'es'})
        self.assertEqual(set(self.oracle), {case['id'] for case in self.cases})
        self.assertEqual(len(self.cases), len(set(self.oracle)))
        self.assertTrue(set(runner.SMOKE) <= set(self.oracle))

    def test_size_observation_distinguishes_duplicate_and_unique_bytes(self):
        (self.root / 'one').write_bytes(b'abc')
        (self.root / 'two').write_bytes(b'abc')
        result = runner.size_observation(self.root)
        self.assertEqual(result['stored_bytes'], 6)
        self.assertEqual(result['unique_bytes'], 3)
        self.assertEqual(result['files'], 2)


if __name__ == '__main__':
    unittest.main()
