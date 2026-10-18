"""A capture or lint script that sits outside the working directory is still named in the evidence.

Guarantee: when `capture.py` or `lint_runner.py` runs from the install folder (outside cwd), the record
names the executing script by absolute path and sha256 instead of dropping it from the inputs; the reader
refuses a record whose program identity is malformed or no longer matches the file; and inside cwd the
record stays as it always was, with the script among the hashed inputs and no `program` field.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))
from maintaining.install_root import current_root  # noqa: E402
INSTALL = current_root(ROOT)
CAPTURE = INSTALL / 'scripts/capture.py'
LINT = INSTALL / 'scripts/lint_runner.py'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class OutsideCwdPrograms(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve()
        (self.root / 'initiative').mkdir()
        (self.root / 'input.txt').write_text('x\n')
        (self.root / 'child.py').write_text("print('ok')\n")
        spec = dict(workspace='initiative', argv=[sys.executable, 'child.py'],
                    selectors=[dict(glob='input.txt', required=True)], artifacts=[], timeout_seconds=5)
        (self.root / 'spec.json').write_text(json.dumps(spec))
        self.reader = load('outside_cwd_reader', CAPTURE)

    def capture(self, script):
        run = subprocess.run([sys.executable, '-I', str(script), 'spec.json'], cwd=self.root,
                             capture_output=True, timeout=20)
        self.assertEqual(run.returncode, 0, run.stderr)
        return Path(run.stdout.decode().strip()).parent

    def test_capture_outside_cwd_names_itself_with_its_sha256(self):
        out = self.capture(CAPTURE)
        record = json.loads((out / 'result.json').read_text())
        self.assertEqual(record['program'], dict(path=str(CAPTURE.resolve()), sha256=sha(CAPTURE)))
        self.assertEqual(json.loads((out / 'start.json').read_text())['program'], record['program'])
        self.assertTrue(self.reader.read_record(out, require_pass=True)['accepted'])

    def test_capture_inside_cwd_keeps_the_v9_record_shape(self):
        shutil.copy(CAPTURE, self.root / 'capture.py')
        out = self.capture(self.root / 'capture.py')
        record = json.loads((out / 'result.json').read_text())
        self.assertNotIn('program', record)
        self.assertIn('capture.py', record['inputs_before'])

    def test_a_tampered_script_no_longer_matches_its_recorded_hash(self):
        bin_dir = self.root.parent / (self.root.name + '-bin')
        bin_dir.mkdir()
        self.addCleanup(shutil.rmtree, bin_dir, True)
        copy = bin_dir / 'capture.py'
        shutil.copy(CAPTURE, copy)
        out = self.capture(copy)
        self.assertEqual(json.loads((out / 'result.json').read_text())['program']['sha256'], sha(CAPTURE))
        copy.write_text(copy.read_text() + '\n# tampered\n')
        with self.assertRaisesRegex(ValueError, 'program bytes changed'):
            self.reader.read_record(out, require_pass=True)

    def test_a_malformed_program_identity_is_refused(self):
        out = self.capture(CAPTURE)
        record = json.loads((out / 'result.json').read_text())
        for bad in ({'path': 'relative.py', 'sha256': sha(CAPTURE)}, {'path': str(CAPTURE), 'sha256': 'abc'},
                    {'path': str(CAPTURE)}, 'capture.py'):
            with self.subTest(program=bad):
                (out / 'result.json').write_text(json.dumps(dict(record, program=bad)))
                with self.assertRaises(ValueError):
                    self.reader.read_record(out)

    def test_lint_runner_outside_cwd_names_both_scripts_in_its_summary(self):
        config = dict(workspace='initiative', slug='demo',
                      rows=[12], selectors=[dict(glob='input.txt', required=True)], timeout_seconds=5)
        (self.root / 'lint.json').write_text(json.dumps(config))
        run = subprocess.run([sys.executable, '-I', str(LINT), 'lint.json'], cwd=self.root,
                             capture_output=True, timeout=30)
        summary = json.loads(Path(run.stdout.decode().strip()).read_text())
        self.assertEqual(summary['programs'], {'lint_runner': dict(path=str(LINT.resolve()), sha256=sha(LINT)),
                                               'capture': dict(path=str(CAPTURE.resolve()), sha256=sha(CAPTURE))})
        record = self.reader.read_record(self.root / summary['rows']['12']['observation'])
        self.assertEqual(record['program'], summary['programs']['capture'])

    def test_a_row_record_without_the_capture_program_is_an_error(self):
        lint = load('outside_cwd_lint', LINT)
        out = self.capture(CAPTURE)
        record = json.loads((out / 'result.json').read_text())
        source = (INSTALL / 'scripts/lint.py').read_bytes()
        digest = hashlib.sha256(source).hexdigest()
        wrong = dict(path=str(CAPTURE.resolve()), sha256='0' * 64)
        self.assertEqual(lint.captured_lint_verdict(source, digest, 'demo', 12, 'row.sh', record, out, wrong), 'ERROR')
        stripped = {k: v for k, v in record.items() if k != 'program'}
        self.assertEqual(lint.captured_lint_verdict(source, digest, 'demo', 12, 'row.sh', stripped, out,
                                                    record['program']), 'ERROR')


if __name__ == '__main__':
    unittest.main()
