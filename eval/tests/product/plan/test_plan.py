"""The PLAN side: the plan template keeps the section order its consumers read."""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[4]
import sys
sys.path.insert(0, str(ROOT))
from maintaining.install_root import current_root  # noqa: E402
INSTALL = current_root(ROOT)



class PlanProtocol(unittest.TestCase):
    def test_plan_template_keeps_stable_section_consumers(self):
        template = (INSTALL / "references/plan.tmpl.md").read_text()
        headings = [
            "## 5. Task decomposition",
            "## 6. Readiness and acceptance",
            "### 6.1 Universal per-task acceptance",
            "### 6.2 Initiative-level acceptance",
        ]
        positions = [template.index(heading) for heading in headings]
        self.assertEqual(positions, sorted(positions))
        self.assertLess(template.index("### Behavior and outputs"), positions[0])
        self.assertLess(template.index("### Acceptance and test strategy"), positions[0])
