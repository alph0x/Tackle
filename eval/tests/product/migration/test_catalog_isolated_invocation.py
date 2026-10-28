"""The installed catalog's literal commands use real isolated Python under poisoned PYTHONPATH."""
from pathlib import Path
import json,os,shlex,shutil,sys,unittest
from unittest import mock
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from maintaining.install_root import current_root
from eval.tests.product.migration import test_compact_migration as fixture

class CatalogInvocationIsolationTests(unittest.TestCase):
    def test_both_current_commands_are_isolated_and_ignore_ambient_modules(self):
        catalog=json.loads((current_root(ROOT)/'references/guides/migration-catalog.json').read_text())
        commands=[]
        for rule in catalog['rules']:
            for instruction in rule['instructions']:
                for fragment in instruction['text'].split('`')[1::2]:
                    if 'scripts/lint.py <slug>' in fragment:commands.append(fragment)
        self.assertEqual(len(commands),2)
        for command in commands:self.assertEqual(shlex.split(command),['python3','-I','scripts/lint.py','<slug>'])
        h=fixture.CompactMigrationTests('runTest')
        with h.lab() as lab:
            installed=h.install(lab);project,source=h.fixture(lab,'catalog-consumer',old=False)
            shutil.copytree(source,installed/'docs/plans/demo',symlinks=True)
            binaries=lab/'bin';binaries.mkdir();(binaries/'python3').symlink_to(sys.executable)
            shadow=lab/'shadow';shadow.mkdir();marker=lab/'ambient-module-loaded'
            (shadow/'subprocess.py').write_text('open('+repr(str(marker))+', "w").write("loaded")\nraise RuntimeError("ambient module loaded")\n')
            bound_path=str(binaries)+os.pathsep+os.environ.get('PATH','')
            configured=shlex.split(commands[0].replace('<slug>','demo'))
            with mock.patch.dict(os.environ,{'PATH':bound_path,'PYTHONPATH':''}):
                clean=h.run_child(configured,installed)
            with mock.patch.dict(os.environ,{'PATH':bound_path,'PYTHONPATH':str(shadow)}):
                control=h.run_child([sys.executable,'-B','scripts/lint.py','demo'],installed,1)
                self.assertTrue(marker.exists(),'the live poison control must import the ambient subprocess module')
                self.assertIn(b'ambient module loaded',control[2]);marker.unlink()
                isolated=h.run_child(configured,installed)
            self.assertFalse(marker.exists())
            self.assertEqual((isolated[0]['exit'],isolated[1],isolated[2]),(clean[0]['exit'],clean[1],clean[2]))

if __name__=='__main__':unittest.main()
