import copy
import importlib.util
import json
from pathlib import Path
import shutil
import signal
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('measurement', ROOT / 'measurement.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
CASES = json.loads((ROOT / 'oracle/answers.json').read_text())['cases']


class Measurement(unittest.TestCase):
    def test_manifest_and_all_family_cases(self):
        m.verify_manifest(ROOT)
        self.assertEqual({c['family'] for c in CASES}, {f'T{i:02}' for i in range(1, 10)})
        self.assertEqual(len({c['id'] for c in CASES}), len(CASES))
        for family in {c['family'] for c in CASES}:
            self.assertEqual({c['accept'] for c in CASES if c['family'] == family}, {False, True})

    def test_always_accept_and_reject_mutants_are_killed(self):
        for constant in [False, True]:
            for family in {c['family'] for c in CASES}:
                self.assertTrue(any(c['accept'] != constant for c in CASES if c['family'] == family))

    def test_missing_and_malformed_inputs_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'trace.json'
            self.assertFalse(m.validate_paths('T01', path, path))
            path.write_text('{broken')
            self.assertFalse(m.validate_paths('T01', path, path))
        for family in {c['family'] for c in CASES}:
            self.assertFalse(m.validate(family, {}, {}))

    def test_wrong_scalar_evidence_paths_fail_closed_without_writes(self):
        case = next(c for c in CASES if c['id'] == 'T01-valid')
        with tempfile.TemporaryDirectory() as temp:
            task, trace = Path(temp) / 'task.json', Path(temp) / 'trace.json'
            task.write_text(json.dumps(case['task']))
            for value in [1, None, []]:
                evidence = dict(case['trace'], csv=value)
                trace.write_text(json.dumps(evidence))
                before = (task.read_bytes(), trace.read_bytes())
                self.assertFalse(m.validate_paths('T01', task, trace))
                self.assertEqual(before, (task.read_bytes(), trace.read_bytes()))

    def test_actual_child_failure_cannot_hide_in_wrapper_pass(self):
        case = next(c for c in CASES if c['id'] == 'T04-valid')
        for exit_code in [0, 7]:
            trace = copy.deepcopy(case['trace'])
            trace['child'] = m.observe_child([sys.executable, '-c', f'print("PASS"); raise SystemExit({exit_code})'])
            self.assertEqual(trace['child']['exit'], exit_code)
            self.assertEqual(m.validate('T04', case['task'], trace), exit_code == 0)

    def test_actual_timeout_and_signal(self):
        timeout = m.observe_child([sys.executable, '-c', 'import time; time.sleep(10)'], timeout=.05)
        self.assertIs(timeout['timeout'], True)
        self.assertFalse(m.successful(timeout))
        killed = m.observe_child([sys.executable, '-c', 'import os,signal; os.kill(os.getpid(),signal.SIGTERM)'])
        self.assertEqual(killed['signal'], signal.SIGTERM)
        self.assertEqual(killed['exit'], -signal.SIGTERM)
        self.assertFalse(m.successful(killed))

    def test_staging_is_exact_and_preserves_evidence(self):
        before = {p: p.read_bytes() for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
        with tempfile.TemporaryDirectory() as temp:
            sentinel = Path(temp) / 'sentinel'
            sentinel.write_bytes(b'keep\x00\n')
            for family in {c['family'] for c in CASES}:
                stage = Path(temp) / family
                self.assertEqual(m.stage_participant(ROOT, family, stage), ['input.json', 'task.md'])
                self.assertEqual({p.relative_to(stage).as_posix() for p in stage.rglob('*')}, {'input.json', 'task.md'})
                for filename in ['input.json', 'task.md']:
                    self.assertEqual((stage / filename).read_bytes(), (ROOT / 'fixtures' / family / filename).read_bytes())
            self.assertEqual(sentinel.read_bytes(), b'keep\x00\n')
        self.assertEqual(before, {p: p.read_bytes() for p in before})

    def mutation(self, mutate):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'suite'
            shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns('__pycache__'))
            mutate(root)
            with self.assertRaises((ValueError, OSError)):
                m.verify_manifest(root)

    def test_empty_fixture_mutation_is_rejected(self):
        self.mutation(lambda root: (root / 'fixtures/T01/task.md').write_text('No actionable task or examples.\n'))

    def test_forged_source_hashes_are_rejected(self):
        def mutate(root):
            path = root / 'manifest.json'; manifest = json.loads(path.read_text())
            manifest['sources'] = {p: '0'*64 for p in manifest['sources']}
            path.write_text(json.dumps(manifest))
        self.mutation(mutate)

    def test_self_granted_source_exception_is_rejected(self):
        def mutate(root):
            path = root / 'manifest.json'; manifest = json.loads(path.read_text())
            manifest['allowed_p01_changes'] = ['SKILL.md']
            path.write_text(json.dumps(manifest))
        self.mutation(mutate)

    def test_oracle_drift_is_rejected(self):
        self.mutation(lambda root: (root / 'oracle/answers.json').write_text('{"cases":[]}'))

    def test_nested_leak_is_rejected(self):
        def mutate(root):
            nested = root / 'fixtures/T01/nested'; nested.mkdir()
            (nested / 'answers.json').write_bytes((root / 'oracle/answers.json').read_bytes())
        self.mutation(mutate)

    def test_symlink_is_rejected(self):
        def mutate(root):
            path = root / 'fixtures/T01/input.json'; path.unlink()
            path.symlink_to(root / 'oracle/answers.json')
        self.mutation(mutate)

    def test_oracle_cannot_be_allowlisted_for_participant(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'suite'
            shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns('__pycache__'))
            path = root / 'manifest.json'; manifest = json.loads(path.read_text())
            manifest['participant_files']['T01'].append('oracle/answers.json')
            path.write_text(json.dumps(manifest))
            with self.assertRaises(ValueError):
                m.stage_participant(root, 'T01', Path(temp) / 'participant')


def case_test(case):
    def test(self):
        task, trace = copy.deepcopy(case['task']), copy.deepcopy(case['trace'])
        self.assertIs(m.validate(case['family'], task, trace), case['accept'])
        self.assertEqual(task, case['task'])
        self.assertEqual(trace, case['trace'])
    return test


for case in CASES:
    setattr(Measurement, 'test_case_' + case['id'].replace('-', '_'), case_test(case))
