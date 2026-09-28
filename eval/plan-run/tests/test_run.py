"""The RUN side: one state machine and an integrated close bar in the RUN card, and templates bound
to RUN without competing loops."""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
# The RUN chain: the RUN card and its depth, run.md.
RUN = "\n".join((ROOT.parent.parent / "references/guides" / name).read_text()
                for name in ("run-card.md", "run.md"))


class RunProtocol(unittest.TestCase):
    def test_protocol_has_one_state_machine_and_integrated_close_bar(self):
        for phrase in [
            "single execution protocol", "explicit execution intent", "| Ready to run | In progress |",
            "the task check", "the affected integration checks", "deliverable acceptance", "complete",
            "with `migrate first`",
        ]:
            self.assertIn(phrase, RUN)
        self.assertEqual(RUN.count("## State transitions"), 1)
        self.assertIn("All tasks passing is insufficient", RUN)

    def test_docs_bind_templates_to_run_without_competing_loops(self):
        team = (ROOT.parent.parent / "references/team.tmpl.md").read_text()
        agents = (ROOT.parent.parent / "references/AGENTS.tmpl.md").read_text()
        current_work = (ROOT.parent.parent / "references/current-work.tmpl.md").read_text()
        for text in [team, agents]:
            self.assertIn("references/guides/run.md", text)
            self.assertNotIn("Pre-wave verification gate", text)
            self.assertNotIn("Rework bound", text)
        self.assertIn("non-goals are explicit exclusions", agents)
        self.assertNotIn("Rework bound", current_work)
        self.assertIn("Initiative unowned-integration cycles", current_work)

    def test_run_guidance_refuses_an_older_workspace_before_its_first_write(self):
        references = ROOT.parent.parent / "references"
        card = " ".join((references / "guides/run-card.md").read_text().split())
        refusal = card.index("stop with `migrate first` before any write unless it declares `Schema: tackle-workspace/5`")
        self.assertLess(card.index("1. **Read.**"), refusal)
        self.assertLess(refusal, card.index("3. **Claim.**"))
        focused = " ".join((references / "lite-plan.tmpl.md").read_text().split())
        stop = focused.index("Before any write, stop with `migrate first`")
        self.assertLess(focused.index("1. **Prepare.**"), stop)
        self.assertLess(stop, focused.index("create plan.md, history.md and resource-usage.md"))
        status = " ".join((references / "guides/status.md").read_text().split())
        self.assertIn("On a workspace that reads `migrate first`, the handoff writes nothing", status)
        self.assertIn("a bucket other than `5`, or a Focused plan on older paths, reads `migrate first`", status)


if __name__ == "__main__":
    unittest.main()
