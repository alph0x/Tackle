from pathlib import Path
from datetime import datetime, timezone
import hashlib
import re
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SOURCE = (ROOT / 'references/guides/lint-spec.md').read_bytes()
DIGEST = hashlib.sha256(SOURCE).hexdigest()
RECIPES = re.findall(r'```python\n(.*?)\n```',
                     (ROOT / 'references/guides/full-checks.md').read_text(), re.S)
NAMESPACE = {'__name__': 'workspace_compatibility_test'}
exec(RECIPES[1], NAMESPACE)
HEADER = ('| Run ID | Event | Point | Role | Harness | Tier | Model | Effort | At | Outcome | Attempts | Rework | Verification | Source |\n'
          '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n')
START = '| trial | start | n/a | executor | test | n/a | n/a | n/a | n/a | running | 0 | n/a | pending | observed |\n'
FINISH = '| trial | finish | n/a | executor | test | n/a | n/a | n/a | n/a | complete | 0 | n/a | check | observed |\n'


class WorkspaceCompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='tackle-workspace-compat-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.slug = 'probe'
        self.workspace = self.root / 'docs/plans' / self.slug
        self.workspace.mkdir(parents=True)

    def write(self, name, text):
        path = self.workspace / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def lite(self):
        self.write('plan.md', 'Gate: Lite\n# Task\n\n- State: complete\n')
        self.write('log.md', '# Log\n\n## 2026-09-20 · session 1\nObserved.\n')
        self.write('usage.md', '# Usage\n\nSchema: tackle-observability/2\n\n' + HEADER + START + FINISH)

    def full(self):
        self.lite()
        self.write('plan.md', '# Task\n\n## 5. Point decomposition\n| Point | Responsibility |\n|---|---|\n| P-01 | Work |\n')
        self.write('board.md', '| Point | What | Briefing | Depends on | Status | Confidence |\n|---|---|---|---|---|---|\n| P-01 | Work | points/P-01.md | none | 🔴 | E0 |\n')
        self.write('points/P-01.md', '# Point P-01\n\n- **Depends on**: none\n- **Effort**: high\n')
        self.write('reference.md', '# Reference\n')
        self.write('AGENTS.md', '# Instructions\n')

    def row(self, number):
        rows = NAMESPACE['canonical_rows'](SOURCE, DIGEST, self.slug)
        script = self.root / ('row-%02d.sh' % number)
        script.write_bytes(rows[number]['command'])
        result = subprocess.run(['sh', str(script)], cwd=self.root, capture_output=True, timeout=10)
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

    def test_dotted_and_legacy_slugs_preserve_exact_extraction(self):
        for slug in ['demo', 'release-8.1', 'v8.1.0', 'a..b']:
            with self.subTest(slug=slug):
                rows = NAMESPACE['canonical_rows'](SOURCE, DIGEST, slug)
                self.assertEqual(set(rows), set(range(1, 17)))
                self.assertIn(('docs/plans/' + slug + '/usage.md').encode(), rows[16]['command'])
                self.assertEqual(rows[16]['command_sha256'], hashlib.sha256(rows[16]['command']).hexdigest())

    def test_unsafe_slugs_are_rejected_before_execution(self):
        for slug in ['', '.', '..', '../x', 'a/../b', 'x/y', '/abs', '.hidden', 'x y',
                     'x\ny', 'x;touch sentinel', '$(true)', '`true`', "x'y", 'x\\y', 'x*', '-x']:
            with self.subTest(slug=slug), self.assertRaises(ValueError):
                NAMESPACE['canonical_rows'](SOURCE, DIGEST, slug)

    def test_minimal_lite_all_rows_pass_without_full_artifacts_or_mutation(self):
        self.lite()
        before = {p.name: p.read_bytes() for p in self.workspace.iterdir()}
        for number in range(1, 17):
            with self.subTest(row=number):
                self.assert_pass(number)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.workspace.iterdir()})

    def test_dotted_full_workspace_still_passes_all_rows(self):
        self.full()
        destination = self.workspace.with_name('release-8.1')
        self.workspace.rename(destination)
        self.workspace = destination
        self.slug = destination.name
        for number in range(1, 17):
            with self.subTest(row=number):
                self.assert_pass(number)

    def test_dotted_lite_workspace_passes_all_rows(self):
        self.lite()
        destination = self.workspace.with_name('release-8.1')
        self.workspace.rename(destination)
        self.workspace = destination
        self.slug = destination.name
        for number in range(1, 17):
            with self.subTest(row=number):
                self.assert_pass(number)

    def test_unmarked_missing_board_does_not_select_lite(self):
        self.lite()
        self.write('plan.md', '# Full task\n')
        self.assert_blocked(2)
        self.assert_blocked(11)

    def test_fenced_and_prose_markers_do_not_select_lite(self):
        self.lite()
        for plan in ['# Task\n```\nGate: Lite\n```\n', '# Task\nRoute discussed: Gate: Lite\n',
                     '\nGate: Lite\n# Task\n']:
            with self.subTest(plan=plan):
                self.write('plan.md', plan)
                self.assert_blocked(2)

    def test_lite_with_board_or_points_is_rejected(self):
        self.lite()
        self.write('board.md', '# An incompatible board\n')
        self.assert_blocked(1)
        (self.workspace / 'board.md').unlink()
        (self.workspace / 'points').mkdir()
        self.assert_blocked(1)

    def test_lite_with_dangling_full_artifact_is_rejected(self):
        self.lite()
        (self.workspace / 'board.md').symlink_to('missing-board')
        self.assert_blocked(1)

    def test_lite_full_decomposition_is_rejected_but_fenced_example_is_valid(self):
        self.lite()
        self.write('plan.md', 'Gate: Lite\n# Task\n\n## 5. Point decomposition\n| P-01 | Work |\n')
        self.assert_blocked(1)
        self.write('plan.md', 'Gate: Lite\n# Task\n\n```\n## 5. Point decomposition\n```\n')
        self.assert_pass(1)

    def test_missing_required_lite_artifacts_block(self):
        for name in ['plan.md', 'log.md', 'usage.md']:
            with self.subTest(name=name):
                self.lite()
                (self.workspace / name).unlink()
                self.assert_blocked(2 if name == 'plan.md' else 1)

    def test_lite_placeholders_are_checked_with_fence_exemption(self):
        self.lite()
        self.write('plan.md', 'Gate: Lite\n# Task\n{{unfinished}}\n')
        self.assert_blocked(1)
        self.write('plan.md', 'Gate: Lite\n# Task\n```\n{{example}}\n```\n')
        self.assert_pass(1)

    def test_lite_citations_and_optional_reference_are_checked(self):
        self.lite()
        self.write('target.md', 'observed fragment\n')
        self.write('plan.md', 'Gate: Lite\n# Task\n`target.md:1 — "observed fragment"`\n')
        self.assert_pass(4)
        self.write('reference.md', '`target.md:1 — "stale fragment"`\n')
        self.assert_blocked(4)
        self.write('reference.md', '`target.md:1 — "observed fragment"`\n')
        self.write('target.md', 'changed content\n')
        self.assert_blocked(4)

    def test_lite_plan_seals_require_exact_decision(self):
        self.lite()
        self.write('plan.md', 'Gate: Lite\n# Task\n<!-- SEALED: D-01 -->\n')
        self.write('decisions.md', '## D-010 — unrelated\n')
        self.assert_blocked(7)
        self.write('decisions.md', '## D-01 — approved\n')
        self.assert_pass(7)

    def test_lite_chronology_and_lifecycle_remain_mandatory(self):
        self.lite()
        self.write('log.md', '# Log\n## 2026-09-20\n## 2026-09-19\n')
        self.assert_blocked(6)
        for contents in [HEADER + FINISH, HEADER + START + START + FINISH,
                         HEADER + START + FINISH.replace('| 0 |', '| -1 |')]:
            with self.subTest(contents=contents):
                self.write('usage.md', contents)
                self.assert_blocked(16)

    def test_optional_lite_metadata_defaults_and_warnings(self):
        self.lite()
        self.assert_pass(13)
        self.assert_pass(15)
        self.write('AGENTS.md', 'Log archive threshold: 1\nReference staleness window: 14\n')
        self.assertEqual(self.row(13)[0], 'WARN')
        self.write('reference-docs/source.md', 'captured: 2000-01-01\nold\n')
        self.assertEqual(self.row(15)[0], 'WARN')
        self.write('reference-docs/source.md', 'captured: ' + datetime.now(timezone.utc).date().isoformat() + '\ncurrent\n')
        self.assert_pass(15)

    def test_full_invalid_status_effort_and_missing_board_still_block(self):
        self.full()
        self.write('board.md', '| P-01 | Work | points/P-01.md | none | BROKEN | E0 |\n')
        self.assert_blocked(3)
        self.write('points/P-01.md', '# Point P-01\n- **Effort**: highXYZ\n')
        self.assert_blocked(12)
        (self.workspace / 'board.md').unlink()
        self.assert_blocked(2)

    def test_v5_board_accepts_ready_citation_and_waiting_on_owner(self):
        self.write('plan.md', '# Task\n\n## 5. Task decomposition\n| Task | Responsibility |\n|---|---|\n'
                              '| T-01 | Ready work |\n| T-02 | Waiting work |\n')
        self.write('history.md', '# History\n\n## 2026-09-20 · session 1\nObserved.\n')
        self.write('reference.md', '# Reference\n')
        self.write('resource-usage.md', '# Resource usage\n\nSchema: tackle-observability/2\n\n' + HEADER + START + FINISH)
        self.write('task-board.md', 'Schema: tackle-workspace/5\n\n'
                                    '| Task | What | Brief | Depends on | Status | Verification |\n|---|---|---|---|---|---|\n'
                                    '| T-01 | Ready work | tasks/T-01.md | none | Ready to run | ready: D-01 |\n'
                                    '| T-02 | Waiting work | tasks/T-02.md | none | Waiting on owner | waiting: Q-01 |\n')
        self.write('tasks/T-01.md', '# Task T-01 — Ready work\n')
        self.write('tasks/T-02.md', '# Task T-02 — Waiting work\n')
        for number in range(1, 17):
            with self.subTest(row=number):
                self.assert_pass(number)


if __name__ == '__main__':
    unittest.main()
