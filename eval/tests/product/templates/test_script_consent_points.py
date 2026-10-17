"""The script consent rule stands where a guide sends the agent to a script.

Guarantee: every installed guide that links a script under `scripts/` also links the script consent and says
that running or importing it needs the owner's explicit authorization or a grant under that consent; no
installed guide or template holds a fenced Python example over 60 words; and the RUN card's Check step carries the same
rule. A guide that gains a script link without the consent link, or a card that drops the sentence, fails here.
"""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from maintaining.install_root import current_root  # noqa: E402

INSTALL = current_root(ROOT)
GUIDES = INSTALL / 'references/guides'
SCRIPT_LINK = re.compile(r'\]\(((?:\.\./)+scripts/[^)#]*\.py)\)')
CONSENT_LINK = '](../../scripts/README.md#consent)'
# These guides only name a script: the run card's Check step carries the rule (tested below), and the intake
# guide names the file the state script reads while system-one.md holds its run and import instructions.
NAMES_ONLY = {'run-card.md', 'intake-and-gate.md'}


class ScriptConsentPoints(unittest.TestCase):
    def test_every_guide_that_links_a_script_links_the_script_consent(self):
        linked = 0
        for guide in sorted(GUIDES.glob('*.md')):
            if guide.name in NAMES_ONLY:
                continue
            text = guide.read_text(encoding='utf-8')
            targets = SCRIPT_LINK.findall(text)
            if not targets:
                continue
            linked += 1
            with self.subTest(guide=guide.name):
                self.assertIn(CONSENT_LINK, text)
                for target in targets:
                    self.assertTrue((GUIDES / target).resolve().is_file(), target)
        self.assertGreaterEqual(linked, 10)

    def test_no_installed_markdown_holds_a_fenced_python_program_over_sixty_words(self):
        fence = re.compile(r'(?ms)^```(?:python|py)\b[^\n]*\n(.*?)^```')
        for path in sorted((INSTALL / 'references').rglob('*.md')) + [INSTALL / 'SKILL.md']:
            for match in fence.finditer(path.read_text(encoding='utf-8')):
                with self.subTest(path=path.name):
                    self.assertLessEqual(len(match.group(1).split()), 60)

    def test_the_run_card_check_step_carries_the_rule(self):
        card = ' '.join((GUIDES / 'run-card.md').read_text(encoding='utf-8').split())
        step = card.split('6. **Check.**', 1)[1].split('7. **', 1)[0]
        self.assertIn("Before running or importing a script to make a record, get the owner's explicit authorization.", step)
        self.assertIn("Without it, use a harness capability or the project's tools, or report the record unavailable.", step)


if __name__ == '__main__':
    unittest.main()
