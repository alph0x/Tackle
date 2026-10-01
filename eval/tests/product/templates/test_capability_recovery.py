"""Static contract checks for installed role routing and blocker recovery instructions.

These cases consume the installed skill tree. They do not run an agent and cannot establish
feature-specific CAP/BLOCK behavior; those obligations remain separate from this text boundary.
"""
import re
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from maintaining.install_root import current_root  # noqa: E402

INSTALL = current_root(ROOT)
SKILL = (INSTALL / 'SKILL.md').read_text(encoding='utf-8')
AGENTS = (INSTALL / 'references/AGENTS.tmpl.md').read_text(encoding='utf-8')
TEAM = (INSTALL / 'references/team.tmpl.md').read_text(encoding='utf-8')
DECOMPOSE = (INSTALL / 'references/guides/decompose-and-lint.md').read_text(encoding='utf-8')
INTAKE = (INSTALL / 'references/guides/intake-and-gate.md').read_text(encoding='utf-8')
COMMUNICATION = (INSTALL / 'references/guides/communication.md').read_text(encoding='utf-8')
MIGRATE = (INSTALL / 'references/guides/migrate.md').read_text(encoding='utf-8')


def section(text, heading, next_heading=None):
    if heading not in text:
        return ''
    start = text.index(heading)
    body = text[start + len(heading):]
    if next_heading is None:
        next_heading = re.search(r'\n#{1,3} ', body)
        return body[:next_heading.start()] if next_heading else body
    return body.split(next_heading, 1)[0]


def normalized(text):
    return ' '.join(text.split())


def recovery_slots(text):
    """Check connected recovery obligations while allowing their order to vary."""
    value = normalized(text).lower()
    return {
        'expected and observed': bool(re.search(r'expected.{0,180}observed|observed.{0,180}expected', value)),
        'evidence': bool(re.search(r'\b(evidence|record)\b', value)),
        'affected work': bool(re.search(r'affected (work|task|scope)', value)),
        'owner choice': bool(re.search(r'(owner.{0,80}(choice|answer|solution))|((choice|answer|solution).{0,80}owner)', value)),
        'viable options': bool(re.search(r'(viable|available) options?', value)),
        'recommendation': bool(re.search(r'recommend(ed|ation)?', value)),
        'consequences': bool(re.search(r'consequences?', value)),
        'owner alternative': bool(re.search(r'(invite|offer).{0,100}(owner|own solution)', value)),
        'affected-only wait': bool(re.search(r'wait.{0,100}only.{0,100}affected|affected.{0,100}wait.{0,100}only', value)),
        'independent work continues': bool(re.search(r'(continue.{0,100}independent)|(independent.{0,100}continue)', value)),
        'refusal respected': bool(re.search(r'respect.{0,60}refusal|refusal.{0,60}respect', value)),
        'time is not consent': bool(re.search(r'time.{0,60}(not|never).{0,30}consent|time passing.{0,30}consent', value)),
    }


def complete_recovery(text):
    return all(recovery_slots(text).values())


class HostCapabilityRoutingTests(unittest.TestCase):
    """The role proposal uses observed host capability and binding information."""

    def test_model_map_records_states_controls_source_and_unknowns(self):
        model_map = section(AGENTS, '## Model map', '\n<a id="executor-contract-when-you-work-a-point"></a>')
        normalized_map = normalized(model_map).lower()
        self.assertIn('supported | unsupported | unknown', normalized_map)
        self.assertIn('model-binding', normalized_map)
        self.assertIn('effort-binding', normalized_map)
        self.assertIn('observed source', normalized_map)
        self.assertIn('telemetry', normalized_map)
        self.assertIn('n/a', normalized_map)
        self.assertIn('portable', normalized_map)
        self.assertIn('actual host', normalized_map)

    def test_role_proposal_uses_only_observed_models_and_binding_controls(self):
        proposal = normalized(section(DECOMPOSE, '## Model and tier proposal (compile time)')).lower()
        self.assertRegex(proposal, r'host.{0,240}before proposing roles')
        self.assertRegex(proposal, r'(model names|concrete models).{0,180}(binding|effort) controls')
        self.assertRegex(proposal, r'supported.{0,30}unsupported.{0,30}unknown')
        self.assertRegex(proposal, r'(actual available models|models actually available)')
        self.assertRegex(proposal, r'unavailable exact.{0,220}(alternative|unavailable)')
        self.assertRegex(proposal, r'(never|do not).{0,100}invent(?:ed|ing)? (?:a )?(?:vendor )?(?:equivalent|binding)')

    def test_planner_strength_depends_on_suitable_bound_tiers_and_states_one_tier_limit(self):
        proposal = normalized(section(DECOMPOSE, '## Model and tier proposal (compile time)')).lower()
        self.assertRegex(proposal, r'(stronger planner|planning always).{0,180}more than one suitable tier binds')
        self.assertRegex(proposal, r'one-tier harness.{0,100}limitation')

    def test_portable_effort_and_unexposed_telemetry_are_not_inferred(self):
        proposal = normalized(section(DECOMPOSE, '## Model and tier proposal (compile time)')).lower()
        self.assertRegex(proposal, r'portable.{0,100}(schema|effort).{0,100}actual host controls')
        self.assertRegex(proposal, r'unexposed telemetry.{0,40}n/a')

    def test_static_team_defaults_are_proposals_after_observation(self):
        binding = normalized(section(TEAM, '## Model binding', '\n## Team sizing')).lower()
        self.assertRegex(binding, r'(defaults|role table).{0,140}(proposal|starting point)')
        self.assertIn('observed model map', binding)
        self.assertIn('only supported tiers', binding)

    def test_unavailable_exact_model_witness_cannot_be_filled_by_an_invented_binding(self):
        # Fixed bad-bound witness: observed map contains only gpt-6-luna; a response calls the
        # absent gpt-6-orbit model a supported frontier binding. This case checks the installed
        # policy boundary, not whether a live model follows it.
        observed_models = {'fast': {'model': 'gpt-6-luna', 'status': 'supported', 'source': 'host map'}}
        requested_model = 'gpt-6-orbit'
        bad_response = 'Bind gpt-6-orbit as the supported frontier model.'
        self.assertNotIn(requested_model, {entry['model'] for entry in observed_models.values()})
        self.assertIn(requested_model, bad_response)
        proposal = normalized(section(DECOMPOSE, '## Model and tier proposal (compile time)')).lower()
        self.assertRegex(proposal, r'only.{0,80}actual available models')
        self.assertRegex(proposal, r'unavailable exact.{0,220}(alternative|unavailable)')
        self.assertRegex(proposal, r'never.{0,80}invent')


class ActionableRecoveryTests(unittest.TestCase):
    """Blockers offer authorized choices and wait only on the affected work."""

    def test_installed_recovery_paragraph_connects_evidence_choice_and_wait_effect(self):
        recovery = section(COMMUNICATION, '## Actionable blocker recovery', '\n## Match the message to the situation')
        paragraph = next((part for part in recovery.split('\n\n') if 'expected' in part.lower()), '')
        slots = recovery_slots(paragraph)
        missing = [name for name, present in slots.items() if not present]
        self.assertEqual(missing, [], 'missing connected recovery obligations: %s' % ', '.join(missing))

    def test_reordered_valid_alternative_keeps_the_same_recovery_effects(self):
        alternate = (
            'Evidence: the local profile is absent. The observed result was “file missing”; the '
            'expected result was a readable model map. I recommend waiting for the owner to name '
            'a source, because a guessed model would be unsafe; another viable option is using '
            'the already observed Luna binding, with the consequence that the planner stays '
            'one-tier. This blocks affected work in role selection only. Continue independent '
            'work; wait only on that affected work, invite the owner’s own solution, respect refusal, and do not '
            'treat time passing as consent.'
        )
        slots = recovery_slots(alternate)
        missing = [name for name, present in slots.items() if not present]
        self.assertEqual(missing, [], 'alternate wording lost recovery effects: %s' % ', '.join(missing))

    def test_keyword_impostor_does_not_satisfy_connected_recovery_contract(self):
        impostor = (
            'Capability is supported. Options, recommendations, evidence and consequences are '
            'important. The owner can wait. Continue every task while the blocked capability is '
            'being resolved, because time has passed.'
        )
        self.assertFalse(complete_recovery(impostor))

    def test_missing_prerequisite_stops_dependent_discovery_and_links_recovery(self):
        intake = section(INTAKE, '# Step 1 — Intake', '\n# Step 2')
        check_at = intake.index('Check named owner prerequisites')
        missing_at = intake.index('A confirmed missing owner prerequisite')
        stop_at = intake.index('Do not read intake or run workspace inventories')
        self.assertLess(check_at, missing_at)
        self.assertLess(missing_at, stop_at)
        blocked = normalized(intake[missing_at:stop_at]).lower()
        self.assertIn('affected work', blocked)
        self.assertIn('communication.md#actionable-blocker-recovery', blocked)
        self.assertIn('independently authorized work continue', normalized(intake[stop_at:]).lower())

    def test_same_release_migration_checklist_adopts_observed_capability_map(self):
        migration = normalized(MIGRATE).lower()
        self.assertRegex(migration, r'active 9\.0\.0 workspace adopts 9\.0\.1.{0,140}same-release checklist below')
        self.assertIn('## v9.0.0 → v9.0.1 checklist', MIGRATE)
        checklist = normalized(section(MIGRATE, '## v9.0.0 → v9.0.1 checklist')).lower()
        for requirement in (
                'exposed model names', 'tier capabilities', 'binding and effort controls',
                'supported', 'unsupported', 'unknown', '`n/a`', 'portable effort tokens',
                'stronger planner', 'only one tier', 'affected-only wait', 'closed task records'):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, checklist)


if __name__ == '__main__':
    unittest.main()
