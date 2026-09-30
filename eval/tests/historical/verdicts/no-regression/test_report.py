"""report.py's rendering, its `--check` regression contract, its artifact-tie check and its input scope --
all on synthetic cohorts, mirrored into a temporary directory laid out exactly like the real one
(report.py's sibling import of protocol-v2's check.py resolves against wherever the *script* lives, so a
faithful subprocess-level test copies the script there too, rather than pointing the real file at fake
data).

Adapted from the second candidate cohort's test_report.py: `EscalationModelCheck` is dropped (no
escalation mechanism exists here); `ArtifactHashes` becomes `ArtifactCheck` (both hashes now come from the
manifest, plus the close-chain tie: every record's artifact_sha256 must equal its arm's).
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

HERE = (Path(__file__).resolve().parents[5] / 'eval/cohorts/2026-09-third-candidate')
ROOT = HERE.parents[2]
PROTOCOL_DIR = ROOT / 'eval' / 'protocol-v2'

decision_spec = importlib.util.spec_from_file_location('third_candidate_decision_for_report_test', HERE / 'decision.py')
decision = importlib.util.module_from_spec(decision_spec)
decision_spec.loader.exec_module(decision)

report_spec = importlib.util.spec_from_file_location('third_candidate_report', HERE / 'report.py')
report = importlib.util.module_from_spec(report_spec)
report_spec.loader.exec_module(report)

# Only plain functions, never a TestCase subclass: importing one would make unittest discover count and
# run it a second time under this module too, breaking the suite registry's exact test count.
from test_decision import build_manifest, write_cohort, episode_line, sha_file, S62, S63, S64, NA, H, ZERO  # noqa: E402


def mirror(tmp):
    protocol = tmp / 'eval' / 'protocol-v2'
    protocol.mkdir(parents=True)
    shutil.copy(PROTOCOL_DIR / 'check.py', protocol / 'check.py')
    shutil.copy(PROTOCOL_DIR / 'verdict.py', protocol / 'verdict.py')
    cohort_dir = tmp / 'eval' / 'cohorts' / '2026-09-third-candidate'
    cohort_dir.mkdir(parents=True)
    shutil.copy(HERE / 'report.py', cohort_dir / 'report.py')
    shutil.copy(HERE / 'decision.py', cohort_dir / 'decision.py')
    shutil.copy(HERE / 'price-table.json', cohort_dir / 'price-table.json')
    return cohort_dir


def sealed_manifest(cohort_id):
    clause = 'decision.py sha256=%s; price-table sha256=%s' % (sha_file(HERE / 'decision.py'),
                                                                sha_file(HERE / 'price-table.json'))
    return build_manifest(cohort_id, 'sealed for a mirrored report test; ' + clause)


def rec(scenario_id, arm, outcome, artifact_sha256, tokens_in=100000, tokens_out=1000, model='claude-haiku-4-5'):
    return {'scenario_id': scenario_id, 'variant_id': 'v1', 'arm': arm, 'outcome': outcome,
           'executor': {'model': model}, 'roles': [], 'artifact_sha256': artifact_sha256,
           'cost': {'tokens_in': tokens_in, 'tokens_out': tokens_out}}


def row(record, judgment=None, audit=None):
    return (record, judgment or {}, audit or {'verdict': 'clean', 'reason': None, 'outside_paths': [], 'skill_used': False})


class ArtifactCheck(unittest.TestCase):
    """Both hashes now come from the manifest's own two-slot artifacts object; the tie holds when every
    record's artifact_sha256 matches its arm's expected hash, and names the offending episode(s) when it
    does not."""

    def test_matching_records_report_no_mismatch(self):
        manifest = {'artifacts': {'baseline_sha256': 'b' * 64, 'candidate_sha256': 'c' * 64}}
        rows = [row({'episode_id': 'e1', 'arm': 'method', 'artifact_sha256': 'b' * 64}),
               row({'episode_id': 'e2', 'arm': 'method:candidate', 'artifact_sha256': 'c' * 64})]
        baseline, candidate, mismatches = report.artifact_check(manifest, rows)
        self.assertEqual((baseline, candidate), ('b' * 64, 'c' * 64))
        self.assertEqual(mismatches, [])

    def test_a_record_with_the_wrong_arm_s_hash_is_named(self):
        manifest = {'artifacts': {'baseline_sha256': 'b' * 64, 'candidate_sha256': 'c' * 64}}
        rows = [row({'episode_id': 'e1', 'arm': 'method', 'artifact_sha256': 'b' * 64}),
               row({'episode_id': 'e2', 'arm': 'method:candidate', 'artifact_sha256': 'WRONG'.ljust(64, '0')})]
        _, _, mismatches = report.artifact_check(manifest, rows)
        self.assertEqual(mismatches, ['e2'])


class NotCountedLine(unittest.TestCase):
    def test_no_excluded_episodes_reads_none(self):
        rows = [row(rec(S62, 'method', 'avoided', 'x'))]
        self.assertEqual(report.not_counted_line(rows), 'Not counted: none.')

    def test_an_invalid_episode_is_named_with_its_reason(self):
        record = dict(rec(S62, 'method', 'invalid', 'x'), episode_id='pilot-9', invalid_reason='the audit flagged it')
        rows = [row(record)]
        line = report.not_counted_line(rows)
        self.assertIn('pilot-9', line)
        self.assertIn('invalid', line)
        self.assertIn('the audit flagged it', line)


class RenderAndCheck(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix='third-report-mirror-'))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.cohort_dir = mirror(self.tmp)

    def run_report(self, *args):
        return subprocess.run([sys.executable, str(self.cohort_dir / 'report.py')] + list(args),
                              capture_output=True, text=True, cwd=str(self.cohort_dir))

    def test_render_then_check_is_byte_identical_and_no_split_text_appears(self):
        manifest = sealed_manifest('2026-09-third-candidate-report-test')
        default_cost = {'tokens_in': 1000, 'tokens_out': 100, 'wall_seconds': 10, 'tool_calls': 2, 'files_written': 0}
        data = {}
        for scenario in (S62, S64):
            for seed in (1, 2, 3):
                data[(scenario, 'method', seed)] = ('fell', dict(default_cost, tokens_in=800000, tool_calls=16),
                                                    'claude-haiku-4-5-20251001')
                data[(scenario, 'method:candidate', seed)] = ('avoided', dict(default_cost, tokens_in=400000, tool_calls=8),
                                                              'claude-haiku-4-5-20251001')
        write_cohort(self.cohort_dir, manifest, data)
        write_result = self.run_report()
        self.assertEqual(write_result.returncode, 0, write_result.stdout + write_result.stderr)
        report_text = (self.cohort_dir / 'report.md').read_text(encoding='utf-8')
        self.assertIn('`candidate`: **PASS**', report_text)
        self.assertIn('no-regression: PASS', report_text)
        self.assertNotIn('`split`', report_text)
        self.assertNotIn('RULE', report_text)
        self.assertNotIn('RECOMMENDATION', report_text)
        self.assertIn('Artifacts: baseline (method, 8.4.1)', report_text)
        self.assertIn("matches its arm's: yes", report_text)
        self.assertIn('Not counted: none.', report_text)
        # The pooled explanation must sit immediately after the verdict block that actually holds a native
        # `pooled[...]` line, wherever that line prints, not only once in the document's own preamble
        # (report.py's LIMIT states it there too; that copy stays).
        lines = report_text.splitlines()
        pooled_line_indexes = [i for i, line in enumerate(lines) if line.startswith('pooled[')]
        self.assertTrue(pooled_line_indexes, 'no native pooled[...] line rendered for this synthetic cohort')
        for index in pooled_line_indexes:
            fence_close = next(i for i in range(index, len(lines)) if lines[i] == '```')
            self.assertEqual(lines[fence_close + 1], '')
            self.assertTrue(lines[fence_close + 2].startswith('The `pooled[candidate]` line pools'),
                            'the pooled sentence must directly follow the fence that holds %r' % lines[index])
        check_result = self.run_report('--check')
        self.assertEqual(check_result.returncode, 0, check_result.stdout + check_result.stderr)
        (self.cohort_dir / 'report.md').write_text(report_text + 'stray line\n', encoding='utf-8')
        drifted = self.run_report('--check')
        self.assertEqual(drifted.returncode, 1)

    def test_smoke_section_prints_no_comparison_instead_of_an_empty_fence(self):
        manifest = sealed_manifest('2026-09-third-candidate-report-smoke-test')
        write_cohort(self.cohort_dir, manifest, {})
        smoke_dir = self.cohort_dir / 'smoke'
        order = [dict(episode_id='smoke-candidate', scenario_id=S62, variant_id='v1', arm='method:candidate', seed=1),
                dict(episode_id='smoke-method', scenario_id=S62, variant_id='v1', arm='method', seed=1)]
        smoke_manifest = dict(
            schema='tackle-cohort/1', cohort_id='2026-09-third-candidate-smoke-report-test',
            hypothesis='A synthetic smoke hypothesis for testing.',
            primary_metric='fall rate', decision_rule='development-grade smoke, mechanical only; no comparison.',
            n_min=1, seeds=[1],
            variants=[dict(scenario_id=S62, variant_id='v1', split='development', class_='outcome-trap',
                          fixture_sha256=H('fixture smoke'))],
            arms=['method', 'method:candidate'], comparisons=[],
            executor=dict(harness='claude-code-subagent', model='claude-haiku-4-5', effort='n/a'),
            judge=dict(model_family='n/a', blinded=True),
            artifacts=manifest['artifacts'], oracle_sha256=H('oracle'),
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
        self.assertIn('(no comparison: development-grade smoke)', report_text)

    def test_report_never_opens_a_path_outside_its_own_scope(self):
        manifest = sealed_manifest('2026-09-third-candidate-report-scope-test')
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
