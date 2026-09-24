"""Execute the exact documented recipes; no installed runtime helper."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
GUIDE = ROOT / 'references/guides/full-checks.md'
CAPTURE, LINT = re.findall(r'```python\n(.*?)\n```', GUIDE.read_text(), re.S)
CANONICAL = (ROOT / 'references/guides/lint-spec.md').read_bytes()
DIGEST = hashlib.sha256(CANONICAL).hexdigest()
NS = {}; exec(LINT, NS)

class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'capture.py').write_text(CAPTURE)
        (self.root / 'SPEC.md').write_text('fixed')
        (self.root / 'test_original.py').write_text('protected')
        self.spec = dict(argv=['python3', 'child.py'], selectors=[
            dict(glob='test*.py', required=True), dict(glob='SPEC.md', required=True)],
            artifacts=[], destination='evidence', timeout_seconds=2)
    def run_capture(self, child, expected=0):
        (self.root / 'child.py').write_text(child)
        (self.root / 'check.json').write_text(json.dumps(self.spec))
        p = subprocess.run(['python3', 'capture.py', 'check.json'], cwd=self.root,
                           capture_output=True, timeout=8)
        self.assertEqual(p.returncode, expected, p.stderr)
        if not p.stdout: return None, None
        out = Path(p.stdout.decode().strip()).parent
        return out, json.loads((out / 'result.json').read_text())
    def test_binary_streams_and_automatic_script_spec_inputs(self):
        out, r = self.run_capture("import os; os.write(1,b'\\xff'); os.write(2,b'\\x00')")
        self.assertTrue(r['accepted'])
        self.assertEqual(set(r['inputs_before']), {'capture.py','check.json','child.py','SPEC.md','test_original.py'})
        for name, digest in r['inputs_before'].items():
            self.assertEqual((out/'blobs'/digest).read_bytes(), (self.root/name).read_bytes())
        for name, digest in r['streams'].items():
            self.assertEqual(hashlib.sha256((out/name).read_bytes()).hexdigest(), digest)
        self.assertEqual((out/'stdout.bin').read_bytes(), b'\xff')
    def test_absolute_interpreter_is_valid(self):
        import sys
        self.spec['argv'][0] = sys.executable
        _, r = self.run_capture('pass')
        self.assertTrue(r['accepted'])
    def test_child_failure_not_printed_pass(self):
        _, r = self.run_capture("print('PASS'); raise SystemExit(7)", 1)
        self.assertEqual(r['child_exit'], 7); self.assertFalse(r['accepted'])
    def test_checked_compound_propagates_first_failure(self):
        _, r = self.run_capture("import subprocess; subprocess.run(['sh','-c','exit 9'],check=True); print('PASS')",1)
        self.assertNotEqual(r['child_exit'], 0)
    def test_additive_tests_captured(self):
        (self.root/'test_added.py').write_text('added')
        _, r = self.run_capture('pass')
        self.assertIn('test_added.py', r['inputs_before'])
    def test_new_test_membership_invalidates_result(self):
        _, r = self.run_capture("from pathlib import Path; Path('test_new.py').write_text('new')",1)
        self.assertFalse(r['inputs_stable']); self.assertIn('test_new.py', r['inputs_after'])
    def test_changed_script_preserves_both_versions(self):
        old="from pathlib import Path; Path('child.py').write_text('new')"
        out, r = self.run_capture(old,1)
        self.assertEqual((out/'blobs'/r['inputs_before']['child.py']).read_text(),old)
        self.assertEqual((out/'blobs'/r['inputs_after']['child.py']).read_text(),'new')
    def test_second_observation_preserves_first(self):
        old,r=self.run_capture('print(1)'); frozen={str(p):p.read_bytes() for p in old.rglob('*') if p.is_file()}
        new,r=self.run_capture('print(2)')
        self.assertNotEqual(old,new)
        self.assertTrue(all(Path(p).read_bytes()==b for p,b in frozen.items()))
    def test_missing_required_selector_fails_before_child(self):
        (self.root/'test_original.py').unlink()
        self.run_capture("from pathlib import Path; Path('ran').touch()",1)
        self.assertFalse((self.root/'ran').exists())
    def test_optional_empty_membership_recorded(self):
        self.spec['selectors'].append(dict(glob='optional*.json',required=False))
        _,r=self.run_capture('pass');self.assertEqual(r['membership_before']['optional*.json'],[])
    def test_missing_artifact_rejected(self):
        self.spec['artifacts']=['missing'];_,r=self.run_capture('pass',1)
        self.assertFalse(r['artifacts_present'])
    def test_signal_recorded(self):
        _,r=self.run_capture('import os,signal; os.kill(os.getpid(),signal.SIGTERM)',1)
        self.assertEqual(r['signal'],15)
    def test_timeout_partial_output(self):
        self.spec['timeout_seconds']=.1
        out,r=self.run_capture("import time; print('partial',flush=True);time.sleep(1)",1)
        self.assertTrue(r['timeout']);self.assertEqual((out/'stdout.bin').read_bytes(),b'partial\n')
    def test_symlink_input_escape_rejected(self):
        (self.root/'test_escape.py').symlink_to('/etc/hosts')
        self.run_capture('pass',1)
    def test_selector_traversal_rejected(self):
        self.spec['selectors']=[dict(glob='../*',required=True)]
        self.run_capture('pass',1)

class CanonicalTests(unittest.TestCase):
    def rows(self, source=CANONICAL, digest=DIGEST, slug='demo'):
        return NS['canonical_rows'](source,digest,slug)
    def verdict(self,row,code=0,out=b'',err=b'',**changes):
        r=dict(child_exit=code,timeout=False,launch_error=None,signal=None,inputs_stable=True,artifacts_present=True)
        r.update(changes);return NS['lint_verdict'](row,r,out,err)
    def test_all_literal_cells_preserved(self):
        rows=self.rows();self.assertEqual(len(rows),16)
        for line in CANONICAL.decode().splitlines():
            if not re.match(r'^\| [0-9]+ ·',line):continue
            head,cell,_=line.split(' | ',2);n=int(head[2:].split(' ·')[0])
            # Independent expected bytes: canonical has no meaningful boundary padding.
            expected=cell.strip('`').strip().replace('<slug>','demo').encode()
            self.assertEqual(rows[n]['command'],expected)
    def test_source_mutation_rejected(self):
        with self.assertRaises(ValueError):self.rows(CANONICAL.replace(b'awk ',b'true ',1))
    def test_missing_and_duplicate_rows_rejected(self):
        row=next(x for x in CANONICAL.splitlines(True) if x.startswith(b'| 5 '))
        for altered in [CANONICAL.replace(row,b''),CANONICAL+row]:
            with self.assertRaises(ValueError):self.rows(altered,hashlib.sha256(altered).hexdigest())
    def test_slug_cannot_inject_shell(self):
        for slug in ['../x','x; touch /tmp/no','$(true)','x/y']:
            with self.assertRaises(ValueError):self.rows(slug=slug)
    def test_backticks_quotes_and_substitutions_preserved(self):
        rows=self.rows();self.assertIn(b'`[^`]+`',rows[8]['command'])
        self.assertIn(b'$(sed',rows[2]['command']);self.assertIn(b'awk -v prefix="$prefix"',rows[2]['command'])
    def test_findings_with_exit_zero_are_not_pass(self):
        self.assertEqual(self.verdict(4,out=b'stale citation\n'),'FAIL')
    def test_grep_one_is_pass_zero_empty_is_error_two_is_error(self):
        self.assertEqual(self.verdict(5,1),'PASS')
        self.assertEqual(self.verdict(5,0),'ERROR')
        self.assertEqual(self.verdict(5,2,err=b'missing'),'ERROR')
        self.assertEqual(self.verdict(5,0,out=b'status'),'FAIL')
    def test_canonical_diagnostic_exit_one_is_data_failure(self):
        for row in [6,11,16]:
            self.assertEqual(self.verdict(row,1,out=b'row diagnostic'),'FAIL')
            self.assertEqual(self.verdict(row,1),'ERROR')
    def test_warning_severity_preserved(self):
        for row in [8,13,15]:self.assertEqual(self.verdict(row,out=b'finding'),'WARN')
        self.assertEqual(self.verdict(15,1),'PASS')
    def test_errors_and_changed_inputs_never_pass(self):
        for kw in [dict(timeout=True),dict(signal=15),dict(launch_error='bad'),dict(inputs_stable=False),dict(artifacts_present=False),dict(err=b'error')]:
            self.assertEqual(self.verdict(3,**kw),'ERROR')
    def test_actual_awk_exit_zero_finding(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'row.sh';p.write_text("awk 'BEGIN {print \"stale\"}'")
            r=subprocess.run(['sh',str(p)],capture_output=True)
            self.assertEqual(r.returncode,0);self.assertEqual(self.verdict(4,r.returncode,r.stdout,r.stderr),'FAIL')
    def test_actual_grep_missing_vs_no_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'input';p.write_text('fine')
            r=subprocess.run(['grep','bad',str(p)],capture_output=True)
            self.assertEqual(self.verdict(5,r.returncode,r.stdout,r.stderr),'PASS')
            p.unlink();r=subprocess.run(['grep','bad',str(p)],capture_output=True)
            self.assertEqual(self.verdict(5,r.returncode,r.stdout,r.stderr),'ERROR')
    def test_actual_fresh_and_stale_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);w=root/'docs/plans/demo';(w/'reference-docs').mkdir(parents=True)
            (w/'AGENTS.md').write_text('Reference staleness window: 14\n')
            script=root/'row.sh';script.write_bytes(self.rows()[15]['command'])
            from datetime import datetime,timezone
            for date,expect in [(datetime.now(timezone.utc).date().isoformat(),'PASS'),('2000-01-01','WARN')]:
                (w/'reference-docs/ref.md').write_text('captured: '+date+'\n')
                r=subprocess.run(['sh',str(script)],cwd=root,capture_output=True)
                self.assertEqual(self.verdict(15,r.returncode,r.stdout,r.stderr),expect,r.stderr)

if __name__=='__main__':unittest.main()
