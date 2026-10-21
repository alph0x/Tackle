"""Horizon-scoped readiness: the verify guide defines the next wave and verifies it at full depth while later
work is checked at interface level, the decomposition guide limits internal detail to next-wave briefs, and the
PLAN card's step 5 points there. Also the MEDIUM part of the executor-centric severity sentence. Text shape only:
these checks protect the guides an agent reads, not the agent's obedience to them.
"""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from maintaining.install_root import current_root  # noqa: E402

GUIDES = current_root(ROOT) / 'references/guides'


def section(text, heading):
    out, inside = [], False
    for line in text.splitlines():
        if line == heading:
            inside = True
            continue
        if inside and line.startswith('## '):
            break
        if inside:
            out.append(line)
    return ' '.join(' '.join(out).split())


def horizon_ok(verify_text):
    body = section(verify_text, '## Milestone readiness')
    return all(phrase in body for phrase in (
        '**Horizon depth.**',
        'The next wave is the open tasks whose every dependency is Complete, In progress or Checking, or that depend on nothing.',
        'PLAN prepares the next wave at `**Detail**: full` and leaves later tasks Draft at `**Detail**: interface`.',
        'Verification runs at full depth only on the selected next-wave tasks',
        'requirement ownership in the coverage matrix, dependency sanity, the symbol ledger and decision ownership',
        'is out of scope and is dismissed by this rule.',
        'An interface brief is never Ready to run.'))


def step5(card_text):
    return card_text.split('5. **Decompose to the fewest tasks.**', 1)[1].split('6. **Lint.**', 1)[0]


class HorizonReadinessTests(unittest.TestCase):
    def test_verify_guide_defines_the_next_wave_and_its_depth(self):
        self.assertTrue(horizon_ok((GUIDES / 'verify.md').read_text()))

    def test_decomposition_limits_internal_detail_to_the_next_wave(self):
        body = section((GUIDES / 'decompose-and-lint.md').read_text(), '## Preparation horizon')
        self.assertIn('only in next-wave briefs', body)
        self.assertIn('(verify.md#milestone-readiness)', body)

    def test_plan_card_step_5_points_to_the_horizon_rule(self):
        text = step5((GUIDES / 'plan-card.md').read_text())
        self.assertIn('Prepare only the next wave at `**Detail**: full`', text)
        self.assertIn('(verify.md#milestone-readiness)', text)

    def test_severity_states_the_medium_executor_impact(self):
        flat = ' '.join((GUIDES / 'verify.md').read_text().split('## Step 0')[0].split())
        self.assertIn('It is MEDIUM when the executor would likely produce a wrong result that the stated checks would accept.', flat)


class OracleDiscriminationTests(unittest.TestCase):
    def test_horizon_words_outside_their_section_are_rejected(self):
        text = (GUIDES / 'verify.md').read_text()
        self.assertTrue(horizon_ok(text))
        moved = text.replace('## Milestone readiness\n', '## Milestone readiness\n\n## Elsewhere\n', 1)
        self.assertFalse(horizon_ok(moved))


if __name__ == '__main__':
    unittest.main()
