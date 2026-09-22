"""Execute the shipped Markdown recipes against disposable storage only."""
from contextlib import redirect_stdout
import errno
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]


def recipe(name):
    return re.findall(r'```python\n(.*?)\n```',
                      (ROOT / 'references/guides' / name).read_text(), re.S)[0]


class Records(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.workspace = self.root / 'initiative'
        self.workspace.mkdir()
        self.store = self.workspace / 'evidence'
        (self.root / 'capture.py').write_text(recipe('full-checks.md'))
        (self.root / 'lifecycle.py').write_text(recipe('record-lifecycle.md'))
        (self.root / 'input.bin').write_bytes(b'x' * 1048576)
        (self.root / 'child.py').write_text("print('checked')\n")
        self.spec = dict(workspace='initiative', argv=[sys.executable, 'child.py'],
                         selectors=[dict(glob='input.bin', required=True)],
                         artifacts=[], timeout_seconds=2)
        self.old = Path.cwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, self.old)
        self.capture = self.load('capture')
        self.lifecycle = self.load('lifecycle')

    def load(self, name):
        spec = importlib.util.spec_from_file_location(name, self.root / (name + '.py'))
        module = importlib.util.module_from_spec(spec)
        old = sys.modules.get(name)
        sys.modules[name] = module
        self.addCleanup(lambda: sys.modules.pop(name, None) if old is None else sys.modules.__setitem__(name, old))
        spec.loader.exec_module(module)
        return module

    def run_capture(self, expected=True):
        (self.root / 'check.json').write_text(json.dumps(self.spec))
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(self.capture.capture('check.json'), expected)
        out = Path(output.getvalue().strip()).parent
        return out, self.capture.read_record(out)

    def policy(self, retire=(), current=(), pinned=(), active=(), resolved=()):
        relative = lambda paths: [str(p.relative_to(self.store)) for p in paths]
        (self.workspace / 'obligations.json').write_text(json.dumps(dict(current=relative(current),
                                                                        pinned=relative(pinned), active=relative(active))))
        return dict(current=relative(current), pinned=relative(pinned), active=relative(active),
                    resolved_failures=relative(resolved), retire=relative(retire),
                    reference_sources=['obligations.json'], reference_writes_coordinated=True,
                    reason='Fixture policy: superseded proof has no remaining byte obligation')

    def test_three_actual_events_one_copy_of_identical_input_and_streams(self):
        observations = [self.run_capture() for _ in range(3)]
        self.assertEqual(len({str(o) for o, _ in observations}), 3)
        digest = hashlib.sha256(b'x' * 1048576).hexdigest()
        objects = list((self.store / 'objects').glob(digest))
        self.assertEqual(sum(p.stat().st_size for p in objects), 1048576)
        for out, record in observations:
            self.assertTrue(record['accepted'])
            self.assertEqual((out / 'blobs' / digest).read_bytes(), b'x' * 1048576)
            self.assertEqual(record['event_id'], out.name)
        self.assertEqual(len({r['streams']['stdout.bin'] for _, r in observations}), 1)

    def test_changed_input_preserves_both_revisions(self):
        first, before = self.run_capture()
        (self.root / 'input.bin').write_bytes(b'new input')
        second, after = self.run_capture()
        self.assertNotEqual(before['inputs_before']['input.bin'], after['inputs_before']['input.bin'])
        self.capture.read_record(first, require_pass=True)
        self.capture.read_record(second, require_pass=True)

    def test_broad_selector_excludes_store_and_bounded_prior_record_remains_verifiable(self):
        first, _ = self.run_capture()
        self.spec['selectors'] = [dict(glob='**/*', required=True)]
        self.spec['prior_records'] = [str(first.relative_to(self.root))]
        second, record = self.run_capture()
        names = record['membership_before']['**/*']
        self.assertFalse(any('/evidence/' in n for n in names))
        self.assertEqual(len(record['prior_records']), 1)
        self.assertTrue(record['prior_objects'])
        self.capture.read_record(second, require_pass=True)

    def test_missing_or_corrupt_objects_cannot_be_current(self):
        out, record = self.run_capture()
        blob = self.store / 'objects' / record['inputs_before']['input.bin']
        blob.unlink()
        with self.assertRaises((OSError, ValueError)):
            self.capture.read_record(out, require_pass=True)
        blob.write_bytes(b'corrupt')
        with self.assertRaises(ValueError):
            self.capture.read_record(out, require_pass=True)
        with self.assertRaises(ValueError):
            self.run_capture()

    def test_altered_metadata_and_false_stability_do_not_validate(self):
        out, record = self.run_capture()
        altered = dict(record, argv=['forged-success'])
        (out / 'result.json').write_text(json.dumps(altered))
        with self.assertRaises(ValueError):
            self.capture.read_record(out, require_pass=True)
        altered = dict(record, inputs_after={})
        (out / 'result.json').write_text(json.dumps(altered))
        with self.assertRaises(ValueError):
            self.capture.read_record(out, require_pass=True)

    def test_wrong_metadata_types_cannot_be_success(self):
        out, record = self.run_capture()
        for key, value in [('child_exit', False), ('accepted', 1), ('timeout', 0),
                           ('inputs_stable', 'yes'), ('artifacts_present', []),
                           ('streams', []), ('signal', False), ('argv', 'python3')]:
            with self.subTest(field=key):
                (out / 'result.json').write_text(json.dumps(dict(record, **{key: value})))
                with self.assertRaises(ValueError):
                    self.capture.read_record(out, require_pass=True)
        lint = re.findall(r'```python\n(.*?)\n```',
                          (ROOT / 'references/guides/full-checks.md').read_text(), re.S)[1]
        namespace = {}
        exec(lint, namespace)
        self.assertEqual(namespace['lint_verdict'](1, dict(record, child_exit=False), b'', b''), 'ERROR')

    def test_missing_provenance_cannot_be_reused_and_failed_missing_after_is_inspectable(self):
        out, record = self.run_capture()
        original_start = (out / 'start.json').read_bytes()
        for field in ('signal', 'cwd', 'capture_runtime', 'actor', 'model', 'effort', 'start', 'end'):
            altered = dict(record)
            altered.pop(field)
            (out / 'result.json').write_text(json.dumps(altered))
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.capture.read_record(out, require_pass=True)
        (out / 'result.json').write_text(json.dumps(record))
        (out / 'start.json').write_text('{}')
        with self.assertRaises(ValueError):
            self.capture.read_record(out, require_pass=True)
        (out / 'start.json').write_bytes(original_start)
        (self.root / 'child.py').write_text("from pathlib import Path; Path('input.bin').unlink()")
        failed, raw = self.run_capture(expected=False)
        self.assertNotIn('inputs_after', raw)
        self.assertFalse(self.capture.read_record(failed)['accepted'])
        with self.assertRaises(ValueError):
            self.capture.read_record(failed, require_pass=True)

    def test_explicit_workspace_and_destinations_cannot_escape(self):
        self.spec['destination'] = 'outside'
        with self.assertRaises(ValueError):
            self.run_capture()
        self.assertFalse((self.root / 'evidence').exists())
        self.assertFalse((self.root / 'outside').exists())

    def test_new_lint_specs_use_explicit_shared_workspace(self):
        lint = re.findall(r'```python\n(.*?)\n```',
                          (ROOT / 'references/guides/full-checks.md').read_text(), re.S)[1]
        (self.root / 'lint.py').write_text(lint)
        source = ROOT / 'references/guides/lint-spec.md'
        config = dict(source=str(source), source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                      workspace='initiative', slug='demo', rows=[12], capture_script='capture.py',
                      selectors=[dict(glob='input.bin', required=True)], timeout_seconds=2)
        (self.root / 'lint.json').write_text(json.dumps(config))
        run = subprocess.run([sys.executable, 'lint.py', 'lint.json'], cwd=self.root,
                             capture_output=True, timeout=10)
        self.assertTrue(run.stdout, run.stderr)
        summary = json.loads(Path(run.stdout.decode().strip()).read_text())
        self.assertEqual(summary['total'], 1)
        observation = self.root / summary['rows']['12']['observation']
        record = self.capture.read_record(observation)
        self.assertEqual(record['layout'], 'shared-v1')
        self.assertTrue(observation.is_relative_to(self.store))
        self.assertFalse((self.root / 'evidence').exists())

    def test_store_and_pool_symlinks_cannot_redirect_authorized_writes(self):
        sibling = self.root / 'outside'
        sibling.mkdir()
        self.store.symlink_to(sibling, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.run_capture()
        self.assertEqual(list(sibling.iterdir()), [])
        self.store.unlink()
        self.store.mkdir()
        (self.store / 'objects').symlink_to(sibling, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.run_capture()
        self.assertEqual(list(sibling.iterdir()), [])

    def test_legacy_destination_only_capture_and_old_reader_layout(self):
        self.spec.pop('workspace')
        self.spec['destination'] = 'legacy-evidence'
        out, record = self.run_capture()
        self.assertEqual((out / 'blobs' / record['inputs_before']['input.bin']).stat().st_size, 1048576)
        legacy = self.root / 'legacy-observation'
        shutil.copytree(out, legacy, symlinks=False)
        raw = json.loads((legacy / 'result.json').read_text())
        for key in ('layout', 'store', 'event_id', 'prior_records', 'prior_objects'):
            raw.pop(key, None)
        (legacy / 'result.json').write_text(json.dumps(raw))
        start = json.loads((legacy / 'start.json').read_text())
        for key in ('layout', 'store', 'event_id', 'prior_records', 'prior_objects'):
            start.pop(key, None)
        (legacy / 'start.json').write_text(json.dumps(start))
        self.assertTrue(self.capture.read_record(legacy, require_pass=True)['accepted'])

    def test_storage_failure_and_interrupt_never_publish_an_accepted_record(self):
        with patch.object(self.capture, 'put_object', side_effect=OSError(errno.ENOSPC, 'disk full')):
            with self.assertRaises(OSError):
                self.run_capture()
        self.assertFalse(list(self.store.rglob('observation-*')))
        self.assertTrue((self.store / '.lock').exists())
        self.lifecycle.recover_lock(self.store, writers_stopped=True, authorized=True)
        with patch.object(self.capture.subprocess, 'run', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.run_capture()
        self.assertTrue(list(self.store.glob('.pending-*')))
        self.assertFalse(list(self.store.glob('observation-*')))
        self.assertTrue((self.store / '.lock').exists())

    def test_concurrent_capture_and_maintenance_fail_closed(self):
        out, _ = self.run_capture()
        policy = self.policy(retire=[out])
        proposal = self.lifecycle.preview(self.store, policy)
        with self.capture.exclusive(self.store):
            with self.assertRaises(FileExistsError):
                self.run_capture()
            with self.assertRaises(FileExistsError):
                self.lifecycle.maintain(self.store, policy, proposal['fingerprint'], authorized=True)
        self.capture.read_record(out, require_pass=True)

    def test_preview_is_read_only_and_protects_current_pinned_failed_and_active(self):
        current, _ = self.run_capture()
        pinned, _ = self.run_capture()
        (self.root / 'child.py').write_text('raise SystemExit(9)')
        failed, _ = self.run_capture(expected=False)
        pending = self.store / '.pending-interrupted'
        pending.mkdir()
        (pending / 'stdout.bin').write_bytes(b'partial')
        before = self.lifecycle.inventory(self.store)
        policy = self.policy(retire=[current, pinned, failed], current=[current], pinned=[pinned])
        first = self.lifecycle.preview(self.store, policy)
        self.assertEqual(first, self.lifecycle.preview(self.store, policy))
        self.assertEqual(before, self.lifecycle.inventory(self.store))
        self.assertEqual(first['candidates'], [])
        self.assertEqual(first['recoverable_bytes'], 0)
        self.assertIn(str(failed.relative_to(self.store)), first['protected'])
        self.assertIn(pending.name, first['protected'])

    def test_retention_rejects_object_pool_redirection(self):
        out, record = self.run_capture()
        objects = self.store / 'objects'
        objects.rename(self.root / 'redirected')
        objects.symlink_to(self.root / 'redirected', target_is_directory=True)
        policy = self.policy(retire=[out])
        with self.assertRaises(ValueError):
            self.lifecycle.preview(self.store, policy)
        self.assertTrue((self.root / 'redirected' / record['inputs_before']['input.bin']).exists())

    def test_retirement_is_authorized_idempotent_and_not_reusable(self):
        old, record = self.run_capture()
        (self.root / 'input.bin').write_bytes(b'current')
        current, _ = self.run_capture()
        outside = self.workspace / 'unrelated.txt'
        outside.write_text('preserve')
        policy = self.policy(retire=[old], current=[current])
        proposal = self.lifecycle.preview(self.store, policy)
        self.assertGreaterEqual(proposal['recoverable_bytes'], 1048576)
        with self.assertRaises(PermissionError):
            self.lifecycle.maintain(self.store, policy, proposal['fingerprint'])
        self.lifecycle.maintain(self.store, policy, proposal['fingerprint'], authorized=True)
        self.assertTrue((old / 'retired.json').exists())
        marker = json.loads((old / 'retired.json').read_text())
        self.assertEqual(marker['historical_outcome']['accepted'], record['accepted'])
        self.assertEqual(marker['provenance']['argv'], record['argv'])
        self.assertFalse((old / 'result.json').exists())
        self.assertFalse((old / 'start.json').exists())
        self.assertGreater(proposal['metadata_recoverable_bytes'], 0)
        with self.assertRaises(ValueError):
            self.capture.read_record(old, require_pass=True)
        self.capture.read_record(current, require_pass=True)
        again = self.lifecycle.preview(self.store, policy)
        self.lifecycle.maintain(self.store, policy, again['fingerprint'], authorized=True)
        self.assertEqual(outside.read_text(), 'preserve')
        self.assertFalse((self.store / 'objects' / record['inputs_before']['input.bin']).exists())

    def test_stale_preview_cannot_delete_new_capture(self):
        old, _ = self.run_capture()
        policy = self.policy(retire=[old])
        proposal = self.lifecycle.preview(self.store, policy)
        new, _ = self.run_capture()
        with self.assertRaises(ValueError):
            self.lifecycle.maintain(self.store, policy, proposal['fingerprint'], authorized=True)
        self.capture.read_record(new, require_pass=True)
        self.capture.read_record(old, require_pass=True)

    def test_changed_authoritative_references_reject_stale_retention_policy(self):
        out, _ = self.run_capture()
        policy = self.policy(retire=[out])
        proposal = self.lifecycle.preview(self.store, policy)
        (self.workspace / 'obligations.json').write_text(json.dumps(dict(current=[out.name])))
        with self.assertRaises(ValueError):
            self.lifecycle.maintain(self.store, policy, proposal['fingerprint'], authorized=True)
        self.capture.read_record(out, require_pass=True)

    def test_interrupted_retirement_preserves_live_bytes_and_retry_finishes(self):
        old, _ = self.run_capture()
        (self.root / 'input.bin').write_bytes(b'current')
        current, _ = self.run_capture()
        policy = self.policy(retire=[old], current=[current])
        proposal = self.lifecycle.preview(self.store, policy)
        with patch.object(self.lifecycle, 'remove_object', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.lifecycle.maintain(self.store, policy, proposal['fingerprint'], authorized=True)
        self.capture.read_record(current, require_pass=True)
        self.lifecycle.recover_lock(self.store, writers_stopped=True, authorized=True)
        proposal = self.lifecycle.preview(self.store, policy)
        self.assertTrue(proposal['objects'])
        self.lifecycle.maintain(self.store, policy, proposal['fingerprint'], authorized=True)
        self.capture.read_record(current, require_pass=True)

    def test_interrupted_metadata_retirement_retries_from_compact_marker(self):
        old, record = self.run_capture()
        policy = self.policy(retire=[old])
        proposal = self.lifecycle.preview(self.store, policy)
        with patch.object(self.lifecycle, 'remove_metadata', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.lifecycle.maintain(self.store, policy, proposal['fingerprint'], authorized=True)
        self.assertTrue((old / 'retired.json').exists())
        self.assertTrue((old / 'result.json').exists())
        marker = (old / 'retired.json').read_bytes()
        self.lifecycle.recover_lock(self.store, writers_stopped=True, authorized=True)
        proposal = self.lifecycle.preview(self.store, policy)
        self.assertIn(str((old / 'result.json').relative_to(self.store)), proposal['metadata'])
        self.lifecycle.maintain(self.store, policy, proposal['fingerprint'], authorized=True)
        self.assertFalse((old / 'result.json').exists())
        self.assertEqual((old / 'retired.json').read_bytes(), marker)

    def test_export_restore_has_transitive_bytes_without_original_directory(self):
        first, _ = self.run_capture()
        self.spec['prior_records'] = [str(first.relative_to(self.root))]
        second, record = self.run_capture()
        name = str(second.relative_to(self.store))
        bundle = self.lifecycle.export_records(self.store, [name], self.root / 'bundle')
        restored = self.lifecycle.restore_records(bundle, self.root / 'restored')
        shutil.rmtree(self.store)
        self.assertEqual(self.capture.read_record(restored / name, require_pass=True), record)
        self.assertTrue((restored / 'export.json').exists())

    def test_export_rejects_escape_and_restore_detects_missing_bytes(self):
        out, record = self.run_capture()
        with self.assertRaises(ValueError):
            self.lifecycle.export_records(self.store, ['../unrelated'], self.root / 'escape')
        bundle = self.lifecycle.export_records(self.store, [out.name], self.root / 'bundle')
        (bundle / 'objects' / record['inputs_before']['input.bin']).unlink()
        with self.assertRaises((ValueError, OSError)):
            self.lifecycle.restore_records(bundle, self.root / 'restored')
        self.assertFalse((self.root / 'restored').exists())

    def test_small_recipe_requires_existing_workspace_without_root_side_effect(self):
        script = recipe('evidence-capture.md')
        run = subprocess.run([sys.executable, '-c', script], cwd=self.root, capture_output=True)
        self.assertNotEqual(run.returncode, 0)
        self.assertFalse((self.root / 'evidence').exists())

    def test_small_recipe_rejects_store_symlink_escape_before_writes(self):
        sibling = self.root / 'outside'
        sibling.mkdir()
        self.store.symlink_to(sibling, target_is_directory=True)
        script = recipe('evidence-capture.md')
        run = subprocess.run([sys.executable, '-c', script, str(self.workspace)],
                             cwd=self.root, capture_output=True)
        self.assertNotEqual(run.returncode, 0)
        self.assertEqual(list(sibling.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
