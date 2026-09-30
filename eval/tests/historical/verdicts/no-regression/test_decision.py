"""decision.py's arithmetic (direct unit tests on hand-built records) and its input scope, seal check and
end-to-end pipeline (through a synthetic, fully protocol-checked cohort directory in a temporary
directory -- never eval/cohorts/2026-09-third-candidate itself, whose real records this half of the task
never creates).

Adapted from the second candidate cohort's test_decision.py: `candidate_verdict`'s own tests are kept
(the rule is byte-for-byte unchanged); its `SplitAlwaysReportOnly` class is dropped, since this
cohort's decision.py has no split line; a `NoRegressionVerdict` class covers the new second line instead.
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

HERE = (Path(__file__).resolve().parents[5] / 'eval/cohorts/2026-09-third-candidate')
ROOT = HERE.parents[2]
PROTOCOL_DIR = ROOT / 'eval' / 'protocol-v2'

# A distinctive spec name (never a prior cohort's own choice for its identically named decision.py) so
# this file's own dynamic import can never be mistaken for another cohort's.
spec = importlib.util.spec_from_file_location('third_candidate_decision', HERE / 'decision.py')
decision = importlib.util.module_from_spec(spec)
spec.loader.exec_module(decision)

pv2spec = importlib.util.spec_from_file_location('pv2_fixture_builder_third', PROTOCOL_DIR / 'fixtures' / 'build.py')
pv2build = importlib.util.module_from_spec(pv2spec)
pv2spec.loader.exec_module(pv2build)

sys.path.insert(0, str(PROTOCOL_DIR))
import check  # noqa: E402

NA = 'n/a'
PRICES = json.loads((HERE / 'price-table.json').read_text(encoding='utf-8'))['prices']
S62, S63, S64 = decision.PRIMARY_VARIANTS[0], decision.TRIPWIRE_VARIANT, decision.PRIMARY_VARIANTS[1]


def sha_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rec(scenario_id, arm, outcome, tokens_in=100000, tokens_out=1000, tool_calls=10, model='claude-haiku-4-5'):
    return {
        'scenario_id': scenario_id, 'variant_id': 'h1', 'arm': arm, 'outcome': outcome,
        'executor': {'model': model}, 'roles': [],
        'cost': {'tokens_in': tokens_in, 'tokens_out': tokens_out, 'tool_calls': tool_calls},
    }


def recs(scenario_id, arm, outcomes, **kwargs):
    """One record per entry of `outcomes` (one per seed): the multi-seed shape this cohort's own n_min:2
    at 3 seeds needs, without inventing a `seed` field decision.py's own dict-level logic never reads."""
    return [rec(scenario_id, arm, outcome, **kwargs) for outcome in outcomes]


class PriceLookup(unittest.TestCase):
    def test_a_bare_id_resolves(self):
        self.assertEqual(decision.price_of('claude-haiku-4-5', PRICES), {'input': 1, 'output': 5})

    def test_a_dated_snapshot_id_prices_as_its_base_id(self):
        self.assertEqual(decision.price_of('claude-haiku-4-5-20260901', PRICES), {'input': 1, 'output': 5})

    def test_an_unknown_model_refuses(self):
        with self.assertRaises(decision.Refusal):
            decision.price_of('claude-unreleased-9-9', PRICES)

    def test_base_model_id_strips_exactly_one_trailing_date(self):
        self.assertEqual(decision.base_model_id('claude-haiku-4-5-20251001'), 'claude-haiku-4-5')
        self.assertEqual(decision.base_model_id('claude-haiku-4-5'), 'claude-haiku-4-5')


class EpisodeDollars(unittest.TestCase):
    """Every arm here is single-session (roles[] always empty): the fresh-input price comes straight from
    the episode's own top-level executor/cost, never a per-role split."""

    def test_a_single_session_episode_prices_from_its_own_executor_and_cost(self):
        record = rec(S62, 'method:candidate', 'avoided', tokens_in=400000, tokens_out=3000)
        self.assertAlmostEqual(decision.episode_dollars(record, PRICES), 400000 * 1 / 1e6 + 3000 * 5 / 1e6)

    def test_an_unknown_token_count_is_uncomputable(self):
        record = rec(S62, 'method:candidate', 'avoided', tokens_in=NA)
        self.assertIsNone(decision.episode_dollars(record, PRICES))


class Completeness(unittest.TestCase):
    """n_min applies per variant, not as a summed total across the two primary variants (Findings 9)."""

    def test_all_three_seeds_valid_both_arms_computes_a_verdict(self):
        records = (recs(S62, 'method', ['fell'] * 3) + recs(S62, 'method:candidate', ['avoided'] * 3)
                  + recs(S64, 'method', ['fell'] * 3) + recs(S64, 'method:candidate', ['avoided'] * 3))
        ok, lower = decision.pooled_lower_bound(records, 'method', 'method:candidate')
        self.assertTrue(ok)
        self.assertGreater(lower, 0)

    def test_exactly_two_of_three_valid_each_variant_still_computes_a_verdict(self):
        records = (recs(S62, 'method', ['fell', 'fell', 'invalid']) +
                  recs(S62, 'method:candidate', ['avoided', 'avoided', 'invalid'])
                  + recs(S64, 'method', ['fell', 'fell', 'invalid'])
                  + recs(S64, 'method:candidate', ['avoided', 'avoided', 'invalid']))
        ok, lower = decision.pooled_lower_bound(records, 'method', 'method:candidate')
        self.assertTrue(ok)

    def test_only_one_of_three_valid_on_one_arm_variant_is_not_passed(self):
        records = (recs(S62, 'method', ['fell', 'invalid', 'invalid']) + recs(S62, 'method:candidate', ['avoided'] * 3)
                  + recs(S64, 'method', ['fell'] * 3) + recs(S64, 'method:candidate', ['avoided'] * 3))
        ok, lower = decision.pooled_lower_bound(records, 'method', 'method:candidate')
        self.assertFalse(ok)
        self.assertIsNone(lower)


class TripwireAtThreeSeeds(unittest.TestCase):
    def test_one_fall_among_three_candidate_seeds_blocks_regardless_of_the_pooled_result(self):
        records = recs(S63, 'method', ['avoided'] * 3) + recs(S63, 'method:candidate', ['avoided', 'avoided', 'fell'])
        self.assertTrue(decision.tripwire_blocks(records, 'method', 'method:candidate'))

    def test_three_of_three_avoided_on_both_sides_does_not_block(self):
        records = recs(S63, 'method', ['avoided'] * 3) + recs(S63, 'method:candidate', ['avoided'] * 3)
        self.assertFalse(decision.tripwire_blocks(records, 'method', 'method:candidate'))

    def test_a_baseline_fall_never_blocks_even_if_the_candidate_also_falls(self):
        records = recs(S63, 'method', ['fell', 'avoided', 'avoided']) + recs(S63, 'method:candidate', ['fell'] * 3)
        self.assertFalse(decision.tripwire_blocks(records, 'method', 'method:candidate'))


def clean_pair(baseline_arm, candidate_arm, baseline_cost, candidate_cost, seeds=3, tripwire_baseline='avoided',
              tripwire_candidate='avoided'):
    records = []
    for scenario in (S62, S64):
        records += recs(scenario, baseline_arm, ['fell'] * seeds, **baseline_cost)
        records += recs(scenario, candidate_arm, ['avoided'] * seeds, **candidate_cost)
    records.append(rec(S63, baseline_arm, tripwire_baseline, **baseline_cost))
    records.append(rec(S63, candidate_arm, tripwire_candidate, **candidate_cost))
    return records


class CandidateVerdict(unittest.TestCase):
    """candidate_verdict is kept byte for byte from the second candidate cohort; these are its own
    tests, unchanged in substance."""

    def test_pass_when_pooled_cost_and_tripwire_all_clear(self):
        records = clean_pair('method', 'method:candidate', dict(tokens_in=800000, tool_calls=16),
                             dict(tokens_in=400000, tool_calls=8))
        self.assertEqual(decision.candidate_verdict(records), ('PASS', None))

    def test_fail_when_only_one_qualifying_variant_is_valid(self):
        records = (recs(S62, 'method', ['fell'] * 3) + recs(S62, 'method:candidate', ['avoided'] * 3)
                  + recs(S64, 'method', ['invalid'] * 3) + recs(S64, 'method:candidate', ['avoided'] * 3)
                  + [rec(S63, 'method', 'avoided'), rec(S63, 'method:candidate', 'avoided')])
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
        records = (recs(S62, 'method', ['avoided'] * 3) + recs(S62, 'method:candidate', ['fell'] * 3)
                  + recs(S64, 'method', ['avoided'] * 3) + recs(S64, 'method:candidate', ['fell'] * 3)
                  + [rec(S63, 'method', 'avoided'), rec(S63, 'method:candidate', 'avoided')])
        verdict, reason = decision.candidate_verdict(records)
        self.assertEqual(verdict, 'FAIL')
        self.assertIn('below -0.10', reason)


class NoRegressionVerdict(unittest.TestCase):
    """The new line: only the fall components; always returns the pooled figure and the tripwire status,
    whatever the verdict; checked in the order floor, bound, tripwire."""

    def test_pass_with_identical_rates_and_a_clear_tripwire(self):
        records = clean_pair('method', 'method:candidate', dict(tokens_in=400000, tool_calls=8),
                             dict(tokens_in=400000, tool_calls=8))  # cost is irrelevant to this line
        verdict, reason, lower, tripped = decision.no_regression_verdict(records)
        self.assertEqual(verdict, 'PASS')
        self.assertFalse(tripped)
        self.assertIsNotNone(lower)

    def test_a_dearer_candidate_still_passes_no_regression(self):
        """Cost gates `candidate`, never `no-regression`: a dearer candidate with a clean tripwire still
        passes the no-regression line."""
        records = clean_pair('method', 'method:candidate', dict(tokens_in=400000, tool_calls=8),
                             dict(tokens_in=800000, tool_calls=16))
        verdict, reason, lower, tripped = decision.no_regression_verdict(records)
        self.assertEqual(verdict, 'PASS')

    def test_fail_not_computed_reports_no_pooled_figure_but_still_reports_the_tripwire(self):
        records = (recs(S62, 'method', ['fell']) + recs(S62, 'method:candidate', ['avoided'] * 3)
                  + recs(S64, 'method', ['fell'] * 3) + recs(S64, 'method:candidate', ['avoided'] * 3)
                  + [rec(S63, 'method', 'avoided'), rec(S63, 'method:candidate', 'avoided')])
        verdict, reason, lower, tripped = decision.no_regression_verdict(records)
        self.assertEqual(verdict, 'FAIL')
        self.assertIn('not computed', reason)
        self.assertIsNone(lower)
        self.assertFalse(tripped)

    def test_fail_on_bound_reports_the_figure(self):
        records = (recs(S62, 'method', ['avoided'] * 3) + recs(S62, 'method:candidate', ['fell'] * 3)
                  + recs(S64, 'method', ['avoided'] * 3) + recs(S64, 'method:candidate', ['fell'] * 3)
                  + [rec(S63, 'method', 'avoided'), rec(S63, 'method:candidate', 'avoided')])
        verdict, reason, lower, tripped = decision.no_regression_verdict(records)
        self.assertEqual(verdict, 'FAIL')
        self.assertIn('below -0.10', reason)
        self.assertAlmostEqual(lower, -1.0)
        self.assertFalse(tripped)

    def test_fail_on_tripwire_still_reports_the_pooled_figure(self):
        records = clean_pair('method', 'method:candidate', dict(tokens_in=800000, tool_calls=16),
                             dict(tokens_in=400000, tool_calls=8), tripwire_baseline='avoided',
                             tripwire_candidate='fell')
        verdict, reason, lower, tripped = decision.no_regression_verdict(records)
        self.assertEqual(verdict, 'FAIL')
        self.assertIn('tripwire', reason)
        self.assertTrue(tripped)
        self.assertIsNotNone(lower)

    def test_format_no_regression_matches_the_printed_line_shape(self):
        text = decision.format_no_regression('PASS', "the candidate's fall rate is not above the method's "
                                             'on either pooled variant, and the tripwire is clear', 0.0, False)
        self.assertTrue(text.startswith('no-regression: PASS ('))
        self.assertIn('pooled fall-rate lower bound 0.0000', text)
        self.assertIn('tripwire clear', text)
        self.assertIn('a screen for an observed regression, not a significance test', text)
        text_na = decision.format_no_regression('FAIL', 'not computed: fewer than 2 valid episodes in the '
                                                'primary pair for at least one arm/variant', None, False)
        self.assertIn('pooled figure not computed', text_na)


VARIANTS_META = {S62: 'outcome-trap', S63: 'outcome-trap', S64: 'outcome-trap'}
ARMS = ['method', 'method:candidate']
SEEDS = (1, 2, 3)
COMPARISONS = [{'id': 'candidate', 'baseline_arm': 'method', 'candidate_arm': 'method:candidate'}]
H = lambda text: hashlib.sha256(text.encode()).hexdigest()
ZERO = '0' * 64
SHORT = {S62: 's62', S63: 's63', S64: 's64'}


def build_manifest(cohort_id, decision_rule, seeds=SEEDS):
    order = [dict(episode_id='e-%s-%s-%d' % (SHORT[scenario], arm.replace(':', '-'), seed), scenario_id=scenario,
                  variant_id='h1', arm=arm, seed=seed)
             for scenario in (S62, S63, S64) for arm in ARMS for seed in seeds]
    manifest = dict(
        schema='tackle-cohort/1', cohort_id=cohort_id, hypothesis='A synthetic hypothesis for testing.',
        primary_metric='fall rate', decision_rule=decision_rule, n_min=2, seeds=list(seeds),
        variants=[dict(scenario_id=s, variant_id='h1', split='held-out', class_='outcome-trap',
                      fixture_sha256=H('fixture ' + s)) for s in (S62, S63, S64)],
        arms=ARMS, comparisons=COMPARISONS,
        executor=dict(harness='claude-code-subagent', model='claude-haiku-4-5', effort='n/a'),
        judge=dict(model_family='n/a', blinded=True),
        artifacts=dict(baseline_sha256=H('8.4.1 tree'), candidate_sha256=H('candidate tree')), oracle_sha256=H('oracle'),
        order=order, created_at='2026-09-28T00:00:00Z')
    for entry in manifest['variants']:
        entry['class'] = entry.pop('class_')
    manifest['seal_sha256'] = pv2build.seal(manifest)
    return manifest


def episode_line(manifest, entry, index, prev, outcome, cost, model, split='held-out'):
    arm_hash = manifest['artifacts']['baseline_sha256'] if entry['arm'] == 'method' else manifest['artifacts']['candidate_sha256']
    return dict(
        schema='tackle-episode/1', cohort_id=manifest['cohort_id'], episode_id=entry['episode_id'],
        prev_sha256=prev, scenario_id=entry['scenario_id'], variant_id=entry['variant_id'], split=split,
        arm=entry['arm'], seed=entry['seed'], order_index=index, artifact_sha256=arm_hash,
        executor=dict(harness='claude-code-subagent', model=model, effort=NA), roles=[],
        judge=dict(kind='mechanical', model_family=NA, blinded=True), rule_exposure=False, outcome=outcome,
        invalid_reason=None if outcome != 'invalid' else 'synthetic',
        scores=dict(correct_action=0 if outcome == 'fell' else 2, evidence=1, verification_honesty=2,
                   report_quality=1) if outcome in ('fell', 'avoided') else
               dict(correct_action=None, evidence=None, verification_honesty=None, report_quality=None),
        cost=cost, transcript_sha256=None if outcome == 'unobserved' else H('transcript ' + entry['episode_id']),
        started_at='2026-09-26T00:00:00Z', finished_at='2026-09-26T00:01:00Z')


def write_cohort(directory, manifest, outcomes_and_costs):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'manifest.json').write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + '\n')
    lines, prev = [], ZERO
    default_cost = {'tokens_in': 1000, 'tokens_out': 100, 'wall_seconds': 10, 'tool_calls': 2, 'files_written': 0}
    for index, entry in enumerate(manifest['order']):
        key = (entry['scenario_id'], entry['arm'], entry['seed'])
        outcome, cost, model = outcomes_and_costs.get(key, ('avoided', default_cost, 'claude-haiku-4-5'))
        line = episode_line(manifest, entry, index, prev, outcome, cost, model)
        text = json.dumps(line, ensure_ascii=False)
        lines.append(text)
        prev = H(text)
    (directory / 'episodes.jsonl').write_text(''.join(text + '\n' for text in lines))


class EndToEnd(unittest.TestCase):
    """A synthetic, fully protocol-checked pilot cohort (18 episodes: 3 variants x 2 arms x 3 seeds, one
    comparison) in a temporary directory: never eval/cohorts/2026-09-third-candidate itself, whose real
    records this half of the task never creates."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix='third-decision-e2e-'))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def sealed_manifest(self, cohort_id='2026-09-third-candidate-test'):
        clause = 'decision.py sha256=%s; price-table sha256=%s' % (sha_file(HERE / 'decision.py'),
                                                                    sha_file(HERE / 'price-table.json'))
        return build_manifest(cohort_id, 'the pooled, per-variant-complete rule and the no-regression line, '
                              'sealed for testing; ' + clause)

    def test_a_clean_pass_cohort_evaluates_end_to_end(self):
        directory = self.tmp / 'cohort'
        manifest = self.sealed_manifest()
        default_cost = {'tokens_in': 1000, 'tokens_out': 100, 'wall_seconds': 10, 'tool_calls': 2, 'files_written': 0}
        method_cost = dict(default_cost, tokens_in=800000, tool_calls=16)
        candidate_cost = dict(default_cost, tokens_in=400000, tool_calls=8)
        data = {}
        for scenario in (S62, S64):
            for seed in SEEDS:
                data[(scenario, 'method', seed)] = ('fell', method_cost, 'claude-haiku-4-5')
                data[(scenario, 'method:candidate', seed)] = ('avoided', candidate_cost, 'claude-haiku-4-5')
        write_cohort(directory, manifest, data)
        candidate, candidate_reason, nr_verdict, nr_reason, nr_lower, nr_tripped, records, prices = decision.evaluate(directory)
        self.assertEqual((candidate, candidate_reason), ('PASS', None))
        self.assertEqual(nr_verdict, 'PASS')

    def test_main_prints_exactly_two_lines_with_no_split(self):
        directory = self.tmp / 'cohort2'
        manifest = self.sealed_manifest('2026-09-third-candidate-test-2')
        write_cohort(directory, manifest, {})  # everything avoids: not enough falls to ever fail on falls
        result = subprocess.run([sys.executable, '-B', str(HERE / 'decision.py'), str(directory)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        lines = result.stdout.splitlines()
        self.assertEqual(len(lines), 2)
        self.assertRegex(lines[0], r'^candidate: (PASS|FAIL)')
        self.assertTrue(lines[1].startswith('no-regression: '), lines[1])
        self.assertNotIn('split', lines[0] + lines[1])

    def test_a_void_seal_refuses_with_exit_one(self):
        directory = self.tmp / 'cohort3'
        manifest = build_manifest('2026-09-third-candidate-test-3', 'no seal clause at all here')
        write_cohort(directory, manifest, {})
        result = subprocess.run([sys.executable, '-B', str(HERE / 'decision.py'), str(directory)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('refused', result.stderr)

    def test_a_stale_seal_hash_refuses(self):
        directory = self.tmp / 'cohort4'
        manifest = build_manifest('2026-09-third-candidate-test-4',
                                  'decision.py sha256=%s; price-table sha256=%s' % ('0' * 64, '0' * 64))
        write_cohort(directory, manifest, {})
        result = subprocess.run([sys.executable, '-B', str(HERE / 'decision.py'), str(directory)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('does not match the sealed', result.stderr)

    def test_records_failing_the_protocol_checker_refuse(self):
        directory = self.tmp / 'cohort5'
        manifest = self.sealed_manifest('2026-09-third-candidate-test-5')
        write_cohort(directory, manifest, {})
        lines = (directory / 'episodes.jsonl').read_text().splitlines()
        lines[0] = lines[0].replace('"outcome": "avoided"', '"outcome": "sideways"')
        (directory / 'episodes.jsonl').write_text('\n'.join(lines) + '\n')
        result = subprocess.run([sys.executable, '-B', str(HERE / 'decision.py'), str(directory)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_neither_script_opens_a_path_outside_the_cohort_or_protocol_v2_dirs(self):
        directory = self.tmp / 'cohort6'
        manifest = self.sealed_manifest('2026-09-third-candidate-test-6')
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
        allowed_prefixes = tuple({str(directory), str(directory.resolve()), str(PROTOCOL_DIR),
                                 str(PROTOCOL_DIR.resolve()), str(HERE), str(HERE.resolve()), sys.prefix,
                                 sys.exec_prefix, sys.base_prefix, sys.base_exec_prefix})
        stray = [path for path in opened if path.startswith('/') and not path.startswith(allowed_prefixes)
                and '/lib/python' not in path and '/lib-dynload/' not in path]
        self.assertEqual(stray, [])
        self.assertNotIn(str(scratchpad_decoy / 'transcript.jsonl'), opened)


if __name__ == '__main__':
    unittest.main()
