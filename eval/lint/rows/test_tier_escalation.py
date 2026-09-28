"""Row 12's Tier / Tier reason / Escalation vocabulary: valid values, omission, and every declared
negative case.

Reuses test_lint_rows.py's row extractor (``rows()``/``run_row``) and template-derived ``brief()``
instead of re-implementing row 12's command or hand-writing a second brief generator.
"""
import tempfile
import unittest
from pathlib import Path

import test_lint_rows as base

FENCED_TIER_EXAMPLE = (
    '\n```text\n'
    '- **Tier**: (fast / standard / frontier; omit the whole field when the map cannot propose one)\n'
    '- **Escalation**: (declared; omit when the task does not permit the one capped retry)\n'
    '```\n'
)

FENCED_INVALID_EFFORT = (
    '\n```text\n'
    '- **Effort**: extreme\n'
    '```\n'
)


def brief_with(identity, tier=None, tier_reason=None, escalation=None, effort='- **Effort**: low',
               trailer=''):
    """A template-derived brief (base.brief) with explicit Tier/Tier reason/Escalation lines spliced
    in immediately after Effort, mirroring where the Contract places them in task.tmpl.md."""
    text = base.brief(identity, effort=effort)
    insert = []
    if tier is not None:
        insert.append('- **Tier**: ' + tier)
    if tier_reason is not None:
        insert.append('- **Tier reason**: ' + tier_reason)
    if escalation is not None:
        insert.append('- **Escalation**: ' + escalation)
    out = []
    for line in text.split('\n'):
        out.append(line)
        if line.startswith('- **Effort**:'):
            out.extend(insert)
    return '\n'.join(out) + trailer


class TierEscalationVocabularyTests(unittest.TestCase):
    def workspace(self, text):
        temporary = tempfile.TemporaryDirectory(prefix='tackle-tier-escalation-')
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name) / 'root'
        root.mkdir()
        base.materialize(root, 'pass-full')
        (root / 'docs/plans' / base.SLUG / 'tasks/demo.md').write_text(text)
        return root

    def run12(self, text):
        root = self.workspace(text)
        return base.run_row(12, root, None)

    def workspace_two(self, first_text, second_text):
        """Two briefs, named so `tasks/*.md` globs `aaa-*.md` before `zzz-*.md`: an orphan report
        naming the wrong file would misattribute the first file's finding to the second."""
        temporary = tempfile.TemporaryDirectory(prefix='tackle-tier-escalation-')
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name) / 'root'
        root.mkdir()
        base.materialize(root, 'pass-full')
        tasks = root / 'docs/plans' / base.SLUG / 'tasks'
        (tasks / 'aaa-first.md').write_text(first_text)
        (tasks / 'zzz-second.md').write_text(second_text)
        return root

    # --- C1: valid Tier values and omission ---

    def test_every_valid_tier_value_is_clean(self):
        for tier in ('fast', 'standard', 'frontier'):
            with self.subTest(tier=tier):
                verdict, child = self.run12(brief_with('DEMO', tier=tier, tier_reason='default'))
                self.assertEqual(verdict, 'PASS', child.stdout)

    def test_omitted_tier_is_clean(self):
        verdict, child = self.run12(brief_with('DEMO'))
        self.assertEqual(verdict, 'PASS', child.stdout)

    def test_fenced_tier_and_escalation_example_is_ignored(self):
        verdict, child = self.run12(brief_with('DEMO', trailer=FENCED_TIER_EXAMPLE))
        self.assertEqual(verdict, 'PASS', child.stdout)

    def test_invalid_effort_inside_a_fenced_block_is_still_red(self):
        """The fence-skip exempts only the new Tier/Tier reason/Escalation checks: the pre-existing
        Effort check has no fence-awareness at base and must not gain one here."""
        verdict, child = self.run12(brief_with('DEMO', trailer=FENCED_INVALID_EFFORT))
        self.assertEqual(verdict, 'FAIL', child.stdout)
        self.assertIn('Effort**: extreme', child.stdout.decode())

    # --- C1 negative: independently red ---

    def test_unknown_tier_value_is_red(self):
        verdict, child = self.run12(brief_with('DEMO', tier='turbo', tier_reason='default'))
        self.assertEqual(verdict, 'FAIL', child.stdout)
        self.assertIn('Tier**: turbo', child.stdout.decode())

    def test_capitalized_tier_value_is_red(self):
        verdict, child = self.run12(brief_with('DEMO', tier='Fast', tier_reason='default'))
        self.assertEqual(verdict, 'FAIL', child.stdout)

    def test_trailing_punctuation_tier_value_is_red(self):
        verdict, child = self.run12(brief_with('DEMO', tier='fast.', tier_reason='default'))
        self.assertEqual(verdict, 'FAIL', child.stdout)

    def test_valid_tier_beside_invalid_effort_is_independently_red(self):
        verdict, child = self.run12(brief_with('DEMO', tier='fast', tier_reason='default',
                                                effort='- **Effort**: extreme'))
        self.assertEqual(verdict, 'FAIL', child.stdout)
        out = child.stdout.decode()
        self.assertIn('Effort**: extreme', out)
        self.assertNotIn('Tier**: fast', out)

    # --- C2: Tier reason required exactly when Tier present; a reason with no Tier is clean, since
    # it may record an Effort-only deviation from the compiled default ---

    def test_tier_reason_present_with_tier_is_clean(self):
        verdict, child = self.run12(brief_with('DEMO', tier='standard', tier_reason='default'))
        self.assertEqual(verdict, 'PASS', child.stdout)

    def test_tier_without_tier_reason_is_red(self):
        verdict, child = self.run12(brief_with('DEMO', tier='standard'))
        self.assertEqual(verdict, 'FAIL', child.stdout)
        self.assertIn('Tier without Tier reason', child.stdout.decode())

    def test_tier_reason_without_tier_is_clean_as_an_effort_only_deviation(self):
        verdict, child = self.run12(brief_with('DEMO', tier_reason='effort raised for a security review'))
        self.assertEqual(verdict, 'PASS', child.stdout)

    # --- C3: Escalation vocabulary: declared/omission clean; other value red; orphaned red ---

    def test_declared_escalation_with_tier_is_clean(self):
        verdict, child = self.run12(brief_with('DEMO', tier='frontier', tier_reason='default',
                                                escalation='declared'))
        self.assertEqual(verdict, 'PASS', child.stdout)

    def test_omitted_escalation_is_clean(self):
        verdict, child = self.run12(brief_with('DEMO', tier='frontier', tier_reason='default'))
        self.assertEqual(verdict, 'PASS', child.stdout)

    def test_other_escalation_value_is_red(self):
        verdict, child = self.run12(brief_with('DEMO', tier='frontier', tier_reason='default',
                                                escalation='yes'))
        self.assertEqual(verdict, 'FAIL', child.stdout)
        self.assertIn('Escalation**: yes', child.stdout.decode())

    def test_escalation_without_tier_is_orphaned_and_red(self):
        verdict, child = self.run12(brief_with('DEMO', escalation='declared'))
        self.assertEqual(verdict, 'FAIL', child.stdout)
        self.assertIn('Escalation without Tier', child.stdout.decode())

    # --- An orphan report names the file it was found in, not whichever file sorts last ---

    def test_orphan_in_the_first_of_two_files_is_reported_against_that_file(self):
        # Escalation-without-Tier (not Tier reason-without-Tier, now clean as an Effort-only
        # deviation reason) is the orphan case exercised here, to keep covering the row12
        # filename-attribution regression.
        root = self.workspace_two(brief_with('AAA', escalation='declared'), brief_with('ZZZ'))
        verdict, child = base.run_row(12, root, None)
        self.assertEqual(verdict, 'FAIL', child.stdout)
        out = child.stdout.decode()
        self.assertIn('aaa-first.md: Escalation without Tier', out)
        self.assertNotIn('zzz-second.md: Escalation without Tier', out)

    def test_orphan_in_the_second_of_two_files_is_reported_against_that_file(self):
        root = self.workspace_two(brief_with('AAA'), brief_with('ZZZ', escalation='declared'))
        verdict, child = base.run_row(12, root, None)
        self.assertEqual(verdict, 'FAIL', child.stdout)
        out = child.stdout.decode()
        self.assertIn('zzz-second.md: Escalation without Tier', out)
        self.assertNotIn('aaa-first.md: Escalation without Tier', out)


if __name__ == '__main__':
    unittest.main()
