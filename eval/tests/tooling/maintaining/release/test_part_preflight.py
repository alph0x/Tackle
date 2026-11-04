"""A release part runs the committed-text preflight after applying its edit and before staging it.

Guarantee: `steps.py --phase part` refuses to stage or commit when the committed-text preflight finds a
workspace-shaped identifier added since the previous release, leaving HEAD and the index untouched; a clean
part still commits, with the preflight recorded before the stage.
Concrete fault: a release part stages and commits first and only a later phase inspects committed text.
Consumer: the standing release procedure. Valid alternative: a clean candidate commits exactly as before.
Each case builds a disposable repository; nothing is written inside this repository.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[5]
STEPS = ROOT / 'maintaining/release/steps.py'
README = ('**Tackle 2.3.3** · Model-agnostic\n'
          "npx skills add 'https://github.com/example-org/Tackle.git#v2.3.3' --skill tackle\n"
          'Public routes have not been probed for 2.3.3.\n'
          'The migration catalog targets Tackle 2.3.3 and older plans.\n'
          'with 4 installation-relative files\nagainst the 4 expected files\n'
          '### What the scripts do\n| Scripts |\n|---|\n| `b.py`, `a.py` |\n| `tool/` |\n'
          '### Next\n')


class PartPreflight(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(os.path.realpath(temp.name))
        self.repo = self.root / 'candidate'
        self.workspace = self.root / 'main/docs/plans/relfixture'
        self.workspace.mkdir(parents=True)
        (self.repo / 'eval/rules').mkdir(parents=True)
        shutil.copy2(ROOT / 'eval/rules/committed_text.py', self.repo / 'eval/rules/committed_text.py')
        catalog = self.repo / 'skills/tackle/references/guides/migration-catalog.json'
        catalog.parent.mkdir(parents=True)
        catalog.write_text(json.dumps({'target_methodology': '2.3.4'}) + '\n')
        for name in ('a.py', 'b.py', 'tool/inside.py'):
            script = self.repo / 'skills/tackle/scripts' / name
            script.parent.mkdir(parents=True, exist_ok=True)
            script.write_text('# fixture\n')
        (self.repo / 'eval/records').mkdir(parents=True)
        (self.repo / 'eval/records/claims.json').write_text(json.dumps({'claims': [{'section': 'old'}]}, indent=1) + '\n')
        (self.repo / 'CHANGELOG.md').write_text('# Tackle changelog\n\n## Tackle 2.3.3\n')
        (self.repo / 'README.md').write_text(README)
        self.env = dict(os.environ, GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
                        GIT_AUTHOR_NAME='fixture', GIT_AUTHOR_EMAIL='fixture@invalid',
                        GIT_COMMITTER_NAME='fixture', GIT_COMMITTER_EMAIL='fixture@invalid')
        self.git('init', '-q')
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture')
        self.git('tag', 'v2.3.3')

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], env=self.env, text=True).strip()

    def part(self, part='readme', claims=None, attack=None):
        base = self.git('rev-parse', 'HEAD')
        self.git('switch', '-qc', 'release-2.3.4')
        runtime = {'path': sys.executable, 'version': list(sys.version_info[:3])}
        entry, record = self.workspace / 'entry', self.workspace / 'record'
        entry.write_text('## Tackle 2.3.4\n\nChanges.\n')
        record.write_text('Release record.\n')
        config = {'schema': 'tackle-release/1', 'version': '2.3.4', 'from_version': '2.3.3', 'base': base,
                  'branch': 'release-2.3.4', 'catalog_revision': [1, 2],
                  'runtimes': {'py310': runtime, 'py314': runtime}, 'workspace': str(self.workspace),
                  'initiative': 'relfixture', 'changelog': {'path': str(entry), 'sha256': hashlib.sha256(entry.read_bytes()).hexdigest()},
                  'record': {'path': str(record), 'sha256': hashlib.sha256(record.read_bytes()).hexdigest(),
                             'destination': 'eval/records/demo.md'},
                  'claims': claims or [], 'parts': [part], 'install_count': 4, 'expected_ledger_gate': '',
                  'expected_sweep': '', 'gating_workspaces': ['relfixture']}
        if attack:
            key, kind = attack
            if kind in ('outside', 'symlink'):
                outside = self.root / ('outside-' + key)
                original = entry if key == 'changelog.path' else record
                outside.write_bytes(original.read_bytes())
                target = outside
                if kind == 'symlink':
                    target = self.workspace / ('link-' + key)
                    target.symlink_to(outside)
                config[key.split('.')[0]]['path'] = str(target)
            else:
                config['record']['destination'] = '../outside-report.md'
        path = self.root / 'release.json'
        path.write_text(json.dumps(config))
        if attack:
            result = subprocess.run(
                [sys.executable, '-I', '-B', str(ROOT / 'maintaining/release/release_edit.py'),
                 '--config', str(path), '--repo', str(self.repo), '--workspace', str(self.workspace),
                 '--candidate', base, '--records', str(self.root / 'editor-records'),
                 '--version', '2.3.4', '--from-version', '2.3.3', '--part', part],
                cwd=self.repo, env=self.env, capture_output=True, text=True)
            return base, result
        records = self.root / 'records'
        result = subprocess.run([sys.executable, '-I', '-B', str(STEPS), '--config', str(path), '--repo', str(self.repo),
                                 '--records', str(records), '--phase', 'part', '--part', part],
                                cwd=self.root, env=self.env, capture_output=True, text=True)
        phase = json.loads((records / ('part-' + part) / 'phase.json').read_text())
        return base, result, [item['name'] for item in phase['results']], {item['name']: item for item in phase['results']}

    def test_identifier_added_since_release_blocks_before_staging(self):
        (self.repo / 'notes.md').write_text('Carried over from ' + '-'.join(('T', str(7).zfill(2))) + '.\n')
        self.git('add', 'notes.md')
        self.git('commit', '-qm', 'notes')
        before = self.git('ls-files', '-s')
        base, result, order, facts = self.part()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertFalse(facts['committed-preflight']['met'])
        self.assertNotIn('stage', order)
        self.assertNotIn('commit', order)
        self.assertEqual(self.git('rev-parse', 'HEAD'), base)
        self.assertEqual(self.git('diff', '--cached', '--name-only'), '')
        self.assertEqual(self.git('ls-files', '-s'), before)

    def test_clean_part_commits_after_the_preflight(self):
        base, result, order, facts = self.part()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(facts['committed-preflight']['met'])
        self.assertLess(order.index('second'), order.index('committed-preflight'))
        self.assertLess(order.index('committed-preflight'), order.index('stage'))
        self.assertEqual(self.git('rev-parse', 'HEAD^'), base)
        self.assertEqual(self.git('log', '-1', '--format=%s'), 'Point the README at Tackle 2.3.4')
        self.assertEqual(self.git('status', '--porcelain'), '')

    def assert_refused(self, expected):
        before = self.git('ls-files', '-s')
        base, result, order, facts = self.part()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertFalse(facts['apply']['met'])
        self.assertIn(expected, (self.root / 'records/part-readme/apply.stderr').read_text())
        self.assertEqual(self.git('rev-parse', 'HEAD'), base)
        self.assertEqual(self.git('ls-files', '-s'), before)

    def test_stale_count_refuses(self):
        path = self.repo / 'README.md'
        path.write_text(README.replace('with 4 installation-relative files', 'with 3 installation-relative files'))
        self.git('add', 'README.md')
        self.git('commit', '-qm', 'stale count')
        self.assert_refused('with 4 installation-relative files')

    def test_missing_script_refuses(self):
        (self.repo / 'skills/tackle/scripts/new.py').write_text('# new\n')
        path = self.repo / 'README.md'
        path.write_text(README.replace(' 4 ', ' 5 '))
        self.git('add', '.')
        self.git('commit', '-qm', 'new script')
        self.assert_refused('new.py')

    def test_extra_script_refuses(self):
        path = self.repo / 'README.md'
        path.write_text(README.replace('`b.py`', '`extra.py`, `b.py`'))
        self.git('add', 'README.md')
        self.git('commit', '-qm', 'extra script')
        self.assert_refused('extra.py')

    def test_untracked_files_do_not_count(self):
        script = self.repo / 'skills/tackle/scripts/untracked.py'
        script.write_text('# untracked\n')
        cache = self.repo / 'skills/tackle/scripts/__pycache__/x.pyc'
        cache.parent.mkdir()
        cache.write_bytes(b'cache')
        result = subprocess.run([sys.executable, '-I', str(ROOT / 'maintaining/release/readme_currency.py'),
                                 '--repo', str(self.repo)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_changelog_without_claims(self):
        before = (self.repo / 'eval/records/claims.json').read_bytes()
        for key, kind in (('changelog.path', 'outside'), ('record.path', 'outside'),
                          ('changelog.path', 'symlink'), ('record.path', 'symlink'),
                          ('record.destination', 'parent')):
            with self.subTest(key=key, kind=kind):
                fixture = PartPreflight('test_changelog_without_claims')
                fixture.setUp()
                try:
                    index = fixture.git('ls-files', '-s')
                    head, refusal = fixture.part('changelog', attack=(key, kind))
                    self.assertNotEqual(refusal.returncode, 0, refusal.stdout + refusal.stderr)
                    self.assertIn(key, refusal.stderr)
                    self.assertNotIn('rolled back', refusal.stderr)
                    self.assertFalse((fixture.root / 'outside-report.md').exists())
                    self.assertEqual(fixture.git('rev-parse', 'HEAD'), head)
                    self.assertEqual(fixture.git('ls-files', '-s'), index)
                    self.assertEqual(fixture.git('status', '--porcelain'), '')
                finally:
                    fixture.doCleanups()
        base, result, _, _ = self.part('changelog')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.git('diff', '--name-only', base, 'HEAD').splitlines(),
                         ['CHANGELOG.md', 'eval/records/demo.md'])
        self.assertEqual((self.repo / 'eval/records/claims.json').read_bytes(), before)
        self.assertEqual(self.git('status', '--porcelain'), '')

    def test_changelog_with_claims(self):
        claim = {'source': 'CHANGELOG.md', 'section': 'Tackle 2.3.4', 'unit': 'Changes.',
                 'kind': 'test', 'reason': 'fixture'}
        base, result, _, _ = self.part('changelog', [claim])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.git('diff', '--name-only', base, 'HEAD').splitlines(),
                         ['CHANGELOG.md', 'eval/records/claims.json', 'eval/records/demo.md'])
        self.assertEqual(json.loads((self.repo / 'eval/records/claims.json').read_text())['claims'],
                         [claim, {'section': 'old'}])
        self.assertEqual(self.git('log', '-1', '--format=%B'), 'Record the Tackle 2.3.4 changes')
        self.assertEqual(self.git('status', '--porcelain'), '')


if __name__ == '__main__':
    unittest.main()
