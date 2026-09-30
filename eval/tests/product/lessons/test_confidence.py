"""Extraction-and-cross-check tests for the one shipped, calibrated confidence recipe.

`references/guides/retro.md` carries a single, self-contained ```awk fenced recipe implementing the
Wilson score interval's lower bound (z=1.96) over each Hypotheses/Directives bullet's own
`observations` list. This suite extracts that exact recipe text (never reimplementing the formula,
the parsing, or the retirement threshold comparison independently) and:

- runs it over synthetic fixture profiles under `fixtures/` (never the real `.tackle/profile.md` or
  `~/.tackle/user-profile.md` — this suite never reads either), and
- separately imports `eval/protocol-v2/verdict.py`'s `wilson()` as an independent oracle, confirming
  the two agree on the same fixture inputs.

Standard library only; no network, container or model call.
"""
import importlib.util
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
import sys
sys.path.insert(0, str(ROOT))
from maintaining.install_root import current_root  # noqa: E402
INSTALL = current_root(ROOT)

HERE = (Path(__file__).resolve().parents[4] / 'eval/lessons')
RETRO = INSTALL / 'references/guides/retro.md'


def load_verdict():
    spec = importlib.util.spec_from_file_location('verdict', ROOT / 'eval/protocol-v2/verdict.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VERDICT = load_verdict()


def extract_confidence_recipe(text=None):
    """The exact ```awk fenced recipe retro.md ships (extracted, never re-typed)."""
    text = text if text is not None else RETRO.read_text(encoding='utf-8')
    match = re.search(r'```awk\n(.*?)\n```', text, re.S)
    if not match:
        raise AssertionError('no ```awk fenced confidence recipe found')
    program = match.group(1)
    for forbidden in ('eval/',):
        assert forbidden not in program, 'recipe (or a comment inside it) cites a repository path: %r' % forbidden
    return program


class Row:
    """One parsed output row: `<id> N M n confidence status` (or the n/a/unranked shape)."""

    def __init__(self, line):
        parts = line.split()
        self.id = parts[0]
        self.raw = parts[1:]
        if parts[1] == 'n/a':
            self.n_check = self.n_cross = self.n_total = self.confidence = None
            self.status = 'unranked'
        else:
            self.n_check, self.n_cross, self.n_total = int(parts[1]), int(parts[2]), int(parts[3])
            self.confidence = float(parts[4])
            self.status = parts[5]


def run_recipe(profile_text, program=None):
    """Run the (extracted or given) recipe over profile_text; return {id: Row}."""
    program = program if program is not None else extract_confidence_recipe()
    with tempfile.TemporaryDirectory(prefix='tackle-learning-loop-') as scratch:
        profile_path = Path(scratch) / 'profile.md'
        profile_path.write_text(profile_text, encoding='utf-8')
        child = subprocess.run(['awk', program, str(profile_path)], capture_output=True, text=True, timeout=30)
    assert child.returncode == 0, (child.returncode, child.stdout, child.stderr)
    assert child.stderr == ''
    rows = {}
    for line in child.stdout.splitlines():
        row = Row(line)
        rows[row.id] = row
    return rows


def fixture(name):
    return (HERE / 'fixtures' / name).read_text(encoding='utf-8')


class ConfidenceGoldenTests(unittest.TestCase):
    """C2: the extracted recipe agrees with the independent `verdict.wilson()` oracle, including
    the real audit's own 9/9 -> ~0.70 and 1/1 -> ~0.21, an n=0 (assumed-only) entry, a mutated
    observation, and the assumed-acceptance falsifying case."""

    def setUp(self):
        self.program = extract_confidence_recipe()
        self.text = fixture('profile-wilson-golden.md')

    def test_nine_of_nine_and_one_of_one_match_the_independent_oracle(self):
        rows = run_recipe(self.text, self.program)
        self.assertAlmostEqual(rows['H01'].confidence, VERDICT.wilson(9, 9)[0], places=4)
        self.assertAlmostEqual(rows['H02'].confidence, VERDICT.wilson(1, 1)[0], places=4)
        self.assertEqual(rows['H01'].status, 'active')
        self.assertEqual(rows['H02'].status, 'active')

    def test_n_equals_zero_assumed_only_is_n_a_not_a_crash(self):
        rows = run_recipe(self.text, self.program)
        self.assertEqual(rows['H03'].status, 'unranked')
        self.assertIsNone(rows['H03'].confidence)

    def test_a_mutated_observation_changes_the_value(self):
        baseline = run_recipe(
            '## Hypotheses\n\n- id: HM · baseline · confidence: x · observations: a:\u2713@2026-01-01; b:\u2713@2026-01-02 · status: active\n',
            self.program)['HM']
        mutated = run_recipe(
            '## Hypotheses\n\n- id: HM · baseline · confidence: x · observations: a:\u2713@2026-01-01; b:\u2717@2026-01-02 · status: active\n',
            self.program)['HM']
        self.assertNotAlmostEqual(baseline.confidence, mutated.confidence, places=4)
        self.assertEqual(baseline.n_check, 2)
        self.assertEqual(mutated.n_check, 1)
        self.assertEqual(mutated.n_cross, 1)

    def test_appending_one_assumed_item_changes_neither_counts_nor_confidence(self):
        """A falsifying case: an implementation that
        computes Wilson correctly but still counts every accepted suggestion toward N/M/n must be
        caught here."""
        before = run_recipe(
            '## Hypotheses\n\n- id: HA · baseline · confidence: x · observations: a:\u2713@2026-01-01; b:\u2713@2026-01-02 · status: active\n',
            self.program)['HA']
        after = run_recipe(
            '## Hypotheses\n\n- id: HA · baseline · confidence: x · observations: a:\u2713@2026-01-01; b:\u2713@2026-01-02; '
            'c:assumed@2026-01-03 · status: active\n',
            self.program)['HA']
        self.assertEqual((before.n_check, before.n_cross, before.n_total), (after.n_check, after.n_cross, after.n_total))
        self.assertEqual(before.confidence, after.confidence)


class DuplicateHypothesisTests(unittest.TestCase):
    """C3: two bullets sharing one hypothesis's text merge by the union of their observations'
    initiatives, never by summing two entries' N/M (which double-counts a shared initiative)."""

    def test_the_pinned_union_result_is_4_over_0_never_the_naive_sum_7_over_0(self):
        rows = run_recipe(fixture('profile-duplicate.md'))
        # H10 is the 3-initiative entry seen first in the file: its own union-so-far is 3/0.
        self.assertEqual((rows['H10'].n_check, rows['H10'].n_cross), (3, 0))
        # H11 repeats H10's exact text with one added initiative (delta+shared): the recipe must
        # report the union (4/0), not the naive per-entry sum (7/0, double-counting the 3 shared).
        self.assertEqual((rows['H11'].n_check, rows['H11'].n_cross), (4, 0))
        self.assertNotEqual(rows['H11'].n_check, 3 + 4)
        self.assertAlmostEqual(rows['H11'].confidence, VERDICT.wilson(4, 4)[0], places=4)
        naive_sum_lower = VERDICT.wilson(7, 7)[0]
        self.assertNotAlmostEqual(rows['H11'].confidence, naive_sum_lower, places=2)

    def test_the_union_is_order_independent(self):
        """Reversing which duplicate bullet (the subset or its superset) appears first must not
        change either entry's reported union: both still read the full 4/0, never a partial count
        or an n/a for whichever bullet the file happens to list second."""
        reversed_text = (
            '## Hypotheses\n\n'
            '- id: HX · Reordered duplicate text · confidence: x · observations: '
            'alpha:\u2713@2026-01-01; beta:\u2713@2026-01-02; gamma:\u2713@2026-01-03; delta:\u2713@2026-01-04 · status: active\n'
            '- id: HY · Reordered duplicate text · confidence: x · observations: '
            'alpha:\u2713@2026-01-01; beta:\u2713@2026-01-02; gamma:\u2713@2026-01-03 · status: active\n'
        )
        rows = run_recipe(reversed_text)
        self.assertEqual((rows['HX'].n_check, rows['HX'].n_cross), (4, 0))
        self.assertEqual((rows['HY'].n_check, rows['HY'].n_cross), (4, 0))

    def test_an_assumed_observation_in_one_duplicate_never_blocks_a_later_real_one(self):
        """C3: an `assumed` token for an initiative must never occupy that
        (hypothesis, initiative) union slot, so a later duplicate bullet's real check/cross for
        the same initiative still counts."""
        text = (
            '## Hypotheses\n\n'
            '- id: HP · Same hypothesis text · confidence: x · observations: alpha:assumed@2026-01-01 · status: active\n'
            '- id: HQ · Same hypothesis text · confidence: x · observations: alpha:\u2713@2026-01-02 · status: active\n'
        )
        rows = run_recipe(text)
        self.assertEqual(rows['HP'].status, 'unranked', 'assumed-only stays n/a for its own bullet')
        self.assertEqual((rows['HQ'].n_check, rows['HQ'].n_cross), (1, 0),
                         'the later real check for the same initiative must still be counted')


class TopKMechanicsTests(unittest.TestCase):
    """C4 (mechanical half): profile.tmpl.md:13's Top-K rule sorts by confidence and cuts at 10.
    Applying that documented rule over the recipe's own emitted rows (never reimplementing the
    parsing, formula or threshold) checks that the cut actually reacts to the computed value
    and that an n=0/assumed-only entry is excluded from the cut entirely, never merely
    sorted last."""

    @staticmethod
    def ranked_ids(rows, limit=10):
        """The Top-K ids: ranked (non-unranked) rows sorted by confidence descending, cut at
        limit -- profile.tmpl.md:13's documented rule, applied to the recipe's own output."""
        ranked = [row for row in rows.values() if row.status != 'unranked']
        ranked.sort(key=lambda row: row.confidence, reverse=True)
        return [row.id for row in ranked[:limit]]

    def test_mutating_the_entry_just_below_the_cut_swaps_it_with_the_entry_just_above(self):
        text = fixture('profile-topk-11.md')
        marker = 'observations: a1:✓@2026-01-01 · status'
        self.assertIn(marker, text, 'fixture shape changed; update this mutation to match')
        before = run_recipe(text)
        top_before = self.ranked_ids(before)
        self.assertIn('E02', top_before)
        self.assertNotIn('E01', top_before)
        mutated_text = text.replace(marker, 'observations: a1:✓@2026-01-01; z1:✓@2026-01-31 · status')
        after = run_recipe(mutated_text)
        top_after = self.ranked_ids(after)
        self.assertIn('E01', top_after, 'the mutated entry must now enter the Top-10 cut')
        self.assertNotIn('E02', top_after, 'the weakest previously-included entry must now fall out')

    def test_the_assumed_only_entry_is_excluded_from_the_cut_not_merely_sorted_last(self):
        """10 total entries (9 numeric + 1 n/a) at the Top-10 boundary exactly: a wrong
        implementation that merely sorts the n/a entry last, instead of excluding it from the
        ranking pool, would still show all 10 rows here -- the correct one shows 9."""
        rows = run_recipe(fixture('profile-topk-9.md'))
        self.assertEqual(rows['F10'].status, 'unranked')
        top = self.ranked_ids(rows)
        self.assertEqual(len(top), 9, 'only the 9 numeric entries are ranked; F10 never occupies a Top-10 slot')
        self.assertNotIn('F10', top)


class SectionScopingTests(unittest.TestCase):
    """The recipe only reads Hypotheses/Directives bullets: a Rules (or any other) section's own
    bullets, which share the leading '- ' marker but carry neither `observations:` nor
    `evidence:`, must not be misread as confidence-less entries."""

    def test_rules_section_bullets_produce_no_rows(self):
        text = (
            '## Rules\n\n'
            '- **Single write path**: the retro workflow is the only action that writes to this file.\n'
            '- **Top-K limit**: only the top <= 10 entries by confidence enter a session.\n\n'
            '## Hypotheses\n\n'
            '- id: H01 · some text · confidence: x · observations: a:\u2713@2026-01-01 · status: active\n'
        )
        rows = run_recipe(text)
        self.assertEqual(set(rows), {'H01'})


class LegacyReadCompatTests(unittest.TestCase):
    """C5: the same shipped recipe reads three old-format shapes without crashing or
    rewriting: plain N-check/M-cross, N-check/M-null (the null bucket excluded from n entirely),
    and a confidence/evidence-less directive (n/a, unranked)."""

    def test_three_legacy_shapes_read_without_crashing(self):
        rows = run_recipe(fixture('profile-legacy.md'))
        by_line = sorted(rows.values(), key=lambda r: int(r.id.split(':')[1]))
        plain, null_shape, confidenceless = by_line
        self.assertEqual((plain.n_check, plain.n_cross, plain.n_total), (3, 0, 3))
        self.assertEqual((null_shape.n_check, null_shape.n_cross, null_shape.n_total), (1, 0, 1),
                         'a null observation must be excluded from n entirely (neither check nor cross)')
        self.assertEqual(confidenceless.status, 'unranked')
        self.assertIsNone(confidenceless.confidence)


class RetirementBoundaryTests(unittest.TestCase):
    """The retirement rule (cross-count >= 3 AND raw confidence < 0.3) fires/doesn't exactly
    on five boundary fixtures, checked by reading the recipe's own emitted status (never
    recomputed independently)."""

    def setUp(self):
        self.rows = run_recipe(fixture('profile-retirement.md'))

    def test_zero_checked_three_crossed_retires(self):
        self.assertEqual(self.rows['RB01'].status, 'retired')
        self.assertAlmostEqual(self.rows['RB01'].confidence, VERDICT.wilson(0, 3)[0], places=4)

    def test_four_checked_three_crossed_retires_on_the_raw_unrounded_value(self):
        row = self.rows['RB02']
        self.assertEqual(row.status, 'retired')
        self.assertLess(row.confidence, 0.3)
        self.assertAlmostEqual(row.confidence, VERDICT.wilson(4, 7)[0], places=4)
        self.assertEqual(round(row.confidence, 1), 0.3, 'the raw value must retire even though a 1-decimal display rounds to 0.3')

    def test_five_checked_three_crossed_stays_active(self):
        row = self.rows['RB03']
        self.assertEqual(row.status, 'active')
        self.assertGreaterEqual(row.confidence, 0.3)

    def test_zero_checked_two_crossed_stays_active_below_n_min(self):
        self.assertEqual(self.rows['RB04'].status, 'active')

    def test_one_checked_zero_crossed_stays_active_below_n_min(self):
        self.assertEqual(self.rows['RB05'].status, 'active')

    def test_both_conjuncts_are_required_independently(self):
        """Dropping either the cross-count>=3 conjunct or the <0.3 conjunct changes a
        fixture's outcome. RB04 falsifies 'confidence alone decides retirement' (its raw value is
        as low as RB01's, yet it must stay active); RB03 falsifies 'cross-count alone decides
        retirement' (it has 3 crosses like RB01/RB02, yet it must stay active)."""
        self.assertEqual(self.rows['RB04'].status, 'active')
        self.assertLess(self.rows['RB04'].confidence, 0.3)
        self.assertEqual(self.rows['RB03'].status, 'active')


class RecipePortabilityTests(unittest.TestCase):
    """The recipe never cites a repository path, and a malformed/empty profile does not
    crash it (defensive, not part of the case matrix)."""

    def test_no_bare_eval_path_anywhere_in_the_recipe_or_its_comments(self):
        program = extract_confidence_recipe()
        self.assertNotIn('eval/', program)

    def test_empty_profile_produces_no_rows_and_does_not_crash(self):
        rows = run_recipe('# empty profile\n')
        self.assertEqual(rows, {})


if __name__ == '__main__':
    unittest.main()
