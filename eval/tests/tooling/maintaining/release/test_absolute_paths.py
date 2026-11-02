import importlib.util
import ast
import json
import tempfile
import os
from pathlib import Path
import types
import unittest

ROOT = Path(__file__).resolve().parents[5]
spec = importlib.util.spec_from_file_location('release_support', ROOT / 'maintaining/release/release_support.py')
support = importlib.util.module_from_spec(spec)
spec.loader.exec_module(support)


class AbsolutePaths(unittest.TestCase):
    def test_scalar_and_list(self):
        args = types.SimpleNamespace(path='a/../b', values=['/a/../b', 'c'], optional=None)
        support.absolute(args, ('path', 'values', 'optional'))
        self.assertEqual(args.path, os.path.abspath('a/../b'))
        self.assertEqual(args.values, ['/a/../b', os.path.abspath('c')])
        self.assertIsNone(args.optional)

    def test_empty_refused(self):
        with self.assertRaises(SystemExit) as error:
            support.absolute(types.SimpleNamespace(path=''), ('path',))
        self.assertEqual(error.exception.code, 2)

    def test_absolute_spelling_and_symlink_are_not_normalized(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'target' / 'child').mkdir(parents=True)
            (root / 'link').symlink_to(root / 'target' / 'child')
            spelling = str(root) + '/link/../file'
            args = types.SimpleNamespace(path=spelling, values=['/alpha//./beta/../gamma'])
            support.absolute(args, ('path', 'values'))
            self.assertEqual(args.path, spelling)
            self.assertEqual(args.values, ['/alpha//./beta/../gamma'])

    def test_release_entry_coverage(self):
        expected = {
            'steps.py': ('config', 'repo', 'records'),
            'self_lint.py': ('config', 'repo', 'workspace', 'records', 'interpreter'),
            'catalog_checks.py': ('config', 'repo', 'workspace', 'records', 'interpreter'),
            'workspace_sweep.py': ('config', 'repo', 'workspace', 'records'),
            'install_local.py': ('config', 'repo', 'workspace', 'records'),
            'release_edit.py': ('config', 'repo', 'workspace', 'records'),
            'verify_release_notes.py': ('config', 'repo', 'workspace', 'records'),
            'full_registry.py': ('config', 'repo', 'workspace', 'records', 'interpreter'),
            'ci_replay.py': ('config', 'repo', 'workspace', 'records', 'registry310', 'registry314', 'interpreter310', 'interpreter314'),
            'committed_guard_strict.py': ('config', 'repo', 'records'),
        }
        for filename, names in expected.items():
            with self.subTest(filename=filename):
                tree = ast.parse((ROOT / 'maintaining/release' / filename).read_text())
                calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                         and isinstance(node.func, ast.Attribute) and node.func.attr == 'absolute']
                self.assertEqual(len(calls), 1)
                self.assertEqual(ast.literal_eval(calls[0].args[1]), names)

    def test_config_rejects_each_relative_path(self):
        spec = importlib.util.spec_from_file_location('release_config_test', ROOT / 'maintaining/release/config.py')
        config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config)
        base = {'schema': 'tackle-release/1', 'version': '1', 'from_version': '0',
                'base': 'revision', 'branch': 'branch', 'catalog_revision': [1, 2],
                'runtimes': {'py310': {'path': '/interpreter', 'version': [3, 10, 0]},
                             'py314': {'path': '/interpreter', 'version': [3, 14, 0]}},
                'workspace': '/workspace', 'initiative': 'example',
                'changelog': {'path': '/changes', 'sha256': 'x'},
                'record': {'path': '/record', 'sha256': 'x', 'destination': 'relative'},
                'claims': [], 'parts': [], 'install_count': 1,
                'expected_ledger_gate': '', 'expected_sweep': '', 'gating_workspaces': []}
        paths = [('workspace',), ('changelog', 'path'), ('record', 'path'),
                 ('runtimes', 'py310', 'path'), ('runtimes', 'py314', 'path')]
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'config.json'
            target.write_text(json.dumps(base))
            self.assertEqual(config.load(target), base)
            for keys in paths:
                value = json.loads(json.dumps(base))
                parent = value
                for key in keys[:-1]:
                    parent = parent[key]
                parent[keys[-1]] = 'relative'
                target.write_text(json.dumps(value))
                with self.assertRaisesRegex(ValueError, 'config[.]' + '[.]'.join(keys) + ': expected absolute path'):
                    config.load(target)
