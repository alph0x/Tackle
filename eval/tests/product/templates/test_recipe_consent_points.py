"""The recipe consent rule stands where the agent decides to save or run a guide's program.

Guarantee: every Python program embedded in an installed guide is preceded by the stop line that asks for the
owner's explicit authorization (or a recorded grant) and names the honest alternatives, with only an anchor or
marker line between that stop line and the fence; and the RUN card's Check step carries the same rule. A guide
that gains a program without the stop line, or a card that drops the sentence, fails here.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from maintaining.install_root import current_root  # noqa: E402

INSTALL = current_root(ROOT)
GUIDES = INSTALL / 'references/guides'
STOP = "**Stop before the program below.** Save or run it only with the owner's explicit authorization for this use,"
REST = ("or under a grant in [recipe consent](../recipes/README.md#consent). Otherwise use an equivalent harness",
        "capability or the project's own tools, or report the record unavailable.")


class RecipeConsentPoints(unittest.TestCase):
    def test_every_guide_program_is_preceded_by_the_stop_line(self):
        found = 0
        for guide in sorted(GUIDES.glob('*.md')):
            lines = guide.read_text(encoding='utf-8').split('\n')
            for k, line in enumerate(lines):
                if not line.startswith('```python'):
                    continue
                found += 1
                j = k
                while j > 0 and (lines[j - 1].startswith('<a id=') or lines[j - 1].startswith('<!--')):
                    j -= 1
                with self.subTest(guide=guide.name, line=k + 1):
                    self.assertEqual(lines[j - 1], '')
                    self.assertEqual(lines[j - 4:j - 1], [STOP, REST[0], REST[1]])
        self.assertGreaterEqual(found, 8)

    def test_the_run_card_check_step_carries_the_rule(self):
        card = ' '.join((GUIDES / 'run-card.md').read_text(encoding='utf-8').split())
        step = card.split('6. **Check.**', 1)[1].split('7. **', 1)[0]
        self.assertIn("Before saving or running a guide's program to make a record, get the owner's explicit authorization.", step)
        self.assertIn("Without it, use a harness capability or the project's tools, or report the record unavailable.", step)


if __name__ == '__main__':
    unittest.main()
