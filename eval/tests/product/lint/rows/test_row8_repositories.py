"""Row 8 across repositories: two active workspaces that name different repositories but the same relative
Write scope path are reported as a collision, as the scaffold guide documents. Row 8 itself is unchanged.

Each fixture is built here, at run time, from the workspace shape row 8 reads: an active board row and a
brief whose Write scope line names the path. Workspace ids are composed at run time, never written out.
"""
import tempfile
import unittest
from pathlib import Path

import test_lint_rows as base


BOARD = ('Schema: tackle-workspace/4\n\n| Task | What | Brief | Depends on | Status | Verification |\n'
         '|---|---|---|---|---|---|\n| %s | Work | tasks/%s.md | none | In progress | pending |\n')
BRIEF = ('# Task %s — Work\n\n- **Repository**: %s\n- **Write scope**: `src/app.py`\n')


class Row8Repositories(unittest.TestCase):
    def repository_workspace(self):
        temporary = tempfile.TemporaryDirectory(prefix='tackle-row8-repository-')
        self.addCleanup(temporary.cleanup)
        return Path(temporary.name) / 'root'

    def write_workspace(self, root, name, repository):
        task = 'T-%02d' % 1
        workspace = root / 'docs/plans' / name
        (workspace / 'tasks').mkdir(parents=True)
        (workspace / 'task-board.md').write_text(BOARD % (task, task), encoding='utf-8')
        (workspace / 'tasks' / (task + '.md')).write_text(BRIEF % (task, repository), encoding='utf-8')

    def test_same_relative_path_in_two_repositories_is_reported(self):
        root = self.repository_workspace()
        root.mkdir()
        self.write_workspace(root, 'plan-api', 'api')
        self.write_workspace(root, 'plan-web', 'web')
        verdict, child = base.run_row(8, root, None)
        stdout = child.stdout.decode()
        self.assertEqual(verdict, 'WARN', (child.returncode, stdout, child.stderr[:400]))
        collisions = [line for line in stdout.splitlines() if line.startswith('collision:')]
        self.assertEqual(len(collisions), 1, stdout)
        self.assertIn('src/app.py', collisions[0])
        self.assertIn('plan-api', collisions[0])
        self.assertIn('plan-web', collisions[0])


if __name__ == '__main__':
    unittest.main()
