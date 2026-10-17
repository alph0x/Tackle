"""The confidence script prints what the original awk program printed for malformed counts.

Guarantee: a negative or overflowing count in a legacy `evidence:` line yields the same row the awk program
printed (a `nan` confidence, 64-bit saturated integers) and never a Python exception. Expected rows are the
awk program's own output for these inputs.
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from maintaining.install_root import current_root  # noqa: E402
SCRIPT = current_root(ROOT) / 'scripts/retro_confidence.py'
MAX = '9223372036854775807'

CASES = (
    ('-1✓ 4✗', 'line:2 -1 4 3 nan active'),
    ('-5✓/-3✗', 'line:2 -5 -3 -8 nan active'),
    ('1e400✓', 'line:2 %s 0 %s nan active' % (MAX, MAX)),
    ('2✓/1e400✗', 'line:2 2 %s %s 0.0000 retired' % (MAX, MAX)),
    ('7✓/2✗', 'line:2 7 2 9 0.4526 active'),
)


class MalformedCounts(unittest.TestCase):
    def test_each_case_prints_the_awk_row(self):
        for evidence, expected in CASES:
            with self.subTest(evidence=evidence), tempfile.TemporaryDirectory() as scratch:
                path = Path(scratch) / 'profile.md'
                path.write_text('## Hypotheses\n- t · confidence: 0.5 · evidence: %s · status: active\n' % evidence,
                                encoding='utf-8')
                run = subprocess.run([sys.executable, '-I', str(SCRIPT), str(path)], capture_output=True, text=True)
                self.assertEqual((run.returncode, run.stdout.strip(), run.stderr), (0, expected, ''))


if __name__ == '__main__':
    unittest.main()
