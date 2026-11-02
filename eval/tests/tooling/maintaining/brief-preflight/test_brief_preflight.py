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
