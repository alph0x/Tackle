"""The rows on the two current workspace shapes: a Focused workspace (`Gate: Lite` on the plan's first line,
with `history.md` and `resource-usage.md`) and a Coordinated one on a `/5` board, including slugs with dots,
and the slugs the extractor refuses before any row runs.

Each test extracts the rows with the shipped extractor in `references/guides/full-checks.md`, runs them from a
disposable root, and reads the verdict with the shipped `lint_verdict`.
"""
from pathlib import Path
import hashlib
import re
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[5]
import sys
sys.path.insert(0, str(ROOT))
from maintaining.install_root import current_root  # noqa: E402
from eval.support.lint import lint_namespace, write_files, run_lint_row  # noqa: E402
INSTALL = current_root(ROOT)

SOURCE = (INSTALL / 'references/guides/lint-spec.md').read_bytes()
DIGEST = hashlib.sha256(SOURCE).hexdigest()
NAMESPACE = lint_namespace()

HEADER = ('| Run ID | Event | Task | Role | Harness | Tier | Model | Effort | At | Outcome | Attempts | Rework | Verification | Source |\n'
          '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n')
UNSUPPORTED_START = '| trial | start | n/a | executor | test | n/a | n/a | n/a | n/a | running | 0 | n/a | pending | observed |\n'
UNSUPPORTED_FINISH = '| trial | finish | n/a | executor | test | n/a | n/a | n/a | n/a | complete | 0 | n/a | check | observed |\n'
START = UNSUPPORTED_START.replace('| n/a | executor |', '| T-A | executor |').replace('| observed |', '| history.md#absence-trial |')
FINISH = (UNSUPPORTED_FINISH.replace('| n/a | executor |', '| T-A | executor |')
          .replace('| complete |', '| success |').replace('| observed |', '| history.md#absence-trial |'))
ABSENCE = ('### Event absence-trial\nTask ID: T-A\nRun ID: trial\n'
           'Kind: observed-absence\nObserved: no correction or escalation in this run\n')


class ShapeCase(unittest.TestCase):
    """Builds one workspace under `docs/plans/<slug>/` of a disposable root and runs single rows on it."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='tackle-workspace-shape-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.slug = 'probe'
        self.workspace = self.root / 'docs/plans' / self.slug
        self.workspace.mkdir(parents=True)

    def write(self, name, text):
        write_files(self.workspace, {name: text})

    def focused(self):
        self.write('plan.md', 'Gate: Lite\n# Task\n\n- State: complete\n')
        self.write('history.md', '# History\n\n## 2026-09-20 · session 1\nObserved.\n\n' + ABSENCE)
        self.write('resource-usage.md', '# Resource usage\n\nSchema: tackle-observability/2\n\n' + HEADER + START + FINISH)

    def coordinated(self):
        self.focused()
        self.write('plan.md', '# Task\n\n## 5. Task decomposition\n| Task | Responsibility |\n|---|---|\n| T-A | Work |\n')
        self.write('task-board.md', 'Schema: tackle-workspace/5\n\n'
                                    '| Task | What | Brief | Depends on | Status | Verification |\n|---|---|---|---|---|---|\n'
                                    '| T-A | Work | tasks/T-A.md | none | Draft | pending |\n')
        self.write('tasks/T-A.md', '# Task T-A — Work\n\n- **Depends on**: none\n- **Effort**: low\n')
        self.write('reference.md', '# Reference\n')
        self.write('AGENTS.md', '# Instructions\n')

    def rename(self, slug):
        destination = self.workspace.with_name(slug)
        self.workspace.rename(destination)
        self.workspace = destination
        self.slug = slug

    def row(self, number):
        result = run_lint_row(self.root, number, slug=self.slug, source=SOURCE, script=True)
        record = dict(child_exit=result.returncode, timeout=False, launch_error=None,
                      signal=None, inputs_stable=True, artifacts_present=True)
        verdict = NAMESPACE['lint_verdict'](number, record, result.stdout, result.stderr)
        return verdict, result

    def assert_pass(self, number):
        verdict, result = self.row(number)
        self.assertEqual(verdict, 'PASS', (number, result.returncode, result.stdout, result.stderr))

    def assert_blocked(self, number):
        verdict, result = self.row(number)
        self.assertIn(verdict, ('FAIL', 'ERROR'), (number, result.returncode, result.stdout, result.stderr))


class UnsafeSlugTests(unittest.TestCase):
    def test_unsafe_slugs_are_rejected_before_execution(self):
        for slug in ['', '.', '..', '../x', 'a/../b', 'x/y', '/abs', '.hidden', 'x y',
                     'x\ny', 'x;touch sentinel', '$(true)', '`true`', "x'y", 'x\\y', 'x*', '-x']:
            with self.subTest(slug=slug), self.assertRaises(ValueError):
                NAMESPACE['canonical_rows'](SOURCE, DIGEST, slug)


class DottedSlugTests(ShapeCase):
    def test_dotted_slugs_preserve_exact_extraction(self):
        for slug in ['demo', 'release-8.1', 'v8.1.0', 'a..b']:
            with self.subTest(slug=slug):
                rows = NAMESPACE['canonical_rows'](SOURCE, DIGEST, slug)
                self.assertEqual(set(rows), set(range(1, 18)))
                self.assertIn(('ws=docs/plans/' + slug + '; usage="$ws/resource-usage.md"').encode(), rows[16]['command'])
                self.assertEqual(rows[16]['command_sha256'], hashlib.sha256(rows[16]['command']).hexdigest())

    def test_dotted_coordinated_workspace_passes_every_row(self):
        self.coordinated()
        self.rename('release-8.1')
        for number in range(1, 18):
            with self.subTest(row=number):
                self.assert_pass(number)

    def test_dotted_focused_workspace_passes_every_row(self):
        self.focused()
        self.rename('release-8.1')
        for number in range(1, 18):
            with self.subTest(row=number):
                self.assert_pass(number)


class FocusedWorkspaceTests(ShapeCase):
    def test_minimal_focused_workspace_passes_every_row_and_is_left_unchanged(self):
        self.focused()
        before = {p.name: p.read_bytes() for p in self.workspace.iterdir()}
        for number in range(1, 18):
            with self.subTest(row=number):
                self.assert_pass(number)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.workspace.iterdir()})

    def test_fenced_prose_and_later_markers_do_not_select_focused(self):
        self.focused()
        for plan in ['# Task\n```\nGate: Lite\n```\n', '# Task\nRoute discussed: Gate: Lite\n',
                     '\nGate: Lite\n# Task\n']:
            with self.subTest(plan=plan):
                self.write('plan.md', plan)
                self.assert_blocked(2)

    def test_a_dangling_coordinated_artifact_is_rejected(self):
        self.focused()
        (self.workspace / 'task-board.md').symlink_to('missing-board')
        verdict, result = self.row(1)
        self.assertIn(verdict, ('FAIL', 'ERROR'), result.stdout)
        self.assertIn(b'Lite has Full artifact', result.stdout)

    def test_a_decomposition_heading_is_rejected_but_a_fenced_example_is_valid(self):
        self.focused()
        self.write('plan.md', 'Gate: Lite\n# Task\n\n## 5. Task decomposition\n| T-A | Work |\n')
        self.assert_blocked(1)
        self.write('plan.md', 'Gate: Lite\n# Task\n\n```\n## 5. Task decomposition\n```\n')
        self.assert_pass(1)

    def test_each_missing_focused_file_blocks(self):
        for name in ['plan.md', 'history.md', 'resource-usage.md']:
            with self.subTest(name=name):
                self.focused()
                (self.workspace / name).unlink()
                self.assert_blocked(2 if name == 'plan.md' else 1)

    def test_placeholders_are_checked_with_a_fence_exemption(self):
        self.focused()
        self.write('plan.md', 'Gate: Lite\n# Task\n{{unfinished}}\n')
        self.assert_blocked(1)
        self.write('plan.md', 'Gate: Lite\n# Task\n```\n{{example}}\n```\n')
        self.assert_pass(1)

    def test_plan_citations_and_an_optional_reference_are_checked(self):
        self.focused()
        self.write('target.md', 'observed fragment\n')
        self.write('plan.md', 'Gate: Lite\n# Task\n`target.md:1 — "observed fragment"`\n')
        self.assert_pass(4)
        self.write('reference.md', '`target.md:1 — "stale fragment"`\n')
        self.assert_blocked(4)
        self.write('reference.md', '`target.md:1 — "observed fragment"`\n')
        self.write('target.md', 'changed content\n')
        self.assert_blocked(4)

    def test_plan_seals_need_the_exact_decision(self):
        self.focused()
        self.write('plan.md', 'Gate: Lite\n# Task\n<!-- SEALED: D-1 -->\n')
        # A heading whose id only starts with the sealed id (built here so no committed line holds that id).
        self.write('decisions.md', '## D-1' + '0 — unrelated\n')
        self.assert_blocked(7)
        self.write('decisions.md', '## D-1 — approved\n')
        self.assert_pass(7)

    def test_chronology_and_lifecycle_remain_mandatory(self):
        self.focused()
        self.write('history.md', '# History\n## 2026-09-20\n## 2026-09-19\n')
        self.assert_blocked(6)
        for contents in [HEADER + UNSUPPORTED_START + UNSUPPORTED_FINISH,
                         HEADER + FINISH, HEADER + START + START + FINISH,
                         HEADER + START + FINISH.replace('| 0 |', '| -1 |')]:
            with self.subTest(contents=contents):
                self.write('resource-usage.md', contents)
                self.assert_blocked(16)


if __name__ == '__main__':
    unittest.main()
