"""Packaging checks only; behavioral decisions require the fresh-agent trials."""
from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]


class PackagingTests(unittest.TestCase):
    def test_one_installed_entry(self):
        skill = (ROOT / 'SKILL.md').read_text()
        self.assertRegex(skill, r'(?m)^name: tackle$')
        self.assertLessEqual(len(skill.split()), 1100)
        self.assertFalse(list((ROOT / 'references').rglob('SKILL.md')))

    def test_invocation_links_resolve(self):
        path = ROOT / 'references/guides/invocation.md'
        for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
            self.assertTrue((path.parent / target).is_file(), target)

    def test_active_request_tables_do_not_advertise_legacy_commands(self):
        for name in ('SKILL.md', 'README.md', 'references/guides/invocation.md'):
            rows = [line for line in (ROOT / name).read_text().splitlines() if line.startswith('|')]
            self.assertFalse(any('/tackle-' in line for line in rows), name)

    def test_trial_ids_are_unique(self):
        cases = json.loads(Path(__file__).with_name('cases.json').read_text())
        self.assertEqual(len(cases), len({case['id'] for case in cases}))
        self.assertTrue(all(set(case) == {'id', 'request', 'expected'} for case in cases))


if __name__ == '__main__':
    unittest.main()
