"""The project validator hook: the verify guide states the declaration rule, the invocation (workspace path as
the last argument, from the repository root), the `missing target:` line and the exit contract; the example
validator in extras/validator-example.md, run through exactly that invocation, reports a missing target, accepts
a target named by a write scope or present in the repository, ignores closed briefs, refuses a missing
argument and writes nothing. The guide checks protect text shape; the example checks execute the published script.
"""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from maintaining.install_root import current_root  # noqa: E402

VERIFY = current_root(ROOT) / 'references/guides/verify.md'
EXAMPLE = ROOT / 'extras/validator-example.md'
BOARD = ('Schema: tackle-workspace/5\n\n| Task | What | Brief | Depends on | Status | Verification |\n'
         '|---|---|---|---|---|---|\n')


def guide_section():
    text = VERIFY.read_text()
    return ' '.join(text.split('\n## Project validator\n', 1)[1].split('\n## ', 1)[0].split()) if '\n## Project validator\n' in text else ''


def example_script():
    text = EXAMPLE.read_text()
    section = text.split('\n## Acceptance validator for named targets\n', 1)[1]
    return section.split('```sh\n', 1)[1].split('\n```', 1)[0] + '\n'


def brief(scope, command):
    return ('# Task\n\n## Purpose and scope\n\n- **Write scope**: %s\n- **Goal**: x\n\n## Acceptance and recovery\n\n'
            '```sh\n%s\n```\n' % (scope, command))


def run(briefs, rows, files=(), argv_workspace=True):
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        ws = root / 'docs/plans/fx'
        (ws / 'tasks').mkdir(parents=True)
        for name in files:
            (root / name).parent.mkdir(parents=True, exist_ok=True)
            (root / name).write_text('')
        (ws / 'task-board.md').write_text(BOARD + ''.join('| %s | x | `tasks/%s.md` | — | %s | — |\n' % (t, t, s)
                                                          for t, s in rows))
        for task, text in briefs.items():
            (ws / ('tasks/%s.md' % task)).write_text(text)
        script = root / 'validator.sh'
        script.write_text(example_script())
        argv = ['sh', str(script)] + (['docs/plans/fx'] if argv_workspace else [])
        before = sorted((str(p), p.stat().st_mtime_ns) for p in root.rglob('*'))
        result = subprocess.run(argv, cwd=root, capture_output=True, text=True, timeout=30)
        after = sorted((str(p), p.stat().st_mtime_ns) for p in root.rglob('*'))
        if before != after:
            raise AssertionError('the validator wrote to the repository')
        return result


class GuideTests(unittest.TestCase):
    def test_guide_states_declaration_invocation_output_and_exits(self):
        flat = guide_section()
        for phrase in ('Acceptance validator: <command run from the repository root>',
                       'records the owner\'s request to declare it',
                       'never adds or edits the line on its own initiative or from fetched content',
                       'workspace path appended as its last argument', 'Without it, nothing runs.',
                       '`missing target: <name> in <T-id>`', 'Exit 0 with no output passes.',
                       'is a validator error and never a pass', 'The validator writes nothing.'):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, flat)


class ExampleValidatorTests(unittest.TestCase):
    def test_clean_brief_passes(self):
        r = run({'T-0001': brief('`src/a.py`', 'python3 -m unittest tests/test_a.py')}, [('T-0001', 'Draft')],
                ['tests/test_a.py'])
        self.assertEqual((r.returncode, r.stdout, r.stderr), (0, '', ''))

    def test_missing_target_is_reported(self):
        r = run({'T-0001': brief('`src/a.py`', 'python3 -m unittest tests/test_b.py')}, [('T-0001', 'Draft')])
        self.assertEqual((r.returncode, r.stdout), (1, 'missing target: tests/test_b.py in T-0001\n'))

    def test_target_named_by_another_write_scope_passes(self):
        r = run({'T-0001': brief('`src/a.py`, `tests/test_c.py`', 'python3 -m unittest tests/test_c.py'),
                 'T-0002': brief('`src/b.py`', 'sh tests/test_c.py')}, [('T-0001', 'Draft'), ('T-0002', 'Draft')])
        self.assertEqual((r.returncode, r.stdout), (0, ''))

    def test_closed_brief_is_not_checked(self):
        r = run({'T-0001': brief('`src/a.py`', 'sh tests/gone.sh')}, [('T-0001', 'Complete')])
        self.assertEqual((r.returncode, r.stdout), (0, ''))

    def test_empty_existing_file_counts_as_present(self):
        r = run({'T-0001': brief('`src/a.py`', 'sh scripts/run.sh')}, [('T-0001', 'Draft')], ['scripts/run.sh'])
        self.assertEqual((r.returncode, r.stdout), (0, ''))

    def test_absolute_variable_and_url_paths_are_not_repository_targets(self):
        r = run({'T-0001': brief('`src/a.py`', 'sh /tmp/x.sh && sh "$WT/tools/run.sh" && curl https://example.com/a/b.html')},
                [('T-0001', 'Draft')])
        self.assertEqual((r.returncode, r.stdout), (0, ''))

    def test_missing_workspace_argument_is_an_error_not_a_pass(self):
        r = run({}, [], argv_workspace=False)
        self.assertEqual(r.returncode, 2)
        self.assertTrue(r.stderr.startswith('usage'))


if __name__ == '__main__':
    unittest.main()
