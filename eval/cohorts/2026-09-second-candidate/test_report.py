"""report.py's rendering, its `--check` regression contract, its escalation-mechanism post-hoc model
check, and its input scope — all on synthetic cohorts, several mirrored into a temporary directory
laid out exactly like the real one (report.py's sibling import of protocol-v2's check.py resolves against
wherever the *script* lives, so a faithful subprocess-level test copies the script there too, rather than
pointing the real file at fake data).
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

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PROTOCOL_DIR = ROOT / 'eval' / 'protocol-v2'

# A distinctive spec name (never 'candidate_decision_for_report_test', the prior cohort's own choice).
decision_spec = importlib.util.spec_from_file_location('second_candidate_decision_for_report_test', HERE / 'decision.py')
decision = importlib.util.module_from_spec(decision_spec)
decision_spec.loader.exec_module(decision)

# report.py's own module-level code only sets up sys.path and imports check/decision; it touches no file
# at import time, so importing it directly (unmirrored) is safe for testing its pure functions.
report_spec = importlib.util.spec_from_file_location('second_candidate_report', HERE / 'report.py')
report = importlib.util.module_from_spec(report_spec)
report_spec.loader.exec_module(report)

# Only plain functions, never a TestCase subclass: importing one would make unittest discover count and
# run it a second time under this module too, breaking the suite registry's exact test count.
from test_decision import build_manifest, write_cohort, episode_line, sha_file, S62, S63, S64, NA, H, ZERO  # noqa: E402


def mirror(tmp):
    """<tmp>/eval/protocol-v2/{check.py,verdict.py} and <tmp>/eval/cohorts/2026-09-second-candidate/
    {report.py,decision.py,price-table.json}, so the mirrored report.py's own sys.path bootstrapping
    resolves exactly as it does at its real location."""
    protocol = tmp / 'eval' / 'protocol-v2'
    protocol.mkdir(parents=True)
    shutil.copy(PROTOCOL_DIR / 'check.py', protocol / 'check.py')
    shutil.copy(PROTOCOL_DIR / 'verdict.py', protocol / 'verdict.py')
    cohort_dir = tmp / 'eval' / 'cohorts' / '2026-09-second-candidate'
    cohort_dir.mkdir(parents=True)
    shutil.copy(HERE / 'report.py', cohort_dir / 'report.py')
    shutil.copy(HERE / 'decision.py', cohort_dir / 'decision.py')
    shutil.copy(HERE / 'price-table.json', cohort_dir / 'price-table.json')
    return cohort_dir


def sealed_manifest(cohort_id):
    clause = 'decision.py sha256=%s; price-table sha256=%s' % (sha_file(HERE / 'decision.py'),
                                                                sha_file(HERE / 'price-table.json'))
    return build_manifest(cohort_id, 'sealed for a mirrored report test; ' + clause)


def role(model, tokens_in, tokens_out, role_name='executor', tier='fast'):
    return {'role': role_name, 'tier': tier, 'model': model, 'effort': NA, 'tokens_in': tokens_in,
           'tokens_out': tokens_out}


def rec(scenario_id, arm, outcome, roles=(), tokens_in=100000, tokens_out=1000, model='claude-haiku-4-5'):
    """A minimal record shaped enough for escalation_model_check/artifact_hashes, never a full protocol-v2
    record: these tests exercise report.py's own pure functions directly, not check.py's schema."""
    return {'scenario_id': scenario_id, 'variant_id': 'v1', 'arm': arm, 'outcome': outcome,
           'executor': {'model': model}, 'roles': list(roles), 'artifact_sha256': None if arm == 'control' else H('tree'),
           'cost': {'tokens_in': tokens_in, 'tokens_out': tokens_out}}


def row(record, judgment=None, audit=None):
    return (record, judgment or {}, audit or {'verdict': 'clean', 'reason': None, 'outside_paths': [], 'skill_used': False})


class EscalationModelCheck(unittest.TestCase):
    """The live escalation mechanism episode's own post-hoc model check — the merged record's
    roles[2].model (the only real proof of the tier actually served) must equal claude-sonnet-5 and differ
    from roles[1].model and roles[0].model."""

    def test_the_expected_three_role_shape_passes(self):
        rows = [row(rec(S62, 'method:split', 'avoided', roles=[
            role('claude-haiku-4-5', 50000, 500, 'planner', 'fast'),
            role('claude-haiku-4-5', 10000, 100, 'executor', 'fast'),
            role('claude-sonnet-5', 400000, 3000, 'executor', 'standard')]))]
        outcome, models = report.escalation_model_check(rows)
        self.assertEqual(outcome, 'pass')
        self.assertEqual(models, ['claude-haiku-4-5', 'claude-haiku-4-5', 'claude-sonnet-5'])

    def test_a_dated_served_id_is_normalized_before_comparison(self):
        """Real served ids are often dated (a snapshot id such as <id>-YYYYMMDD); an exact-string compare
        would spuriously fail even though the tier truly differs."""
        rows = [row(rec(S62, 'method:split', 'avoided', roles=[
            role('claude-haiku-4-5-20251001', 50000, 500, 'planner', 'fast'),
            role('claude-haiku-4-5-20251001', 10000, 100, 'executor', 'fast'),
            role('claude-sonnet-5-20260901', 400000, 3000, 'executor', 'standard')]))]
        outcome, _ = report.escalation_model_check(rows)
        self.assertEqual(outcome, 'pass')

    def test_session_three_on_the_same_model_as_session_two_fails(self):
        """The escalation must be real: session 3 served at the same model as session 2 fails, disclosed
        as a finding about that one episode, never silently accepted. Session 3 is itself claude-sonnet-5
        here (so a check that only asked "does session 3 equal claude-sonnet-5" would wrongly pass this
        case) — the point is that session 2 was *also* dispatched at that model, so no real escalation to
        a distinct tier happened."""
        rows = [row(rec(S62, 'method:split', 'avoided', roles=[
            role('claude-haiku-4-5', 50000, 500, 'planner', 'fast'),
            role('claude-sonnet-5', 10000, 100, 'executor', 'fast'),
            role('claude-sonnet-5', 400000, 3000, 'executor', 'standard')]))]
        outcome, models = report.escalation_model_check(rows)
        self.assertEqual(outcome, 'fail')
        self.assertEqual(models[2], models[1])

    def test_session_three_matching_session_one_instead_fails(self):
        rows = [row(rec(S62, 'method:split', 'avoided', roles=[
            role('claude-sonnet-5', 50000, 500, 'planner', 'fast'),
            role('claude-haiku-4-5', 10000, 100, 'executor', 'fast'),
            role('claude-sonnet-5', 400000, 3000, 'executor', 'standard')]))]
        outcome, models = report.escalation_model_check(rows)
        self.assertEqual(outcome, 'fail')
        self.assertEqual(models[2], models[0])

    def test_no_three_role_record_is_not_observed_never_a_default_pass(self):
        rows = [row(rec(S62, 'method:split', 'avoided', roles=[
            role('claude-haiku-4-5', 50000, 500, 'planner', 'fast'),
            role('claude-haiku-4-5', 10000, 100, 'executor', 'fast')]))]
        outcome, models = report.escalation_model_check(rows)
        self.assertEqual(outcome, 'not observed')
        self.assertIsNone(models)

    def test_an_empty_rows_list_is_not_observed(self):
        outcome, models = report.escalation_model_check([])
        self.assertEqual(outcome, 'not observed')
        self.assertIsNone(models)


class ArtifactHashes(unittest.TestCase):
    def test_candidate_from_manifest_and_method_from_its_own_episode(self):
        manifest = {'artifacts': {'candidate_sha256': 'c' * 64}}
        rows = [row(rec(S62, 'method', 'avoided'))]
        candidate_sha, method_sha = report.artifact_hashes(manifest, rows)
        self.assertEqual(candidate_sha, 'c' * 64)
        self.assertEqual(method_sha, rows[0][0]['artifact_sha256'])

    def test_no_method_episode_yet_is_na(self):
        manifest = {'artifacts': {'candidate_sha256': 'c' * 64}}
        rows = [row(rec(S62, 'method:candidate', 'avoided'))]
        _, method_sha = report.artifact_hashes(manifest, rows)
        self.assertEqual(method_sha, NA)


class RenderAndCheck(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix='second-report-mirror-'))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.cohort_dir = mirror(self.tmp)

    def run_report(self, *args):
        return subprocess.run([sys.executable, str(self.cohort_dir / 'report.py')] + list(args),
                              capture_output=True, text=True, cwd=str(self.cohort_dir))

    def test_render_then_check_is_byte_identical_and_split_is_never_pass_fail_shaped(self):
        manifest = sealed_manifest('2026-09-second-candidate-report-test')
        default_cost = {'tokens_in': 1000, 'tokens_out': 100, 'wall_seconds': 10, 'tool_calls': 2, 'files_written': 0}
        data = {}
        for scenario in (S62, S64):
            for seed in (1, 2, 3):
                data[(scenario, 'method', seed)] = ('fell', [], dict(default_cost, tokens_in=800000, tool_calls=16),
                                                    'claude-haiku-4-5-20251001')
                data[(scenario, 'method:candidate', seed)] = ('avoided', [],
                                                              dict(default_cost, tokens_in=400000, tool_calls=8),
                                                              'claude-haiku-4-5-20251001')
                data[(scenario, 'method:split', seed)] = ('avoided', [
                    role('claude-haiku-4-5-20251001', 50000, 500, 'planner', 'fast'),
                    role('claude-haiku-4-5-20251001', 30000, 400, 'executor', 'fast')],
                    dict(default_cost, tokens_in=1, tool_calls=1), 'claude-haiku-4-5-20251001')
        write_cohort(self.cohort_dir, manifest, data)
        write_result = self.run_report()
        self.assertEqual(write_result.returncode, 0, write_result.stdout + write_result.stderr)
        self.assertTrue((self.cohort_dir / 'report.md').is_file())
        report_text = (self.cohort_dir / 'report.md').read_text(encoding='utf-8')
        self.assertIn('`candidate`: **PASS**', report_text)
        self.assertIn('`split`: report-only', report_text)
        self.assertNotIn('RULE', report_text)
        self.assertNotIn('RECOMMENDATION', report_text)
        self.assertIn('Artifacts: candidate', report_text)
        check_result = self.run_report('--check')
        self.assertEqual(check_result.returncode, 0, check_result.stdout + check_result.stderr)
        # A drifted report.md is caught.
        (self.cohort_dir / 'report.md').write_text(report_text + 'stray line\n', encoding='utf-8')
        drifted = self.run_report('--check')
        self.assertEqual(drifted.returncode, 1)

    def test_smoke_section_prints_the_escalation_model_check(self):
        """An end-to-end render with a sibling smoke/ directory whose one episode carries the live
        escalation mechanism's own three-role shape; the smoke section's own line reads pass."""
        manifest = sealed_manifest('2026-09-second-candidate-report-smoke-test')
        write_cohort(self.cohort_dir, manifest, {})
        smoke_dir = self.cohort_dir / 'smoke'
        order = [dict(episode_id='smoke-1', scenario_id=S62, variant_id='v1', arm='method:split', seed=1),
                dict(episode_id='smoke-2', scenario_id=S62, variant_id='v1', arm='method:split', seed=1)]
        smoke_manifest = dict(
            schema='tackle-cohort/1', cohort_id='2026-09-second-candidate-smoke-report-test',
            hypothesis='A synthetic smoke hypothesis for testing.',
            primary_metric='fall rate', decision_rule='development-grade smoke, mechanical only; no comparison.',
            n_min=1, seeds=[1],
            variants=[dict(scenario_id=S62, variant_id='v1', split='development', class_='outcome-trap',
                          fixture_sha256=H('fixture smoke'))],
            arms=['method:split'], comparisons=[],
            executor=dict(harness='claude-code-subagent', model='claude-haiku-4-5', effort='n/a'),
            judge=dict(model_family='n/a', blinded=True),
            artifacts=dict(baseline_sha256=ZERO, candidate_sha256=H('candidate tree')), oracle_sha256=H('oracle'),
            order=order, created_at='2026-09-26T00:00:00Z')
        for entry in smoke_manifest['variants']:
            entry['class'] = entry.pop('class_')
        # protocol-v2's own seal() import is copied alongside check.py; recompute the same way decision's
        # own end-to-end test does, via a tiny inline seal (avoids importing the fixtures/build.py module
        # a second time under a mirrored path).
        body = {k: v for k, v in smoke_manifest.items() if k != 'seal_sha256'}
        smoke_manifest['seal_sha256'] = hashlib.sha256(
            json.dumps(body, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
        smoke_dir.mkdir(parents=True, exist_ok=True)
        (smoke_dir / 'manifest.json').write_text(json.dumps(smoke_manifest, indent=1, ensure_ascii=False) + '\n')
        default_cost = {'tokens_in': 1000, 'tokens_out': 100, 'wall_seconds': 10, 'tool_calls': 2, 'files_written': 0}
        lines, prev = [], ZERO
        roles_by_index = [
            [role('claude-haiku-4-5', 50000, 500, 'planner', 'fast'),
             role('claude-haiku-4-5', 10000, 100, 'executor', 'fast'),
             role('claude-sonnet-5', 400000, 3000, 'executor', 'standard')],
            [role('claude-haiku-4-5', 50000, 500, 'planner', 'fast'),
             role('claude-haiku-4-5', 30000, 400, 'executor', 'fast')],
        ]
        for index, entry in enumerate(smoke_manifest['order']):
            line = episode_line(smoke_manifest, entry, index, prev, 'avoided', roles_by_index[index], default_cost,
                                'claude-haiku-4-5', split='development')
            text = json.dumps(line, ensure_ascii=False)
            lines.append(text)
            prev = H(text)
        (smoke_dir / 'episodes.jsonl').write_text(''.join(t + '\n' for t in lines))
        write_result = self.run_report()
        self.assertEqual(write_result.returncode, 0, write_result.stdout + write_result.stderr)
        report_text = (self.cohort_dir / 'report.md').read_text(encoding='utf-8')
        self.assertIn('Escalation mechanism episode, post-hoc model check: **pass**', report_text)

    def test_report_never_opens_a_path_outside_its_own_scope(self):
        manifest = sealed_manifest('2026-09-second-candidate-report-scope-test')
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
