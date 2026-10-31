"""Install evidence inventories actual files and removes the owned sandbox."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[5]
SPEC = importlib.util.spec_from_file_location('install_local', ROOT / 'maintaining/release/install_local.py')
install = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(install)


class InstallInventoryTest(unittest.TestCase):
    def test_complete_inventory_and_cleanup(self):
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp) / 'sandbox'
            installed = sandbox / 'installed'
            (installed / 'nested').mkdir(parents=True)
            (installed / 'SKILL.md').write_bytes(b'abc')
            (installed / 'nested' / 'empty').write_bytes(b'')
            (sandbox / 'clone').mkdir()
            self.assertEqual(install.inventory(installed, 2), {'files': [
                {'path': 'SKILL.md', 'size': 3, 'sha256': hashlib.sha256(b'abc').hexdigest()},
                {'path': 'nested/empty', 'size': 0, 'sha256': hashlib.sha256(b'').hexdigest()},
            ]})
            install.cleanup_sandbox(sandbox)
            self.assertFalse(sandbox.exists())

    def test_count_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'file').write_text('content')
            with self.assertRaisesRegex(ValueError, 'expected 2'):
                install.inventory(root, 2)


if __name__ == '__main__':
    unittest.main()
