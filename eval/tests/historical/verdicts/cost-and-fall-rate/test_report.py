"""report.py's rendering, its `--check` regression contract, and its input scope, all on a
synthetic cohort mirrored into a temporary directory laid out exactly like the real one (report.py's
sibling import of protocol-v2's check.py resolves against wherever the *script* lives, so a faithful
subprocess-level test copies the script there too, rather than pointing the real file at fake data).
"""
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = (Path(__file__).resolve().parents[5] / 'eval/cohorts/2026-09-candidate')
ROOT = HERE.parents[2]
PROTOCOL_DIR = ROOT / 'eval' / 'protocol-v2'

spec = importlib.util.spec_from_file_location('candidate_decision_for_report_test', HERE / 'decision.py')
decision = importlib.util.module_from_spec(spec)
spec.loader.exec_module(decision)

# Only plain functions, never a TestCase subclass: importing one would make unittest discover count and
# run it a second time under this module too, breaking the suite registry's exact test count.
from test_decision import build_manifest, write_cohort, sha_file, S62, S63, S64, NA  # noqa: E402


def mirror(tmp):
    """<tmp>/eval/protocol-v2/{check.py,verdict.py} and <tmp>/eval/cohorts/2026-09-candidate/
    {report.py,decision.py,price-table.json}, so the mirrored report.py's own sys.path bootstrapping
    resolves exactly as it does at its real location."""
    protocol = tmp / 'eval' / 'protocol-v2'
    protocol.mkdir(parents=True)
    shutil.copy(PROTOCOL_DIR / 'check.py', protocol / 'check.py')
    shutil.copy(PROTOCOL_DIR / 'verdict.py', protocol / 'verdict.py')
    cohort_dir = tmp / 'eval' / 'cohorts' / '2026-09-candidate'
    cohort_dir.mkdir(parents=True)
    shutil.copy(HERE / 'report.py', cohort_dir / 'report.py')
    shutil.copy(HERE / 'decision.py', cohort_dir / 'decision.py')
    shutil.copy(HERE / 'price-table.json', cohort_dir / 'price-table.json')
    return cohort_dir


def sealed_manifest(cohort_id):
    clause = 'decision.py sha256=%s; price-table sha256=%s' % (sha_file(HERE / 'decision.py'),
                                                                sha_file(HERE / 'price-table.json'))
    return build_manifest(cohort_id, 'sealed for a mirrored report test; ' + clause)


class RenderAndCheck(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix='report-mirror-'))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.cohort_dir = mirror(self.tmp)

    def run_report(self, *args):
        return subprocess.run([sys.executable, str(self.cohort_dir / 'report.py')] + list(args),
                              capture_output=True, text=True, cwd=str(self.cohort_dir))

    def test_render_then_check_is_byte_identical(self):
        manifest = sealed_manifest('2026-09-candidate-report-test')
        default_cost = {'tokens_in': 1000, 'tokens_out': 100, 'wall_seconds': 10, 'tool_calls': 2, 'files_written': 0}
        data = {}
        for scenario in (S62, S64):
            data[(scenario, 'method')] = ('fell', [], dict(default_cost, tokens_in=800000, tool_calls=16),
                                          'claude-haiku-4-5-20251001')
            data[(scenario, 'method:candidate')] = ('avoided', [], dict(default_cost, tokens_in=400000, tool_calls=8),
                                                    'claude-haiku-4-5-20251001')
            data[(scenario, 'method:routed')] = ('avoided', [
                {'role': 'planner', 'tier': 'frontier', 'model': 'claude-opus-5-5-20260901', 'effort': NA,
                 'tokens_in': 50000, 'tokens_out': 500},
                {'role': 'executor', 'tier': 'fast', 'model': 'claude-haiku-4-5-20251001', 'effort': NA,
                 'tokens_in': 30000, 'tokens_out': 400}], dict(default_cost, tokens_in=1, tool_calls=1),
                'claude-haiku-4-5-20251001')
        write_cohort(self.cohort_dir, manifest, data)
        write_result = self.run_report()
        self.assertEqual(write_result.returncode, 0, write_result.stdout + write_result.stderr)
        self.assertTrue((self.cohort_dir / 'report.md').is_file())
        report_text = (self.cohort_dir / 'report.md').read_text(encoding='utf-8')
        self.assertIn('candidate`: **PASS**', report_text.replace('- `candidate', '- `candidate'))
        self.assertIn('Artifacts: candidate (9.0.0)', report_text)
        check_result = self.run_report('--check')
        self.assertEqual(check_result.returncode, 0, check_result.stdout + check_result.stderr)
        # A drifted report.md is caught.
        (self.cohort_dir / 'report.md').write_text(report_text + 'stray line\n', encoding='utf-8')
        drifted = self.run_report('--check')
        self.assertEqual(drifted.returncode, 1)

    def test_report_never_opens_a_path_outside_its_own_scope(self):
        manifest = sealed_manifest('2026-09-candidate-report-scope-test')
        write_cohort(self.cohort_dir, manifest, {})
        scratchpad_decoy = self.tmp / 'scratchpad-decoy'
        scratchpad_decoy.mkdir()
        (scratchpad_decoy / 'episode-transcript.jsonl').write_text('should never be opened\n')
        lines = [
            "import sys, json",
            "opened = []",
            "def hook(event, args):",
            "    if event in ('open', 'os.open') and args:",
            "        opened.append(str(args[0]))",
            "sys.addaudithook(hook)",
            "sys.argv = ['report.py', '--check']",
            "import runpy",
            "try:",
            "    runpy.run_path(%r, run_name='__main__')" % str(self.cohort_dir / 'report.py'),
            "except SystemExit:",
            "    pass",
            "print('OPENED_JSON_START')",
            "print(json.dumps(opened))",
        ]
        script = '\n'.join(lines)
        result = subprocess.run([sys.executable, '-c', script], capture_output=True, text=True,
                                cwd=str(self.cohort_dir))
        opened = json.loads(result.stdout.split('OPENED_JSON_START\n')[1]) if 'OPENED_JSON_START' in result.stdout else []
        allowed = tuple({str(self.tmp), str(self.tmp.resolve()), sys.prefix, sys.exec_prefix, sys.base_prefix,
                        sys.base_exec_prefix})
        stray = [p for p in opened if p.startswith('/') and not p.startswith(allowed) and '/lib/python' not in p
                and '/lib-dynload/' not in p]
        self.assertEqual(stray, [])
        self.assertNotIn(str(scratchpad_decoy / 'episode-transcript.jsonl'), opened)


if __name__ == '__main__':
    unittest.main()
