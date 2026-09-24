"""The rule ledger covers every SKILL.md sentence once and its checker rejects each planted defect.

Every case runs check_ledger.py or inventory.py as a subprocess on a fixture repository that
fixtures/build.py builds into a temporary directory, or on this repository itself. Expected units and
labels come from the builder, which states them by hand.
"""
import filecmp
import hashlib
import importlib.util
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
CHECK = HERE / 'check_ledger.py'
INVENTORY = HERE / 'inventory.py'
BUILD = HERE / 'fixtures/build.py'
SUMMARY = re.compile(r'rules=\d+ hot_path=\d+ untested=\d+ warnings=\d+')

spec = importlib.util.spec_from_file_location('ledger_fixture_builder', BUILD)
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
WORK = tempfile.TemporaryDirectory()
FIX = Path(WORK.name) / 'fixtures'


def setUpModule():
    subprocess.run([sys.executable, str(BUILD), str(FIX)], check=True, capture_output=True, timeout=120)


def tearDownModule():
    WORK.cleanup()

SUITE = 'eval/runs/2026-01-01-suite.md'
MIXED = 'eval/runs/2026-01-02-mixed.md'
BASE_WARNINGS = {'warning: %s: hot-path rule is neither safety-invariant nor discriminates' % rid
                 for rid in ('R-ENTRY-01', 'R-INTAKE-01', 'R-INTAKE-02', 'R-STATE-01', 'R-COMM-02')}
ABSENT = 'eval/runs/2026-01-03-absent.md'
STATUSES = 'contaminated, unobserved, method-worse, inert, discriminates, inconclusive, untested'

# fixture -> the exact set of error lines the checker must print (exit 1)
FAILURES = {
    'added-sentence': ['uncovered: SKILL.md:39: Never skip the checks.'],
    'table-row-uncovered': ['uncovered: SKILL.md:16: Handoff writes only its projection.'],
    'wrong-home': ['R-COMM-02: unresolved home SKILL.md:39: fragment not on the line'],
    'duplicate-id': ['duplicate rule_id: R-COMM-02'],
    'hash-drift': ['R-EVID-01: statement_sha256 does not match the statement'],
    'double-coverage': ['double coverage: SKILL.md:39: State the result. (R-COMM-02, R-COMM-03)'],
    'discovery-only': ['R-COMM-01: discriminates rests only on discovering scenarios: s1-demo-trap'],
    'stale-unit': ['stale unit: R-COMM-02: Removed sentence.'],
    'missing-section': ['SKILL.md: missing section: Output'],
    'duplicate-section': ['SKILL.md: duplicate section: Output'],
    'key-collision': ['ambiguous key: SKILL.md:39, SKILL.md:39: State the result.'],
    'unnormalized-statement': ['R-STATE-01: statement must be one normalized line'],
    'long-fragment': ['R-INTAKE-01: home_fragment must be 1 to 60 characters'],
    'retired-hot-path': ['R-STATUS-01: hot_path must be false because the rule is retired'],
    'bad-retired-in': ['R-STATUS-01: retired_in must be a version'],
    'tested-without-cohort': ['R-COMM-03: a tested status requires a cohort_id'],
    'bad-status': ['R-COMM-03: status must be one of ' + STATUSES],
    'bad-added-in': ['R-STATE-01: added_in must be a version or unknown'],
    'bad-as-of': ['R-STATE-01: as_of must be YYYY-MM-DD'],
    'escaping-home': ['R-REL-01: unresolved home ../outside.md:1: not a relative path:line'],
    'bad-ledger-schema': ['ledger: schema must be tackle-rule-ledger/1'],
    'bad-index-schema': ['index: schema must be tackle-historical-index/1'],
    'bad-non-normative': ['non_normative[0]: unit and reason must be text',
                          'uncovered: SKILL.md:30: Version 8.x stays readable.'],
    'absent-with-seeds': ['index: %s: s2-plan-trap: baseline has zero seeds exactly when it is absent' % ABSENT],
    'method-only-with-baseline': ['index: %s: s1-demo-trap: the baseline is absent exactly for method-only comparisons'
                                  % SUITE],
    'bad-comparison': ['index: %s: s2-plan-trap: comparison must be one of no-skill, ablation, prior-version, '
                       'method-only' % SUITE],
    'bad-record-path': ['index: eval/other/2026-01-03-absent.md: record must be eval/runs/<name>.md or an answer '
                        'sheet'],
    'duplicate-entry': ['index: %s: s1-demo-trap: duplicate scenario in the record' % SUITE],
    'bad-index-label': ['index: %s: s2-plan-trap: mapped_label discriminates, expected inert' % SUITE],
    'historical-mismatch': ['R-ENTRY-01: historical does not match the index for its scenarios'],
    'bad-class': ['R-STATE-01: class must be one of safety-invariant, behavioral, format, maintainer'],
    'bad-rule-id': ['R-FOO-01: rule_id must match R-<AREA>-<NN>'],
    'hot-path-mismatch': ['R-RUN-02: hot_path must be false because the home is not SKILL.md'],
    'unknown-scenario': ['R-EVID-01: unknown scenario: s9-missing-trap'],
    'cohort-mismatch': ['R-EVID-01: status untested requires cohort_id null'],
    'bad-record-label': ['index: %s: s2-plan-trap: recorded_label not found in the record' % SUITE],
    'bad-basis-line': ['index: %s: s1-demo-trap: basis line 6 is past the end of the record' % MIXED],
    'basis-quote-mismatch': ['index: %s: s1-demo-trap: basis line 4 does not contain its quote' % MIXED],
    'bad-rule-id-type': ['rules[12]: rule_id must match R-<AREA>-<NN>'],
    'bad-scenario-type': ['index: %s: ?: scenario_id must look like s<N>-<name>' % ABSENT],
    'missing-cohort': ['R-COMM-03: cohort ghost-cohort has no eval/cohorts/ghost-cohort/manifest.json'],
    'wrong-cohort-manifest': ['R-COMM-03: eval/cohorts/demo-cohort/manifest.json names cohort other'],
    'contamination-without-control': ['index: %s: s2-plan-trap: contamination needs an observed baseline arm' % MIXED],
    'seeds-mismatch': ['index: %s: s1-demo-trap: seeds n/a, expected 1' % SUITE],
    'units-off-skill': ['R-COMM-02: units need a SKILL.md home'],
    'bad-mirror': ['R-INTAKE-02: unresolved mirror references/guides/guide.md:40'],
    'unknown-field': ['R-STATE-01: unknown field: notes'],
    'invalid-json': ['ledger: invalid JSON in eval/rules/ledger.json'],
    'missing-ledger': ['ledger: missing eval/rules/ledger.json'],
}


def run(script, *args):
    return subprocess.run([sys.executable, str(script), *map(str, args)], capture_output=True, text=True, timeout=120)


def lines(text, prefix):
    return {line for line in text.splitlines() if line.startswith(prefix)}


def digest(path):
    return {str(p.relative_to(path)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(path.rglob('*')) if p.is_file()}


class RepositoryTests(unittest.TestCase):
    def test_repository_ledger_is_valid(self):
        result = run(CHECK, '--repo', REPO)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(lines(result.stdout, 'error:'), set())
        self.assertRegex(result.stdout.splitlines()[-1], SUMMARY)

    def test_repository_historical_lists_are_current(self):
        result = run(INVENTORY, 'sync', '--repo', REPO, '--check')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class FixtureTests(unittest.TestCase):
    def test_valid_fixtures_pass_with_their_summary(self):
        cases = {'valid-base': 'rules=13 hot_path=11 untested=12 warnings=5',
                 'valid-reordered': 'rules=13 hot_path=11 untested=12 warnings=5',
                 'valid-retired': 'rules=14 hot_path=11 untested=13 warnings=5'}
        for name, summary in cases.items():
            with self.subTest(name):
                result = run(CHECK, '--repo', FIX / name)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(result.stdout.splitlines()[-1], summary)
                self.assertEqual(lines(result.stdout, 'warning:'), BASE_WARNINGS)
                self.assertEqual(lines(result.stdout, 'error:'), set())

    def test_each_defect_fails_with_exactly_its_error(self):
        for name, expected in FAILURES.items():
            with self.subTest(name):
                result = run(CHECK, '--repo', FIX / name)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertEqual(lines(result.stdout, 'error:'), {'error: ' + e for e in expected})
                self.assertIsNone(SUMMARY.search(result.stdout), result.stdout)

    def test_every_fixture_is_exercised(self):
        built = {p.name for p in FIX.iterdir() if p.is_dir()}
        self.assertEqual(built, set(builder.VARIANTS))
        self.assertEqual(set(FAILURES) | {'valid-base', 'valid-reordered', 'valid-retired'}, set(builder.VARIANTS))

    def test_usage_errors_exit_2(self):
        self.assertEqual(run(CHECK).returncode, 2)
        missing = run(CHECK, '--repo', FIX / 'no-such-fixture')
        self.assertEqual(missing.returncode, 2, missing.stdout + missing.stderr)

    def test_checker_never_writes(self):
        for name in ('valid-base', 'bad-record-label'):
            with self.subTest(name):
                before = digest(FIX / name)
                run(CHECK, '--repo', FIX / name)
                self.assertEqual(digest(FIX / name), before)

    def test_fixture_build_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run([sys.executable, str(BUILD), tmp], check=True, capture_output=True, timeout=120)
            for name in builder.VARIANTS:
                with self.subTest(name):
                    self.assertEqual(digest(Path(tmp) / name), digest(FIX / name))
        self.assertEqual(run(BUILD).returncode, 2)


class InventoryTests(unittest.TestCase):
    def test_units_follow_the_coverage_rule(self):
        result = run(INVENTORY, 'units', '--repo', FIX / 'valid-base')
        self.assertEqual(result.returncode, 0, result.stderr)
        expected = ['SKILL.md:%d\t%s' % unit for unit in builder.UNITS]
        self.assertEqual(result.stdout.splitlines(), expected)

    def test_uncovered_lists_only_new_sentences(self):
        self.assertEqual(run(INVENTORY, 'uncovered', '--repo', FIX / 'valid-base').stdout, '')
        result = run(INVENTORY, 'uncovered', '--repo', FIX / 'added-sentence')
        self.assertEqual(result.stdout.splitlines(), ['SKILL.md:39\tNever skip the checks.'])

    def test_sync_detects_and_repairs_stale_historical_lists(self):
        self.assertEqual(run(INVENTORY, 'sync', '--repo', FIX / 'valid-base', '--check').returncode, 0)
        stale = run(INVENTORY, 'sync', '--repo', FIX / 'historical-mismatch', '--check')
        self.assertEqual(stale.returncode, 1)
        self.assertEqual(stale.stdout.splitlines(), ['R-ENTRY-01: historical is stale'])
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / 'repo'
            shutil.copytree(FIX / 'historical-mismatch', copy)
            self.assertEqual(run(INVENTORY, 'sync', '--repo', copy, '--write').returncode, 0)
            self.assertEqual(run(CHECK, '--repo', copy).returncode, 0)
            self.assertTrue(filecmp.cmp(copy / 'eval/rules/ledger.json', FIX / 'valid-base/eval/rules/ledger.json',
                                        shallow=False))


if __name__ == '__main__':
    unittest.main()
