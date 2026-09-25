"""End-to-end tests for `maintaining/field_report.py`, driven through the real CLI by subprocess so a
red run before the tool exists is meaningful and a refusal's exit code is testable.

Case matrix (see README.md): C1 states, C2 ledger, C3 reopenings, C4 telemetry, C5 split, C6
read-only, C7 refusal. C8 (a real run against this repository, over its actual commit history and
local workspaces) is not here: it is a one-off command run from the working tree, not a unit test
against synthetic fixtures.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'maintaining' / 'field_report.py'
FIXTURES = Path(__file__).resolve().parent / 'fixtures' / 'plans'

# Isolated from the real operator's global/system git config (no gpgsign prompts, no name/email
# lookup), and deterministic author/committer dates. Mirrors eval/records/test_currency.py's GIT_ENV.
GIT_ENV = {'GIT_AUTHOR_NAME': 'fixture', 'GIT_AUTHOR_EMAIL': 'fixture@invalid', 'GIT_COMMITTER_NAME': 'fixture',
           'GIT_COMMITTER_EMAIL': 'fixture@invalid', 'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_CONFIG_NOSYSTEM': '1'}


def run_cli(args, env=None):
    full_env = dict(os.environ, **(env or {}))
    return subprocess.run([sys.executable, str(SCRIPT)] + [str(a) for a in args],
                          capture_output=True, text=True, env=full_env)


def copy_plans(destination):
    shutil.copytree(FIXTURES, destination)
    return destination


def hash_tree(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file()}


class RealRepoFixture:
    """--repo needs a real git work tree; the Tackle repository itself always is one, and an empty
    HEAD..HEAD range is cheap, valid regardless of the live branch state, and never touched (see
    test_own_test_family_directory_is_never_modified below, which hashes this test family's own
    directory tree, fixtures included, before and after a real run)."""
    path = ROOT
    since = 'HEAD'
    until = 'HEAD'


class WorkspaceFieldTests(unittest.TestCase):
    """C1 states, C2 ledger, C3 reopenings, C4 telemetry: field-level checks against the static
    fixtures under fixtures/plans/, run directly (read-only) with the real repository as --repo."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name)

    def report(self, plans=FIXTURES, workspaces=None):
        json_path, md_path = self.out / 'report.json', self.out / 'report.md'
        args = ['--plans', plans, '--repo', RealRepoFixture.path, '--since', RealRepoFixture.since,
                '--until', RealRepoFixture.until, '--json', json_path, '--markdown', md_path]
        for slug in workspaces or ():
            args += ['--workspace', slug]
        child = run_cli(args)
        self.assertEqual(child.returncode, 0, child.stderr)
        self.assertTrue(json_path.is_file())
        self.assertTrue(md_path.is_file())
        return json.loads(json_path.read_text(encoding='utf-8')), md_path.read_text(encoding='utf-8')

    # ---- C1: board states, every bucket, legacy emoji and words, ragged/unmapped rows ----

    def test_c1_pre3_bucket_and_every_legacy_state(self):
        data, markdown = self.report(workspaces=['ws-pre3'])
        ws = data['workspaces']['ws-pre3']
        self.assertEqual(ws['bucket'], {'value': 'pre-3', 'source': str(FIXTURES / 'ws-pre3' / 'board.md')})
        self.assertEqual(ws['tasks']['value'], {
            'Draft': 1, 'In progress': 3, 'Ready to run': 1, 'Checking': 4, 'Blocked': 1,
            'Complete': 1, 'Interrupted': 2, 'Skipped': 1, 'Unverifiable': 2,
        })
        self.assertEqual(ws['tasks']['source'], str(FIXTURES / 'ws-pre3' / 'board.md'))
        self.assertEqual(sorted(ws['tasks']['unmapped']), ['', '\U0001F937 dunno'])
        self.assertIn('ws-pre3', markdown)
        self.assertIn(str(FIXTURES / 'ws-pre3' / 'board.md'), markdown)

    def test_c1_schema3_bucket_and_counts(self):
        data, _ = self.report(workspaces=['ws-three'])
        ws = data['workspaces']['ws-three']
        self.assertEqual(ws['bucket']['value'], '3')
        self.assertEqual(ws['tasks']['value'], {'Draft': 1, 'Ready to run': 1, 'In progress': 1, 'Complete': 1})
        self.assertEqual(ws['tasks']['unmapped'], [])

    def test_c1_schema4_bucket_and_every_canonical_state(self):
        data, _ = self.report(workspaces=['ws-four'])
        ws = data['workspaces']['ws-four']
        self.assertEqual(ws['bucket']['value'], '4')
        self.assertEqual(ws['tasks']['value'], {
            'Draft': 1, 'Ready to run': 1, 'In progress': 1, 'Checking': 1, 'Complete': 1,
            'Blocked': 1, 'Interrupted': 1, 'Skipped': 1, 'Unverifiable': 1,
        })

    def test_c1_schema5_bucket_and_waiting_on_owner(self):
        data, _ = self.report(workspaces=['ws-five'])
        ws = data['workspaces']['ws-five']
        self.assertEqual(ws['bucket']['value'], '5')
        self.assertEqual(ws['tasks']['value'], {'Draft': 1, 'Waiting on owner': 1})

    def test_c1_lite_bucket_has_no_board(self):
        data, _ = self.report(workspaces=['ws-lite'])
        ws = data['workspaces']['ws-lite']
        self.assertEqual(ws['bucket'], {'value': 'lite', 'source': str(FIXTURES / 'ws-lite' / 'plan.md')})
        self.assertEqual(ws['tasks'], {'value': 'n/a', 'source': None, 'unmapped': []})

    def test_c1_unknown_bucket_on_a_workspace_with_no_recognized_file(self):
        data, _ = self.report(workspaces=['ws-unknown'])
        ws = data['workspaces']['ws-unknown']
        self.assertEqual(ws['bucket'], {'value': 'unknown', 'source': None})
        self.assertEqual(ws['tasks'], {'value': 'n/a', 'source': None, 'unmapped': []})
        self.assertEqual(ws['attempts'], {'value': 'n/a', 'rows_used': 0, 'rows_skipped': 0, 'source': None})
        self.assertEqual(ws['rework'], {'value': 'n/a', 'rows_used': 0, 'rows_skipped': 0, 'source': None})
        self.assertEqual(ws['reopenings'], {'value': 'n/a', 'source': None})
        self.assertEqual(ws['tokens'], {'value': 'n/a', 'source': None})

    def test_c1_two_board_files_is_unknown_not_a_guess(self):
        # migrate.md#schema-keyed-migration: "a workspace matching more than one row is unknown".
        data, _ = self.report(workspaces=['ws-ambiguous'])
        self.assertEqual(data['workspaces']['ws-ambiguous']['bucket']['value'], 'unknown')

    def test_docs_plans_help_shaped_empty_workspace_never_crashes(self):
        # A workspace directory can be named like a CLI flag (this tool must never treat a slug as
        # an option) and can hold nothing at its root but an empty subdirectory -- an abandoned or
        # never-populated workspace. Both must resolve to "unknown"/"n/a", never a crash.
        with tempfile.TemporaryDirectory() as tmp:
            plans = Path(tmp) / 'plans'
            (plans / '--help' / 'points').mkdir(parents=True)
            data, _ = self.report(plans=plans)
            ws = data['workspaces']['--help']
            self.assertEqual(ws['bucket'], {'value': 'unknown', 'source': None})
            self.assertEqual(ws['tasks']['value'], 'n/a')

    # ---- C2: v2 ledger sums, used/skipped rows, integer/n-a/malformed cells ----

    def test_c2_ledger_sums_integers_and_counts_used_and_skipped_rows(self):
        data, markdown = self.report(workspaces=['ws-four'])
        ws = data['workspaces']['ws-four']
        source = str(FIXTURES / 'ws-four' / 'resource-usage.md')
        self.assertEqual(ws['attempts'], {'value': 6, 'rows_used': 2, 'rows_skipped': 1, 'source': source})
        self.assertEqual(ws['rework'], {'value': 8, 'rows_used': 2, 'rows_skipped': 1, 'source': source})
        self.assertIn(source, markdown)

    def test_c2_no_v2_ledger_is_n_a(self):
        data, _ = self.report(workspaces=['ws-three'])
        ws = data['workspaces']['ws-three']
        self.assertEqual(ws['attempts'], {'value': 'n/a', 'rows_used': 0, 'rows_skipped': 0, 'source': None})
        self.assertEqual(ws['rework'], {'value': 'n/a', 'rows_used': 0, 'rows_skipped': 0, 'source': None})

    # ---- C3: reopenings from the strict "- <task id> -> <State>" history line ----

    def test_c3_counts_complete_to_earlier_state_reopenings_and_ignores_from_state_prose(self):
        data, _ = self.report(workspaces=['ws-four'])
        source = str(FIXTURES / 'ws-four' / 'history.md')
        self.assertEqual(data['workspaces']['ws-four']['reopenings'], {'value': 2, 'source': source})

    def test_c3_transition_lines_with_no_reopening_is_zero_not_n_a(self):
        data, _ = self.report(workspaces=['ws-five'])
        source = str(FIXTURES / 'ws-five' / 'history.md')
        self.assertEqual(data['workspaces']['ws-five']['reopenings'], {'value': 0, 'source': source})

    def test_c3_history_with_no_transition_lines_is_n_a_but_names_the_source(self):
        data, _ = self.report(workspaces=['ws-no-transitions'])
        source = str(FIXTURES / 'ws-no-transitions' / 'history.md')
        self.assertEqual(data['workspaces']['ws-no-transitions']['reopenings'], {'value': 'n/a', 'source': source})

    def test_c3_absent_history_is_n_a_with_no_source(self):
        data, _ = self.report(workspaces=['ws-lite'])
        self.assertEqual(data['workspaces']['ws-lite']['reopenings'], {'value': 'n/a', 'source': None})

    # ---- C4: telemetry sums, absence, and cumulative session-snapshot de-duplication ----

    def test_c4_sums_two_role_scoped_captures(self):
        data, markdown = self.report(workspaces=['ws-telemetry-two'])
        source = str(FIXTURES / 'ws-telemetry-two' / 'resource-usage.telemetry.jsonl')
        self.assertEqual(data['workspaces']['ws-telemetry-two']['tokens'], {
            'value': {'role': {'input_tokens': 150, 'output_tokens': 275,
                               'cache_read_tokens': 10, 'cache_write_tokens': 6}},
            'source': source,
        })
        self.assertIn(source, markdown)

    def test_c4_no_sidecar_is_n_a(self):
        data, _ = self.report(workspaces=['ws-telemetry-none'])
        self.assertEqual(data['workspaces']['ws-telemetry-none']['tokens'], {'value': 'n/a', 'source': None})

    def test_c4_cumulative_session_snapshots_use_latest_not_sum(self):
        # A real capture's own provenance can label it a "session snapshot at capture"; this tool
        # reads that as a later capture for the same scope_id superseding an earlier one, not
        # adding to it (usage-observability.md: scopes are never mixed; "Session/account data is
        # never allocated, divided, or delta-inferred into a role"). Three session rows share one
        # scope_id out of chronological order; only the latest (captured_at 02:00) must count. A
        # role row with a different scope_id sums independently. A metric absent everywhere in a
        # scope is "n/a", never invented as 0.
        data, _ = self.report(workspaces=['ws-telemetry-cumulative'])
        tokens = data['workspaces']['ws-telemetry-cumulative']['tokens']['value']
        self.assertEqual(tokens['session'], {'input_tokens': 40, 'output_tokens': 80,
                                             'cache_read_tokens': 'n/a', 'cache_write_tokens': 'n/a'})
        self.assertEqual(tokens['role'], {'input_tokens': 5, 'output_tokens': 9,
                                          'cache_read_tokens': 2, 'cache_write_tokens': 'n/a'})


class EffortSplitTests(unittest.TestCase):
    """C5: a temporary git repository whose commits touch each class, including one commit that
    spans classes. Uses its own disposable git repository (a fresh `git init` in a temporary
    directory, never the real working tree), isolated from the operator's own git config so it
    depends on, and changes, nothing outside itself."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / 'repo'
        self.repo.mkdir()
        self.git('init', '-q')
        self.git('commit', '-q', '--allow-empty', '-m', 'init')
        self.since = self.git('rev-parse', 'HEAD').stdout.strip()

    def git(self, *args, env=None):
        full = dict(os.environ, **GIT_ENV, **(env or {}))
        result = subprocess.run(['git', '-C', str(self.repo)] + list(args), capture_output=True, text=True, env=full)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def write(self, relative, text):
        target = self.repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    def commit(self, message):
        self.git('add', '-A')
        self.git('commit', '-q', '-m', message)

    def test_c5_lines_and_commits_by_class_including_a_spanning_commit(self):
        self.write('SKILL.md', 'line1\nline2\nline3\n')                 # skill: +3
        self.write('references/x.md', 'a\nb\n')                        # skill: +2
        self.commit('skill commit')                                     # commit A: skill

        self.write('eval/y.py', 'w\nx\ny\nz\n')                        # evaluation: +4
        self.commit('evaluation commit')                                # commit B: evaluation

        self.write('maintaining/z.py', 'm\nn\n')                       # maintenance: +2
        self.write('SKILL.md', 'line1\nline2\nline3\nline4\n')          # skill: +1 (pure append)
        self.commit('spanning commit')                                  # commit C: maintenance + skill

        self.write('docs/w.md', 'p\nq\nr\n')                           # other: +3
        self.commit('other commit')                                     # commit D: other

        out = Path(self.tmp.name) / 'out'
        out.mkdir()
        with tempfile.TemporaryDirectory() as plans_tmp:
            child = run_cli(['--plans', plans_tmp, '--repo', self.repo, '--since', self.since,
                             '--json', out / 'r.json', '--markdown', out / 'r.md'])
        self.assertEqual(child.returncode, 0, child.stderr)
        split = json.loads((out / 'r.json').read_text())['effort_split']
        self.assertEqual(split['classes']['skill'], {'lines': 6, 'commits': 2, 'ratio': 0.4})
        self.assertEqual(split['classes']['evaluation'], {'lines': 4, 'commits': 1, 'ratio': 0.2667})
        self.assertEqual(split['classes']['maintenance'], {'lines': 2, 'commits': 1, 'ratio': 0.1333})
        self.assertEqual(split['classes']['other'], {'lines': 3, 'commits': 1, 'ratio': 0.2})
        self.assertEqual(split['total_lines'], 15)
        self.assertEqual(split['total_commits'], 4)
        markdown = (out / 'r.md').read_text()
        self.assertIn('0.4000', markdown)
        self.assertIn('0.2667', markdown)

    def test_c5_since_boundary_is_exclusive_and_empty_range_is_n_a_not_zero_division(self):
        out = Path(self.tmp.name) / 'out2'
        out.mkdir()
        with tempfile.TemporaryDirectory() as plans_tmp:
            child = run_cli(['--plans', plans_tmp, '--repo', self.repo, '--since', self.since,
                             '--until', self.since, '--json', out / 'r.json', '--markdown', out / 'r.md'])
        self.assertEqual(child.returncode, 0, child.stderr)
        split = json.loads((out / 'r.json').read_text())['effort_split']
        for cls in ('skill', 'evaluation', 'maintenance', 'other'):
            self.assertEqual(split['classes'][cls], {'lines': 0, 'commits': 0, 'ratio': 'n/a'})
        self.assertEqual(split['total_commits'], 0)


class ReadOnlyAndDeterminismTests(unittest.TestCase):
    """C6: every fixture workspace, hashed before and after, is unchanged. Also a cheap,
    direct test of the Goal's "deterministic": two runs over the same inputs are byte-identical
    (no wall-clock stamp may leak into either output)."""

    def test_c6_plans_tree_is_untouched_by_a_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            plans = copy_plans(Path(tmp) / 'plans')
            before = hash_tree(plans)
            out = Path(tmp) / 'out'
            out.mkdir()
            child = run_cli(['--plans', plans, '--repo', RealRepoFixture.path, '--since', RealRepoFixture.since,
                             '--until', RealRepoFixture.until, '--json', out / 'r.json', '--markdown', out / 'r.md'])
            self.assertEqual(child.returncode, 0, child.stderr)
            after = hash_tree(plans)
        self.assertEqual(before, after)

    def test_two_runs_over_the_same_inputs_are_byte_identical(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'out'
            out.mkdir()
            args = lambda n: ['--plans', FIXTURES, '--repo', RealRepoFixture.path, '--since', RealRepoFixture.since,
                              '--until', RealRepoFixture.until, '--json', out / ('%d.json' % n),
                              '--markdown', out / ('%d.md' % n)]
            self.assertEqual(run_cli(args(1)).returncode, 0)
            self.assertEqual(run_cli(args(2)).returncode, 0)
            self.assertEqual((out / '1.json').read_bytes(), (out / '2.json').read_bytes())
            self.assertEqual((out / '1.md').read_bytes(), (out / '2.md').read_bytes())
            text = (out / '1.json').read_text()
        self.assertNotIn('generated', text.lower())

    def test_own_test_family_directory_is_never_modified(self):
        # A real --repo argument is used above; hash this test family's own directory (fixtures
        # included) before and after, so a bug that wrote into it would be caught here too.
        before = hash_tree(ROOT / 'eval' / 'field-report')
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'out'
            out.mkdir()
            child = run_cli(['--plans', FIXTURES, '--repo', RealRepoFixture.path, '--since', RealRepoFixture.since,
                             '--until', RealRepoFixture.until, '--json', out / 'r.json', '--markdown', out / 'r.md'])
            self.assertEqual(child.returncode, 0, child.stderr)
        after = hash_tree(ROOT / 'eval' / 'field-report')
        self.assertEqual(before, after)


class RefusalTests(unittest.TestCase):
    """C7: --repo that is not a git work tree exits 2 and writes nothing. Also two related,
    cheap usage-error checks for the same "nothing is written" contract."""

    def test_c7_repo_not_a_git_work_tree_refuses_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            not_a_repo = Path(tmp) / 'not-a-repo'
            not_a_repo.mkdir()
            out = Path(tmp) / 'out'
            out.mkdir()
            json_path, md_path = out / 'r.json', out / 'r.md'
            child = run_cli(['--plans', FIXTURES, '--repo', not_a_repo, '--since', 'HEAD',
                             '--json', json_path, '--markdown', md_path])
        self.assertEqual(child.returncode, 2)
        self.assertFalse(json_path.exists())
        self.assertFalse(md_path.exists())

    def test_unresolvable_since_revision_refuses_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'out'
            out.mkdir()
            json_path, md_path = out / 'r.json', out / 'r.md'
            child = run_cli(['--plans', FIXTURES, '--repo', RealRepoFixture.path,
                             '--since', 'not-a-real-revision-marker', '--json', json_path, '--markdown', md_path])
        self.assertEqual(child.returncode, 2)
        self.assertFalse(json_path.exists())
        self.assertFalse(md_path.exists())

    def test_unknown_requested_workspace_refuses_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'out'
            out.mkdir()
            json_path, md_path = out / 'r.json', out / 'r.md'
            child = run_cli(['--plans', FIXTURES, '--repo', RealRepoFixture.path, '--since', 'HEAD',
                             '--until', 'HEAD', '--workspace', 'does-not-exist',
                             '--json', json_path, '--markdown', md_path])
        self.assertEqual(child.returncode, 2)
        self.assertFalse(json_path.exists())
        self.assertFalse(md_path.exists())


if __name__ == '__main__':
    unittest.main()
