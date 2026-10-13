from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[5]
import sys
sys.path.insert(0, str(ROOT))
from maintaining.install_root import current_root  # noqa: E402
INSTALL = current_root(ROOT)

TASK_TEMPLATE = 'references/task.tmpl.md'
PLAN_TEMPLATE = 'references/plan.tmpl.md'
DECOMPOSE = 'references/guides/decompose-and-lint.md'
DESIGN_CONTRACT = 'references/guides/design-and-contract.md'

SCENARIO_CASE = (
    'A case may also be a scenario: `#### Scenario: <name>`, then `- WHEN`, `- THEN` and `- Check:` lines; '
    '`- GIVEN` and `- AND` are optional. The Check names a command with its pass condition, or '
    '`review: <rubric> by <reviewer role>`. A scenario without a Check is not ready.'
)
SCENARIO_BEHAVIOR = (
    'A behavior may also be written as WHEN/THEN scenarios; each names its Check, as in `task.tmpl.md`.'
)
SCENARIO_READINESS = (
    '- every WHEN/THEN scenario names its Check: a command with its pass condition, or a named rubric and '
    'reviewer role; `TBD`, a cross-reference or prose is not a Check;'
)
SCENARIO_CONTRACT = (
    'A scenario-form case counts only with its Check; a scenario without one is a readiness gap.'
)


def read(name):
    return (INSTALL / name).read_text(encoding='utf-8')


def section(text, heading, marker='\n## '):
    start = text.index(heading)
    end = text.find(marker, start + len(heading))
    return text[start:] if end < 0 else text[start:end]


class ScenarioChecks(unittest.TestCase):
    def test_task_template_offers_scenario_form(self):
        text = read(TASK_TEMPLATE)
        self.assertIn(SCENARIO_CASE, text)
        start = text.index('| {{invalid}} |')
        at = text.index(SCENARIO_CASE)
        end = text.index('State exact output requirements')
        self.assertTrue(start < at < end)

    def test_plan_template_points_to_scenario_form(self):
        text = read(PLAN_TEMPLATE)
        self.assertIn(SCENARIO_BEHAVIOR, text)
        body = section(text, '### Behavior and outputs', marker='\n### ')
        self.assertIn(SCENARIO_BEHAVIOR, body)

    def test_readiness_blocks_a_checkless_scenario(self):
        text = read(DECOMPOSE)
        self.assertIn(SCENARIO_READINESS, text)
        body = text[text.index('## Step 6.75 — Integrated readiness validation'):text.index('## Preparation horizon')]
        self.assertIn(SCENARIO_READINESS, body)
        self.assertIn('`TBD`', SCENARIO_READINESS)

    def test_design_contract_requires_the_check(self):
        text = read(DESIGN_CONTRACT)
        self.assertIn(SCENARIO_CONTRACT, text)
        body = section(text, '## Acceptance and test strategy')
        self.assertIn(SCENARIO_CONTRACT, body)


if __name__ == '__main__':
    unittest.main()
