"""Text checks over the shipped prose: no case here launches or simulates an agent
proposing, accepting or overriding anything (D-103) -- each assertion reads the rule the guide
states or the anchor/path it names, mechanically.

Standard library only; no network, container or model call.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(relative):
    return (ROOT / relative).read_text(encoding='utf-8')


class C1ConfidenceIsComputedTests(unittest.TestCase):
    """C1: no step asks a human/agent to pick or propose a numeric confidence; the computation
    step names the formula and its inputs; the literal 'Accept => increment check' text is gone."""

    def setUp(self):
        self.retro = read('references/guides/retro.md')

    def test_no_step_proposes_a_numeric_confidence(self):
        self.assertNotIn('A proposed confidence', self.retro)
        self.assertNotIn('proposed confidence (0.0', self.retro)

    def test_the_computation_step_names_the_formula_and_its_inputs(self):
        section = self.retro.split('### Confidence is computed, never proposed', 1)[1].split('\n### ', 1)[0]
        self.assertIn('Wilson score interval', section)
        self.assertIn('z=1.96', section)
        self.assertIn('observations', section)

    def test_the_literal_accept_increment_check_text_is_gone(self):
        self.assertNotIn('Accept ⇒ increment ✓', self.retro)
        self.assertNotIn('Accept => increment', self.retro)


class C4IdsAndTopKTextTests(unittest.TestCase):
    """C4 (text half): profile.tmpl.md's format carries id; intake-and-gate.md's tally names an id
    per accepted/overridden entry; retro.md's counter step reads by id; profile.tmpl.md's Top-K
    rule still names the confidence field."""

    def test_profile_template_entry_format_carries_id(self):
        template = read('references/profile.tmpl.md')
        self.assertIn('id: {{H-id}}', template)
        self.assertIn('id: {{A-id}}', template)
        self.assertIn('observations:', template)

    def test_example_ids_obey_the_id_shape_rule(self):
        # Every example id the rule offers, and every id placeholder the template shows, must itself
        # avoid the forbidden shape; `D-id` already names a decision id elsewhere in the templates.
        shape = re.compile(r'[PTDQRCM]-?[0-9]{2}')
        sentence = read('references/guides/retro.md').split('stable `id` (', 1)[1].split(')', 1)[0]
        examples = re.findall(r'`([A-Za-z0-9-]+)`', sentence)
        self.assertTrue(examples, 'no example ids found in the id sentence')
        for example in examples:
            self.assertIsNone(shape.search(example), example)
        placeholders = re.findall(r'id: \{\{([^}]+)\}\}', read('references/profile.tmpl.md'))
        self.assertEqual(len(placeholders), 2, placeholders)
        for placeholder in placeholders:
            self.assertNotEqual(placeholder, 'D-id', 'D-id names a decision id')
            self.assertIsNone(shape.search(placeholder.replace('-id', '01')), placeholder)

    def test_intake_and_gate_tally_names_an_id_per_accepted_and_overridden_entry(self):
        text = read('references/guides/intake-and-gate.md')
        tally = re.search(r'```\nprofile proposals:.*?\n```', text, re.S)
        self.assertIsNotNone(tally, 'tally fence not found')
        self.assertIn('<id>', tally.group(0))
        self.assertIn('accepted', tally.group(0))
        self.assertIn('overridden', tally.group(0))
        self.assertNotIn('N accepted, M overridden', text, 'the old count-only tally line must not survive')

    def test_retro_counter_step_reads_the_tally_by_id(self):
        retro = read('references/guides/retro.md')
        self.assertIn('reading it by id', retro)

    def test_top_k_rule_still_names_the_confidence_field(self):
        rules_line = read('references/profile.tmpl.md').splitlines()[12]  # 1-indexed line 13
        self.assertIn('Top-K', rules_line)
        self.assertIn('confidence', rules_line)


class C7ArchetypeMechanismTests(unittest.TestCase):
    """C7: every read/write target for reference plans names `.tackle/archetypes/` or
    `~/.tackle/archetypes/`; the `#archetypes` anchor and plan-card.md's link to it resolve; the
    coverage-table recipe sharing is covered by test_coverage_table.py's SharedRecipeTests; no bare
    `eval/` path appears in the recipe text this task ships (also checked per-recipe elsewhere)."""

    TOUCHED_ARCHETYPE_FILES = (
        'references/guides/retro.md',
        'references/guides/intake-and-gate.md',
        'references/archetypes/README.md',
    )

    def test_retro_tmpl_needs_no_path_edit(self):
        """retro.tmpl.md:50 and its two anchors only point at the guide and the format doc
        (§Scope notes) -- it never names an archetype path directly, before or after this task."""
        tmpl = read('references/retro.tmpl.md')
        self.assertIn('format fixed by `references/archetypes/README.md`', tmpl)
        self.assertNotIn('.tackle/archetypes/', tmpl)

    def test_every_touched_file_names_the_new_two_scope_archetype_paths(self):
        for relative in self.TOUCHED_ARCHETYPE_FILES:
            with self.subTest(file=relative):
                text = read(relative)
                self.assertIn('.tackle/archetypes/', text)

    def test_no_file_still_names_the_old_install_path_as_a_read_or_write_target(self):
        """The only tolerated `references/archetypes/` mentions left anywhere are format/citation
        pointers to the README itself (`references/archetypes/README.md`) -- never a bare
        `references/archetypes/<name>.md` or a bare directory read/write target."""
        pattern = re.compile(r'references/archetypes/(?!README\.md)\S*')
        for relative in self.TOUCHED_ARCHETYPE_FILES + ('references/terminology.md', 'README.md'):
            with self.subTest(file=relative):
                text = read(relative)
                self.assertEqual(pattern.findall(text), [], relative)

    def test_archetypes_anchor_and_its_plan_card_link_resolve(self):
        intake = read('references/guides/intake-and-gate.md')
        self.assertIn('<a id="archetypes"></a>', intake)
        card = read('references/guides/plan-card.md')
        self.assertIn('(intake-and-gate.md#archetypes)', card)

    def test_learning_loop_read_anchor_is_unchanged(self):
        """plan-card.md links `intake-and-gate.md#learning-loop-read-if-enabled`; that anchor is
        the auto-slug of the '## Learning-loop read (if enabled)' heading, which this task's write
        scope must not rename."""
        intake = read('references/guides/intake-and-gate.md')
        self.assertIn('## Learning-loop read (if enabled)', intake)
        card = read('references/guides/plan-card.md')
        self.assertIn('intake-and-gate.md#learning-loop-read-if-enabled', card)

    def test_no_bare_eval_path_anywhere_in_the_fixture_recipe_section(self):
        """F1/N2, over the whole rewritten section (not only the extracted command): a shipped
        recipe never sends a reader to a repository-only `eval/` path (it will not exist in an
        installed copy). Scoped to '### Fixture recipe' through the next '##'/'###' heading."""
        retro = read('references/guides/retro.md')
        section = retro.split('### Fixture recipe', 1)[1].split('\n## ', 1)[0]
        self.assertNotIn('eval/', section)


class C8RetroNeverWritesTheInstallTests(unittest.TestCase):
    """C8: retro.md's rewritten '## Where results go' list names exactly the required set, for
    both project and user scope, and none of its own entries names `references/` or `SKILL.md` --
    scoped to that one list, never a whole-file grep (which would false-positive on retro.md:7's
    and retro.tmpl.md:50's legitimate format/instantiation citations, N10)."""

    REQUIRED = (
        '.tackle/profile.md',
        '~/.tackle/user-profile.md',
        '.tackle/archetypes/',
        '~/.tackle/archetypes/',
        'docs/plans/<initiative>/retro.md',
        'history.md',
    )

    def setUp(self):
        retro = read('references/guides/retro.md')
        self.section = retro.split('## Where results go', 1)[1].split('\n## ', 1)[0]
        self.bullets = '\n'.join(line for line in self.section.splitlines() if line.startswith('- ') or line.startswith('  '))

    def test_the_list_names_every_required_destination(self):
        for needle in self.REQUIRED:
            with self.subTest(needle=needle):
                self.assertIn(needle, self.bullets)

    def test_the_list_names_no_path_under_references_or_skill_md(self):
        """Scoped to the list's own bullet lines (never a whole-section or whole-file grep), so a
        surrounding sentence that merely *discusses* the install tree cannot false-positive."""
        self.assertNotIn('references/', self.bullets)
        self.assertNotIn('SKILL.md', self.bullets)

    def test_the_check_does_not_reach_retro_md_or_retro_tmpl_legitimate_citations(self):
        """Confirms those citations are still live (unflagged) and simply outside this section."""
        retro = read('references/guides/retro.md')
        self.assertIn('instantiated from `references/retro.tmpl.md`', retro)
        self.assertIn('(format: `references/archetypes/README.md`)', retro)
        self.assertNotIn('instantiated from `references/retro.tmpl.md`', self.section)
        self.assertNotIn('references/archetypes/README.md', self.section)
        tmpl = read('references/retro.tmpl.md')
        self.assertIn('format fixed by `references/archetypes/README.md`', tmpl)


if __name__ == '__main__':
    unittest.main()
