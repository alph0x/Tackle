import errno
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest


ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))
from eval.support.lint import literal_command, write_files  # noqa: E402

LINT_SOURCE = (ROOT / 'skills/tackle/scripts/lint.py').read_text(encoding='utf-8')
MARKER = 'OUTSIDE-MARKER'


def task(number):
    return 'T-' + str(number)


BOARD_HEADER = ('Schema: tackle-workspace/5\n\n| Task | What | Brief | Depends on | Status | Verification |\n'
                '|---|---|---|---|---|---|\n')
PLAN = ('# Plan\n\n## 5. Task decomposition\n\n| Task | What |\n|---|---|\n'
        f'| {task(1)} | First |\n| {task(2)} | Second |\n')
SIBLING = ('# Workspace\n\n## Sibling workspaces\n\n| Sibling | Path | Relation |\n|---|---|---|\n'
           '| other | `docs/plans/other` | sibling |\n')


def make_tree(case):
    temp = tempfile.TemporaryDirectory()
    case.addCleanup(temp.cleanup)
    root = Path(temp.name)
    workspace = root / 'repo/docs/plans/demo'
    workspace.mkdir(parents=True)
    outside = root / 'outside'
    outside.mkdir()
    return root, workspace, outside


def run_row(number, root):
    program = literal_command(number, LINT_SOURCE).replace('<slug>', 'demo')
    return subprocess.run(['sh', '-c', program], cwd=root / 'repo', capture_output=True, text=True, timeout=10)


def cite(path, line, fragment):
    return f'{path}:{line} — "{fragment}"'


def sha256(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def row_two_files(rows, extra):
    files = {'plan.md': PLAN, 'task-board.md': BOARD_HEADER + ''.join(rows), 'history.md': 'History\n',
             'resource-usage.md': 'Usage\n', 'tasks/README.md': 'Briefs\n'}
    files.update(extra)
    return files


class Observer:
    def __init__(self, path, payload):
        self.path = path
        self.payload = payload
        self.readers = 0
        self.stopping = threading.Event()
        self.thread = threading.Thread(target=self.poll, daemon=True)

    def poll(self):
        while not self.stopping.is_set():
            try:
                descriptor = os.open(self.path, os.O_WRONLY | os.O_NONBLOCK)
            except OSError as error:
                if error.errno != errno.ENXIO:
                    raise
            else:
                self.readers += 1
                try:
                    os.write(descriptor, self.payload)
                except OSError:
                    pass
                finally:
                    os.close(descriptor)
            time.sleep(0.005)

    def start(self):
        self.thread.start()

    def stop(self):
        self.stopping.set()
        self.thread.join()


class CitationReadConfinementTests(unittest.TestCase):
    def test_row_four_absolute_citation_is_refused(self):
        root, workspace, outside = make_tree(self)
        write_files(outside, {'secret.md': MARKER + '\n'})
        citation = cite(outside / 'secret.md', 1, MARKER)
        write_files(workspace, {'plan.md': f'# Plan\n\n{citation}\n', 'reference.md': '# Reference\n'})
        result = run_row(4, root)
        self.assertIn(f'docs/plans/demo/plan.md:3 stale: {citation}', result.stdout)

    def test_row_four_traversal_citation_is_refused(self):
        root, workspace, outside = make_tree(self)
        write_files(outside, {'secret.md': MARKER + '\n'})
        citation = cite('../outside/secret.md', 1, MARKER)
        write_files(workspace, {'plan.md': f'# Plan\n\n{citation}\n', 'reference.md': '# Reference\n'})
        result = run_row(4, root)
        self.assertIn(f'docs/plans/demo/plan.md:3 stale: {citation}', result.stdout)

    def test_row_four_outside_fifo_is_never_opened(self):
        root, workspace, outside = make_tree(self)
        os.mkfifo(outside / 'pipe.md')
        observer = Observer(outside / 'pipe.md', (MARKER + '\n').encode('utf-8'))
        self.addCleanup(observer.stop)
        observer.start()
        citation = cite(outside / 'pipe.md', 1, MARKER)
        write_files(workspace, {'plan.md': f'# Plan\n\n{citation}\n', 'reference.md': '# Reference\n'})
        result = run_row(4, root)
        observer.stop()
        self.assertEqual(observer.readers, 0)
        self.assertIn(f'docs/plans/demo/plan.md:3 stale: {citation}', result.stdout)

    def test_row_four_symlinked_task_input_is_not_read(self):
        root, workspace, outside = make_tree(self)
        write_files(outside, {'brief.md': cite('x.md', 1, MARKER + '-TASK') + '\n',
                              'reference.md': cite('x.md', 1, MARKER + '-REFERENCE') + '\n'})
        write_files(workspace, {'plan.md': '# Plan\n', f'tasks/{task(2)}.md': f'# Task {task(2)}\n'})
        (workspace / f'tasks/{task(1)}.md').symlink_to(outside / 'brief.md')
        (workspace / 'reference.md').symlink_to(outside / 'reference.md')
        result = run_row(4, root)
        self.assertNotIn(MARKER, result.stdout)
        self.assertNotIn(MARKER, result.stderr)

    def test_row_two_traversal_brief_is_refused(self):
        root, workspace, outside = make_tree(self)
        write_files(outside, {f'{task(1)}.md': f'# Task {task(1)}\n'})
        rows = [f'| {task(1)} | Work | tasks/../../../../../outside/{task(1)}.md | none | Ready | n/a |\n',
                f'| {task(2)} | Work | tasks/{task(2)}.md | none | Ready | n/a |\n']
        write_files(workspace, row_two_files(rows, {f'tasks/{task(2)}.md': f'# Task {task(2)}\n'}))
        result = run_row(2, root)
        self.assertIn(f'missing brief: tasks/../../../../../outside/{task(1)}.md', result.stdout)

    def test_row_two_symlinked_brief_is_refused(self):
        root, workspace, outside = make_tree(self)
        write_files(outside, {f'{task(1)}.md': f'# Task {task(1)}\n', f'{task(9)}.md': f'# Task {task(2)}\n'})
        os.mkfifo(outside / 'AGENTS.md')
        rows = [f'| {task(1)} | Work | tasks/{task(1)}.md | none | Complete | reports/{task(1)}-report.md |\n',
                f'| {task(2)} | Work | ../other/tasks/{task(9)}.md | none | Ready | n/a |\n']
        write_files(workspace, row_two_files(rows, {'AGENTS.md': SIBLING}))
        (workspace / f'tasks/{task(1)}.md').symlink_to(outside / f'{task(1)}.md')
        other = root / 'repo/docs/plans/other/tasks'
        other.mkdir(parents=True)
        (other / f'{task(9)}.md').symlink_to(outside / f'{task(9)}.md')
        first = run_row(2, root)
        self.assertIn(f'missing brief: tasks/{task(1)}.md', first.stdout)
        self.assertIn(f'missing brief: ../other/tasks/{task(9)}.md', first.stdout)
        (workspace / 'AGENTS.md').unlink()
        (workspace / 'AGENTS.md').symlink_to(outside / 'AGENTS.md')
        observer = Observer(outside / 'AGENTS.md', b'')
        self.addCleanup(observer.stop)
        observer.start()
        run_row(2, root)
        observer.stop()
        self.assertEqual(observer.readers, 0)

    def test_row_twelve_traversal_brief_is_never_opened(self):
        root, workspace, outside = make_tree(self)
        os.mkfifo(outside / 'brief.md')
        observer = Observer(outside / 'brief.md', ('# Task ' + task(1) + '\n').encode('utf-8'))
        self.addCleanup(observer.stop)
        write_files(outside, {'tier.md': f'**Tier**: {MARKER}\n'})
        rows = [f'| {task(1)} | Work | tasks/../../../../../outside/brief.md | none | Complete | reports/{task(1)}-report.md |\n',
                f'| {task(2)} | Work | tasks/{task(2)}.md | none | Ready | n/a |\n']
        write_files(workspace, {'plan.md': '# Plan\n', 'task-board.md': BOARD_HEADER + ''.join(rows),
                                f'tasks/{task(2)}.md': f'# Task {task(2)}\n'})
        (workspace / f'tasks/{task(3)}.md').symlink_to(outside / 'tier.md')
        observer.start()
        result = run_row(12, root)
        observer.stop()
        self.assertEqual(observer.readers, 0)
        self.assertNotIn(MARKER, result.stdout)
        self.assertNotIn(MARKER, result.stderr)

    def test_row_fourteen_unanchored_id_is_refused(self):
        root, workspace, outside = make_tree(self)
        write_files(outside, {'x-report.md': '**Brief sha256**: bad\n'})
        row = (f'| {task(1)}/../../../../../../outside/x | Work | tasks/{task(1)}.md | none | Complete | '
               f'reports/{task(1)}-report.md |\n')
        write_files(workspace, {'task-board.md': BOARD_HEADER + row, 'history.md': 'History\n',
                                f'tasks/{task(1)}.md': f'# Task {task(1)}\n'})
        (workspace / f'reports/{task(1)}').mkdir(parents=True)
        result = run_row(14, root)
        self.assertIn(f'done task without closure report: {task(1)}/../../../../../../outside/x', result.stdout)
        self.assertNotIn('malformed brief hash', result.stdout)

    def test_row_fourteen_symlinked_brief_is_not_hashed(self):
        root, workspace, outside = make_tree(self)
        write_files(outside, {f'{task(1)}.md': f'# Task {task(1)}\n'})
        row = f'| {task(1)} | Work | tasks/{task(1)}.md | none | Complete | reports/{task(1)}-report.md |\n'
        write_files(workspace, {'task-board.md': BOARD_HEADER + row, 'history.md': 'History\n'})
        (workspace / 'tasks').mkdir()
        (workspace / f'tasks/{task(1)}.md').symlink_to(outside / f'{task(1)}.md')
        digest = sha256(f'# Task {task(1)}\n')
        write_files(workspace, {f'reports/{task(1)}-report.md': f'**Brief sha256**: {digest}\n'})
        result = run_row(14, root)
        self.assertIn(f'closed brief changed: {task(1)}', result.stdout)

    def test_repository_and_workspace_citations_still_resolve(self):
        root, workspace, outside = make_tree(self)
        write_files(root / 'repo', {'skills/x.md': 'alpha line\n'})
        (root / 'repo/link.md').symlink_to('skills/x.md')
        plan = ('# Plan\n\n' + cite('skills/x.md', 1, 'alpha') + '\n' + cite('notes.md', 1, 'beta') + '\n'
                + cite('link.md', 1, 'alpha') + '\n')
        write_files(workspace, {'notes.md': 'beta line\n', 'reference.md': '# Reference\n', 'plan.md': plan})
        result = run_row(4, root)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '', ''))

    def test_regular_and_sibling_briefs_keep_working(self):
        root, workspace, outside = make_tree(self)
        brief = f'# Task {task(1)}\n\n**Tier**: fast\n'
        other = root / 'repo/docs/plans/other/tasks'
        other.mkdir(parents=True)
        write_files(other, {f'{task(9)}.md': f'# Task {task(2)}\n'})
        rows = [f'| {task(1)} | Work | tasks/{task(1)}.md | none | Complete | reports/{task(1)}-report.md |\n',
                f'| {task(2)} | Work | ../other/tasks/{task(9)}.md | none | Ready | n/a |\n']
        files = row_two_files(rows, {f'tasks/{task(1)}.md': brief, 'AGENTS.md': SIBLING,
                                     f'reports/{task(1)}-report.md': f'**Brief sha256**: {sha256(brief)}\n'})
        write_files(workspace, files)
        two = run_row(2, root)
        for text in ('missing brief', 'outside the workspace', 'mismatched brief heading'):
            self.assertNotIn(text, two.stdout)
        self.assertEqual(two.stderr, '')
        for number in (12, 14):
            result = run_row(number, root)
            self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '', ''))


if __name__ == '__main__':
    unittest.main()
