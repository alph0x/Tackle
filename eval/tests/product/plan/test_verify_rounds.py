"""The verify guide's round protocol: a multi-round verification keeps a finding ledger with stable ids and
four states, re-checks open findings before admitting new ones, keeps settled decisions out of scope, stops
after a round with no new HIGH or MEDIUM finding or at a cap of three rounds, and re-verifies the diff after
fixes. Severity weighs executor impact. The PLAN card and the scaffold point to the protocol. Text shape
only: these checks protect the guide an agent reads, not the agent's obedience to it.
"""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from maintaining.install_root import current_root  # noqa: E402

GUIDES = current_root(ROOT) / 'references/guides'
HEADER = '| Finding | Round | Severity | Task | Evidence | State | Reference |'


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
    return '\n'.join(out)


def rounds_ok(verify_text):
    body = section(verify_text, '## Verification rounds')
    flat = ' '.join(body.split())
    return (HEADER in body and '`findings.md`' in flat
            and all('`%s`' % state in flat for state in ('open', 'fixed', 'dismissed', 'settled'))
            and 're-checks each `open` finding by its recorded evidence first' in flat
            and 'deduplicated against every row in any state' in flat
            and 'out of scope for redesign' in flat
            and 'no new HIGH or MEDIUM finding and no `open` HIGH or MEDIUM finding' in flat
            and 'At most three rounds run' in flat and '`Verify round cap: N`' in flat
            and 'rerun every lint row' in flat and 'verify only the diff since the round began' in flat)


def severity_ok(verify_text):
    flat = ' '.join(verify_text.split('## Step 0')[0].split())
    return ('HIGH only when an executor following the brief literally would fail or stall' in flat
            and 'LOW when it has no executor impact' in flat)


class VerifyRoundsTests(unittest.TestCase):
    def test_verify_guide_states_the_round_protocol_in_its_section(self):
        self.assertTrue(rounds_ok((GUIDES / 'verify.md').read_text()))

    def test_severity_weighs_executor_impact_beside_the_certainty_classes(self):
        self.assertTrue(severity_ok((GUIDES / 'verify.md').read_text()))

    def test_plan_card_and_scaffold_point_to_the_protocol(self):
        card = (GUIDES / 'plan-card.md').read_text()
        scaffold = section((GUIDES / 'scaffold.md').read_text(), '## Depth artifacts')
        self.assertIn('(verify.md#verification-rounds)', card.split('**Stop rule.**')[0])
        self.assertIn('`findings.md`', scaffold)
        self.assertIn('<a id="verification-rounds"></a>', (GUIDES / 'verify.md').read_text())


class OracleDiscriminationTests(unittest.TestCase):
    def test_protocol_words_outside_the_section_are_rejected(self):
        text = (GUIDES / 'verify.md').read_text()
        self.assertTrue(rounds_ok(text))
        moved = text.replace('## Verification rounds\n', '## Verification rounds\n\n## Elsewhere\n', 1)
        self.assertFalse(rounds_ok(moved))

    def test_a_reworded_valid_section_keeps_passing_on_wrapping(self):
        text = (GUIDES / 'verify.md').read_text()
        body = section(text, '## Verification rounds')
        self.assertTrue(rounds_ok(text.replace(body, body.replace('\n  ', '\n    '))))


if __name__ == '__main__':
    unittest.main()
