"""The 9.0 to 9.1 adoption path: the checklist heading satisfies the migrate-chain gate for stamp 9.1.0, and a
workspace shaped like 9.0.1 fails row 17 until the checklist's steps are applied, then passes rows 1 through 17.

The steps are applied mechanically from the shipped templates (the obligations section of the board template, the
policy line of the AGENTS template) and judged by the canonical rows, never by a copy of their logic.
"""
import hashlib
import re
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from maintaining.install_root import current_root  # noqa: E402

INSTALL = current_root(ROOT)
REFERENCES = INSTALL / 'references'
MIGRATE = REFERENCES / 'guides/migrate.md'
SPEC = (REFERENCES / 'guides/lint-spec.md').read_bytes()
FIXTURE = ROOT / 'eval/lint/rows/fixtures/pass-obligations'
SLUG = 'demo'
WS = 'docs/plans/' + SLUG


def lint_recipe():
    """The shipped canonical_rows and lint_verdict, executed from the block in full-checks.md."""
    guide = (REFERENCES / 'guides/full-checks.md').read_text(encoding='utf-8')
    block = next(b for b in re.findall(r'```python\n(.*?)\n```', guide, re.S) if 'def canonical_rows' in b)
    namespace = {'__name__': 'migration_lint_recipe'}
    exec(compile(block, 'full-checks.md', 'exec'), namespace)
    return namespace


RECIPE = lint_recipe()
ROWS = RECIPE['canonical_rows'](SPEC, hashlib.sha256(SPEC).hexdigest(), SLUG)
TITLE = '## v9.0 → v9.1 checklist'
ANCHOR = '<a id="v90--v91-checklist"></a>'


def checklist(text):
    return text.split(TITLE, 1)[1].split('\n## ', 1)[0].split('\n<a id=', 1)[0]


def gate_four():
    loader = runpy.run_path(str(ROOT / 'eval/validation-integrity/acceptance.py'))['canonical_gates']
    return loader((ROOT / 'MAINTAINING.md').read_text(encoding='utf-8'))[3]


class ChecklistTests(unittest.TestCase):
    def setUp(self):
        self.text = MIGRATE.read_text(encoding='utf-8')

    def test_the_heading_is_exact_unique_and_anchored_between_the_previous_checklist_and_the_schema_section(self):
        lines = self.text.splitlines()
        self.assertEqual(lines.count(TITLE), 1)
        at = lines.index(TITLE)
        self.assertEqual(lines[at - 1], ANCHOR)
        self.assertLess(self.text.index('## v9.0.0 → v9.0.1 checklist'), self.text.index(TITLE))
        self.assertLess(self.text.index(TITLE), self.text.index('<a id="schema-keyed-migration"></a>'))

    def test_the_migrate_chain_gate_accepts_a_9_1_0_stamp_only_with_this_exact_heading(self):
        command = gate_four()
        migrations = ROOT / 'maintaining/migrations.md'
        for guide, wanted in ((self.text, True), (self.text.replace(TITLE, '## v9.0.1 → v9.1 checklist'), False),
                              (self.text.replace(TITLE, '## v9.0 → v9.1  checklist'), False)):
            with tempfile.TemporaryDirectory(prefix='tackle-gate-four-') as temporary:
                root = Path(temporary)
                (root / 'skills/tackle/references/guides').mkdir(parents=True)
                (root / 'maintaining').mkdir()
                (root / 'skills/tackle/SKILL.md').write_text('# Tackle\n\n**Tackle 9.1.0** — fixture stamp\n', encoding='utf-8')
                (root / 'skills/tackle/references/guides/migrate.md').write_text(guide, encoding='utf-8')
                shutil.copyfile(migrations, root / 'maintaining/migrations.md')
                child = subprocess.run(['sh', '-c', command], cwd=root, capture_output=True, text=True)
                self.assertEqual(child.stderr, '')
                if wanted:
                    self.assertEqual((child.returncode, child.stdout), (0, ''))
                else:
                    self.assertIn('missing migrate checklist → v9.1', child.stdout)

    def test_the_checklist_names_the_artifacts_the_adoption_applies_and_ends_with_the_stamp_bump(self):
        steps = checklist(self.text)
        for phrase in ('rows 1–17', '`**Remains**: none`', 'task-board.tmpl.md', 'Active obligations', 'AGENTS.tmpl.md',
                       'History entry budget', 'Methodology:', '9.1.0'):
            self.assertIn(phrase, steps)
        numbered = re.findall(r'^\d+\. .*(?:\n(?!\d+\. ).*)*', steps, re.M)
        self.assertTrue(numbered)
        self.assertIn('Methodology:', numbered[-1])
        self.assertIn('9.1.0', numbered[-1])

    def test_earlier_checklists_keep_their_sixteen_row_counts(self):
        earlier = self.text.split(TITLE, 1)[0]
        self.assertIn('Run rows 1–16 and the installed capability/recovery consumer', earlier)
        self.assertIn('(`lint: N/16`)', earlier)
        self.assertNotIn('rows 1–17', earlier)


class AdoptionTests(unittest.TestCase):
    def workspace(self):
        temporary = tempfile.TemporaryDirectory(prefix='tackle-adoption-')
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name) / 'root'
        shutil.copytree(FIXTURE, root)
        return root

    def run_rows(self, root):
        """{row: (verdict, output lines)} for rows 1 through 17 under the system AWK."""
        results = {}
        for number in sorted(ROWS):
            child = subprocess.run(['sh', '-c', ROWS[number]['command'].decode()], cwd=root, capture_output=True, timeout=30)
            record = dict(child_exit=child.returncode, timeout=False, launch_error=None, signal=None,
                          inputs_stable=True, artifacts_present=True)
            results[number] = (RECIPE['lint_verdict'](number, record, child.stdout, child.stderr),
                               child.stdout.decode().splitlines())
        return results

    def nine_zero_one(self):
        root = self.workspace()
        board = (root / WS / 'task-board.md').read_text(encoding='utf-8')
        (root / WS / 'task-board.md').write_text(board.split('<a id="obligations"></a>')[0], encoding='utf-8')
        (root / WS / 'reports/T-A-report.md').write_text('# T-A report\n\nReviewer: demo.\n', encoding='utf-8')
        history = (root / WS / 'history.md').read_text(encoding='utf-8')
        (root / WS / 'history.md').write_text(history.replace('- Active obligations: O-01\n', '- Active obligations: none outside the board.\n'),
                                              encoding='utf-8')
        return root

    def test_a_9_0_1_workspace_fails_only_row_17_and_the_checklist_steps_make_it_pass_every_row(self):
        root = self.nine_zero_one()
        before = self.run_rows(root)
        self.assertEqual(sorted(before), list(range(1, 18)))
        self.assertEqual({number for number, (verdict, _) in before.items() if verdict != 'PASS'}, {17}, before)
        self.assertEqual(len(before[17][1]), 1, before[17])
        self.assertIn('T-A', before[17][1][0])
        steps = checklist(MIGRATE.read_text(encoding='utf-8'))

        # Step: add the receipt to each Complete task's report.
        self.assertIn('**Remains**: none', steps)
        report = root / WS / 'reports/T-A-report.md'
        report.write_text(report.read_text(encoding='utf-8') + '\n**Remains**: none\n', encoding='utf-8')
        # Step: copy the obligations section of the board template below the task table.
        template = (REFERENCES / 'task-board.tmpl.md').read_text(encoding='utf-8')
        self.assertIn('<a id="obligations"></a>', template)
        section = '<a id="obligations"></a>' + template.split('<a id="obligations"></a>', 1)[1]
        board = root / WS / 'task-board.md'
        board.write_text(board.read_text(encoding='utf-8').rstrip('\n') + '\n\n' + section, encoding='utf-8')
        # Step: copy the default policy line of the AGENTS template.
        policy = next(line for line in (REFERENCES / 'AGENTS.tmpl.md').read_text(encoding='utf-8').splitlines()
                      if 'History maintenance policy' in line)
        agents = root / WS / 'AGENTS.md'
        agents.write_text(agents.read_text(encoding='utf-8') + '\n' + policy + '\n', encoding='utf-8')

        after = self.run_rows(root)
        self.assertEqual({number: verdict for number, (verdict, _) in after.items()}, {number: 'PASS' for number in range(1, 18)}, after)
        self.assertTrue(all(lines == [] for _, lines in after.values()), after)


if __name__ == '__main__':
    unittest.main()
