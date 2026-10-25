"""Lint row 9 reads a declared repair corridor through the shipped lint script.

A brief may declare `**Corridor**:` with five parts; row 9 flags a missing part or a budget that is
not a positive number of full cycles, and stays silent for a complete corridor, for a brief without
one, for the template's unfilled guidance form, and for prose that only mentions the word.
"""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[5]
LINT = ROOT / 'skills/tackle/scripts/lint.py'
COMPLETE = 'files=src/a.py; invariants=public API unchanged; budget=3; review=15m; verification=unit test'


def row9(briefs):
    with tempfile.TemporaryDirectory(prefix='tackle-corridor-') as directory:
        tasks = Path(directory) / 'docs/plans/demo/tasks'
        tasks.mkdir(parents=True)
        for name, body in briefs.items():
            (tasks / name).write_text(body)
        child = subprocess.run([sys.executable, '-I', str(LINT), '--row', '9', 'demo'],
                               cwd=directory, capture_output=True, text=True, timeout=60)
    return child


def brief(number, corridor=None, prose=''):
    lines = ['# Task T-%04d — fixture' % number, '', '- **Goal**: one observable change.']
    if corridor is not None:
        lines.append('- **Corridor**: ' + corridor)
    if prose:
        lines += ['', prose]
    return '\n'.join(lines) + '\n'


class RepairCorridorRow(unittest.TestCase):
    def test_complete_corridor_and_absent_corridor_are_silent(self):
        child = row9({'T-1001-a.md': brief(1, COMPLETE), 'T-1002-b.md': brief(2),
                      'T-1003-c.md': brief(3, prose='The word **Corridor**: appears in prose only.')})
        self.assertEqual(child.returncode, 0, child.stderr)
        self.assertEqual(child.stdout, '')

    def test_unfilled_template_guidance_is_silent(self):
        guidance = '(repair tasks only: `files=<allowed paths>; budget=<N>`; omit otherwise)'
        child = row9({'T-1001-a.md': brief(1, guidance)})
        self.assertEqual(child.stdout, '')

    def test_star_bullet_declares_like_a_dash_bullet(self):
        child = row9({'T-1001-a.md': '# Task T-1001\n\n* **Corridor**: ' + COMPLETE + '\n'})
        self.assertEqual(child.stdout, '')
        child = row9({'T-1001-a.md': '# Task T-1001\n\n* **Corridor**: files=a.py\n'})
        self.assertIn('corridor missing invariants budget review verification:', child.stdout)

    def test_parenthesized_declaration_is_still_validated(self):
        child = row9({'T-1001-a.md': brief(1, '(budget=0)')})
        self.assertIn('corridor missing files invariants budget review verification:', child.stdout)

    def test_fenced_examples_are_not_declarations(self):
        for fence in ('~~~markdown', '   ```', '```'):
            close = fence.strip()[:3]
            body = '# Task T-1001\n\n' + fence + '\n- **Corridor**: example\n' + close + '\n'
            child = row9({'T-1001-a.md': body})
            self.assertEqual(child.stdout, '', fence)

    def test_live_declaration_after_mixed_indent_fence_is_validated(self):
        body = '# Task T-1001\n\n   ```\nexample\n```\n- **Corridor**: files=a.py\n'
        child = row9({'T-1001-a.md': body})
        self.assertIn('corridor missing invariants budget review verification:', child.stdout)

    def test_shorter_delimiter_inside_a_longer_fence_stays_content(self):
        for opener, inner in (('~~~~', '~~~'), ('````', '```')):
            body = ('# Task T-1001\n\n' + opener + '\n' + inner + '\n- **Corridor**: example\n'
                    + opener + '\n')
            child = row9({'T-1001-a.md': body})
            self.assertEqual(child.stdout, '', opener)

    def test_indented_code_block_is_not_a_declaration(self):
        child = row9({'T-1001-a.md': '# Task T-1001\n\n    - **Corridor**: example\n'})
        self.assertEqual(child.stdout, '')

    def test_comma_separated_list_inside_a_part(self):
        listed = COMPLETE.replace('files=src/a.py', 'files=src/a.py, src/b.py, tests/test_a.py')
        child = row9({'T-1001-a.md': brief(1, listed)})
        self.assertEqual(child.stdout, '')

    def test_repeated_part_is_reported(self):
        child = row9({'T-1001-a.md': brief(1, COMPLETE + '; budget=0')})
        self.assertIn('corridor part repeated: budget:', child.stdout)

    def test_empty_occurrence_counts_toward_the_repeat_limit(self):
        child = row9({'T-1001-a.md': brief(1, 'files=; ' + COMPLETE)})
        self.assertIn('corridor part repeated: files:', child.stdout)

    def test_each_missing_part_is_named(self):
        for part in ('files', 'invariants', 'budget', 'review', 'verification'):
            kept = '; '.join(item for item in COMPLETE.split('; ') if not item.startswith(part + '='))
            child = row9({'T-1001-a.md': brief(1, kept)})
            self.assertIn('corridor missing ' + part + ':', child.stdout, part)

    def test_empty_part_counts_as_missing(self):
        child = row9({'T-1001-a.md': brief(1, COMPLETE.replace('invariants=public API unchanged',
                                                             'invariants='))})
        self.assertIn('corridor missing invariants:', child.stdout)

    def test_budget_must_be_a_positive_number_of_full_cycles(self):
        for budget in ('0', 'three', '-1', '2.5'):
            child = row9({'T-1001-a.md': brief(1, COMPLETE.replace('budget=3', 'budget=' + budget))})
            self.assertIn('corridor budget is not a positive number of full cycles', child.stdout,
                          budget)

    def test_loop_budget_findings_are_unchanged(self):
        child = row9({'T-1001-a.md': '# Task T-1001\n\n- **Type**: discovery\n'})
        self.assertIn('discovery task without Rounds budget', child.stdout)
        self.assertNotIn('corridor', child.stdout)


if __name__ == '__main__':
    unittest.main()
