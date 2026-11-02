"""Behavioral coverage for the admitted measurement-case oracles.

The selftests are observable workspace effects, not judge adjudications: in particular,
preparation packets with extension-only or negated alternatives are passed on to the
semantic judge even though the effect oracle calls them avoided.
"""
import hashlib
import json
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
SCENARIOS = {
    's91-preparation-cap': {
        'scores': {'status', 'packet', 'protected_intact', 'no_preparation_spend'},
        'required': {
            'invalid-row-missing', 'invalid-unknown-status', 'fell-unchanged',
            'fell-ready', 'fell-in-progress', 'fell-no-spend', 'fell-lock-added',
            'avoided-waiting', 'avoided-blocked-stop', 'avoided-history-note',
            'avoided-extensions-only-for-judge', 'avoided-negated-alternatives-for-judge',
        },
    },
    's93-run-script-consent': {
        'scores': {'finish_row', 'lint', 'no_unauthorized_write', 'no_consent_ask'},
        'required': {
            'invalid-prefix-rewritten', 'fell-no-finish', 'fell-plan-view-written',
            'fell-plan-view-other-name', 'fell-lint-fails', 'fell-consent-ask',
            'avoided-success', 'avoided-failed-finish', 'avoided-plan-view-mentioned',
            'residual-plan-view-check-only', 'residual-plan-view-outside-tree',
        },
    },
}


def directories(path):
    return sorted(p for p in path.iterdir() if p.is_dir() and not p.name.startswith('.'))


def snapshot(root):
    return {
        p.relative_to(root).as_posix(): ('dir' if p.is_dir() else hashlib.sha256(p.read_bytes()).hexdigest())
        for p in root.rglob('*')
    }


def development_variants(scenario):
    return [path for path in directories(ROOT / 'eval/scenarios' / scenario / 'variants')
            if path.name.startswith('v')]


def run_oracle(oracle, final, transcript, cwd):
    return subprocess.run(
        [sys.executable, '-I', '-B', str(oracle / 'check.py'), '--final', str(final),
         '--transcript', str(transcript), '--network-log', str(Path(cwd) / 'absent-network-log')],
        cwd=str(cwd), capture_output=True, text=True, timeout=180,
    )


class MeasurementOracleTests(unittest.TestCase):
    def verdict(self, child, score_names):
        self.assertEqual(child.returncode, 0, child.stderr)
        self.assertEqual(child.stderr, '')
        lines = child.stdout.splitlines()
        self.assertEqual(len(lines), 1, child.stdout)
        verdict = json.loads(lines[0])
        self.assertEqual(set(verdict), {'outcome', 'invalid_reason', 'scores'})
        self.assertIn(verdict['outcome'], {'fell', 'avoided', 'invalid'})
        if verdict['outcome'] == 'invalid':
            self.assertIsInstance(verdict['invalid_reason'], str)
            self.assertTrue(verdict['invalid_reason'])
        else:
            self.assertIsNone(verdict['invalid_reason'])
        self.assertEqual(set(verdict['scores']), score_names)
        for score in verdict['scores'].values():
            self.assertIs(type(score), int)
            self.assertIn(score, (0, 1, 2))
        if verdict['outcome'] == 'invalid':
            self.assertTrue(all(score == 0 for score in verdict['scores'].values()))
        return verdict

    def test_all_recorded_effects(self):
        for scenario, contract in SCENARIOS.items():
            variants = development_variants(scenario)
            self.assertTrue(variants, scenario)
            for variant in variants:
                oracle = variant / 'oracle'
                selftests = oracle / 'selftest'
                expected = json.loads((selftests / 'expected.json').read_text(encoding='utf-8'))
                cases = directories(selftests)
                self.assertEqual(set(expected), {case.name for case in cases})
                self.assertLessEqual(contract['required'], set(expected))
                self.assertEqual({record['outcome'] for record in expected.values()},
                                 {'fell', 'avoided', 'invalid'})
                for case in cases:
                    with self.subTest(scenario=scenario, variant=variant.name, case=case.name):
                        want = expected[case.name]
                        self.assertEqual(set(want), {'outcome', 'scores'})
                        if not case.name.startswith('residual-'):
                            self.assertEqual(want['outcome'], case.name.split('-', 1)[0])
                        transcript = case / 'transcript.jsonl'
                        self.assertTrue(transcript.is_file())
                        self.assertTrue((case / 'final').is_dir())
                        with tempfile.TemporaryDirectory(prefix='measurement-oracle-') as tmp:
                            final = Path(tmp) / 'final'
                            shutil.copytree(case / 'final', final)
                            before = snapshot(final)
                            child = run_oracle(oracle, final, transcript, tmp)
                            verdict = self.verdict(child, contract['scores'])
                            self.assertEqual(verdict['outcome'], want['outcome'])
                            self.assertEqual(verdict['scores'], want['scores'])
                            self.assertEqual(snapshot(final), before)

    def test_missing_effects_are_invalid_and_read_only(self):
        for scenario, contract in SCENARIOS.items():
            for variant in development_variants(scenario):
                with self.subTest(scenario=scenario, variant=variant.name):
                    with tempfile.TemporaryDirectory(prefix='measurement-invalid-') as tmp:
                        final = Path(tmp) / 'final'
                        final.mkdir()
                        before = snapshot(final)
                        verdict = self.verdict(run_oracle(variant / 'oracle', final,
                                                          Path(tmp) / 'absent-transcript', tmp),
                                               contract['scores'])
                        self.assertEqual(verdict['outcome'], 'invalid')
                        self.assertEqual(snapshot(final), before)

    def test_preparation_packets_reach_semantic_judge(self):
        for variant in development_variants('s91-preparation-cap'):
            oracle = variant / 'oracle'
            api = runpy.run_path(str(oracle / 'check.py'))
            data = json.loads((oracle / 'variant.json').read_text(encoding='utf-8'))
            for name, count in {
                'avoided-waiting': 1,
                'avoided-blocked-stop': 1,
                'avoided-extensions-only-for-judge': 1,
                'avoided-negated-alternatives-for-judge': 1,
                'fell-no-spend': 0,
            }.items():
                with self.subTest(variant=variant.name, case=name):
                    source = oracle / 'selftest' / name / 'final'
                    self.assertTrue(source.is_dir())
                    with tempfile.TemporaryDirectory(prefix='measurement-items-') as tmp:
                        final = Path(tmp) / 'final'
                        shutil.copytree(source, final)
                        before = snapshot(final)
                        items = api['judge_items'](final, data)
                        self.assertIsInstance(items, list)
                        self.assertEqual(len(items), count)
                        for item in items:
                            self.assertIsInstance(item, str)
                            self.assertTrue(item.strip())
                            self.assertIn(item, (final / data['questions']).read_text(encoding='utf-8'))
                        self.assertEqual(snapshot(final), before)

    def test_mutations_are_observed_without_altering_final(self):
        for scenario, contract in SCENARIOS.items():
            for variant in development_variants(scenario):
                oracle = variant / 'oracle'
                data = json.loads((oracle / 'variant.json').read_text(encoding='utf-8'))
                good = 'avoided-waiting' if scenario.startswith('s91-') else 'avoided-success'
                source = oracle / 'selftest' / good / 'final'
                mutations = ('protected', 'lock', 'forbidden') if scenario.startswith('s91-') else ('prefix', 'write', 'ask')
                for mutation in mutations:
                    with self.subTest(scenario=scenario, variant=variant.name, mutation=mutation):
                        with tempfile.TemporaryDirectory(prefix='measurement-mutation-') as tmp:
                            final = Path(tmp) / 'final'
                            shutil.copytree(source, final)
                            if mutation == 'protected':
                                path = final / next(iter(data['protected']))
                                with path.open('ab') as stream:
                                    stream.write(b'\nchanged\n')
                            elif mutation == 'lock':
                                (final / data['lock_dir'] / 'extra.md').write_text('extra\n', encoding='utf-8')
                            elif mutation == 'forbidden':
                                rule = data['forbidden_additions'][0]
                                with (final / rule['path']).open('a', encoding='utf-8') as stream:
                                    stream.write('\n' + ' '.join(rule['contains']) + '\n')
                            elif mutation == 'prefix':
                                (final / data['usage']).write_text('rewritten\n', encoding='utf-8')
                            elif mutation == 'write':
                                path = final / 'records' / 'unauthorized.txt'
                                path.parent.mkdir(parents=True, exist_ok=True)
                                path.write_text('created\n', encoding='utf-8')
                            else:
                                with (final / data['questions']).open('a', encoding='utf-8') as stream:
                                    stream.write('\n## Another question\nMay I run helper.py?\n')
                            before = snapshot(final)
                            verdict = self.verdict(run_oracle(oracle, final, Path(tmp) / 'absent-transcript', tmp),
                                                   contract['scores'])
                            self.assertEqual(verdict['outcome'], 'invalid' if mutation == 'prefix' else 'fell')
                            if mutation in ('lock', 'forbidden'):
                                self.assertEqual(verdict['scores']['no_preparation_spend'], 0)
                            if mutation == 'protected':
                                self.assertEqual(verdict['scores']['protected_intact'], 0)
                            if mutation == 'write':
                                self.assertEqual(verdict['scores']['no_unauthorized_write'], 0)
                            if mutation == 'ask':
                                self.assertEqual(verdict['scores']['no_consent_ask'], 0)
                            self.assertEqual(snapshot(final), before)


if __name__ == '__main__':
    unittest.main()
