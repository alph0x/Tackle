"""Small execution-level regressions for canonical identity and saved scripts."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
CAPTURE, LINT = re.findall(r'```python\n(.*?)\n```', (ROOT/'references/guides/full-checks.md').read_text(), re.S)
SOURCE = (ROOT/'references/guides/lint-spec.md').read_bytes()
SHA = hashlib.sha256(SOURCE).hexdigest()
NS = {'__name__': 'documented_lint'}
exec(LINT, NS)


class IsolatedVeracity(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name, data in [('capture.py', CAPTURE.encode()), ('lint.py', LINT.encode()), ('lint-spec.md', SOURCE)]:
            (self.root/name).write_bytes(data)
        self.workspace = self.root/'docs/plans/demo'
        (self.workspace/'points').mkdir(parents=True)
        (self.workspace/'points/P-01.md').write_text('- **Effort**: high\n')
        (self.workspace/'plan.md').write_text('P-01\n')
        (self.workspace/'board.md').write_text(
            '| Point | What | Briefing | Depends on | Status | Confidence |\n'
            '|---|---|---|---|---|---|\n'
            '| P-01 | Work | points/P-01.md | none | 🔴 | n/a |\n')

    def captured(self, row=12, command=None):
        canonical = NS['canonical_rows'](SOURCE, SHA, 'demo')[row]['command']
        (self.root/'row.sh').write_bytes(canonical if command is None else command)
        spec = dict(argv=['sh', 'row.sh'], selectors=[dict(glob='docs/plans/demo/points/*.md', required=True)],
                    artifacts=[], destination='evidence', timeout_seconds=2)
        (self.root/'check.json').write_text(json.dumps(spec))
        run = subprocess.run([sys.executable, 'capture.py', 'check.json'], cwd=self.root, capture_output=True, timeout=5)
        out = Path(run.stdout.decode().strip()).parent
        return out, json.loads((out/'result.json').read_text())

    def verdict(self, row, out, record):
        return NS['captured_lint_verdict'](SOURCE, SHA, 'demo', row, 'row.sh', record, out)

    def test_real_canonical_row_is_accepted(self):
        out, record = self.captured()
        self.assertEqual(self.verdict(12, out, record), 'PASS')

    def test_recorded_noncanonical_success_is_rejected(self):
        out, record = self.captured(command=b'true')
        self.assertEqual(record['child_exit'], 0)
        self.assertEqual(self.verdict(12, out, record), 'ERROR')

    def test_observed_row4_quote_mutation_is_rejected(self):
        command = NS['canonical_rows'](SOURCE, SHA, 'demo')[4]['command']
        mutated = command.replace(b'[^\"]+\"/', b'[^\"]+/')
        self.assertNotEqual(command, mutated)
        out, record = self.captured(4, mutated)
        self.assertEqual(self.verdict(4, out, record), 'ERROR')

    def test_stdout_findings_exit_zero_fail(self):
        (self.workspace/'points/P-01.md').write_text('- **Effort**: impossible\n')
        out, record = self.captured()
        self.assertEqual(record['child_exit'], 0)
        self.assertEqual(self.verdict(12, out, record), 'FAIL')

    def test_row12_pattern_mutation_is_rejected(self):
        command = NS['canonical_rows'](SOURCE, SHA, 'demo')[12]['command']
        mutated = command.replace(b'Effort\\*\\*', b'Effort\\*')
        self.assertNotEqual(command, mutated)
        out, record = self.captured(12, mutated)
        self.assertEqual(self.verdict(12, out, record), 'ERROR')

    def test_missing_script_fingerprint_cannot_be_rescued_by_transcript(self):
        out, record = self.captured()
        del record['inputs_before']['row.sh']
        self.assertEqual(self.verdict(12, out, record), 'ERROR')

    def test_forged_mapping_or_missing_blob_rejected(self):
        out, record = self.captured(command=b'true')
        digest = hashlib.sha256(NS['canonical_rows'](SOURCE, SHA, 'demo')[12]['command']).hexdigest()
        record['inputs_before']['row.sh'] = digest
        record['inputs_after']['row.sh'] = digest
        self.assertEqual(self.verdict(12, out, record), 'ERROR')

    def test_tampered_stream_is_not_pass(self):
        out, record = self.captured()
        (out/'stdout.bin').write_bytes(b'hidden finding')
        self.assertEqual(self.verdict(12, out, record), 'ERROR')

    def test_saved_product_script_is_automatic_and_history_survives(self):
        (self.root/'row.sh').write_text('printf first')
        out1, r1 = self.captured(command=b'printf first')
        old = {str(p.relative_to(out1)): p.read_bytes() for p in out1.rglob('*') if p.is_file()}
        out2, r2 = self.captured(command=b'printf second')
        for out, record, data in [(out1, r1, b'printf first'), (out2, r2, b'printf second')]:
            self.assertEqual((out/'blobs'/record['inputs_before']['row.sh']).read_bytes(), data)
            self.assertIn('capture.py', record['inputs_before'])
            self.assertIn('check.json', record['inputs_before'])
        self.assertEqual(old, {str(p.relative_to(out1)): p.read_bytes() for p in out1.rglob('*') if p.is_file()})

    def test_connected_external_readonly_source_is_snapshotted(self):
        self.run_connected_subset(external=True)

    def test_connected_path_uses_literal_rows_and_honest_subset_score(self):
        self.run_connected_subset()

    def run_connected_subset(self, external=False):
        (self.workspace/'points/P-01.md').write_text('- **Effort**: impossible\n')
        config = dict(source='lint-spec.md', source_sha256=SHA, slug='demo', rows=[5,12,15],
                      capture_script='capture.py', selectors=[dict(glob='docs/plans/demo/**/*.md',required=True)],
                      destination='lint-evidence', timeout_seconds=2)
        (self.workspace/'AGENTS.md').write_text('Reference staleness window: 14\n')
        if external:
            config['source'] = str(ROOT/'references/guides/lint-spec.md')
        (self.root/'lint.json').write_text(json.dumps(config))
        run = subprocess.run([sys.executable, 'lint.py', 'lint.json'], cwd=self.root, capture_output=True, timeout=10)
        self.assertEqual(run.returncode, 1, run.stderr)
        summary = json.loads(Path(run.stdout.decode().strip()).read_text())
        self.assertEqual((summary['passed'],summary['total'],summary['complete']), (2,3,False))
        self.assertEqual(summary['rows']['12']['verdict'], 'FAIL')
        for key, result in summary['rows'].items():
            record = json.loads((self.root/result['observation']/'result.json').read_text())
            self.assertEqual((self.root/result['observation']/'blobs'/record['inputs_before'][record['argv'][1]]).read_bytes(),
                             NS['canonical_rows'](SOURCE,SHA,'demo')[int(key)]['command'])


if __name__ == '__main__':
    unittest.main()
