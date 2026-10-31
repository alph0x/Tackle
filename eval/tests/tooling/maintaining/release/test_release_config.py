"""Release configuration contract and command-line entry point."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[5]
SPEC = importlib.util.spec_from_file_location('release_config', ROOT / 'maintaining/release/config.py')
config = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(config)


def sample():
    task = '-'.join(('T', str(7).zfill(2)))
    return {'schema': 'tackle-release/1', 'version': '2.3.4', 'from_version': '2.3.3',
            'base': 'a' * 40, 'branch': 'release-2.3.4', 'catalog_revision': [1, 2],
            'runtimes': {'py310': {'path': '/python310', 'version': [3, 10, 5]},
                         'py314': {'path': '/python314', 'version': [3, 14, 2]}},
            'workspace': '/workspace', 'initiative': 'example',
            'changelog': {'path': '/changelog', 'sha256': 'a' * 64},
            'record': {'path': '/record', 'sha256': 'b' * 64, 'destination': 'eval/records/example.md'},
            'claims': [{'source': 'CHANGELOG.md', 'section': 'Tackle 2.3.4', 'unit': task,
                        'kind': 'mention', 'reason': 'example'}],
            'parts': ['format', 'stamp', 'changelog', 'migrate', 'readme'], 'install_count': 10,
            'expected_ledger_gate': 'gate: example', 'expected_sweep': 'sweep: example',
            'gating_workspaces': ['example']}


def paths(value, prefix=()):
    if isinstance(value, dict):
        for key, child in value.items():
            yield prefix + (key,)
            yield from paths(child, prefix + (key,))
    elif isinstance(value, list):
        for i, child in enumerate(value):
            yield from paths(child, prefix + (i,))


def parent(value, path):
    for key in path[:-1]:
        value = value[key]
    return value


class ReleaseConfigTest(unittest.TestCase):
    def read(self, value):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'config.json'
            path.write_text(json.dumps(value))
            return config.load(path)

    def test_complete_and_each_missing_or_wrong_type(self):
        original = sample()
        self.assertEqual(self.read(original), original)
        for path in paths(original):
            with self.subTest(path=path, fault='missing'):
                broken = copy.deepcopy(original)
                del parent(broken, path)[path[-1]]
                with self.assertRaisesRegex(ValueError, 'missing'):
                    self.read(broken)
            with self.subTest(path=path, fault='type'):
                broken = copy.deepcopy(original)
                parent(broken, path)[path[-1]] = None
                with self.assertRaisesRegex(ValueError, 'expected'):
                    self.read(broken)

    def test_titles_and_runtime(self):
        cfg = sample()
        self.assertEqual(config.titles(cfg), {'format': 'Format the unit dispositions file',
            'stamp': 'Stamp Tackle 2.3.4', 'changelog': 'Record the Tackle 2.3.4 changes',
            'migrate': 'Target the migration catalog at Tackle 2.3.4',
            'readme': 'Point the README at Tackle 2.3.4'})
        self.assertTrue(config.runtime_ok(cfg, 'py310', (3, 10, 5)))
        self.assertFalse(config.runtime_ok(cfg, 'py310', (3, 10, 6)))

    def test_help(self):
        result = subprocess.run([sys.executable, '-I', '-B', str(ROOT / 'maintaining/release/steps.py'), '--help'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('--config', result.stdout)

    def test_relative_config_from_outside_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / 'candidate'
            repo.mkdir()
            workspace = root / 'workspace'
            workspace.mkdir()
            entry = b'## Tackle 2.3.4\n\nRelease wording.\n'
            changelog = root / 'entry.md'
            changelog.write_bytes(entry)
            (repo / 'CHANGELOG.md').write_bytes(b'# Tackle changelog\n\n' + entry + b'\n## Tackle 2.3.3\n\nPrevious.\n')
            cfg = sample()
            cfg['workspace'] = str(workspace)
            cfg['changelog'] = {'path': str(changelog), 'sha256': hashlib.sha256(entry).hexdigest()}
            for label in ('py310', 'py314'):
                cfg['runtimes'][label] = {'path': sys.executable, 'version': list(sys.version_info[:3])}
            (root / 'release.json').write_text(json.dumps(cfg))
            fake_bin = root / 'bin'
            fake_bin.mkdir()
            git = fake_bin / 'git'
            git.write_text('#!/bin/sh\ncase "$*" in\n  "rev-parse HEAD") printf "%s\\n" ' + 'a' * 40 + ';;\n  "status --porcelain") exit 0;;\n  *) exit 98;;\nesac\n')
            git.chmod(0o755)
            env = dict(os.environ, PATH=str(fake_bin) + os.pathsep + os.environ.get('PATH', ''))
            records = root / 'records'
            accepted = records / 'candidate'
            accepted.mkdir(parents=True)
            (accepted / 'phase.json').write_text(json.dumps({'ok': True}))
            (accepted / 'candidate.json').write_text(json.dumps({'candidate': 'a' * 40}))
            result = subprocess.run([sys.executable, '-I', '-B', str(ROOT / 'maintaining/release/steps.py'),
                '--config', 'release.json', '--repo', str(repo), '--records', str(records), '--phase', 'notes'],
                cwd=root, env=env, capture_output=True, text=True)
            child_stderr = (records / 'notes/notes.stderr').read_text()
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr + child_stderr)
            self.assertTrue(json.loads((records / 'notes/phase.json').read_text())['ok'])


if __name__ == '__main__':
    unittest.main()
