"""The multi-repository texts are shipped where the RUN and PLAN guides read them: the Repositories section
before the harness map, the Repository field after the Write scope line, the run card's preflight check,
the evidence capture revision sentence, and the scaffold section that states the per-repository scope rule.
"""
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from maintaining.install_root import current_root  # noqa: E402

INSTALL = current_root(ROOT)
AGENTS = (INSTALL / 'references/AGENTS.tmpl.md').read_text(encoding='utf-8')
TASK = (INSTALL / 'references/task.tmpl.md').read_text(encoding='utf-8')
RUN_CARD = (INSTALL / 'references/guides/run-card.md').read_text(encoding='utf-8')
EVIDENCE = (INSTALL / 'references/guides/evidence-capture.md').read_text(encoding='utf-8')
SCAFFOLD = (INSTALL / 'references/guides/scaffold.md').read_text(encoding='utf-8')

REPOSITORIES_SECTION = '\n'.join([
    '<a id="repositories"></a>',
    '## Repositories',
    '',
    'Only for a workspace that plans work in more than one repository; delete this section otherwise.',
    '',
    '| id | path | revision at PLAN |',
    '|---|---|---|',
    '| {{id}} | {{absolute or planning-repository-relative path}} | {{commit}} |',
    '',
    '',
])
REPOSITORY_FIELD = ('- **Repository**: {{repository id from the workspace Repositories table; omit this field in a '
                    'single-repository workspace}}.')
PREFLIGHT_LINE = ('   In a multi-repository workspace, also check that the task\'s repository path exists and is a git '
                  'repository, and record its revision; a missing repository blocks only its tasks.')
EVIDENCE_PARAGRAPH = 'In a multi-repository workspace, record the revision of every repository a check reads.'
SCAFFOLD_SECTION = '\n'.join([
    '',
    '<a id="multi-repository-workspace"></a>',
    '## Multi-repository workspace',
    '',
    'One workspace, in the repository where planning happens, may plan work that lands in several repositories.',
    'Its `AGENTS.md` then holds the Repositories table, and each brief states `**Repository**: <id>`.',
    'A task\'s Write scope paths are relative to its repository\'s root, and a task writes only inside its own repository.',
    'Each repository keeps its own requirements base and its own gitignore answer (see the requirements base guide), and each delta entry names its `Repository:`.',
    'Lint row 8 compares Write scope paths as text across active workspaces, so two workspaces naming the same relative path in different repositories are reported as a collision; read the Repository fields to resolve it. Row 8 does not compare tasks within one workspace.',
    'A single-repository workspace has no Repositories table and no Repository field.',
    '',
])
REPOSITORY_STATEMENT = ('A task\'s Write scope paths are relative to its repository\'s root, and a task writes only '
                        'inside its own repository.')


class MultiRepoTemplates(unittest.TestCase):
    def test_agents_template_has_repositories_section(self):
        self.assertIn(REPOSITORIES_SECTION + '## Harness map', AGENTS)
        self.assertEqual(AGENTS.count(REPOSITORIES_SECTION), 1)

    def test_task_template_has_repository_field(self):
        lines = TASK.split('\n')
        scope = [index for index, line in enumerate(lines) if line.startswith('- **Write scope**:')]
        self.assertEqual(len(scope), 1)
        self.assertEqual(lines[scope[0] + 1], REPOSITORY_FIELD)

    def test_run_card_preflight_checks_repositories(self):
        start = RUN_CARD.index('4. **Preflight.**')
        end = RUN_CARD.index('5. **Intent, then work.**')
        step = RUN_CARD[start:end]
        self.assertEqual(step.count(PREFLIGHT_LINE + '\n'), 1)
        self.assertIn('   If the task requires write confinement', step)
        self.assertLess(step.index('   If the task requires write confinement'), step.index(PREFLIGHT_LINE))

    def test_evidence_capture_records_each_revision(self):
        self.assertIn('\n' + EVIDENCE_PARAGRAPH + '\n', EVIDENCE)
        self.assertEqual(EVIDENCE.count(EVIDENCE_PARAGRAPH), 1)

    def test_scaffold_states_repository_scope(self):
        self.assertTrue(SCAFFOLD.endswith(SCAFFOLD_SECTION))
        self.assertIn('<a id="multi-repository-workspace"></a>', SCAFFOLD)
        self.assertEqual(SCAFFOLD.count(REPOSITORY_STATEMENT), 1)
        self.assertIn(REPOSITORY_STATEMENT, SCAFFOLD_SECTION)


if __name__ == '__main__':
    unittest.main()
