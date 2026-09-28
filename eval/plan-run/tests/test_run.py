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
            "`board.md`\nis the canonical current state", "`log.md` is append-only history",
        ]:
            self.assertIn(phrase, RUN)
        self.assertEqual(RUN.count("## State transitions"), 1)
        self.assertIn("All tasks passing is insufficient", RUN)

    def test_docs_bind_templates_to_run_without_competing_loops(self):
        team = (ROOT.parent.parent / "references/team.tmpl.md").read_text()
        agents = (ROOT.parent.parent / "references/AGENTS.tmpl.md").read_text()
        coordinator = (ROOT.parent.parent / "references/coordinator.tmpl.md").read_text()
        for text in [team, agents, coordinator]:
            self.assertIn("references/guides/run.md", text)
            self.assertNotIn("Pre-wave verification gate", text)
            self.assertNotIn("Rework bound", text)
        self.assertIn("non-goals are explicit exclusions", agents)
        self.assertIn("Initiative unowned-integration cycles", coordinator)


if __name__ == "__main__":
    unittest.main()
