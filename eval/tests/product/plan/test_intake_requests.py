"""Explore requests write nothing and enter PLAN only on a yes; intake classifies update-vs-new before writing."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from maintaining.install_root import current_root  # noqa: E402

INSTALL = current_root(ROOT)
SKILL_PATH = INSTALL / "SKILL.md"
INVOCATION_PATH = INSTALL / "references/guides/invocation.md"
INTAKE_PATH = INSTALL / "references/guides/intake-and-gate.md"
STEP_HEADING = "# Step 1.5 — Anchor the intake before sizing"
CONTINUING_HEADING = "## Continuing authorized work"

EXPLORE_SENTENCE = (
    " An explore request reads, ranks options and recommends one, writes nothing, and enters PLAN only on an explicit yes."
)
GUIDE_MAP_LINE = (
    "Required behavior across plans: [requirements base](references/guides/requirements-base.md); "
    "several repositories: [multi-repo workspace](references/guides/scaffold.md#multi-repository-workspace)."
)
EXPLORE_SECTION = """<a id="explore"></a>
## Explore

An explore request (`explore`, `explorar`, "think it through first") is PLAN intake that writes nothing.
Read the repository and the named inputs, then answer with findings cited at `file:line`, two to four ranked options with their tradeoffs, and one recommendation.
Explore writes no workspace, seed, profile, requirements base, delta or source; it ends by offering PLAN, and only an explicit yes enters PLAN.
A capture request writes only the artifacts the owner named, through the ordinary scaffold consent.
A request to implement during explore is not acted on there; offer PLAN or RUN with explicit intent instead.

"""
UPDATE_OR_NEW_SECTION = """<a id="update-or-new"></a>
## Update the plan or start a new one

When a request touches an active workspace's goal, classify it before writing anything.
The same goal with a better approach or a corrected detail updates this plan; a changed acceptance needs a superseding decision.
A narrower scope updates this plan to the smaller scope, closes it, and starts a new initiative for the rest.
A different problem, or scope grown into different work, starts a new initiative; never repurpose the old one silently.
When the classification is ambiguous, it is the owner's product decision: ask with a recommendation.

"""


class IntakeRequests(unittest.TestCase):
    def read(self, path):
        return path.read_text(encoding="utf-8")

    def test_skill_names_the_explore_request(self):
        lines = self.read(SKILL_PATH).split("\n")
        self.assertIn("Bare invocation or help offers choices without writes.", lines[12])
        self.assertIn("offers choices without writes." + EXPLORE_SENTENCE, lines[12])

    def test_skill_links_the_new_guides(self):
        text = self.read(SKILL_PATH)
        self.assertIn(GUIDE_MAP_LINE, text.split("\n"))
        self.assertTrue((INSTALL / "references/guides/requirements-base.md").is_file())
        scaffold = INSTALL / "references/guides/scaffold.md"
        self.assertTrue(scaffold.is_file())
        self.assertIn('<a id="multi-repository-workspace"></a>', self.read(scaffold))

    def test_invocation_explore_writes_nothing(self):
        text = self.read(INVOCATION_PATH)
        self.assertIn(EXPLORE_SECTION, text)
        self.assertLess(text.index(EXPLORE_SECTION), text.index(CONTINUING_HEADING))
        self.assertIn(
            "Explore writes no workspace, seed, profile, requirements base, delta or source; "
            "it ends by offering PLAN, and only an explicit yes enters PLAN.",
            text,
        )

    def test_intake_classifies_update_or_new(self):
        text = self.read(INTAKE_PATH)
        self.assertIn(UPDATE_OR_NEW_SECTION, text)
        self.assertLess(text.index(UPDATE_OR_NEW_SECTION), text.index(STEP_HEADING))

    def test_entry_stays_within_budget(self):
        self.assertLessEqual(len(self.read(SKILL_PATH).split()), 1100)


if __name__ == "__main__":
    unittest.main()
