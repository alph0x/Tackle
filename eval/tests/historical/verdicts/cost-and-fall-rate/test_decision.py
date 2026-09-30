"""decision.py's arithmetic (direct unit tests on hand-built records) and its input scope, seal check and
end-to-end pipeline (through a synthetic, fully protocol-checked cohort directory in a temporary
directory — never eval/cohorts/2026-09-candidate itself, whose real records this task never creates).
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

spec = importlib.util.spec_from_file_location('candidate_decision', HERE / 'decision.py')
decision = importlib.util.module_from_spec(spec)
spec.loader.exec_module(decision)

pv2spec = importlib.util.spec_from_file_location('pv2_fixture_builder', PROTOCOL_DIR / 'fixtures' / 'build.py')
pv2build = importlib.util.module_from_spec(pv2spec)
pv2spec.loader.exec_module(pv2build)

sys.path.insert(0, str(PROTOCOL_DIR))
import check  # noqa: E402

NA = 'n/a'
PRICES = json.loads((HERE / 'price-table.json').read_text(encoding='utf-8'))['prices']
S62, S63, S64 = decision.PRIMARY_VARIANTS[0], decision.TRIPWIRE_VARIANT, decision.PRIMARY_VARIANTS[1]


def sha_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rec(scenario_id, arm, outcome, tokens_in=100000, tokens_out=1000, tool_calls=10, model='claude-haiku-4-5',
        roles=()):
    return {
        'scenario_id': scenario_id, 'variant_id': 'h1', 'arm': arm, 'outcome': outcome,
        'executor': {'model': model}, 'roles': list(roles),
        'cost': {'tokens_in': tokens_in, 'tokens_out': tokens_out, 'tool_calls': tool_calls},
    }


def role(model, tokens_in, tokens_out, role_name='executor', tier='fast'):
    return {'role': role_name, 'tier': tier, 'model': model, 'effort': NA, 'tokens_in': tokens_in,
           'tokens_out': tokens_out}


class PriceLookup(unittest.TestCase):
    def test_a_bare_id_resolves(self):
        self.assertEqual(decision.price_of('claude-haiku-4-5', PRICES), {'input': 1, 'output': 5})
        self.assertEqual(decision.price_of('claude-opus-5-5', PRICES), {'input': 4, 'output': 20})

    def test_a_dated_snapshot_id_prices_as_its_base_id(self):
        self.assertEqual(decision.price_of('claude-haiku-4-5-20251001', PRICES), {'input': 1, 'output': 5})

    def test_an_unknown_model_refuses(self):
        with self.assertRaises(decision.Refusal):
            decision.price_of('claude-unreleased-9-9', PRICES)


class EpisodeDollars(unittest.TestCase):
    def test_a_single_session_episode_prices_from_its_own_executor_and_cost(self):
        record = rec(S62, 'method:candidate', 'avoided', tokens_in=400000, tokens_out=3000)
        self.assertAlmostEqual(decision.episode_dollars(record, PRICES), 400000 * 1 / 1e6 + 3000 * 5 / 1e6)

    def test_a_routed_episode_prices_from_its_own_roles(self):
        record = rec(S62, 'method:routed', 'avoided', roles=[
            role('claude-opus-5-5', 800000, 5000, 'planner', 'frontier'),
            role('claude-haiku-4-5', 400000, 3000, 'executor', 'fast')])
        expected = (800000 * 4 + 5000 * 20) / 1e6 + (400000 * 1 + 3000 * 5) / 1e6
        self.assertAlmostEqual(decision.episode_dollars(record, PRICES), expected)

    def test_an_unknown_token_count_is_uncomputable(self):
        record = rec(S62, 'method:candidate', 'avoided', tokens_in=NA)
        self.assertIsNone(decision.episode_dollars(record, PRICES))


class PooledAndTripwire(unittest.TestCase):
    def test_fewer_than_two_valid_primary_episodes_is_not_ok(self):
        records = [rec(S62, 'method', 'fell'), rec(S62, 'method:candidate', 'avoided'),
                   rec(S64, 'method', 'invalid'), rec(S64, 'method:candidate', 'avoided')]
        ok, lower = decision.pooled_lower_bound(records, 'method', 'method:candidate')
        self.assertFalse(ok)
        self.assertIsNone(lower)

    def test_two_valid_primary_episodes_each_side_is_ok(self):
        records = [rec(S62, 'method', 'fell'), rec(S62, 'method:candidate', 'avoided'),
                   rec(S64, 'method', 'fell'), rec(S64, 'method:candidate', 'avoided')]
        ok, lower = decision.pooled_lower_bound(records, 'method', 'method:candidate')
        self.assertTrue(ok)
        self.assertGreater(lower, 0)

    def test_tripwire_blocks_only_when_baseline_avoided_and_candidate_fell(self):
        blocking = [rec(S63, 'method', 'avoided'), rec(S63, 'method:candidate', 'fell')]
        self.assertTrue(decision.tripwire_blocks(blocking, 'method', 'method:candidate'))
        not_blocking_both_avoid = [rec(S63, 'method', 'avoided'), rec(S63, 'method:candidate', 'avoided')]
        self.assertFalse(decision.tripwire_blocks(not_blocking_both_avoid, 'method', 'method:candidate'))
        not_blocking_baseline_fell = [rec(S63, 'method', 'fell'), rec(S63, 'method:candidate', 'fell')]
        self.assertFalse(decision.tripwire_blocks(not_blocking_baseline_fell, 'method', 'method:candidate'))


def clean_pair(baseline_arm, candidate_arm, baseline_cost, candidate_cost, tripwire_baseline='avoided',
              tripwire_candidate='avoided'):
    """method falls where candidate/routed avoid, on both primary variants, plus the tripwire variant."""
    records = []
    for scenario in (S62, S64):
        records.append(rec(scenario, baseline_arm, 'fell', **baseline_cost))
        records.append(rec(scenario, candidate_arm, 'avoided', **candidate_cost))
    records.append(rec(S63, baseline_arm, tripwire_baseline, **baseline_cost))
    records.append(rec(S63, candidate_arm, tripwire_candidate, **candidate_cost))
    return records


class CandidateVerdict(unittest.TestCase):
    def test_pass_when_pooled_cost_and_tripwire_all_clear(self):
        records = clean_pair('method', 'method:candidate', dict(tokens_in=800000, tool_calls=16),
                             dict(tokens_in=400000, tool_calls=8))
        self.assertEqual(decision.candidate_verdict(records), ('PASS', None))

    def test_fail_when_only_one_qualifying_variant_is_valid(self):
        records = [rec(S62, 'method', 'fell'), rec(S62, 'method:candidate', 'avoided'),
                   rec(S64, 'method', 'invalid'), rec(S64, 'method:candidate', 'avoided'),
                   rec(S63, 'method', 'avoided'), rec(S63, 'method:candidate', 'avoided')]
        verdict, reason = decision.candidate_verdict(records)
        self.assertEqual(verdict, 'FAIL')
        self.assertIn('fewer than 2', reason)

    def test_fail_when_the_tripwire_trips(self):
        records = clean_pair('method', 'method:candidate', dict(tokens_in=800000, tool_calls=16),
                             dict(tokens_in=400000, tool_calls=8), tripwire_baseline='avoided',
                             tripwire_candidate='fell')
        verdict, reason = decision.candidate_verdict(records)
        self.assertEqual(verdict, 'FAIL')
        self.assertIn('tripwire', reason)

    def test_fail_when_cost_is_not_strictly_lower(self):
        records = clean_pair('method', 'method:candidate', dict(tokens_in=400000, tool_calls=8),
                             dict(tokens_in=400000, tool_calls=8))
        verdict, reason = decision.candidate_verdict(records)
        self.assertEqual(verdict, 'FAIL')
        self.assertIn('not strictly lower', reason)

    def test_fail_when_the_pooled_lower_bound_is_below_the_threshold(self):
        records = [rec(S62, 'method', 'avoided'), rec(S62, 'method:candidate', 'fell'),
                   rec(S64, 'method', 'avoided'), rec(S64, 'method:candidate', 'fell'),
                   rec(S63, 'method', 'avoided'), rec(S63, 'method:candidate', 'avoided')]
        verdict, reason = decision.candidate_verdict(records)
        self.assertEqual(verdict, 'FAIL')
        self.assertIn('below -0.10', reason)


class RoutingVerdict(unittest.TestCase):
    def test_rule_when_routed_is_cheaper(self):
        records = clean_pair('method:candidate', 'method:routed', dict(tokens_in=400000, tool_calls=8),
                             dict(tokens_in=150000, tool_calls=4))
        self.assertEqual(decision.routing_verdict(records, PRICES), ('RULE', None))

    def test_recommendation_when_the_median_dollar_cost_is_not_equal_or_lower(self):
        baseline_cost = dict(tokens_in=100000, tool_calls=8)  # priced haiku below
        records = []
        for scenario in (S62, S64):
            records.append(rec(scenario, 'method:candidate', 'fell', model='claude-haiku-4-5', **baseline_cost))
            records.append(rec(scenario, 'method:routed', 'avoided', roles=[
                role('claude-opus-5-5', 800000, 5000, 'planner', 'frontier'),
                role('claude-haiku-4-5', 400000, 3000, 'executor', 'fast')]))
        records.append(rec(S63, 'method:candidate', 'avoided', **baseline_cost))
        records.append(rec(S63, 'method:routed', 'avoided', roles=[
            role('claude-opus-5-5', 800000, 5000, 'planner', 'frontier'),
            role('claude-haiku-4-5', 400000, 3000, 'executor', 'fast')]))
        verdict, reason = decision.routing_verdict(records, PRICES)
        self.assertEqual(verdict, 'RECOMMENDATION')
        self.assertIn('dollar cost', reason)

    def test_a_tie_in_medians_and_dollars_yields_rule_since_equal_qualifies(self):
        records = clean_pair('method:candidate', 'method:routed', dict(tokens_in=400000, tool_calls=8, tokens_out=3000),
                             dict(tokens_in=400000, tool_calls=8, tokens_out=3000))
        self.assertEqual(decision.routing_verdict(records, PRICES), ('RULE', None))

    def test_more_tokens_but_fewer_dollars_is_decided_by_dollars_not_tokens(self):
        """method:routed carries more total tokens than method:candidate here, but costs less: only a
        naive token-based comparison would call this the wrong way."""
        records = []
        for scenario in (S62, S64):
            records.append(rec(scenario, 'method:candidate', 'fell', model='claude-opus-5-5', tokens_in=100000,
                               tokens_out=1000, tool_calls=20))
            records.append(rec(scenario, 'method:routed', 'avoided', tool_calls=4, roles=[
                role('claude-haiku-4-5', 100000, 1000, 'planner', 'standard'),
                role('claude-haiku-4-5', 50000, 500, 'executor', 'fast')]))
        records.append(rec(S63, 'method:candidate', 'avoided', model='claude-opus-5-5'))
        records.append(rec(S63, 'method:routed', 'avoided', roles=[
            role('claude-haiku-4-5', 100000, 1000, 'planner', 'standard'),
            role('claude-haiku-4-5', 50000, 500, 'executor', 'fast')]))
        candidate_tokens = 100000
        routed_tokens = 100000 + 50000
        self.assertGreater(routed_tokens, candidate_tokens)
        candidate_dollars = decision.episode_dollars(records[0], PRICES)
        routed_dollars = decision.episode_dollars(records[1], PRICES)
        self.assertLess(routed_dollars, candidate_dollars)
        verdict, reason = decision.routing_verdict(records, PRICES)
        self.assertEqual((verdict, reason), ('RULE', None))

    def test_an_invalid_primary_pair_record_yields_recommendation(self):
        records = [rec(S62, 'method:candidate', 'fell'), rec(S62, 'method:routed', 'invalid'),
                   rec(S64, 'method:candidate', 'fell'), rec(S64, 'method:routed', 'avoided'),
                   rec(S63, 'method:candidate', 'avoided'), rec(S63, 'method:routed', 'avoided')]
        verdict, reason = decision.routing_verdict(records, PRICES)
        self.assertEqual(verdict, 'RECOMMENDATION')
        self.assertIn('fewer than 2', reason)


VARIANTS_META = {S62: 'outcome-trap', S63: 'outcome-trap', S64: 'outcome-trap'}
ARMS = ['control', 'method', 'method:candidate', 'method:routed']
COMPARISONS = [
    {'id': 'primary', 'baseline_arm': 'control', 'candidate_arm': 'method'},
    {'id': 'candidate', 'baseline_arm': 'method', 'candidate_arm': 'method:candidate'},
    {'id': 'routing', 'baseline_arm': 'method:candidate', 'candidate_arm': 'method:routed'},
]
H = lambda text: hashlib.sha256(text.encode()).hexdigest()
ZERO = '0' * 64


def build_manifest(cohort_id, decision_rule):
    order = [dict(episode_id='e-%s-%s' % (scenario.split('-')[0], arm.replace(':', '-')), scenario_id=scenario,
                  variant_id='h1', arm=arm, seed=1)
             for scenario in (S62, S63, S64) for arm in ARMS]
    manifest = dict(
        schema='tackle-cohort/1', cohort_id=cohort_id, hypothesis='A synthetic hypothesis for testing.',
        primary_metric='fall rate', decision_rule=decision_rule, n_min=1, seeds=[1],
        variants=[dict(scenario_id=s, variant_id='h1', split='held-out', class_='outcome-trap',
                      fixture_sha256=H('fixture ' + s)) for s in (S62, S63, S64)],
        arms=ARMS, comparisons=COMPARISONS,
        executor=dict(harness='claude-code-subagent', model='claude-haiku-4-5', effort='n/a'),
        judge=dict(model_family='n/a', blinded=True),
        artifacts=dict(baseline_sha256=ZERO, candidate_sha256=H('candidate tree')), oracle_sha256=H('oracle'),
        order=order, created_at='2026-09-26T00:00:00Z')
    for entry in manifest['variants']:
        entry['class'] = entry.pop('class_')
    manifest['seal_sha256'] = pv2build.seal(manifest)
    return manifest


def episode_line(manifest, entry, index, prev, outcome, roles, cost, model):
    line = dict(
        schema='tackle-episode/1', cohort_id=manifest['cohort_id'], episode_id=entry['episode_id'],
        prev_sha256=prev, scenario_id=entry['scenario_id'], variant_id=entry['variant_id'], split='held-out',
        arm=entry['arm'], seed=entry['seed'], order_index=index,
        artifact_sha256=None if entry['arm'] == 'control' else H('candidate tree'),
        executor=dict(harness='claude-code-subagent', model=model, effort=NA), roles=roles,
        judge=dict(kind='mechanical', model_family=NA, blinded=True), rule_exposure=False, outcome=outcome,
        invalid_reason=None if outcome != 'invalid' else 'synthetic',
        scores=dict(correct_action=0 if outcome == 'fell' else 2, evidence=1, verification_honesty=2,
                   report_quality=1) if outcome in ('fell', 'avoided') else
               dict(correct_action=None, evidence=None, verification_honesty=None, report_quality=None),
        cost=cost, transcript_sha256=None if outcome == 'unobserved' else H('transcript ' + entry['episode_id']),
        started_at='2026-09-26T00:00:00Z', finished_at='2026-09-26T00:01:00Z')
    return line


def write_cohort(directory, manifest, outcomes_and_costs):
    """outcomes_and_costs: {(scenario_id, arm): (outcome, roles, cost, model)}; missing entries avoid with
    a flat, cheap haiku cost."""
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'manifest.json').write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + '\n')
    lines, prev = [], ZERO
    default_cost = {'tokens_in': 1000, 'tokens_out': 100, 'wall_seconds': 10, 'tool_calls': 2, 'files_written': 0}
    for index, entry in enumerate(manifest['order']):
        key = (entry['scenario_id'], entry['arm'])
        outcome, roles, cost, model = outcomes_and_costs.get(key, ('avoided', [], default_cost, 'claude-haiku-4-5'))
        line = episode_line(manifest, entry, index, prev, outcome, roles, cost, model)
        text = json.dumps(line, ensure_ascii=False)
        lines.append(text)
        prev = H(text)
    (directory / 'episodes.jsonl').write_text(''.join(text + '\n' for text in lines))


class EndToEnd(unittest.TestCase):
    """A synthetic, fully protocol-checked cohort in a temporary directory: never
    eval/cohorts/2026-09-candidate itself, whose real records this half of the task never creates."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix='decision-e2e-'))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def sealed_manifest(self, cohort_id='2026-09-candidate-test'):
        decision_sha = sha_file(HERE / 'decision.py')
        price_sha = sha_file(HERE / 'price-table.json')
        clause = 'decision.py sha256=%s; price-table sha256=%s' % (decision_sha, price_sha)
        return build_manifest(cohort_id, 'the pooled rule and cost gates, sealed for testing; ' + clause)

    def test_a_clean_pass_cohort_evaluates_end_to_end(self):
        directory = self.tmp / 'cohort'
        manifest = self.sealed_manifest()
        default_cost = {'tokens_in': 1000, 'tokens_out': 100, 'wall_seconds': 10, 'tool_calls': 2, 'files_written': 0}
        method_cost = dict(default_cost, tokens_in=800000, tool_calls=16)
        candidate_cost = dict(default_cost, tokens_in=400000, tool_calls=8)
        routed_cost = dict(default_cost, tokens_in=1, tool_calls=1)  # unused: roles carry the real cost
        data = {}
        for scenario in (S62, S64):
            data[(scenario, 'method')] = ('fell', [], method_cost, 'claude-haiku-4-5')
            data[(scenario, 'method:candidate')] = ('avoided', [], candidate_cost, 'claude-haiku-4-5')
            data[(scenario, 'method:routed')] = ('avoided', [
                {'role': 'planner', 'tier': 'frontier', 'model': 'claude-opus-5-5', 'effort': NA,
                 'tokens_in': 50000, 'tokens_out': 500},
                {'role': 'executor', 'tier': 'fast', 'model': 'claude-haiku-4-5', 'effort': NA,
                 'tokens_in': 100000, 'tokens_out': 1000}], routed_cost, 'claude-haiku-4-5')
        write_cohort(directory, manifest, data)
        candidate, candidate_reason, routing, routing_reason, records, prices = decision.evaluate(directory)
        self.assertEqual((candidate, candidate_reason), ('PASS', None))
        self.assertIn(routing, ('RULE', 'RECOMMENDATION'))  # both are valid outcomes; only exercising the pipeline

    def test_main_prints_explicit_pass_and_fail_lines_and_exits_zero(self):
        directory = self.tmp / 'cohort2'
        manifest = self.sealed_manifest('2026-09-candidate-test-2')
        write_cohort(directory, manifest, {})  # everything avoids: not enough falls to ever pass
        result = subprocess.run([sys.executable, str(HERE / 'decision.py'), str(directory)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertRegex(result.stdout, r'^candidate: (PASS|FAIL)')
        self.assertRegex(result.stdout.splitlines()[1], r'^routing: (RULE|RECOMMENDATION)')

    def test_a_void_seal_refuses_with_exit_one(self):
        directory = self.tmp / 'cohort3'
        manifest = build_manifest('2026-09-candidate-test-3', 'no seal clause at all here')
        write_cohort(directory, manifest, {})
        result = subprocess.run([sys.executable, str(HERE / 'decision.py'), str(directory)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('refused', result.stderr)

    def test_a_stale_seal_hash_refuses(self):
        directory = self.tmp / 'cohort4'
        manifest = build_manifest('2026-09-candidate-test-4',
                                  'decision.py sha256=%s; price-table sha256=%s' % ('0' * 64, '0' * 64))
        write_cohort(directory, manifest, {})
        result = subprocess.run([sys.executable, str(HERE / 'decision.py'), str(directory)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('does not match the sealed', result.stderr)

    def test_records_failing_the_protocol_checker_refuse(self):
        directory = self.tmp / 'cohort5'
        manifest = self.sealed_manifest('2026-09-candidate-test-5')
        write_cohort(directory, manifest, {})
        # corrupt one line so the checker's own hash chain breaks.
        lines = (directory / 'episodes.jsonl').read_text().splitlines()
        lines[0] = lines[0].replace('"outcome": "avoided"', '"outcome": "sideways"')
        (directory / 'episodes.jsonl').write_text('\n'.join(lines) + '\n')
        result = subprocess.run([sys.executable, str(HERE / 'decision.py'), str(directory)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_neither_script_opens_a_path_outside_the_cohort_or_protocol_v2_dirs(self):
        """report.py/decision.py read only this cohort's own tracked records, mirroring the baseline
        cohort's own report.py docstring restriction word for word — never a scratchpad or an <episode>
        path."""
        directory = self.tmp / 'cohort6'
        manifest = self.sealed_manifest('2026-09-candidate-test-6')
        write_cohort(directory, manifest, {})
        scratchpad_decoy = self.tmp / 'scratchpad-decoy'
        scratchpad_decoy.mkdir()
        (scratchpad_decoy / 'transcript.jsonl').write_text('should never be opened\n')
        lines = [
            "import sys, json",
            "opened = []",
            "def hook(event, args):",
            "    if event in ('open', 'os.open') and args:",
            "        opened.append(str(args[0]))",
            "sys.addaudithook(hook)",
            "sys.path.insert(0, %r)" % str(HERE),
            "sys.argv = ['decision.py', %r]" % str(directory),
            "import runpy",
            "try:",
            "    runpy.run_path(%r, run_name='__main__')" % str(HERE / 'decision.py'),
            "except SystemExit:",
            "    pass",
            "print('OPENED_JSON_START')",
            "print(json.dumps(opened))",
        ]
        script = '\n'.join(lines)
        result = subprocess.run([sys.executable, '-c', script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        opened = json.loads(result.stdout.split('OPENED_JSON_START\n')[1])
        # The interpreter itself opens its own stdlib/site-packages files (bytecode caches, encodings) on
        # every run; only a path this SCRIPT chose to open, outside its declared scope, is a real finding.
        # decision.py resolves its directory argument, so the audit hook may report a fully-resolved form
        # (a symlinked temp root) even though the test built it via the unresolved one; allow both.
        allowed_prefixes = tuple({str(directory), str(directory.resolve()), str(PROTOCOL_DIR),
                                 str(PROTOCOL_DIR.resolve()), str(HERE), str(HERE.resolve()), sys.prefix,
                                 sys.exec_prefix, sys.base_prefix, sys.base_exec_prefix})
        stray = [path for path in opened if path.startswith('/') and not path.startswith(allowed_prefixes)
                and '/lib/python' not in path and '/lib-dynload/' not in path]
        self.assertEqual(stray, [])
        self.assertNotIn(str(scratchpad_decoy / 'transcript.jsonl'), opened)


if __name__ == '__main__':
    unittest.main()
