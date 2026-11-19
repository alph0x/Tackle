import importlib.util
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[5] / 'maintaining/brief_preflight.py'
spec = importlib.util.spec_from_file_location('brief_preflight', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CommandForms(unittest.TestCase):
    def test_unittest_path_refused(self):
        findings = []
        module.commands('`python3 -m unittest path/to/test.py`', findings)
        self.assertEqual(findings[0]['kind'], 'unittest-path-form')

    def test_discovery_accepted(self):
        findings = []
        module.commands('`python3 -m unittest -v discover -s tests`', findings)
        self.assertEqual(findings, [])
        header = '- **Detail**: full\n\n## Required checks\n\n'
        bindings = {
            'cwd': '- **Working directory (cwd)**: `/checkout`',
            'native pass': '- **Native pass condition**: exit 0.',
            'evidence': '- **Evidence destination**: `/records/check`',
        }

        def check(name, omitted=None):
            return ('### Check: ' + name + '\n\nCommand:\n\n```sh\n'
                    + 'python3 -B ' + name + '.py\n```\n'
                    + '\n'.join(value for key, value in bindings.items()
                                if key != omitted) + '\n')

        findings = []
        module.commands(header + check('first') + '\n' + check('second'), findings)
        self.assertEqual(findings, [])
        for missing in bindings:
            with self.subTest(missing=missing):
                findings = []
                module.commands(header + check('first') + '\n'
                                + check('second', missing), findings)
                self.assertEqual(len(findings), 1)
                self.assertIn('second.py', findings[0]['detail'])
                self.assertIn(missing, findings[0]['detail'])
        findings = []
        module.commands(
            header + 'All required mechanical checks use the common working directory '
            '(cwd) `/checkout`.\n'
            'The common native pass condition is exit 0.\n'
            'The declared evidence records root is `/records`.\n\n'
            + check('first', 'cwd').replace(bindings['native pass'] + '\n', '')
            + '\n' + check('second', 'cwd').replace(bindings['native pass'] + '\n', ''),
            findings,
        )
        self.assertEqual(findings, [])

        findings = []
        module.commands(
            header + 'For `python3 check_a.py` only: cwd `/checkout`; '
            'require exit 0; evidence destination `/records/a`.\n\n'
            '```sh\npython3 check_a.py\npython3 check_b.py\n```\n',
            findings,
        )
        self.assertEqual(len(findings), 1)
        self.assertIn('python3 check_b.py', findings[0]['detail'])
        for binding in bindings:
            self.assertIn(binding, findings[0]['detail'])

        for directory in ('Working directory for every command',
                          'Default cwd for every command'):
            for condition in ('Require exit 0.',
                              'Native pass condition: return code 0.',
                              'Native pass condition: command exits successfully.',
                              'Native pass condition: expected exit 2 and the '
                              'diagnostic names the invalid input.'):
                with self.subTest(directory=directory, condition=condition):
                    findings = []
                    module.commands(
                        '- **Detail**: full\n\n## Context\n\n'
                        + directory + ': `/checkout`.\n\n## Check\n\n'
                        + condition + '\nEvidence destination: `/records/a`.\n\n'
                        '```sh\npython3 check_a.py\n```\n',
                        findings,
                    )
                    self.assertEqual(findings, [])

        findings = []
        module.commands(header + '`python3 -I -B check_a.py`\n', findings)
        self.assertEqual(len(findings), 1)
        self.assertIn('python3 -I -B check_a.py', findings[0]['detail'])
        for binding in bindings:
            self.assertIn(binding, findings[0]['detail'])

        for command, label in (
            ('sh smoke.sh', ''),
            ('make check', 'Command: '),
            ("python3.10 -c 'raise SystemExit(0)'", ''),
            ("python -c 'raise SystemExit(0)'", ''),
            ('make verify', 'Check: '),
            ('python3 -I -B check_a.py', 'Required command: '),
            ('python3 -I -B check_b.py', 'Run: '),
        ):
            for omitted in (None, *bindings):
                with self.subTest(command=command, omitted=omitted):
                    findings = []
                    module.commands(
                        '- **Detail**: full\n\n## Required mechanical check\n\n'
                        + '\n'.join(value for key, value in bindings.items()
                                    if key != omitted)
                        + '\n\n' + label + '`' + command + '`\n',
                        findings,
                    )
                    if omitted is None:
                        self.assertEqual(findings, [])
                    else:
                        self.assertEqual(len(findings), 1)
                        self.assertIn(command, findings[0]['detail'])
                        self.assertIn(omitted, findings[0]['detail'])

        findings = []
        module.commands(
            '- **Detail**: full\n\n## Notes\n\n'
            '`source data`\n\n'
            'Use `python3 -I -B for isolated scripts` and `/checkout`.\n',
            findings,
        )
        self.assertEqual(findings, [])

        for directory, valid in (
            ('Working directory (cwd): not supplied.', False),
            ('Working directory (cwd): `/checkout`.', True),
        ):
            with self.subTest(directory=directory):
                findings = []
                module.commands(
                    header + directory + '\nNative pass condition: return code 0.\n'
                    'Evidence destination: `/records/check`.\n\n'
                    '```sh\npython3 check_a.py\n```\n',
                    findings,
                )
                if valid:
                    self.assertEqual(findings, [])
                else:
                    self.assertEqual(len(findings), 1)
                    self.assertIn('python3 check_a.py', findings[0]['detail'])
                    self.assertIn('cwd', findings[0]['detail'])

        for records, valid in (
            ('The common evidence records root is `/records`.', False),
            ('The common evidence records root is `/records` '
             'with alpha and beta records.', True),
            ('The common evidence records root is `/records`; '
             'alpha.py uses a, beta.py uses b.', True),
            ('The common evidence records root is `/records`; '
             '`alpha.py` uses `a`; `beta.py` uses `b`.', True),
            ('The common evidence records root is `/records`; '
             'alpha.py uses a, beta.py uses a.', False),
            ('The common evidence records root is `/records` '
             'with alpha and beta records; '
             'alpha.py uses a, beta.py uses a.', False),
        ):
            with self.subTest(records=records):
                findings = []
                module.commands(
                    '- **Detail**: full\n\n'
                    'Common cwd for every command: `/checkout`.\n'
                    'All required mechanical checks require exit 0.\n'
                    + records + '\n\n## Checks\n\n'
                    '```sh\npython3 alpha.py\npython3 beta.py\n```\n',
                    findings,
                )
                if valid:
                    self.assertEqual(findings, [])
                else:
                    self.assertEqual(len(findings), 2)
                    for command in ('python3 alpha.py', 'python3 beta.py'):
                        self.assertTrue(any(command in finding['detail']
                                            and 'evidence' in finding['detail']
                                            for finding in findings))

        findings = []
        module.commands(
            '- **Detail**: full\n\n## Notes\n\n'
            'Command: `make check`\n',
            findings,
        )
        self.assertEqual(len(findings), 1)
        self.assertIn('make check', findings[0]['detail'])
        for binding in bindings:
            self.assertIn(binding, findings[0]['detail'])

        findings = []
        module.commands(
            '- **Detail**: full\n\n## Required mechanical checks\n\n'
            'For `sh first.sh` only: cwd `/checkout`; require exit 0; '
            'evidence destination `/records/first`.\n\n'
            '`sh first.sh`\n\n`make second`\n',
            findings,
        )
        self.assertEqual(len(findings), 1)
        self.assertIn('make second', findings[0]['detail'])
        for binding in bindings:
            self.assertIn(binding, findings[0]['detail'])

        findings = []
        module.commands(
            header + 'Working directory (cwd): `/checkout`.\n'
            'Require exit 0.\nEvidence destination: `/records/a`.\n\n'
            '`python3 check_a.py`\n',
            findings,
        )
        self.assertEqual(findings, [])

        findings = []
        module.commands(
            header + 'Use `python3 -I -B for isolated scripts` and `/checkout`.\n',
            findings,
        )
        self.assertEqual(findings, [])

        findings = []
        module.commands(
            '- **Detail**: full\n\n'
            'Common cwd for every command: `/checkout`.\n\n## Check\n\n'
            'For `python3 alpha.py` only: require exit 0;\n'
            'evidence destination: `/records/a`.\n\n'
            '```sh\npython3 alpha.py\npython3 beta.py\n```\n',
            findings,
        )
        self.assertEqual(len(findings), 1)
        self.assertIn('python3 beta.py', findings[0]['detail'])
        self.assertIn('native pass', findings[0]['detail'])
        self.assertIn('evidence', findings[0]['detail'])
        self.assertNotIn('cwd', findings[0]['detail'])

        findings = []
        module.commands(
            '- **Detail**: full\n\n'
            'Common cwd for every command: `/checkout`.\n\n## Check\n\n'
            'All required mechanical checks require exit 0;\n'
            'the common evidence records root is `/records` '
            'with alpha and beta records.\n\n'
            '```sh\npython3 alpha.py\npython3 beta.py\n```\n',
            findings,
        )
        self.assertEqual(findings, [])

    def test_multiple_changed_paths_refused(self):
        findings = []
        module.commands('`python3 run.py --changed one two`', findings)
        self.assertEqual(findings[0]['kind'], 'changed-several-paths')

    def test_import_exit_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'module.py'
            for status in (0, 7):
                path.write_text('raise SystemExit(%d)\n' % status)
                with self.assertRaises(ValueError):
                    module.load(path, 'fixture_guard')

    def test_keyboard_interrupt_propagates(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'module.py'
            path.write_text('raise KeyboardInterrupt\n')
            with self.assertRaises(KeyboardInterrupt):
                module.load(path, 'fixture_guard')


class PreflightCli(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(os.path.realpath(self.temp.name))
        self.main = self.root / 'main'
        self.tree = self.root / 'tree'
        self.main.mkdir()
        self.tree.mkdir()
        self.env = dict(os.environ, GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
                        GIT_AUTHOR_NAME='fixture', GIT_AUTHOR_EMAIL='fixture@invalid',
                        GIT_COMMITTER_NAME='fixture', GIT_COMMITTER_EMAIL='fixture@invalid')
        self.git(self.tree, 'init', '-q')
        self.workspace = self.main / 'docs/plans/example'
        (self.workspace / 'tasks').mkdir(parents=True)
        self.brief = self.workspace / 'tasks/example.md'
        self.brief.write_text('- **Write scope**: `source.py`\n')
        repo = SCRIPT.parents[1]
        for name in ('eval/check_selection.py', 'eval/rules/committed_text.py'):
            target = self.tree / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(repo / name, target)
        guide = self.tree / 'skills/tackle/references/guides/verify.md'
        guide.parent.mkdir(parents=True)
        guide.write_text('<a id="seal-integrity-command"></a>\n\n   ```sh\n   exit 0\n   ```\n')
        manifest = {'version': 1, 'suites': [{'path': 'eval/tests/sample', 'files': ['test_sample.py'],
                    'tests': 1, 'source': 'source.py', 'category': 'tooling', 'purpose': 'fixture'}]}
        mapping = {'version': 1, 'families': ['eval/tests/sample'], 'rules': [
                   {'patterns': ['source.py'], 'families': ['eval/tests/sample'], 'exclude': [], 'reason': 'fixture'}],
                   'test_source_regressions': [], 'global_patterns': [], 'ignored_patterns': []}
        (self.tree / 'eval/suite-manifest.json').write_text(json.dumps(manifest))
        (self.tree / 'eval/check-selection.json').write_text(json.dumps(mapping))
        (self.tree / 'source.py').write_text('value = 1\n')
        self.commit()

    def git(self, repo, *args):
        return subprocess.check_output(['/usr/bin/git', '-C', str(repo), *args], env=self.env, text=True).strip()

    def commit(self):
        self.git(self.tree, 'add', '-A')
        self.git(self.tree, 'commit', '-qm', 'fixture')

    def invoke(self, command, output, **values):
        args = [sys.executable, '-I', '-B', str(SCRIPT), command]
        for key, value in values.items():
            args += ['--' + key.replace('_', '-'), str(value)]
        args += ['--out', str(output)]
        return subprocess.run(args, env=self.env, capture_output=True, text=True)

    def scope(self, name):
        out = self.root / name
        result = self.invoke('scope', out, tree=self.tree, workspace=self.workspace, brief=self.brief)
        return result, out

    def test_scope_and_consumer_detection(self):
        result, out = self.scope('scope')
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        report = json.loads((out / 'preflight.json').read_text())
        self.assertEqual(report['consumers'][0]['files'], ['source.py'])
        self.assertEqual(report['consumers'][0]['selection']['families'], ['eval/tests/sample'])
        self.assertEqual(report['consumers'][0]['manifest'], ['eval/tests/sample'])
        self.assertEqual((out / 'seal.stdout').read_text(), '')

    def test_markdown_required_command_requires_bindings(self):
        header = ('- **Detail**: full\n'
                  '- **Write scope**: `source.py`\n\n'
                  '## Required checks\n\n')
        bindings = ('- **Working directory (cwd)**: `/checkout`\n'
                    '- **Native pass condition**: exit 0.\n'
                    '- **Evidence destination**: `/records/check`\n')
        self.brief.write_text(header + 'Command: `python3 verify.py`\n')
        result, out = self.scope('plain-missing-bindings')
        self.assertEqual(result.returncode, 1, result.stderr + result.stdout)

        self.brief.write_text(
            header + '- **Required command**: `python3 verify.py`\n' + bindings)
        result, out = self.scope('markdown-bound')
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(json.loads((out / 'preflight.json').read_text())['findings'], [])

        self.brief.write_text(
            header + '- **Required command**: `python3 verify.py`\n')
        result, out = self.scope('markdown-missing-bindings')
        self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
        findings = json.loads((out / 'preflight.json').read_text())['findings']
        diagnostic = json.dumps(findings).lower()
        self.assertIn('verify.py', diagnostic)
        self.assertTrue('cwd' in diagnostic or 'working directory' in diagnostic, diagnostic)

    def test_native_exit_status_condition_is_accepted(self):
        header = ('- **Detail**: full\n'
                  '- **Write scope**: `source.py`\n\n'
                  '## Required checks\n\n'
                  'Command: `python3 verify.py`\n'
                  '- **Working directory (cwd)**: `/checkout`\n')
        evidence = '- **Evidence destination**: `/records/check`\n'
        self.brief.write_text(
            header + '- **Native pass condition**: exit 0.\n' + evidence)
        result, out = self.scope('numeric-exit-bound')
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(json.loads((out / 'preflight.json').read_text())['findings'], [])

        self.brief.write_text(
            header + '- **Native pass condition**: exit status 0.\n' + evidence)
        result, out = self.scope('native-exit-status-bound')
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(json.loads((out / 'preflight.json').read_text())['findings'], [])

    def test_scope_syntax_and_registration_findings(self):
        for index, scope in enumerate(('`new.py` `other.py`', '`new.py`,', '`new.py`,, `other.py`',
                                       '`test_new.py`', '`new.py`')):
            self.brief.write_text('- **Write scope**: ' + scope + '\n')
            result, out = self.scope('syntax-' + str(index))
            self.assertEqual(result.returncode, 1, result.stderr)
            kinds = {f['kind'] for f in json.loads((out / 'preflight.json').read_text())['findings']}
            self.assertIn('write-scope-text' if index < 3 else ('unregistered-test' if index == 3 else 'unmapped-path'), kinds)

    def test_unnamed_pinned_and_hash_consumers(self):
        import hashlib
        (self.tree / 'reader.py').write_text('source.py\n')
        (self.tree / 'hash.txt').write_text(hashlib.sha256((self.tree / 'source.py').read_bytes()).hexdigest())
        self.commit()
        result, out = self.scope('consumers')
        self.assertEqual(result.returncode, 1, result.stderr)
        findings = json.loads((out / 'preflight.json').read_text())['findings']
        self.assertEqual(sum(f['kind'] == 'unnamed-consumer' for f in findings), 2)

    def test_import_failures_refuse_before_output(self):
        selection = self.tree / 'eval/check_selection.py'
        guard = self.tree / 'eval/rules/committed_text.py'
        originals = {p: p.read_bytes() for p in (selection, guard)}
        index = 0
        for path in (selection, guard):
            for code in ('raise SystemExit(0)', 'raise SystemExit(7)', 'import missing_preflight_fixture'):
                path.write_text(code + '\n')
                self.commit()
                result, out = self.scope('refusal-' + str(index))
                index += 1
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn('refused:', result.stderr)
                self.assertFalse(out.exists())
                path.write_bytes(originals[path])
                self.commit()

    def test_committed_refusals_and_untracked_scan(self):
        base = self.git(self.tree, 'rev-parse', 'HEAD')
        invalid = self.root / 'other'
        invalid.mkdir()
        out = self.root / 'invalid'
        result = self.invoke('committed', out, tree=self.tree, base=base, workspace=invalid)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(out.exists())
        marker = '-'.join(('T', '45'))
        (self.tree / 'untracked.txt').write_text(marker + '\n')
        index = Path(self.git(self.tree, 'rev-parse', '--git-path', 'index'))
        if not index.is_absolute():
            index = self.tree / index
        before = index.read_bytes()
        out = self.root / 'scan'
        result = self.invoke('committed', out, tree=self.tree, base=base, workspace=self.workspace)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn('finding: committed-text:', result.stdout)
        self.assertEqual(index.read_bytes(), before)

    def test_worktree_link_and_ignored_content(self):
        base = self.git(self.tree, 'rev-parse', 'HEAD')
        linked = self.root / 'linked'
        self.git(self.tree, 'worktree', 'add', '--detach', str(linked), base)
        out = self.root / 'linked-report'
        result = self.invoke('worktree', out, repo=self.tree, tree=linked, base=base)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        (linked / '.gitignore').write_text('ignored\n')
        (linked / 'ignored').write_text('data\n')
        out = self.root / 'dirty-report'
        result = self.invoke('worktree', out, repo=self.tree, tree=linked, base=base)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn('finding: dirty-or-ignored:', result.stdout)

    def test_scope_refusals_and_planned_paths(self):
        manifest = self.tree / 'eval/suite-manifest.json'
        manifest.unlink()
        self.commit()
        result, out = self.scope('missing-manifest')
        self.assertEqual(result.returncode, 2)
        self.assertFalse(out.exists())
        self.git(self.tree, 'checkout', 'HEAD^', '--', 'eval/suite-manifest.json')
        self.commit()
        marker = '-'.join(('T', '45'))
        self.brief.write_text('- **Write scope**: `new-' + marker + '.py`, `eval/check-selection.json`\n')
        result, out = self.scope('planned')
        self.assertEqual(result.returncode, 1, result.stderr)
        kinds = {f['kind'] for f in json.loads((out / 'preflight.json').read_text())['findings']}
        self.assertIn('planned-path-id', kinds)

    def test_committed_import_exit_refused(self):
        guard = self.tree / 'eval/rules/committed_text.py'
        base = self.git(self.tree, 'rev-parse', 'HEAD')
        for status in (0, 7):
            guard.write_text('raise SystemExit(%d)\n' % status)
            out = self.root / ('committed-exit-' + str(status))
            result = self.invoke('committed', out, tree=self.tree, base=base, workspace=self.workspace)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn('refused:', result.stderr)
            self.assertFalse(out.exists())

    def test_seal_output_is_finding(self):
        guide = self.tree / 'skills/tackle/references/guides/verify.md'
        guide.write_text('<a id="seal-integrity-command"></a>\n\n   ```sh\n   echo drift\n   exit 1\n   ```\n')
        self.commit()
        result, out = self.scope('seal')
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn('finding: seal: drift', result.stdout)
        self.assertEqual((out / 'seal.stdout').read_text(), 'drift\n')

    def test_existing_output_refused_untouched(self):
        out = self.root / 'existing'
        out.mkdir()
        marker = out / 'marker'
        marker.write_text('unchanged')
        result = self.invoke('scope', out, tree=self.tree, workspace=self.workspace, brief=self.brief)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(marker.read_text(), 'unchanged')

    def test_required_command_admission_and_data_boundaries(self):
        import re

        header = '- **Detail**: full\n- **Write scope**: `source.py`\n\n'
        common = ('- **Working directory (cwd)**: `/checkout`\n'
                  '- **Native pass condition**: exit status 0.\n')
        evidence = '- **Evidence destination**: `/records/check`\n'

        def check(name, body, expected):
            self.brief.write_text(header + body)
            result, out = self.scope(name)
            self.assertEqual(result.returncode, expected, result.stderr + result.stdout)
            findings = json.loads((out / 'preflight.json').read_text())['findings']
            if expected == 0:
                self.assertEqual(findings, [])
            return findings

        def discovered(name, body, command):
            check(name + '-bound', body + common + evidence, 0)
            findings = check(name + '-missing-evidence', body + common, 1)
            self.assertEqual(len(findings), 1, findings)
            matching = [f for f in findings
                        if command.lower() in json.dumps(f).lower()]
            self.assertEqual(len(matching), 1, findings)
            self.assertIn('evidence', json.dumps(matching[0]).lower())

        def assert_line(finding, line):
            if str(finding.get('line', '')) != str(line):
                self.assertRegex(
                    str(finding.get('detail', '')),
                    r'(?i)\bline\s*[:#]?\s*%d\b' % line,
                )

        for name, declaration in (
            ('sh', '```sh\nprintf ok\n```\n'),
            ('shell', '```shell\nprintf ok\n```\n'),
            ('bash', '```bash\nprintf \\\n  ok\n```\n'),
            ('zsh', '```zsh\nprintf ok\n```\n'),
            ('opaque-inner', '````sh\nprintf ok\n'
                             'Command: `make inner`\n'
                             '```text\nexample\n```\n````\n'),
        ):
            with self.subTest(fence=name):
                discovered('fence-' + name, declaration, 'printf')

        for label in ('Check', 'Command', 'Run', 'Required command'):
            for shape, declaration in (
                ('plain', label + ': `make check`\n'),
                ('bullet', '- ' + label + ': `make check`\n'),
                ('bold', '**' + label + '**: `make check`\n'),
                ('bullet-bold', '- **' + label + '**: `make check`\n'),
            ):
                with self.subTest(label=label, shape=shape):
                    discovered('labeled-' + label.replace(' ', '-') + '-' + shape,
                               declaration, 'make check')

        for index, heading in enumerate((
            'Acceptance and recovery',
            'Acceptance and recovery: verification',
            'Required check',
            'Required checks',
            'Required mechanical check',
            'Required mechanical checks',
            '2. REQUIRED MECHANICAL CHECKS: verification <!-- SEALED -->',
        )):
            with self.subTest(heading=heading):
                discovered('heading-' + str(index),
                           '## ' + heading + '\n\n- `make check`\n',
                           'make check')

        for name, body in (
            ('required-bare', '## Required checks\n\n`make check`\n'),
            ('required-bullet', '## Required checks\n\n- `make check`\n'),
            ('legacy-script', '`python3 verify.py`\n'),
            ('legacy-module', '`python3 -m verify`\n'),
            ('ordered-command', '## Required checks\n\n1. `make check`\n'),
            ('ordered-label', '## Required checks\n\n2. Acceptance: `make check`\n'),
            ('acceptance-command', '## Acceptance and recovery\n\n'
                                   '1. `make check`\n'),
            ('acceptance-label', '## Acceptance and recovery\n\n'
                                 '2. Recovery: `make check`\n'),
        ):
            with self.subTest(form=name):
                command = 'python3' if name.startswith('legacy-') else 'make check'
                discovered(name, body, command)

        check('trailing-bound', '## Required checks\n\n'
              'Command: `make check`; cwd `/checkout`; require exit 0; '
              'evidence destination `/records/check`\n', 0)
        findings = check('trailing-missing-evidence', '## Required checks\n\n'
                         'Command: `make check`; cwd `/checkout`; require exit 0\n', 1)
        matching = [f for f in findings if 'make check' in json.dumps(f).lower()]
        self.assertEqual(len(matching), 1, findings)
        self.assertIn('evidence', json.dumps(matching[0]).lower())

        for form, alpha, beta in (
            ('labeled', 'Command: `make alpha`', 'Command: `make beta`'),
            ('required-inline', '`make alpha`', '`make beta`'),
            ('ordered', '1. `make alpha`', '2. `make beta`'),
        ):
            with self.subTest(form=form, suffix='common'):
                check('shared-suffix-' + form, '## Required checks\n\n'
                      + alpha + '; Common cwd for every command: `/checkout`; '
                      'All required mechanical checks require exit 0.\n'
                      '- **Evidence destination**: `/records/alpha`\n\n'
                      + beta + '; evidence destination `/records/beta`\n', 0)
            with self.subTest(form=form, suffix='ordinary'):
                findings = check(
                    'ordinary-suffix-' + form, '## Required checks\n\n'
                    + alpha + '; cwd `/checkout`; require exit 0.\n'
                    '- **Evidence destination**: `/records/alpha`\n\n'
                    + beta + '; evidence destination `/records/beta`\n', 1)
                self.assertEqual(len(findings), 1, findings)
                diagnostic = json.dumps(findings[0]).lower()
                self.assertIn('make beta', diagnostic)
                self.assertNotIn('make alpha', diagnostic)
                self.assertIn('cwd', diagnostic)
                self.assertIn('native', diagnostic)
                self.assertNotIn('evidence', diagnostic)
                assert_line(findings[0], 9)

        check('required-own-suffix-bound', '## Required checks\n\n'
              '`make check`; cwd `/checkout`; require exit 0; '
              'evidence destination `/records/check`\n', 0)
        findings = check('required-explanation-only', '## Required checks\n\n'
                         '`make check`; explanation only.\n', 1)
        self.assertEqual(len(findings), 1, findings)
        self.assertIn('make check', json.dumps(findings[0]).lower())
        assert_line(findings[0], 6)
        check('required-suffix-outside-context', '## Optional checks\n\n'
              '`make check`; explanation only.\n', 0)

        check('ordered-own-suffix-bound', '## Required checks\n\n'
              '1. `make check`; cwd `/checkout`; require exit 0; '
              'evidence destination `/records/check`\n', 0)
        findings = check('ordered-own-suffix-missing-evidence', '## Required checks\n\n'
                         '1. `make check`; cwd `/checkout`; require exit 0\n', 1)
        self.assertEqual(len(findings), 1, findings)
        diagnostic = json.dumps(findings[0]).lower()
        self.assertIn('make check', diagnostic)
        self.assertIn('evidence', diagnostic)
        assert_line(findings[0], 6)

        for label in ('Check', 'Command', 'Run', 'Required command'):
            for shape, introducer in (
                ('plain', label + ':'),
                ('bullet-bold', '- **' + label + '**:'),
            ):
                with self.subTest(introducer=label, shape=shape):
                    discovered('intro-' + label.replace(' ', '-') + '-' + shape,
                               introducer + '\n\n```sh\nprintf ok\n```\n',
                               'printf')

            for name, follower in (
                ('prose', 'This is prose.\n'),
                ('list', '- This is prose.\n'),
                ('heading', '## Another heading\n'),
                ('comment', '<!-- example -->\n'),
                ('text-fence', '```text\nexample\n```\n'),
                ('no-info-fence', '```\nexample\n```\n'),
                ('tilde-fence', '~~~sh\nprintf ok\n~~~\n'),
                ('incomplete-shell', '```sh\nprintf ok\n'),
                ('eof', ''),
            ):
                with self.subTest(introducer=label, follower=name):
                    findings = check(
                        'invalid-' + label.replace(' ', '-') + '-' + name,
                        '## Required checks\n\n' + label + ':\n' + follower, 1)
                    matching = [f for f in findings
                                if f.get('kind') == 'command-binding'
                                and (str(f.get('line', '')) == '6'
                                     or re.search(r'(?i)\bline\s*[:#]?\s*6\b',
                                                  str(f.get('detail', ''))))]
                    self.assertEqual(len(matching), 1, findings)
                    assert_line(matching[0], 6)
                    if name == 'tilde-fence':
                        tilde = [f for f in findings
                                 if f.get('kind') == 'command-binding'
                                 and (str(f.get('line', '')) == '7'
                                      or re.search(r'(?i)\bline\s*[:#]?\s*7\b',
                                                   str(f.get('detail', ''))))]
                        self.assertEqual(len(tilde), 1, findings)
                        assert_line(tilde[0], 7)

        for name, content in (
            ('text-fence', '```text\nCommand: `make check`\n```\n'),
            ('markdown-fence', '```markdown\n`python3 verify.py`\n```\n'),
            ('no-info-fence', '```\nRun: `make check`\n```\n'),
            ('outer-fence', '````text\n```sh\n'
                            'Command: `make check`\n```\n````\n'),
            ('indented-code', '    Check: `make check`\n'),
            ('other-bold-field', '- **Detail**: `python3 verify.py`\n'),
            ('numbered-prose', '1. Explain the result using `make check`\n'),
            ('raw-script', 'python3 verify.py\n'),
            ('raw-module', 'python3 -m verify\n'),
        ):
            with self.subTest(data=name):
                check('data-' + name, '## Required checks\n\n' + content, 0)
        check('unadmitted-heading', '## Optional checks\n\n- `make check`\n', 0)
        check('acceptance-bare-data', '## Acceptance and recovery\n\n'
              '`make check`\n', 0)
        check('judgment', '### Required judgment check: review\n\n'
              '- **Reviewer**: Independent reviewer.\n'
              '- **Rubric**: Inspect the proposed result for completeness and consistency.\n'
              'This is a judgment check and has no mechanical command.\n', 0)
        check('scenario-review', '## Scenario\n\n'
              '- Check: review: completeness by independent reviewer\n', 0)

        check('tilde-shell', '## Required checks\n\n'
              '~~~sh\nprintf ok\n~~~\n', 1)
        findings = check('malformed-bold-label', '## Required checks\n\n'
                         '- **Required command**: prose\n', 1)
        self.assertIn('command', json.dumps(findings).lower())

        findings = check('inline-then-fence', '## Required checks\n\n'
                         'Command: `make check`\n' + common + evidence + '\n'
                         '```sh\npython3 other.py\n```\n', 1)
        diagnostic = json.dumps(findings).lower()
        self.assertIn('other.py', diagnostic)
        self.assertNotIn('make check', diagnostic)

    def test_legacy_block_record_bindings(self):
        header = ('- **Detail**: full\n'
                  '- **Write scope**: `source.py`\n\n'
                  'Common cwd for every command: `/checkout`.\n'
                  'All required mechanical checks require exit 0.\n')

        def check(name, records, script, expected):
            self.brief.write_text(header + records + '\n\n'
                                  '## Required checks\n\n```sh\n' + script + '```\n')
            result, out = self.scope(name)
            self.assertEqual(result.returncode, expected, result.stderr + result.stdout)
            return json.loads((out / 'preflight.json').read_text())['findings']

        root = 'The common evidence records root is `/records`.'
        both = 'python3 alpha.py\npython3 beta.py\n'
        for name, script, commands in (
            ('root-one', 'python3 alpha.py\n', ('alpha.py',)),
            ('root-two', both, ('alpha.py', 'beta.py')),
        ):
            with self.subTest(case=name):
                findings = check(name, root, script, 1)
                self.assertEqual(len(findings), len(commands))
                for command in commands:
                    matching = [f for f in findings if command in json.dumps(f).lower()]
                    self.assertEqual(len(matching), 1)
                    diagnostic = json.dumps(matching[0]).lower()
                    self.assertIn('evidence', diagnostic)
                    if str(matching[0].get('line', '')) != '10':
                        self.assertRegex(
                            str(matching[0].get('detail', '')),
                            r'(?i)\bline\s*[:#]?\s*10\b')
                    self.assertNotIn('cwd', diagnostic)
                    self.assertNotIn('native', diagnostic)

        for index, records in enumerate((
            root + ' with alpha and beta records.',
            root + ' alpha.py uses a, beta.py uses b.',
            root + ' `alpha.py` uses `a`; `beta.py` uses `b`.',
        )):
            with self.subTest(records=records):
                self.assertEqual(check('distinct-records-' + str(index), records, both, 0), [])

        findings = check('partial-record-map', root + ' alpha.py uses a.', both, 1)
        self.assertEqual(len(findings), 1)
        diagnostic = json.dumps(findings).lower()
        self.assertIn('beta.py', diagnostic)
        self.assertIn('evidence', diagnostic)
        self.assertNotIn('alpha.py', diagnostic)

        findings = check('duplicate-record-map',
                         root + ' alpha.py uses a, beta.py uses a.', both, 1)
        self.assertEqual(len(findings), 2)
        for command in ('alpha.py', 'beta.py'):
            self.assertTrue(any(command in json.dumps(f).lower()
                                and 'evidence' in json.dumps(f).lower()
                                for f in findings))
