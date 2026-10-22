"""The brief and decision templates carry the declaration grammar that lint reads: a `**Detail**` field, a
symbol ledger whose `**Consumes**` sub-items name their source and whose `**Produces**` sub-items name what
the task creates, and a decision line naming its `**Owner**` task and changed `**Clauses**`. The brief
guidance states when the ledger is required. Text shape only: these checks protect the template a planner
copies, not a planner's obedience to it.
"""
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from maintaining.install_root import current_root  # noqa: E402

INSTALL = current_root(ROOT)
TASK = INSTALL / 'references/task.tmpl.md'
DECISIONS = INSTALL / 'references/decisions.tmpl.md'
GUIDE = INSTALL / 'references/guides/design-and-contract.md'
SUB_ITEM = re.compile(r'^[ \t]+[-*+][ \t]+`[^`]+`')


def section(text, heading):
    """Lines from a heading through the line before the next heading of the same or a higher level."""
    lines = text.splitlines()
    level = len(heading) - len(heading.lstrip('#'))
    out, inside = [], False
    for line in lines:
        if line.strip() == heading:
            inside = True
            continue
        if inside and line.startswith('#') and len(line) - len(line.lstrip('#')) <= level:
            break
        if inside:
            out.append(line)
    return out


def field_block(lines, label):
    for i, line in enumerate(lines):
        if re.match(r'^[-*+][ \t]+[*][*]%s[*][*]:' % re.escape(label), line):
            block = [line]
            for nxt in lines[i + 1:]:
                if SUB_ITEM.match(nxt):
                    block.append(nxt)
                else:
                    break
            return block
    return None


def detail_ok(text):
    block = field_block(section(text, '## Purpose and scope'), 'Detail')
    return bool(block) and 'full' in block[0] and 'interface' in block[0] and not block[0].rstrip().endswith('.')


def ledger_ok(text):
    lines = section(text, '### Interface and invariants')
    consumes, produces = field_block(lines, 'Consumes'), field_block(lines, 'Produces')
    if not consumes or not produces or len(produces) < 2:
        return False
    subs = consumes[1:]
    return (any(' from ' in s and '[sibling]' in s for s in subs)
            and any(re.search(r'` exists `[^`]*:NN[^`]* — "[^"]*"`', s) for s in subs)
            and 'none' in consumes[0] and 'none' in produces[0])


def owner_ok(text):
    lines = text.splitlines()
    for i, line in enumerate(lines[:-1]):
        if line.startswith('**Supersedes**:'):
            nxt = lines[i + 1]
            return nxt.startswith('**Owner**: ') and ' · **Clauses**: ' in nxt
    return False


def guide_ok(text):
    brief = ' '.join(section(text, '## Task brief'))
    contracts = ' '.join(section(text, '## Contracts and decisions'))
    return ('`**Detail**: full`' in brief and '`interface`' in brief and '`**Produces**`' in brief
            and '`**Consumes**`' in brief and '`from T-NN [sibling]`' in brief and 'under `full` both fields are required' in brief
            and '`**Owner**`' in contracts and '`**Clauses**`' in contracts
            and 'carries each named clause compiled' in contracts)


class TemplateGrammarTests(unittest.TestCase):
    def test_brief_template_declares_the_detail_level_as_a_bare_field(self):
        self.assertTrue(detail_ok(TASK.read_text()))

    def test_brief_template_ledger_names_sources_and_products(self):
        self.assertTrue(ledger_ok(TASK.read_text()))

    def test_decision_template_names_owner_and_clauses_after_supersedes(self):
        self.assertTrue(owner_ok(DECISIONS.read_text()))

    def test_brief_guidance_states_detail_ledger_and_decision_ownership(self):
        self.assertTrue(guide_ok(GUIDE.read_text()))


class OracleDiscriminationTests(unittest.TestCase):
    """Each oracle rejects a keyword-only template and accepts a valid alternative."""

    def test_keyword_only_template_is_rejected(self):
        prose = ('## Purpose and scope\n\nThe Detail level is full or interface.\n\n### Interface and invariants\n\n'
                 '- **Consumes**: inputs from T-NN [sibling] or exists.\n- **Produces**: names.\n')
        self.assertFalse(detail_ok(prose))
        self.assertFalse(ledger_ok(prose))
        self.assertFalse(owner_ok('**Supersedes**: none\nOwner and Clauses are named in prose.\n'))

    def test_valid_alternative_markers_are_accepted(self):
        alt = ('## Purpose and scope\n\n* **Detail**: {{full or interface}}\n\n### Interface and invariants\n\n'
               '+ **Consumes**: {{none, or sub-items}}\n    * `{{name}}` from {{T-NN or T-NN [sibling]}}\n'
               '    * `{{name}}` exists `{{path.ext:NN}} — "{{fragment}}"`\n+ **Produces**: {{none, or sub-items}}\n'
               '    * `{{name}}`\n')
        self.assertTrue(detail_ok(alt))
        self.assertTrue(ledger_ok(alt))


if __name__ == '__main__':
    unittest.main()
