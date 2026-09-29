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
GATE_WORK = tempfile.TemporaryDirectory()
GATE_FIX = Path(GATE_WORK.name) / 'gate'
GATE_AUTO_FIX = Path(GATE_WORK.name) / 'gate-auto'
FIX.mkdir()
GATE_FIX.mkdir()
GATE_AUTO_FIX.mkdir()
GATE_BASES = {}
GATE_AUTO_ROOTS = {}
PREFLIGHT_BASE = '8b12ba7f11595adbbd13e06c1871e741155c6004'  # this task's own starting commit


def setUpModule():
    subprocess.run([sys.executable, str(BUILD), str(FIX)], check=True, capture_output=True, timeout=120)
    global GATE_BASES, GATE_AUTO_ROOTS
    GATE_BASES = builder.build_gate(GATE_FIX)
    GATE_AUTO_ROOTS = builder.build_gate_auto(GATE_AUTO_FIX)


def tearDownModule():
    WORK.cleanup()
    GATE_WORK.cleanup()


def gate(repo, base_rev, cohort=None, timeout=60):
    args = [sys.executable, str(CHECK), '--repo', str(repo), '--gate', base_rev]
    if cohort is not None:
        args += ['--evidence-cohort', cohort]
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout)

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


class GateCases(unittest.TestCase):
    """The change gate (`check_ledger.py --gate`): every fixture is a single-commit git repository whose
    committed tree is the base revision and whose (uncommitted) working tree is the candidate; the gate
    reads the base through `git show` and the candidate straight off disk, so no second commit is needed."""

    def root(self, name):
        return GATE_FIX / name

    def test_add_without_evidence_fails(self):
        result = gate(self.root('c1-add-untested'), GATE_BASES['c1-add-untested'], '2026-09-candidate')
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn('R-INTAKE-90: added rule needs held-out evidence: status is untested', result.stdout)

    def test_delete_without_inventory_fails(self):
        result = gate(self.root('c2-delete-no-inventory'), GATE_BASES['c2-delete-no-inventory'])
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn('R-INTAKE-91: deleted rule needs prior evidence or resolving mirrors: mirrors is empty',
                      result.stdout)

    def test_add_validated_only_by_its_discovering_scenario_fails(self):
        result = gate(self.root('c3-add-discovery-only'), GATE_BASES['c3-add-discovery-only'], '2026-09-candidate')
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn('discriminates rests only on discovering scenarios', result.stdout)

    def test_add_with_held_out_evidence_passes(self):
        result = gate(self.root('c4-add-held-out-evidence'), GATE_BASES['c4-add-held-out-evidence'],
                     '2026-09-candidate')
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn('in-scope: R-INTAKE-93: added, evidence inconclusive', result.stdout)

    def test_reword_with_no_semantic_change_needs_no_evidence(self):
        result = gate(self.root('c5-reword-no-semantic-change'), GATE_BASES['c5-reword-no-semantic-change'])
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn('gate: added=0 changed=1 deleted=0', result.stdout)
        self.assertNotIn('needs held-out evidence', result.stdout)

    def test_add_citing_an_unrelated_cohort_fails(self):
        result = gate(self.root('c21-add-unrelated-cohort'), GATE_BASES['c21-add-unrelated-cohort'],
                     '2026-09-candidate')
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn('not tied to this cohort', result.stdout)

    def test_delete_with_prior_evidence_passes(self):
        result = gate(self.root('c22-delete-prior-evidence'), GATE_BASES['c22-delete-prior-evidence'])
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn('in-scope: R-INTAKE-95: deleted, prior evidence inert', result.stdout)

    def test_delete_restated_elsewhere_passes(self):
        result = gate(self.root('c23-delete-restated-elsewhere'), GATE_BASES['c23-delete-restated-elsewhere'])
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn('in-scope: R-INTAKE-96: deleted, mirrors references/guide.md:1', result.stdout)

    def test_retire_in_place_with_no_evidence_is_still_a_deletion(self):
        result = gate(self.root('c29-retire-in-place'), GATE_BASES['c29-retire-in-place'])
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn('R-INTAKE-97: deleted rule needs prior evidence or resolving mirrors: mirrors is empty',
                      result.stdout)

    def test_a_non_hot_path_add_is_out_of_scope(self):
        result = gate(self.root('c30a-out-of-scope-add'), GATE_BASES['c30a-out-of-scope-add'])
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("untested (outside the gate's scope): R-INTAKE-98", result.stdout)

    def test_scope_survives_a_demotion_to_non_hot_path(self):
        result = gate(self.root('c30b-scope-survives-demotion'), GATE_BASES['c30b-scope-survives-demotion'])
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn('R-INTAKE-99: changed rule needs held-out evidence', result.stdout)

    def test_change_with_evidence_passes(self):
        result = gate(self.root('c31-change-with-evidence'), GATE_BASES['c31-change-with-evidence'],
                     '2026-09-candidate')
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn('in-scope: R-EVID-90: changed, evidence inert', result.stdout)

    def test_a_recorded_exception_applies(self):
        result = gate(self.root('c32-exception-applies'), GATE_BASES['c32-exception-applies'])
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn('exception: applied R-EVID-91', result.stdout)

    def test_a_recorded_exception_voids_when_the_statement_moves_again(self):
        result = gate(self.root('c33-exception-void'), GATE_BASES['c33-exception-void'])
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn('void exception (statement changed since it was recorded)', result.stdout)
        self.assertIn('exception: void R-EVID-91', result.stdout)

    def test_safety_invariant_retired_with_only_an_outside_mirror_fails(self):
        result = gate(self.root('c34a-safety-invariant-outside-only'), GATE_BASES['c34a-safety-invariant-outside-only'])
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn('a safety invariant needs a mirror inside SKILL.md or references/', result.stdout)

    def test_safety_invariant_retired_with_one_inside_mirror_passes(self):
        result = gate(self.root('c34b-safety-invariant-one-inside'), GATE_BASES['c34b-safety-invariant-one-inside'])
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn('in-scope: R-EVID-92: deleted, mirrors', result.stdout)

    def test_reclassifying_a_safety_invariant_does_not_excuse_its_deletion(self):
        result = gate(self.root('c34c-safety-invariant-reclassified'),
                     GATE_BASES['c34c-safety-invariant-reclassified'])
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn('a safety invariant needs a mirror inside SKILL.md or references/', result.stdout)

    def test_exceptions_never_excuse_a_deletion(self):
        result = gate(self.root('c35-no-exception-for-deletion'), GATE_BASES['c35-no-exception-for-deletion'])
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn('R-EVID-93: deleted rule needs prior evidence or resolving mirrors: mirrors is empty',
                      result.stdout)
        # exceptions never apply to a deletion: this one is at most dormant, never applied.
        self.assertNotIn('exception: applied', result.stdout)

    def test_exception_naming_an_absent_rule_is_void(self):
        result = gate(self.root('c36a-exception-ghost-rule'), GATE_BASES['c36a-exception-ghost-rule'])
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn('void exception (rule is not in the candidate ledger)', result.stdout)
        self.assertIn('exception: void R-EVID-94', result.stdout)

    def test_exception_on_an_untouched_rule_is_dormant(self):
        result = gate(self.root('c36b-exception-dormant'), GATE_BASES['c36b-exception-dormant'])
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn('exception: dormant R-ENTRY-01', result.stdout)

    def test_no_exceptions_file_on_a_clean_diff_passes(self):
        result = gate(self.root('c36c-no-exceptions-file'), GATE_BASES['c36c-no-exceptions-file'])
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertNotIn('exception:', result.stdout)

    def test_gate_prints_the_added_changed_deleted_counts(self):
        result = gate(self.root('c4-add-held-out-evidence'), GATE_BASES['c4-add-held-out-evidence'],
                     '2026-09-candidate')
        self.assertIn('gate: added=1 changed=0 deleted=0', result.stdout)


class GateAutoResolution(unittest.TestCase):
    """`--gate auto`'s base resolution: a tag reachable from HEAD^ whose tree holds the ledger, else the
    commit that first added it. Each fixture is checked for its resolved base only; whether that specific
    diff then passes or fails is not the point of this resolution rule."""

    def resolved_base(self, name):
        result = gate(GATE_AUTO_ROOTS[name], 'auto')
        lines = [line for line in result.stdout.splitlines() if line.startswith('gate: base=')]
        self.assertEqual(len(lines), 1, result.stdout)
        return lines[0][len('gate: base='):], result

    def test_falls_back_to_the_first_commit_that_added_the_ledger_when_every_tag_predates_it(self):
        base, result = self.resolved_base('c28a-only-tags-predate-ledger')
        first_add = subprocess.run(['git', '-C', str(GATE_AUTO_ROOTS['c28a-only-tags-predate-ledger']), 'log',
                                    '--diff-filter=A', '--format=%H', '--', 'eval/rules/ledger.json'],
                                   capture_output=True, text=True).stdout.split()[-1]
        self.assertEqual(base, first_add)
        self.assertNotIn('error:', result.stdout)

    def test_resolves_to_the_nearest_ledger_bearing_tag_behind_head(self):
        base, result = self.resolved_base('c28b-ledger-tag-behind-head')
        self.assertEqual(base, 'v2')

    def test_never_resolves_to_a_tag_on_head_itself(self):
        base, result = self.resolved_base('c28c-tag-on-head-itself')
        self.assertEqual(base, 'v1')
        self.assertNotEqual(base, 'v2')  # v2 is the tag on HEAD itself



def packaging_relocated_note(repo, base):
    """Recognize one byte-identical packaging move, never a path-wide exemption.

    Bind both historical blobs, the complete candidate bytes and exactly one
    inherited line. Any changed byte, duplicate, retained old path or failed Git
    lookup disables this treatment; the unchanged scanner then reports additions.
    """
    old_path = 'references/guides/lint-spec.md'
    new_path = 'skills/tackle/' + old_path
    line_hash = '3896f92f66de37480f7b52a44d13fd8038016a2a151c67ca6e56a025d745bbb0'
    if base != PREFLIGHT_BASE or (repo / old_path).exists() or (repo / old_path).is_symlink():
        return None
    target = repo / new_path
    if not target.is_file() or target.is_symlink():
        return None
    blobs = []
    for revision, expected in [(PREFLIGHT_BASE, '1ada4d66448f57942f887d588a2b3dc32ed3cc6b37b4092aaa82d602e2273c71'),
                               ('v9.0.0', '5aeab0c7be0715b8b3f61e9490a4809139b8beac9d4919c9643eade49f8a3b93')]:
        result = subprocess.run(['git', '-C', str(repo), 'show', revision + ':' + old_path],
                                capture_output=True, check=False)
        if result.returncode or hashlib.sha256(result.stdout).hexdigest() != expected:
            return None
        blobs.append(result.stdout)
    current = target.read_bytes()
    if current != blobs[1]:
        return None
    for blob in [*blobs, current]:
        if sum(hashlib.sha256(line).hexdigest() == line_hash for line in blob.splitlines()) != 1:
            return None
    return new_path, line_hash


class RepositoryGateRegressionTests(unittest.TestCase):
    """The gate is additive: a plain run never changes, and every new prose word this task commits stays
    free of a workspace-local id."""

    def test_plain_mode_is_byte_identical_between_the_old_and_new_code(self):
        """Compares code, not the live ledger (whose add/changed/deleted counts move by design as this
        task's own edits land): both the pre-task and the post-task check_ledger.py run against one fixed,
        unrelated fixture snapshot that neither of them touches."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            old_check = tmp / 'check_ledger.py'
            old = subprocess.run(['git', '-C', str(REPO), 'show', '%s:eval/rules/check_ledger.py' % PREFLIGHT_BASE],
                                 capture_output=True, text=True, check=True)
            old_check.write_text(old.stdout, encoding='utf-8')
            old_inventory = subprocess.run(['git', '-C', str(REPO), 'show', '%s:eval/rules/inventory.py' % PREFLIGHT_BASE],
                                           capture_output=True, text=True, check=True)
            (tmp / 'inventory.py').write_text(old_inventory.stdout, encoding='utf-8')
            fixture = FIX / 'valid-base'
            before = run(old_check, '--repo', fixture)
            after = run(CHECK, '--repo', fixture)
            self.assertEqual((before.returncode, before.stdout), (after.returncode, after.stdout))
            self.assertEqual(before.stderr, after.stderr)

    def test_no_staged_addition_carries_a_workspace_id_or_slug(self):
        """A grep over every '+'-prefixed line of the diff between this task's own starting commit and the
        working tree, repo-wide (not only the files this task's brief names): a bare `<letter><NN>` token
        for the seven letters this repository's workspace ids use, or the workspace's own directory slug.
        Refined with two guards a blind sweep would need in this codebase: a rule id such as R-EVID-01 or
        R-COMM-03 is not a leak (the letter sits mid-word, preceded by another letter), and an ISO timestamp
        such the ones this test suite writes (`...T00:00:00`) is not a leak (immediately followed by a
        colon, never true of a real workspace id). This check's own source is exempt: it must spell out
        the pattern and the slug literally to define them, exactly as the pre-existing credential guard
        (eval/maintaining/suite-integrity/test_credential_guard.py) already exempts itself from its own home-path scan.
        The one other exemption is the `decision_rule` field of a sealed cohort manifest: that text is
        pre-registered and sealed before any episode runs, so it cannot change afterwards. Every other line
        of a manifest is still scanned. One exact inherited line in a byte-proven packaging
        relocation is handled mechanically; any changed byte or duplicate disables it."""
        self_path = str(Path(__file__).resolve().relative_to(REPO))
        pattern = re.compile(r'(?<![A-Za-z])[PTDQRCM]-?[0-9]{2}(?!:)|tackle' + '-9')
        SEALED_MANIFEST = re.compile(r'^eval/cohorts/[^/]+/(?:[^/]+/)?manifest\.json$')
        result = subprocess.run(['git', '-C', str(REPO), 'diff', PREFLIGHT_BASE, '--unified=0'],
                                capture_output=True, text=True, check=True)
        relocated_note = packaging_relocated_note(REPO, PREFLIGHT_BASE)
        found, path = [], None
        for line in result.stdout.splitlines():
            if line.startswith('+++ '):
                name = line[4:]
                path = None if name == '/dev/null' else name[2:] if name.startswith('b/') else name
            elif (path and path != self_path and line.startswith('+') and not line.startswith('+++')
                  and pattern.search(line[1:])
                  and not (SEALED_MANIFEST.match(path) and line[1:].lstrip().startswith('"decision_rule":'))
                  and relocated_note != (path, hashlib.sha256(line[1:].encode('utf-8')).hexdigest())):
                found.append('%s: %s' % (path, line[1:]))
        self.assertEqual(found, [])


if __name__ == '__main__':
    unittest.main()
