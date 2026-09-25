"""Registry guard (D-45/D-46/R14): no tracked eval code may mount, copy or pass a credential into a
participant environment, and no hard-coded home path may appear. Also proves the three legacy
runners' `run` entry points are retired to eval/protocol-v2/PROTOCOL.md (D-53)."""
from __future__ import annotations

import importlib.util
import io
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SELF = Path(__file__).resolve()
EXTENSIONS = ('.py', '.sh', '.js')
EXCLUDED_PREFIXES = ('eval/scenarios/', 'eval/runs/')
RETIRED = 'retired: model runs moved to the protocol v2 harness; see eval/protocol-v2/PROTOCOL.md'

# A container mount or environment option that carries an auth file, a credential file or an API
# key into a container.
CREDENTIAL_PATTERNS = (
    (re.compile(r'\.codex/auth\.json'), 'codex-auth-mount'),
    (re.compile(r'\.claude/\.credentials'), 'claude-credentials-mount'),
    (re.compile(r'dst=[^,\s\'"]*auth[^,\s\'"]*', re.IGNORECASE), 'auth-destination-mount'),
    (re.compile(r'ANTHROPIC_API_KEY|OPENAI_API_KEY'), 'named-api-key'),
    (re.compile(r'[A-Z][A-Z0-9_]*_API_KEY\s*='), 'api-key-assignment'),
)
# A hard-coded home path.
HOME_PATH_PATTERN = re.compile(r'/Users/[A-Za-z0-9_.-]+|/home/[A-Za-z0-9_.-]+')

# Exact (path, literal) pairs that are pre-existing look-alikes: other checkers' own planted leak
# or path-validation fixtures, not real credential/home-path violations in eval tooling. Exempting
# by pair (not by file) keeps teeth: a genuinely new home-path literal anywhere else, including new
# content in these same two files, still fails (see
# test_an_exempted_literal_in_a_different_file_still_fails).
HOME_PATH_EXEMPTIONS = {
    ('eval/records/test_currency.py', '/Users/somebody'),
    ('eval/records/test_currency.py', '/Users/alice'),
    ('eval/records/test_currency.py', '/home/x'),
    ('eval/protocol-v2/fixtures/build.py', '/Users/someone'),
}


def eligible(paths, guard_relative):
    """Filter a list of repo-relative path strings down to the guard's scan scope."""
    return [relative for relative in paths
            if relative.endswith(EXTENSIONS) and not relative.startswith(EXCLUDED_PREFIXES)
            and relative != guard_relative]


def tracked_files(root):
    """The tracked *.py/*.sh/*.js paths under eval/ this guard scans, read from git's path list
    (never a git blob: a path added to the index but edited on disk must be read as edited)."""
    result = subprocess.run(['git', 'ls-files', '-z', '--', 'eval'], cwd=root, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError('git ls-files failed: ' + result.stderr.decode(errors='replace'))
    paths = [entry for entry in result.stdout.decode('utf-8', 'surrogateescape').split('\0') if entry]
    guard_relative = str(SELF.relative_to(root)) if SELF.is_relative_to(root) else None
    return eligible(paths, guard_relative)


def findings_for(root, relative):
    """Every guard finding in one file, as 'path:line: rule' strings. Reads the working tree."""
    text = (root / relative).read_text(encoding='utf-8', errors='replace')
    findings = []
    for number, line in enumerate(text.splitlines(), 1):
        for pattern, rule in CREDENTIAL_PATTERNS:
            if pattern.search(line):
                findings.append('%s:%d: %s' % (relative, number, rule))
        for match in HOME_PATH_PATTERN.finditer(line):
            if (relative, match.group(0)) not in HOME_PATH_EXEMPTIONS:
                findings.append('%s:%d: home-path-literal' % (relative, number))
    return findings


def scan(root):
    findings = []
    for relative in tracked_files(root):
        findings.extend(findings_for(root, relative))
    return findings


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def init_repo(root):
    for args in (['init', '-q'], ['config', 'user.email', 'test@example.com'], ['config', 'user.name', 'Test']):
        subprocess.run(['git'] + args, cwd=root, check=True, capture_output=True)


def commit(root, relative, text):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    subprocess.run(['git', 'add', relative], cwd=root, check=True, capture_output=True)
    subprocess.run(['git', 'commit', '-q', '-m', relative], cwd=root, check=True, capture_output=True)


class RepositoryGuardTests(unittest.TestCase):
    """Case: 'guard on the repository' — tracked eval code after the fix; the guard passes."""

    def test_guard_passes_on_the_repository(self):
        files = tracked_files(ROOT)
        # No vacuous pass: the scan set must be real and must include the three retired runners.
        self.assertTrue(files, 'the scan set must not be empty')
        for expected in ('eval/clear-language/runner.py', 'eval/single-entry/behavioral.py',
                          'eval/validation-integrity/behavioral.py'):
            self.assertIn(expected, files)
        findings = scan(ROOT)
        if findings:
            print('credential guard findings:')
            print('\n'.join(findings))
        self.assertEqual(findings, [])


class FilterTests(unittest.TestCase):
    """Pure filtering logic (extension, scenarios/runs exclusion, self-exclusion); no git needed."""

    def test_scenarios_and_runs_are_excluded_by_prefix(self):
        paths = ['eval/scenarios/s1/bad.py', 'eval/runs/bad.py', 'eval/example/good.py']
        self.assertEqual(eligible(paths, None), ['eval/example/good.py'])

    def test_guard_excludes_itself(self):
        paths = ['eval/suite-integrity/test_credential_guard.py', 'eval/suite-integrity/test_discovery.py']
        self.assertEqual(eligible(paths, 'eval/suite-integrity/test_credential_guard.py'),
                         ['eval/suite-integrity/test_discovery.py'])

    def test_non_source_extensions_are_ignored(self):
        paths = ['eval/example/data.json', 'eval/example/notes.md', 'eval/example/tool.py']
        self.assertEqual(eligible(paths, None), ['eval/example/tool.py'])


class GuardTeethTests(unittest.TestCase):
    """Case: 'guard teeth' — planted positive samples and clean look-alikes in temporary files."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='tackle-credential-guard-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def plant(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return relative

    def test_planted_credential_mount_fails_with_file_and_line(self):
        # Built by concatenation so this planted sample is not itself a static-scanner match in
        # this tracked file; the guard scans the file it is WRITTEN to (bad_mount.py), never this one.
        auth_target = '/root/.co' + 'dex/auth.json'
        relative = self.plant('eval/example/bad_mount.py',
            "p = None\n"
            "command = ['--mount', f'type=bind,src={p},dst=" + auth_target + ",readonly']\n")
        findings = findings_for(self.root, relative)
        print('planted credential-mount finding:', findings)
        self.assertTrue(any(item.startswith(relative + ':2:') for item in findings), findings)

    def test_planted_env_flag_api_key_fails_in_list_form(self):
        # Docker args are built as Python list items, not a single 'flag value' string.
        key_name = 'OPENAI' + '_API_KEY'
        relative = self.plant('eval/example/bad_env.py',
            "argv = ['docker', 'run',\n"
            "        '-e', '" + key_name + "']\n")
        findings = findings_for(self.root, relative)
        print('planted -e', key_name, 'finding:', findings)
        self.assertTrue(any(item.startswith(relative + ':2:') for item in findings), findings)

    def test_planted_api_key_assignment_fails(self):
        relative = self.plant('eval/example/bad_assign.sh',
            "#!/bin/sh\n"
            "export MY_CUSTOM_API_KEY=sk-test-not-real\n")
        findings = findings_for(self.root, relative)
        print('planted _API_KEY= finding:', findings)
        self.assertTrue(any(item.startswith(relative + ':2:') for item in findings), findings)

    def test_planted_home_literal_fails(self):
        # A synthetic path, concatenated, so this developer's real checkout path is never written
        # into tracked source by this guard's own test (that literal is exactly what T-31 removes).
        home_like = '/Users/' + 'example/project'
        relative = self.plant('eval/example/bad_home.js',
            "const outside = '" + home_like + "';\n")
        findings = findings_for(self.root, relative)
        print('planted home-path finding:', findings)
        self.assertTrue(any(item.startswith(relative + ':1:') for item in findings), findings)

    def test_clean_lookalikes_pass(self):
        relative = self.plant('eval/example/clean.py',
            "import argparse\n"
            "parser.add_argument('--credential-file')\n"
            "# Do not access authentication files; ask the user to authorize.\n")
        self.assertEqual(findings_for(self.root, relative), [])

    def test_an_exempted_literal_in_a_different_file_still_fails(self):
        # '/Users/somebody' is exempted only in eval/records/test_currency.py.
        relative = self.plant('eval/example/copycat.py', "note = '/Users/somebody/.tackle/cache'\n")
        findings = findings_for(self.root, relative)
        self.assertTrue(findings, 'an exempted literal must not be exempt outside its own file')


class GitIntegrationTests(unittest.TestCase):
    """The guard reads the git path list but the working-tree bytes, over a real, disposable repo."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='tackle-credential-guard-git-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        init_repo(self.root)

    def test_scan_reads_working_tree_edits_not_the_committed_blob(self):
        auth_target = '.co' + 'dex/auth.json'
        commit(self.root, 'eval/example/thing.py', 'x = 1\n')
        (self.root / 'eval/example/thing.py').write_text("x = '" + auth_target + "'\n")
        findings = scan(self.root)
        self.assertTrue(any(item.startswith('eval/example/thing.py:1:') for item in findings), findings)

    def test_untracked_files_are_not_scanned(self):
        auth_target = '.co' + 'dex/auth.json'
        commit(self.root, 'eval/example/tracked.py', 'x = 1\n')
        (self.root / 'eval/example/untracked.py').write_text("x = '" + auth_target + "'\n")
        self.assertEqual(scan(self.root), [])

    def test_scenarios_and_runs_directories_are_excluded_when_tracked(self):
        auth_target = '.co' + 'dex/auth.json'
        commit(self.root, 'eval/scenarios/s1/bad.py', "x = '" + auth_target + "'\n")
        commit(self.root, 'eval/runs/bad.py', "x = '" + auth_target + "'\n")
        self.assertEqual(scan(self.root), [])


def stage_minimal_clear_cohort(runner, root, auth_file):
    cases = json.loads((runner.HERE / 'cases.json').read_text())
    oracle = json.loads((runner.HERE / 'oracle.json').read_text())
    cohort = root / 'cohort'
    seal = runner.prepare(cohort, {'SKILL.md': b'baseline'}, {'SKILL.md': b'candidate'},
                          cases, oracle, b'protocol', runner.SMOKE[:1])
    auth_file.write_text('not a real credential')
    return cohort, seal


class ClearLanguageRetirementTests(unittest.TestCase):
    """Case: 'CLEAR run retired' — runner.py run ...; exit 2, the pointer, no process started."""

    def test_run_is_retired_and_starts_no_process(self):
        runner = load_module('t31_guard_clear_runner', ROOT / 'eval/clear-language/runner.py')
        with tempfile.TemporaryDirectory(prefix='tackle-guard-clear-') as directory:
            root = Path(directory)
            cohort, seal = stage_minimal_clear_cohort(runner, root, root / 'dummy-auth.json')
            argv = ['runner.py', 'run', str(cohort), '--seal', seal, '--output', str(root / 'out'),
                    '--image', 'sha256:' + '0' * 64, '--model', 'test-model', '--effort', 'low',
                    '--auth', str(root / 'dummy-auth.json'), '--authorized-model-usage']
            fake_probe_result = SimpleNamespace(returncode=1, stdout=b'', stderr=b'')
            captured = io.StringIO()
            with patch.object(sys, 'argv', argv), \
                 patch.object(runner.subprocess, 'run', return_value=fake_probe_result) as mock_run, \
                 patch('sys.stderr', captured):
                with self.assertRaises(SystemExit) as ctx:
                    runner.main()
        self.assertEqual(ctx.exception.code, 2)
        self.assertIn(RETIRED, captured.getvalue())
        mock_run.assert_not_called()


class ValidationIntegrityRetirementTests(unittest.TestCase):
    """Case: 'validation-integrity run retired' — the former run entry point; exit 2, the pointer.

    No test_*.py file under eval/validation-integrity/ is in this task's write scope, so this
    retirement case is proved here instead (see the T-31 report's departure note)."""

    def test_run_is_retired_and_starts_no_process(self):
        behavioral = load_module('t31_guard_validation_integrity', ROOT / 'eval/validation-integrity/behavioral.py')
        with tempfile.TemporaryDirectory(prefix='tackle-guard-validation-') as directory:
            root = Path(directory)
            destination = root / 'dest'
            case = destination / 'case-01'
            case.mkdir(parents=True)
            (case / 'SKILL.md').write_text('test')
            (destination / 'manifest.json').write_text(json.dumps(
                {'cases': [{'id': 'case-01', 'family': 'routing', 'ordinal': 1}]}))
            argv = ['behavioral.py', 'run', str(destination), '--output', str(root / 'out')]
            fake_probe_result = SimpleNamespace(returncode=1, stdout=b'', stderr=b'')
            captured = io.StringIO()
            with patch.object(sys, 'argv', argv), \
                 patch.object(behavioral.subprocess, 'run', return_value=fake_probe_result) as mock_run, \
                 patch('sys.stderr', captured):
                with self.assertRaises(SystemExit) as ctx:
                    behavioral.main()
        self.assertEqual(ctx.exception.code, 2)
        self.assertIn(RETIRED, captured.getvalue())
        mock_run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
