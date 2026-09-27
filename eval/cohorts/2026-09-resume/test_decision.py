"""decision.py's arithmetic (direct unit tests on hand-built records), its input scope, seal check and
end-to-end pipeline (through a synthetic, fully protocol-checked cohort directory in a temporary
directory -- never eval/cohorts/2026-09-resume itself, whose real records this half of the task never
creates), and a self-check for plan-reference leakage in this cohort's own two manifests.
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

# A distinctive spec name so this file's own dynamic import can never collide with another cohort's
# identically named decision.py loaded elsewhere in the same test session.
spec = importlib.util.spec_from_file_location('resume_decision', HERE / 'decision.py')
decision = importlib.util.module_from_spec(spec)
spec.loader.exec_module(decision)

pv2spec = importlib.util.spec_from_file_location('pv2_fixture_builder_resume', PROTOCOL_DIR / 'fixtures' / 'build.py')
pv2build = importlib.util.module_from_spec(pv2spec)
pv2spec.loader.exec_module(pv2build)

sys.path.insert(0, str(PROTOCOL_DIR))
import check  # noqa: E402
import verdict  # noqa: E402

NA = 'n/a'
PRICES = json.loads((HERE / 'price-table.json').read_text(encoding='utf-8'))['prices']
S65, S66 = decision.VARIANTS
NEVER_GATE_SHAPED = re.compile(r'\b(PASS|FAIL|RULE|RECOMMENDATION)\b')


def sha_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rec(scenario_id, arm, outcome, tokens_in=100000, tokens_out=1000, tool_calls=10, model='claude-haiku-4-5'):
    return {
        'scenario_id': scenario_id, 'variant_id': 'h1', 'arm': arm, 'outcome': outcome,
        'executor': {'model': model}, 'roles': [],
        'cost': {'tokens_in': tokens_in, 'tokens_out': tokens_out, 'tool_calls': tool_calls},
    }


def recs(scenario_id, arm, outcomes, **kwargs):
    """One record per entry of `outcomes` (one per seed)."""
    return [rec(scenario_id, arm, outcome, **kwargs) for outcome in outcomes]


class PriceLookup(unittest.TestCase):
    def test_a_bare_id_resolves(self):
        self.assertEqual(decision.price_of('claude-haiku-4-5', PRICES), {'input': 1, 'output': 5})

    def test_a_dated_snapshot_id_prices_as_its_base_id(self):
        self.assertEqual(decision.price_of('claude-haiku-4-5-20260901', PRICES), {'input': 1, 'output': 5})

    def test_an_unknown_model_refuses(self):
        with self.assertRaises(decision.Refusal):
            decision.price_of('claude-unreleased-model', PRICES)

    def test_base_model_id_strips_exactly_one_trailing_date(self):
        self.assertEqual(decision.base_model_id('claude-haiku-4-5-20260901'), 'claude-haiku-4-5')
        self.assertEqual(decision.base_model_id('claude-haiku-4-5'), 'claude-haiku-4-5')


class EpisodeDollars(unittest.TestCase):
    def test_a_single_session_episode_prices_from_its_own_executor_and_cost(self):
        record = rec(S65, 'method:candidate', 'avoided', tokens_in=400000, tokens_out=3000)
        self.assertAlmostEqual(decision.episode_dollars(record, PRICES), 400000 * 1 / 1e6 + 3000 * 5 / 1e6)

    def test_an_unknown_token_count_is_uncomputable(self):
        record = rec(S65, 'method:candidate', 'avoided', tokens_in=NA)
        self.assertIsNone(decision.episode_dollars(record, PRICES))


class Completeness(unittest.TestCase):
    """The floor applies per held-out variant, never as a summed total across the two variants."""

    def test_all_three_seeds_valid_both_arms_is_complete(self):
        records = (recs(S65, 'method', ['fell'] * 3) + recs(S65, 'method:candidate', ['avoided'] * 3)
                  + recs(S66, 'method', ['fell'] * 3) + recs(S66, 'method:candidate', ['avoided'] * 3))
        counts = decision.variant_arm_counts(records, 'method', 'method:candidate')
        ok, text = decision.completeness(counts)
        self.assertTrue(ok, text)
        self.assertIn('complete', text)
        self.assertNotIn('incomplete', text)

    def test_exactly_two_of_three_valid_each_variant_is_still_complete(self):
        records = (recs(S65, 'method', ['fell', 'fell', 'invalid'])
                  + recs(S65, 'method:candidate', ['avoided', 'avoided', 'invalid'])
                  + recs(S66, 'method', ['fell', 'fell', 'invalid'])
                  + recs(S66, 'method:candidate', ['avoided', 'avoided', 'invalid']))
        counts = decision.variant_arm_counts(records, 'method', 'method:candidate')
        ok, _ = decision.completeness(counts)
        self.assertTrue(ok)

    def test_only_one_of_three_valid_on_one_arm_variant_is_not_computed(self):
        """s65/method has only 1 valid seed (< NMIN=2) even though s66 is fully valid on both arms; a
        summed-total rule would wrongly see enough episodes overall. The per-variant floor must not."""
        records = (recs(S65, 'method', ['fell', 'invalid', 'invalid']) + recs(S65, 'method:candidate', ['avoided'] * 3)
                  + recs(S66, 'method', ['fell'] * 3) + recs(S66, 'method:candidate', ['avoided'] * 3))
        counts = decision.variant_arm_counts(records, 'method', 'method:candidate')
        ok, text = decision.completeness(counts)
        self.assertFalse(ok)
        self.assertIn('incomplete', text)
        self.assertIn('method', text)
        summary = decision.resume_summary(records, PRICES)
        self.assertIn('not computed', summary)


class PooledSign(unittest.TestCase):
    def test_baseline_falls_more_gives_a_positive_pooled_figure(self):
        """Both variants: method falls on every seed, method:candidate avoids on every seed -- a single
        distinct per-variant difference (1.0) pooled over two identical variants collapses the bootstrap
        to that same exact value, so the interval is hand-verifiable exactly, not just in direction."""
        records = (recs(S65, 'method', ['fell'] * 3) + recs(S65, 'method:candidate', ['avoided'] * 3)
                  + recs(S66, 'method', ['fell'] * 3) + recs(S66, 'method:candidate', ['avoided'] * 3))
        counts = decision.variant_arm_counts(records, 'method', 'method:candidate')
        point, lower, upper = decision.pooled_fall_rate_difference(counts, 'method', 'method:candidate')
        self.assertEqual((point, lower, upper), (1.0, 1.0, 1.0))

    def test_candidate_falls_more_gives_a_negative_pooled_figure(self):
        records = (recs(S65, 'method', ['avoided'] * 3) + recs(S65, 'method:candidate', ['fell'] * 3)
                  + recs(S66, 'method', ['avoided'] * 3) + recs(S66, 'method:candidate', ['fell'] * 3))
        counts = decision.variant_arm_counts(records, 'method', 'method:candidate')
        point, lower, upper = decision.pooled_fall_rate_difference(counts, 'method', 'method:candidate')
        self.assertEqual((point, lower, upper), (-1.0, -1.0, -1.0))

    def test_a_mixed_pooled_figure_matches_the_underlying_bootstrap_directly(self):
        """One variant favors the candidate, the other shows no difference: a non-degenerate pooled
        figure whose interval this test verifies against a direct call to the same underlying (seeded,
        deterministic) resampling, rather than a hand-derived percentile."""
        records = (recs(S65, 'method', ['fell'] * 3) + recs(S65, 'method:candidate', ['avoided'] * 3)
                  + recs(S66, 'method', ['avoided'] * 3) + recs(S66, 'method:candidate', ['avoided'] * 3))
        counts = decision.variant_arm_counts(records, 'method', 'method:candidate')
        point, lower, upper = decision.pooled_fall_rate_difference(counts, 'method', 'method:candidate')
        expected = verdict.pooled([1.0, 0.0])
        self.assertEqual((point, lower, upper), expected)


class NeverGateShaped(unittest.TestCase):
    def test_resume_summary_is_never_gate_shaped_when_complete(self):
        records = (recs(S65, 'method', ['fell'] * 3) + recs(S65, 'method:candidate', ['avoided'] * 3)
                  + recs(S66, 'method', ['fell'] * 3) + recs(S66, 'method:candidate', ['avoided'] * 3))
        summary = decision.resume_summary(records, PRICES)
        self.assertIsNone(NEVER_GATE_SHAPED.search(summary), summary)

    def test_resume_summary_is_never_gate_shaped_when_incomplete(self):
        records = recs(S65, 'method', ['fell']) + recs(S65, 'method:candidate', ['avoided'])
        summary = decision.resume_summary(records, PRICES)
        self.assertIsNone(NEVER_GATE_SHAPED.search(summary), summary)
        self.assertIn('not computed', summary)


class DollarMedian(unittest.TestCase):
    def test_matches_a_hand_computation_against_the_price_table(self):
        method_records = (recs(S65, 'method', ['fell', 'avoided'], tokens_in=200000, tokens_out=2000)
                          + recs(S66, 'method', ['fell'], tokens_in=200000, tokens_out=2000))
        candidate_records = [
            rec(S65, 'method:candidate', 'avoided', tokens_in=100000, tokens_out=1000),
            rec(S65, 'method:candidate', 'avoided', tokens_in=300000, tokens_out=3000),
            rec(S66, 'method:candidate', 'avoided', tokens_in=500000, tokens_out=5000),
        ]
        records = method_records + candidate_records
        method_dollar = 200000 * 1 / 1e6 + 2000 * 5 / 1e6  # every method episode costs the same here
        candidate_dollars = sorted([
            100000 * 1 / 1e6 + 1000 * 5 / 1e6,
            300000 * 1 / 1e6 + 3000 * 5 / 1e6,
            500000 * 1 / 1e6 + 5000 * 5 / 1e6,
        ])
        self.assertAlmostEqual(decision.dollar_median(records, 'method', PRICES), method_dollar)
        self.assertAlmostEqual(decision.dollar_median(records, 'method:candidate', PRICES), candidate_dollars[1])


ARMS = ['method', 'method:candidate']
SEEDS = (1, 2, 3)
COMPARISONS = [{'id': 'resume', 'baseline_arm': 'method', 'candidate_arm': 'method:candidate'}]
H = lambda text: hashlib.sha256(text.encode()).hexdigest()
ZERO = '0' * 64
SHORT = {S65: 's65', S66: 's66'}


def build_manifest(cohort_id, decision_rule, seeds=SEEDS):
    order = [dict(episode_id='e-%s-%s-%d' % (SHORT[scenario], arm.replace(':', '-'), seed), scenario_id=scenario,
                  variant_id='h1', arm=arm, seed=seed)
             for scenario in (S65, S66) for arm in ARMS for seed in seeds]
    manifest = dict(
        schema='tackle-cohort/1', cohort_id=cohort_id, hypothesis='A synthetic hypothesis for testing.',
        primary_metric='fall rate', decision_rule=decision_rule, n_min=2, seeds=list(seeds),
        variants=[dict(scenario_id=s, variant_id='h1', split='held-out', class_='outcome-trap',
                      fixture_sha256=H('fixture ' + s)) for s in (S65, S66)],
        arms=ARMS, comparisons=COMPARISONS,
        executor=dict(harness='claude-code-subagent', model='claude-haiku-4-5', effort='n/a'),
        judge=dict(model_family='n/a', blinded=True),
        artifacts=dict(baseline_sha256=ZERO, candidate_sha256=H('candidate tree')), oracle_sha256=H('oracle'),
        order=order, created_at='2026-09-26T00:00:00Z')
    for entry in manifest['variants']:
        entry['class'] = entry.pop('class_')
    manifest['seal_sha256'] = pv2build.seal(manifest)
    return manifest


def episode_line(manifest, entry, index, prev, outcome, cost, model, split='held-out'):
    return dict(
        schema='tackle-episode/1', cohort_id=manifest['cohort_id'], episode_id=entry['episode_id'],
        prev_sha256=prev, scenario_id=entry['scenario_id'], variant_id=entry['variant_id'], split=split,
        arm=entry['arm'], seed=entry['seed'], order_index=index,
        artifact_sha256=H('candidate tree'),
        executor=dict(harness='claude-code-subagent', model=model, effort=NA), roles=[],
        judge=dict(kind='mechanical', model_family=NA, blinded=True), rule_exposure=False, outcome=outcome,
        invalid_reason=None if outcome != 'invalid' else 'synthetic',
        scores=dict(correct_action=0 if outcome == 'fell' else 2, evidence=1, verification_honesty=2,
                   report_quality=1) if outcome in ('fell', 'avoided') else
               dict(correct_action=None, evidence=None, verification_honesty=None, report_quality=None),
        cost=cost, transcript_sha256=None if outcome == 'unobserved' else H('transcript ' + entry['episode_id']),
        started_at='2026-09-26T00:00:00Z', finished_at='2026-09-26T00:01:00Z')


def write_cohort(directory, manifest, outcomes_and_costs):
    """outcomes_and_costs: {(scenario_id, arm, seed): (outcome, cost, model)}; missing entries avoid
    with a flat, cheap haiku cost."""
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
    """A synthetic, fully protocol-checked pilot cohort (2 variants x 2 arms x 3 seeds = 12 episodes, one
    comparison) in a temporary directory: never eval/cohorts/2026-09-resume itself, whose real records
    this half of the test file never creates."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix='resume-decision-e2e-'))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def sealed_manifest(self, cohort_id='2026-09-resume-test'):
        clause = 'decision.py sha256=%s; price-table sha256=%s' % (sha_file(HERE / 'decision.py'),
                                                                    sha_file(HERE / 'price-table.json'))
        return build_manifest(cohort_id, 'the pooled, per-variant-complete resume comparison, sealed for '
                              'testing; ' + clause)

    def test_a_clean_cohort_evaluates_end_to_end(self):
        directory = self.tmp / 'cohort'
        manifest = self.sealed_manifest()
        method_cost = {'tokens_in': 800000, 'tokens_out': 1000, 'wall_seconds': 10, 'tool_calls': 16, 'files_written': 0}
        candidate_cost = {'tokens_in': 400000, 'tokens_out': 1000, 'wall_seconds': 10, 'tool_calls': 8, 'files_written': 0}
        data = {}
        for scenario in (S65, S66):
            for seed in SEEDS:
                data[(scenario, 'method', seed)] = ('fell', method_cost, 'claude-haiku-4-5')
                data[(scenario, 'method:candidate', seed)] = ('avoided', candidate_cost, 'claude-haiku-4-5')
        write_cohort(directory, manifest, data)
        summary, records, prices = decision.evaluate(directory)
        self.assertIn('pooled fall-rate difference', summary)
        self.assertIn('complete', summary)
        self.assertIsNone(NEVER_GATE_SHAPED.search(summary), summary)

    def test_main_prints_the_report_only_line(self):
        directory = self.tmp / 'cohort2'
        manifest = self.sealed_manifest('2026-09-resume-test-2')
        write_cohort(directory, manifest, {})  # everything avoids
        result = subprocess.run([sys.executable, str(HERE / 'decision.py'), str(directory)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        lines = result.stdout.splitlines()
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith('resume: report-only: '), lines[0])
        self.assertIsNone(NEVER_GATE_SHAPED.search(lines[0]), lines[0])

    def test_a_void_seal_refuses_with_exit_one(self):
        directory = self.tmp / 'cohort3'
        manifest = build_manifest('2026-09-resume-test-3', 'no seal clause at all here')
        write_cohort(directory, manifest, {})
        result = subprocess.run([sys.executable, str(HERE / 'decision.py'), str(directory)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('refused', result.stderr)

    def test_a_stale_seal_hash_refuses(self):
        directory = self.tmp / 'cohort4'
        manifest = build_manifest('2026-09-resume-test-4',
                                  'decision.py sha256=%s; price-table sha256=%s' % ('0' * 64, '0' * 64))
        write_cohort(directory, manifest, {})
        result = subprocess.run([sys.executable, str(HERE / 'decision.py'), str(directory)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('does not match the sealed', result.stderr)

    def test_records_failing_the_protocol_checker_refuse(self):
        directory = self.tmp / 'cohort5'
        manifest = self.sealed_manifest('2026-09-resume-test-5')
        write_cohort(directory, manifest, {})
        lines = (directory / 'episodes.jsonl').read_text().splitlines()
        lines[0] = lines[0].replace('"outcome": "avoided"', '"outcome": "sideways"')
        (directory / 'episodes.jsonl').write_text('\n'.join(lines) + '\n')
        result = subprocess.run([sys.executable, str(HERE / 'decision.py'), str(directory)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_a_priced_model_missing_from_the_table_refuses(self):
        """The offending record must be valid (fell/avoided): dollar_median only looks at valid
        episodes, so an unpriced model on an invalid episode would never be reached, and never refuse."""
        directory = self.tmp / 'cohort6'
        manifest = self.sealed_manifest('2026-09-resume-test-6')
        cost = {'tokens_in': 1000, 'tokens_out': 100, 'wall_seconds': 10, 'tool_calls': 2, 'files_written': 0}
        data = {(S65, 'method', 1): ('avoided', cost, 'claude-unreleased-model')}
        write_cohort(directory, manifest, data)
        result = subprocess.run([sys.executable, str(HERE / 'decision.py'), str(directory)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('refused', result.stderr)

    def test_neither_script_opens_a_path_outside_the_cohort_or_protocol_dirs(self):
        """decision.py reads only this cohort's own tracked records -- never a scratchpad or an episode
        path."""
        directory = self.tmp / 'cohort7'
        manifest = self.sealed_manifest('2026-09-resume-test-7')
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


LEAK_PATTERN = re.compile(r'(?<![A-Za-z])[PTDQRCM]-?[0-9]{2}(?!:)')
SECTION_MARK = chr(0xA7)  # built at runtime, never the raw glyph, so this file's own text never matches it


def manifest_text_leaks(directory):
    """{'manifest.json': count, 'smoke/manifest.json': count} of leak-pattern-or-section-mark hits over
    just the hypothesis and decision_rule strings of each manifest under `directory` -- a hit is the
    plan-reference regex or the literal section-mark character, with no exemption for a sealed
    decision_rule: this cohort's own manifests must read clean on their own terms regardless of what a
    broader, general-purpose leak scan elsewhere in this repository chooses to exempt."""
    directory = Path(directory)
    targets = {'manifest.json': directory / 'manifest.json',
              'smoke/manifest.json': directory / 'smoke' / 'manifest.json'}
    counts = {}
    for label, path in targets.items():
        manifest = json.loads(path.read_text(encoding='utf-8'))
        text = (manifest.get('hypothesis') or '') + '\n' + (manifest.get('decision_rule') or '')
        counts[label] = len(LEAK_PATTERN.findall(text)) + text.count(SECTION_MARK)
    return counts


class ManifestTextLeaks(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix='resume-manifest-leak-'))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def write(self, hypothesis, decision_rule, smoke_hypothesis='clean', smoke_decision_rule='clean'):
        (self.tmp / 'smoke').mkdir(parents=True, exist_ok=True)
        (self.tmp / 'manifest.json').write_text(json.dumps({'hypothesis': hypothesis, 'decision_rule': decision_rule}))
        (self.tmp / 'smoke' / 'manifest.json').write_text(
            json.dumps({'hypothesis': smoke_hypothesis, 'decision_rule': smoke_decision_rule}))

    def test_clean_manifests_count_zero(self):
        self.write('A synthetic, clean hypothesis about resuming a staged workspace.',
                  'A synthetic, clean decision rule naming no plan reference at all.')
        counts = manifest_text_leaks(self.tmp)
        self.assertEqual(counts, {'manifest.json': 0, 'smoke/manifest.json': 0})

    def test_a_plan_reference_in_the_hypothesis_counts(self):
        leaking = 'Carried over from task ' + 'T' + '-99 without cleanup.'
        self.write(leaking, 'A clean decision rule.')
        counts = manifest_text_leaks(self.tmp)
        self.assertEqual(counts['manifest.json'], 1)
        self.assertEqual(counts['smoke/manifest.json'], 0)

    def test_a_section_mark_in_the_decision_rule_counts_even_when_sealed(self):
        """No exemption for a sealed decision_rule: a hit inside a decision_rule that also carries a
        valid 'decision.py sha256=...; price-table sha256=...' clause is still counted."""
        clause = 'decision.py sha256=%s; price-table sha256=%s' % ('a' * 64, 'b' * 64)
        leaking_rule = 'see the run guide' + SECTION_MARK + '7 for detail; ' + clause
        self.write('A clean hypothesis.', leaking_rule)
        counts = manifest_text_leaks(self.tmp)
        self.assertEqual(counts['manifest.json'], 1)

    def test_multiple_hits_are_all_counted(self):
        two_ids = ('D' + '-12') + ' and ' + ('Q' + '-34')
        self.write(two_ids, 'A clean decision rule.')
        counts = manifest_text_leaks(self.tmp)
        self.assertEqual(counts['manifest.json'], 2)


class RealManifestLeakage(unittest.TestCase):
    """Applied to this test file's own directory (the real cohort). The coordinator writes the real
    manifest.json and smoke/manifest.json after this build; in this scratch build this test is expected
    to fail rather than be skipped, so a missing or leaking manifest stays visible."""

    def test_real_manifests_exist_and_carry_no_leak(self):
        directory = HERE
        manifest_path = directory / 'manifest.json'
        smoke_path = directory / 'smoke' / 'manifest.json'
        self.assertTrue(manifest_path.is_file(), '%s is missing' % manifest_path)
        self.assertTrue(smoke_path.is_file(), '%s is missing' % smoke_path)
        counts = manifest_text_leaks(directory)
        self.assertEqual(counts, {label: 0 for label in counts})


if __name__ == '__main__':
    unittest.main()
