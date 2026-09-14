"""Exercise the literal capture's generated receipt, not a surrogate implementation."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
RECIPE = (ROOT / 'references/guides/evidence-capture.md').read_text().split('```python\n', 1)[1].split('\n```', 1)[0]


class ReceiptTests(unittest.TestCase):
    def run_capture(self, source, extra=(), env=None):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'module.py').write_text(source)
            (root / 'test_module.py').write_text('protected\n')
            (root / 'SPEC.md').write_text('contract\n')
            argv = [sys.executable, 'module.py', *extra]
            script = RECIPE.replace('argv = ["python3", "-m", "unittest", "discover", "-v"]', 'argv = ' + repr(argv))
            (root / 'capture.py').write_text(script, encoding='utf-8')
            child = subprocess.run([sys.executable, 'capture.py'], cwd=root, capture_output=True, timeout=10, env=env)
            out = next((root / 'evidence').iterdir())
            return child, {p.name: p.read_bytes() for p in out.iterdir()}, argv

    def parse_receipt(self, files):
        text = files['receipt.md'].decode()
        match = re.search(r'(?m)^(`{3,})json\n', text)
        self.assertIsNotNone(match)
        end = text.index('\n' + match[1] + '\n', match.end())
        return json.loads(text[match.end():end])

    def test_receipt_is_exact_record_with_actual_binary_stream_hashes(self):
        run, files, argv = self.run_capture("import os; os.write(1,b'\\xff');os.write(2,b'\\x00')")
        self.assertEqual(run.returncode, 0)
        record = self.parse_receipt(files)
        self.assertEqual(record, json.loads(files['result.json']))
        self.assertEqual(record['argv'], argv)
        for name in ['stdout.bin', 'stderr.bin']:
            self.assertEqual(record['streams'][name], hashlib.sha256(files[name]).hexdigest())
        self.assertIn(b'Role finish: n/a', files['receipt.md'])
        self.assertNotIn('role_end', record)
        self.assertTrue(run.stdout.strip().endswith(b'/receipt.md'))

    def test_command_markup_and_unicode_round_trip(self):
        run, files, argv = self.run_capture('pass', ('```\nnot a fence\n````', '雪', 'a|b'))
        self.assertEqual(run.returncode, 0)
        self.assertEqual(self.parse_receipt(files)['argv'], argv)

    def test_single_backtick_argument_still_has_a_valid_fence(self):
        run, files, argv = self.run_capture("pass", ("a`b",))
        self.assertEqual(run.returncode, 0)
        self.assertEqual(self.parse_receipt(files)["argv"], argv)

    def test_receipt_has_explicit_utf8_under_ascii_locale(self):
        env = dict(os.environ, LC_ALL="C", LANG="C", PYTHONUTF8="0", PYTHONCOERCECLOCALE="0")
        run, files, _ = self.run_capture("pass", env=env)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(self.parse_receipt(files), json.loads(files["result.json"]))

    def test_failed_child_receipt_never_becomes_success(self):
        run, files, _ = self.run_capture("print('PASS');raise SystemExit(9)")
        self.assertNotEqual(run.returncode, 0)
        record = self.parse_receipt(files)
        self.assertEqual(record['child_exit'], 9)
        self.assertFalse(record['accepted'])
        self.assertEqual(record, json.loads(files['result.json']))

    def test_changed_revision_receipt_preserves_failed_stability(self):
        run, files, _ = self.run_capture("from pathlib import Path;Path('test_module.py').write_text('changed')")
        self.assertNotEqual(run.returncode, 0)
        record = self.parse_receipt(files)
        self.assertFalse(record['accepted'])
        self.assertFalse(record['inputs_stable'])
        self.assertNotEqual(record['inputs_before'], record['inputs_after'])


if __name__ == '__main__':
    unittest.main()
