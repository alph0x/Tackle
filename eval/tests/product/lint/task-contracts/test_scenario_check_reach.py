from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[5]
import sys
sys.path.insert(0, str(ROOT))
from maintaining.install_root import current_root  # noqa: E402
INSTALL = current_root(ROOT)

PLAN_CARD = 'references/guides/plan-card.md'
TASK_TEMPLATE = 'references/task.tmpl.md'

READINESS_TEXT = (
    ' A WHEN/THEN case whose Check is `TBD`, a cross-reference or prose also blocks it from Ready to run.'
)
TEMPLATE_ANCHOR = 'A scenario without a Check is not ready.'
TEMPLATE_TEXT = ' `TBD`, a cross-reference or prose is not a Check.'


def read(name):
    return (INSTALL / name).read_text(encoding='utf-8')


class ScenarioCheckReach(unittest.TestCase):
    def test_plan_card_readiness_blocks_an_unchecked_scenario(self):
        text = read(PLAN_CARD)
        start = text.index('7. **Readiness validation.**')
        end = text.index('Three of this')
        self.assertIn('and a LOW finding is advisory.' + READINESS_TEXT, text)
        at = text.index('and a LOW finding is advisory.' + READINESS_TEXT)
        self.assertTrue(start < at < end)

    def test_task_template_names_the_cross_reference(self):
        lines = [line for line in read(TASK_TEMPLATE).splitlines() if TEMPLATE_ANCHOR in line]
        self.assertEqual(len(lines), 1)
        self.assertIn(TEMPLATE_ANCHOR + TEMPLATE_TEXT, lines[0])


if __name__ == '__main__':
    unittest.main()
