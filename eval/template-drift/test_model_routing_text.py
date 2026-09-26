"""Text-presence checks for the per-task model routing rule: dispatch, the capped capability
escalation, the once-per-initiative confirmation, and the routing default's wording (C5-C6).

Mechanical only: every required element of the dispatch/escalation rule is present, verbatim or as a
required literal token, in the shipped guide and template text. Whether the wording is a faithful
paraphrase of the owner's escalation policy is the fresh reviewer's job, not this file's; this file
only checks that the required words are there.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN_CARD = (ROOT / 'references/guides/run-card.md').read_text(encoding='utf-8')
RUN_MD = (ROOT / 'references/guides/run.md').read_text(encoding='utf-8')
DECOMPOSE = (ROOT / 'references/guides/decompose-and-lint.md').read_text(encoding='utf-8')
TEAM = (ROOT / 'references/team.tmpl.md').read_text(encoding='utf-8')
AGENTS = (ROOT / 'references/AGENTS.tmpl.md').read_text(encoding='utf-8')
USAGE = (ROOT / 'references/guides/usage-observability.md').read_text(encoding='utf-8')
TASK_TEMPLATE = (ROOT / 'references/task.tmpl.md').read_text(encoding='utf-8')


def escalation_limits_section():
    after = RUN_MD.split('## Tier dispatch and escalation limits', 1)[1]
    return after.split('\n## ', 1)[0]


class RunCardDispatchAndEscalationTests(unittest.TestCase):
    """C5: the RUN card states the core dispatch/escalation rule and links to the full limits."""

    def test_preflight_step_points_to_the_tier_model_map_binding(self):
        self.assertIn('4. **Preflight.**', RUN_CARD)
        preflight = RUN_CARD.split('4. **Preflight.**', 1)[1].split('5. **Intent', 1)[0]
        self.assertIn('compiled Tier', preflight)
        self.assertIn('model-map binding', preflight)
        self.assertIn('run.md#tier-dispatch-and-escalation-limits', preflight)

    def test_the_linked_run_md_section_states_bound_model_and_unsupported(self):
        # The card's Preflight clause is a pointer only; "bound model" and `unsupported` are the
        # linked run.md section's job, not the card's.
        section = escalation_limits_section()
        self.assertIn('bound model', section)
        self.assertIn('`unsupported`', section)
        self.assertIn('never an invented binding', section)

    def test_correct_within_budget_states_a_declared_once_only_capability_escalation(self):
        self.assertIn('7. **Correct within budget.**', RUN_CARD)
        step7 = RUN_CARD.split('7. **Correct within budget.**', 1)[1].split('8. **Close.**', 1)[0]
        self.assertIn('implementation fault is corrected', step7)
        self.assertIn('capability failure', step7)
        self.assertIn('declared in the brief', step7)
        self.assertIn('only once', step7)
        self.assertIn('tier', step7.lower())

    def test_task_pool_first_validation_wording_is_scoped_to_implementation_faults(self):
        # The pre-existing "first validation is not a cycle" sentence sits right next to the new
        # state-table row and must not read as carving out the capability escalation's own
        # first-validation charge (run.md's "always, including on the task's first validation").
        step7 = RUN_CARD.split('7. **Correct within budget.**', 1)[1].split('8. **Close.**', 1)[0]
        self.assertIn('first validation of an implementation fault', ' '.join(step7.split()))

    def test_dispatch_and_escalation_both_link_to_the_run_md_depth_anchor(self):
        self.assertEqual(RUN_CARD.count('run.md#tier-dispatch-and-escalation-limits'), 3,
                         'expected the Preflight link, the Correct-within-budget link, and the Depth entry')

    def test_state_table_has_its_own_declared_escalation_row_not_a_reused_one(self):
        table = RUN_CARD.split('## State transitions', 1)[1].split('## Depth', 1)[0]
        self.assertIn('| Checking | In progress | Declared capability escalation (once per task) | One cycle, always |',
                      table)
        self.assertIn('| Checking | In progress | Implementation fault | One cycle; none for the first validation |',
                      table, 'the existing Implementation-fault row must stay unchanged, not reused')


class RunMdEscalationLimitsTests(unittest.TestCase):
    """C5: the anchored run.md section carries every element the card's link points to."""

    def test_anchor_and_heading_exist(self):
        self.assertIn('<a id="tier-dispatch-and-escalation-limits"></a>', RUN_MD)
        self.assertIn('## Tier dispatch and escalation limits', RUN_MD)

    def test_required_tokens_are_all_present(self):
        section = escalation_limits_section()
        for token in ('declared', 'once', 'next', 'never', 'unbound', 'topmost', 'effort', 'control'):
            with self.subTest(token=token):
                self.assertIn(token, section.lower())

    def test_never_appears_for_each_of_unbound_topmost_and_control(self):
        section = escalation_limits_section().lower()
        # The unbound-tier stop, the topmost-tier ceiling and the control-arm exclusion are each
        # their own "never", not one word shared across all three.
        self.assertGreaterEqual(section.count('never'), 3)

    def test_states_the_recording_shape(self):
        section = escalation_limits_section()
        self.assertIn('Attempts', section)
        self.assertIn('Run ID', section)
        self.assertIn('history.md', section)


class DecomposeAndLintWordingTests(unittest.TestCase):
    """C5: the tier proposal states the planning-tier rule, with no plan-id leak."""

    def test_model_and_tier_proposal_section_exists(self):
        self.assertIn('## Model and tier proposal (compile time)', DECOMPOSE)

    def section(self):
        after = DECOMPOSE.split('## Model and tier proposal (compile time)', 1)[1]
        return after

    def test_states_the_planning_tier_rule(self):
        section = ' '.join(self.section().split())
        self.assertIn("Planning always runs on a more capable tier than the Executor's", section)
        self.assertNotIn('not yet a fixed rule', section)

    def test_states_the_model_map_read_and_the_tier_and_effort_proposal(self):
        section = ' '.join(self.section().split())
        for phrase in ('AGENTS.md` model map', 'once per initiative', '**Tier**', '**Effort**',
                       'cheapest bindable tier', '**Tier reason**'):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, section)

    def test_deviation_reason_trigger_covers_tier_or_effort(self):
        # The owner's model-and-effort reconfirmation policy covers effort, not Tier alone.
        section = ' '.join(self.section().split())
        self.assertIn('deviation from the routine default, of Tier or Effort, needs a reason', section)


class TeamAndAgentsTemplateTests(unittest.TestCase):
    """C6: the per-task override clause and the once-per-initiative confirmation line."""

    def test_team_template_connects_the_static_table_to_the_per_task_override(self):
        self.assertIn('per-task override', TEAM)
        self.assertIn('**Tier**', TEAM)
        self.assertIn('**Tier reason**', TEAM)

    def test_team_template_override_trigger_covers_effort_deviation(self):
        # The confirmed-again trigger must not be Tier-scoped only.
        sentence = TEAM.split('per-task override', 1)[1].split('.', 1)[0]
        self.assertIn('Effort', sentence)

    def test_agents_template_has_the_confirmed_for_this_initiative_line(self):
        self.assertIn('**Confirmed for this initiative**:', AGENTS)
        clause = AGENTS.split('**Confirmed for this initiative**:', 1)[1].split('\n\n', 1)[0]
        self.assertIn('Tier reason', clause)

    def test_agents_template_confirmation_trigger_covers_effort_deviation(self):
        clause = AGENTS.split('**Confirmed for this initiative**:', 1)[1].split('\n\n', 1)[0]
        self.assertIn('Effort', clause)


class TaskTemplateTierReasonFieldTests(unittest.TestCase):
    """The field text itself names an Effort deviation, not only a Tier one."""

    def test_tier_reason_field_text_covers_effort_deviation(self):
        after = TASK_TEMPLATE.split('- **Tier reason**:', 1)[1].split('- **Escalation**:', 1)[0]
        self.assertIn('Effort', after)


class UsageObservabilityTests(unittest.TestCase):
    """C5: Attempts now names a declared capability escalation."""

    def test_attempts_sentence_names_the_declared_capability_escalation(self):
        sentence = USAGE.split('Attempts records', 1)[1].split('. ', 1)[0]
        self.assertIn('capability escalation', sentence)
        self.assertIn('once', sentence)

    def test_attempts_sentence_first_validation_wording_is_unambiguous(self):
        # The capability escalation charges a cycle even on the first validation; the adjacent
        # "do not count" carve-out is scoped to an implementation fault's own checks.
        sentence = ' '.join(USAGE.split('Attempts records', 1)[1].split('. ', 1)[0].split())
        self.assertIn("always, including on the task's first validation", sentence)
        self.assertIn('repeated tests of an implementation fault do not count', sentence)


class TaskTemplateFieldsTests(unittest.TestCase):
    """The three new optional fields sit immediately after Effort, in the Contract's exact order."""

    def test_tier_tier_reason_and_escalation_follow_effort_in_order(self):
        after_effort = TASK_TEMPLATE.split('- **Effort**:', 1)[1]
        tier_at = after_effort.index('- **Tier**:')
        reason_at = after_effort.index('- **Tier reason**:')
        escalation_at = after_effort.index('- **Escalation**:')
        budget_at = after_effort.index('- **Budget**:')
        self.assertTrue(tier_at < reason_at < escalation_at < budget_at)


if __name__ == '__main__':
    unittest.main()
