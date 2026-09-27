"""report.py's rendering, its `--check` byte-for-byte contract, its ordering-check section and its input
scope -- on synthetic cohorts, several mirrored into a temporary directory laid out exactly like the real
one (report.py's sibling import of protocol-v2's check.py resolves against wherever the *script* lives,
so a faithful subprocess-level test copies the script there too, rather than pointing the real file at
fake data).
"""
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PROTOCOL_DIR = ROOT / 'eval' / 'protocol-v2'
NEVER_GATE_SHAPED = re.compile(r'\b(PASS|FAIL|RULE|RECOMMENDATION)\b')

# report.py's own module-level code only sets up sys.path and imports check/decision; it touches no file
# at import time, so importing it directly (unmirrored) is safe for testing its pure functions.
report_spec = importlib.util.spec_from_file_location('resume_report', HERE / 'report.py')
report = importlib.util.module_from_spec(report_spec)
report_spec.loader.exec_module(report)

# Only plain functions and constants, never a TestCase subclass: importing one would make unittest
# discover count and run it a second time under this module too, breaking the suite registry's exact
# test count -- and RealManifestLeakage's own expected failure would then be reported twice.
from test_decision import build_manifest, write_cohort, episode_line, sha_file, S65, S66, NA, H, ZERO  # noqa: E402


def mirror(tmp):
    """<tmp>/eval/protocol-v2/{check.py,verdict.py} and <tmp>/eval/cohorts/2026-09-resume/
    {report.py,decision.py,price-table.json}, so the mirrored report.py's own sys.path bootstrapping
    resolves exactly as it does at its real location."""
    protocol = tmp / 'eval' / 'protocol-v2'
    protocol.mkdir(parents=True)
    shutil.copy(PROTOCOL_DIR / 'check.py', protocol / 'check.py')
    shutil.copy(PROTOCOL_DIR / 'verdict.py', protocol / 'verdict.py')
    cohort_dir = tmp / 'eval' / 'cohorts' / '2026-09-resume'
    cohort_dir.mkdir(parents=True)
    shutil.copy(HERE / 'report.py', cohort_dir / 'report.py')
    shutil.copy(HERE / 'decision.py', cohort_dir / 'decision.py')
    shutil.copy(HERE / 'price-table.json', cohort_dir / 'price-table.json')
    return cohort_dir


def sealed_manifest(cohort_id):
    clause = 'decision.py sha256=%s; price-table sha256=%s' % (sha_file(HERE / 'decision.py'),
                                                                sha_file(HERE / 'price-table.json'))
    return build_manifest(cohort_id, 'sealed for a mirrored report test; ' + clause)


def write_judgment(cohort_dir, episode_id, order):
    directory = cohort_dir / 'judgments'
    directory.mkdir(parents=True, exist_ok=True)
    (directory / ('%s.json' % episode_id)).write_text(json.dumps({'order': order}))


def rec(scenario_id, variant_id, arm, outcome, episode_id=None, invalid_reason=None):
    """A minimal record shaped enough for report.py's own pure functions, never a full protocol-v2
    record: these tests exercise report.py's own functions directly, not check.py's schema."""
    return {'scenario_id': scenario_id, 'variant_id': variant_id, 'arm': arm, 'outcome': outcome,
           'episode_id': episode_id or ('%s-%s-%s-%s' % (scenario_id, variant_id, arm, outcome)),
           'invalid_reason': invalid_reason, 'executor': {'model': 'claude-haiku-4-5'}, 'roles': [],
           'cost': {'tokens_in': 1000, 'tokens_out': 100}}


class PureSections(unittest.TestCase):
    """report.py's own pure functions, tested directly against hand-built records -- never PASS/FAIL or
    RULE/RECOMMENDATION-shaped anywhere in their output."""

    def test_variant_arm_table_counts_each_outcome_bucket(self):
        manifest = {'variants': [{'scenario_id': S65, 'variant_id': 'h1'}], 'arms': ['method', 'method:candidate']}
        records = [
            rec(S65, 'h1', 'method', 'fell'), rec(S65, 'h1', 'method', 'avoided'),
            rec(S65, 'h1', 'method', 'invalid'),
            rec(S65, 'h1', 'method:candidate', 'avoided'), rec(S65, 'h1', 'method:candidate', 'avoided'),
        ]
        rows = report.variant_arm_table(manifest, records)
        self.assertIn('| s65-migration-replay/h1 | method | 3 | 2 | 1 | 1 | 1 |', rows)
        self.assertIn('| s65-migration-replay/h1 | method:candidate | 2 | 2 | 2 | 0 | 0 |', rows)
        self.assertIsNone(NEVER_GATE_SHAPED.search('\n'.join(rows)))

    def test_invalid_section_lists_ids_and_reasons_or_none(self):
        records = [rec(S65, 'h1', 'method', 'invalid', episode_id='e-1', invalid_reason='path escape')]
        self.assertIn('- e-1: path escape.', report.invalid_section(records))
        self.assertIn('- none.', report.invalid_section([]))

    def test_artifact_section_reads_the_sealed_clause_and_manifest_fields(self):
        clause = 'decision.py sha256=%s; price-table sha256=%s' % ('a' * 64, 'b' * 64)
        manifest = {'decision_rule': 'text; ' + clause,
                   'artifacts': {'baseline_sha256': 'c' * 64, 'candidate_sha256': 'd' * 64},
                   'oracle_sha256': 'e' * 64}
        lines = report.artifact_section(manifest)
        self.assertIn('- decision.py (sealed): `%s`.' % ('a' * 64), lines)
        self.assertIn('- price-table.json (sealed): `%s`.' % ('b' * 64), lines)
        self.assertIn('- manifest artifacts.candidate_sha256: `%s`.' % ('d' * 64), lines)
        self.assertIn('- manifest oracle_sha256: `%s`.' % ('e' * 64), lines)


class RenderAndCheck(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix='resume-report-mirror-'))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.cohort_dir = mirror(self.tmp)

    def run_report(self, *args):
        return subprocess.run([sys.executable, str(self.cohort_dir / 'report.py')] + list(args),
                              capture_output=True, text=True, cwd=str(self.cohort_dir))

    def test_render_then_check_is_byte_identical_and_never_pass_fail_shaped(self):
        manifest = sealed_manifest('2026-09-resume-report-test')
        method_cost = {'tokens_in': 800000, 'tokens_out': 1000, 'wall_seconds': 10, 'tool_calls': 16, 'files_written': 0}
        candidate_cost = {'tokens_in': 400000, 'tokens_out': 1000, 'wall_seconds': 10, 'tool_calls': 8, 'files_written': 0}
        data = {}
        for scenario in (S65, S66):
            for seed in (1, 2, 3):
                data[(scenario, 'method', seed)] = ('fell', method_cost, 'claude-haiku-4-5-20251001')
                data[(scenario, 'method:candidate', seed)] = ('avoided', candidate_cost, 'claude-haiku-4-5-20251001')
        write_cohort(self.cohort_dir, manifest, data)
        write_result = self.run_report()
        self.assertEqual(write_result.returncode, 0, write_result.stdout + write_result.stderr)
        self.assertTrue((self.cohort_dir / 'report.md').is_file())
        report_bytes = (self.cohort_dir / 'report.md').read_bytes()
        report_text = report_bytes.decode('utf-8')
        self.assertIn('Decision: resume: report-only:', report_text)
        self.assertIsNone(NEVER_GATE_SHAPED.search(report_text), report_text)
        check_result = self.run_report('--check')
        self.assertEqual(check_result.returncode, 0, check_result.stdout + check_result.stderr)
        # A drifted report.md is caught, byte for byte.
        (self.cohort_dir / 'report.md').write_bytes(report_bytes + b'stray byte, no trailing newline')
        drifted = self.run_report('--check')
        self.assertEqual(drifted.returncode, 1)

    def test_an_unpriced_model_refuses_with_a_message_rather_than_a_traceback(self):
        """decision.dollar_median (called while building the dollar-cost section) can raise
        decision.Refusal on an unpriced model, same as decision.py's own CLI; report.py's main() must
        catch it too, rather than letting a raw traceback out."""
        manifest = sealed_manifest('2026-09-resume-report-refusal-test')
        cost = {'tokens_in': 1000, 'tokens_out': 100, 'wall_seconds': 10, 'tool_calls': 2, 'files_written': 0}
        data = {(S65, 'method', 1): ('avoided', cost, 'claude-unreleased-model')}
        write_cohort(self.cohort_dir, manifest, data)
        result = self.run_report()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('report:', result.stderr)


class OrderingSection(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix='resume-report-order-'))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.cohort_dir = mirror(self.tmp)

    def run_report(self, *args):
        return subprocess.run([sys.executable, str(self.cohort_dir / 'report.py')] + list(args),
                              capture_output=True, text=True, cwd=str(self.cohort_dir))

    def test_folded_episodes_are_named_and_missing_order_is_counted(self):
        manifest = sealed_manifest('2026-09-resume-report-order-test')
        cost = {'tokens_in': 1000, 'tokens_out': 100, 'wall_seconds': 10, 'tool_calls': 2, 'files_written': 0}
        data = {}
        for scenario in (S65, S66):
            for seed in (1, 2, 3):
                data[(scenario, 'method', seed)] = ('fell', cost, 'claude-haiku-4-5')
                data[(scenario, 'method:candidate', seed)] = ('avoided', cost, 'claude-haiku-4-5')
        write_cohort(self.cohort_dir, manifest, data)
        folded_id = 'e-s65-method-candidate-1'
        ordered_id = 'e-s65-method-candidate-3'
        # e-s65-method-candidate-2 gets no judgments/<id>.json at all -- it counts as missing.
        write_judgment(self.cohort_dir, folded_id, order={'result': 'unordered', 'folded': True})
        write_judgment(self.cohort_dir, ordered_id, order={'result': 'ordered', 'folded': False})
        write_result = self.run_report()
        self.assertEqual(write_result.returncode, 0, write_result.stdout + write_result.stderr)
        report_text = (self.cohort_dir / 'report.md').read_text(encoding='utf-8')
        self.assertIn('- method: ordered=0, unordered=0, n/a no-marker=0, not run=0, missing=6.', report_text)
        self.assertIn('- method:candidate: ordered=1, unordered=1, n/a no-marker=0, not run=0, missing=4.',
                     report_text)
        self.assertIn('Folded: %s.' % folded_id, report_text)


class SmokeSection(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix='resume-report-smoke-'))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.cohort_dir = mirror(self.tmp)

    def run_report(self, *args):
        return subprocess.run([sys.executable, str(self.cohort_dir / 'report.py')] + list(args),
                              capture_output=True, text=True, cwd=str(self.cohort_dir))

    def test_smoke_section_reports_both_episodes_and_checker_acceptance(self):
        manifest = sealed_manifest('2026-09-resume-report-smoke-test')
        write_cohort(self.cohort_dir, manifest, {})
        smoke_dir = self.cohort_dir / 'smoke'
        order = [dict(episode_id='smoke-1', scenario_id=S65, variant_id='v1', arm='method', seed=1),
                dict(episode_id='smoke-2', scenario_id=S65, variant_id='v1', arm='method:candidate', seed=1)]
        smoke_manifest = dict(
            schema='tackle-cohort/1', cohort_id='2026-09-resume-smoke-report-test',
            hypothesis='A synthetic smoke hypothesis for testing.',
            primary_metric='fall rate', decision_rule='development-grade smoke, mechanical only; no comparison.',
            n_min=1, seeds=[1],
            variants=[dict(scenario_id=S65, variant_id='v1', split='development', class_='outcome-trap',
                          fixture_sha256=H('fixture smoke'))],
            arms=['method', 'method:candidate'], comparisons=[],
            executor=dict(harness='claude-code-subagent', model='claude-haiku-4-5', effort='n/a'),
            judge=dict(model_family='n/a', blinded=True),
            artifacts=dict(baseline_sha256=ZERO, candidate_sha256=H('candidate tree')), oracle_sha256=H('oracle'),
            order=order, created_at='2026-09-26T00:00:00Z')
        for entry in smoke_manifest['variants']:
            entry['class'] = entry.pop('class_')
        body = {k: v for k, v in smoke_manifest.items() if k != 'seal_sha256'}
        smoke_manifest['seal_sha256'] = hashlib.sha256(
            json.dumps(body, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
        smoke_dir.mkdir(parents=True, exist_ok=True)
        (smoke_dir / 'manifest.json').write_text(json.dumps(smoke_manifest, indent=1, ensure_ascii=False) + '\n')
        default_cost = {'tokens_in': 1000, 'tokens_out': 100, 'wall_seconds': 10, 'tool_calls': 2, 'files_written': 0}
        lines, prev = [], ZERO
        for index, entry in enumerate(smoke_manifest['order']):
            line = episode_line(smoke_manifest, entry, index, prev, 'avoided', default_cost, 'claude-haiku-4-5',
                               split='development')
            text = json.dumps(line, ensure_ascii=False)
            lines.append(text)
            prev = H(text)
        (smoke_dir / 'episodes.jsonl').write_text(''.join(t + '\n' for t in lines))
        write_result = self.run_report()
        self.assertEqual(write_result.returncode, 0, write_result.stdout + write_result.stderr)
        report_text = (self.cohort_dir / 'report.md').read_text(encoding='utf-8')
        self.assertIn('checker accepts: yes (0 error(s)).', report_text)
        self.assertIn('smoke-1', report_text)
        self.assertIn('smoke-2', report_text)

    def test_no_smoke_directory_is_named_rather_than_a_crash(self):
        manifest = sealed_manifest('2026-09-resume-report-no-smoke-test')
        write_cohort(self.cohort_dir, manifest, {})
        write_result = self.run_report()
        self.assertEqual(write_result.returncode, 0, write_result.stdout + write_result.stderr)
        report_text = (self.cohort_dir / 'report.md').read_text(encoding='utf-8')
        self.assertIn('no smoke directory found', report_text)


class ReportScope(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix='resume-report-scope-'))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.cohort_dir = mirror(self.tmp)

    def test_report_never_opens_a_path_outside_its_own_scope(self):
        manifest = sealed_manifest('2026-09-resume-report-scope-test')
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
        opened = (json.loads(result.stdout.split('OPENED_JSON_START\n')[1])
                 if 'OPENED_JSON_START' in result.stdout else [])
        allowed = tuple({str(self.tmp), str(self.tmp.resolve()), sys.prefix, sys.exec_prefix, sys.base_prefix,
                        sys.base_exec_prefix})
        stray = [p for p in opened if p.startswith('/') and not p.startswith(allowed) and '/lib/python' not in p
                and '/lib-dynload/' not in p]
        self.assertEqual(stray, [])
        self.assertNotIn(str(scratchpad_decoy / 'episode-transcript.jsonl'), opened)


if __name__ == '__main__':
    unittest.main()
