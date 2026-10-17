"""Row 8 symlinked scope: a Write scope path with an existing symlink component, including a dangling
link, a link to a directory and a link deeper in the path, is reported as unresolved scope and is never
compared. The row lists the tree's links once and reads that list in awk, so the command starts no
process per path; an ordinary path beside the links still collides.

Each fixture is built here, at run time, from the workspace shape row 8 reads: an active board row and a
brief whose Write scope line names the path.
"""
import os
import re
import tempfile
import unittest
from pathlib import Path

import test_lint_rows as base


BOARD = ('Schema: tackle-workspace/5\n\n| Task | What | Brief | Depends on | Status | Verification |\n'
         '|---|---|---|---|---|---|\n| %s | Work | tasks/%s.md | none | In progress | pending |\n')
BRIEF = '# Task %s — Work\n\n- **Write scope**: %s\n'


class Row8Symlinks(unittest.TestCase):
    def root(self):
        temporary = tempfile.TemporaryDirectory(prefix='tackle-row8-symlink-')
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name) / 'root'
        (root / 'src/inner').mkdir(parents=True)
        (root / 'target').mkdir()
        os.symlink('target', root / 'linked')
        os.symlink('missing', root / 'dangling')
        os.symlink('../../target', root / 'src/inner/deep')
        return root

    def write_workspace(self, root, name, scope):
        task = 'T-%02d' % 1
        workspace = root / 'docs/plans' / name
        (workspace / 'tasks').mkdir(parents=True)
        (workspace / 'task-board.md').write_text(BOARD % (task, task), encoding='utf-8')
        (workspace / 'tasks' / (task + '.md')).write_text(BRIEF % (task, scope), encoding='utf-8')

    def run_row(self, root):
        verdict, child = base.run_row(8, root, None)
        return verdict, child.stdout.decode(), child.stderr.decode()

    def test_each_symlink_component_is_unresolved_scope(self):
        for scope in ('linked/file.py', 'dangling', 'dangling/file.py', 'src/inner/deep/file.py'):
            with self.subTest(scope=scope):
                root = self.root()
                self.write_workspace(root, 'plan-a', '`%s`' % scope)
                self.write_workspace(root, 'plan-b', '`%s`' % scope)
                verdict, stdout, stderr = self.run_row(root)
                self.assertEqual(verdict, 'WARN', (stdout, stderr))
                self.assertEqual(stderr, '')
                self.assertEqual(stdout.splitlines(), ['unresolved scope: %s (symlink component)' % scope] * 2)

    def test_ordinary_path_beside_links_still_collides(self):
        root = self.root()
        self.write_workspace(root, 'plan-a', '`src/inner/file.py`')
        self.write_workspace(root, 'plan-b', '`src`')
        verdict, stdout, stderr = self.run_row(root)
        self.assertEqual(verdict, 'WARN', (stdout, stderr))
        self.assertEqual(stdout.splitlines(), ['collision: src (plan-a + plan-b)'])

    def test_the_row_starts_no_process_per_path(self):
        command = base.rows()[8]['command'].decode()
        self.assertNotRegex(command, r'(?<![.\w])system\(')
        self.assertEqual(len(re.findall(r'find \. -type l', command)), 1)


if __name__ == '__main__':
    unittest.main()
