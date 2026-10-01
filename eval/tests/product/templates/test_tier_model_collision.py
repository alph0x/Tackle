"""A next tier whose model map binding collides with the model actually used for the current,
failed attempt is unavailable, exactly like an unbound tier: the task stops with evidence and returns
to the planner or owner, with no skip to a further tier either way.

Comparing against the model actually used, rather than "the current tier's bound model", keeps the
check well-defined even when the current tier itself was unbindable and dispatched through the
existing fallback path (which already records the model actually used).

Reuses test_model_routing_text.py's escalation_limits_section() instead of re-reading run.md, so this
file never re-implements the anchor/section extraction it already provides.
"""
import unittest

from test_model_routing_text import escalation_limits_section


class SameModelEscalationTests(unittest.TestCase):
    """The anchored run.md section states the same-model collision, its model-id comparison, the
    fallback-dispatch coverage, and the shared no-skip-further outcome."""

    def test_states_the_same_model_collision_is_unavailable(self):
        section = ' '.join(escalation_limits_section().split())
        self.assertIn(
            "a next tier whose bound model id matches the model actually used for the failed attempt "
            "— both stop the task with evidence and return to the planner or owner instead",
            section)

    def test_states_the_comparison_is_by_model_id(self):
        section = ' '.join(escalation_limits_section().split())
        self.assertIn('bound model id matches the model actually used for the failed attempt', section)

    def test_states_no_skip_to_a_further_tier(self):
        section = ' '.join(escalation_limits_section().lower().split())
        self.assertIn('never skipping to a further tier', section)

    def test_the_comparison_reuses_the_existing_fallback_vocabulary(self):
        # "the model actually used" is not new vocabulary invented for this clause — it is the same
        # term the Preflight paragraph already uses for an unbindable tier's fallback dispatch, so the
        # comparison stays well-defined even when the current tier itself was unbindable.
        section = ' '.join(escalation_limits_section().split())
        self.assertIn('An unbindable Tier records `unsupported` and the model actually used, '
                      'never an invented binding', section)
        self.assertIn('bound model id matches the model actually used for the failed attempt', section)


if __name__ == '__main__':
    unittest.main()
