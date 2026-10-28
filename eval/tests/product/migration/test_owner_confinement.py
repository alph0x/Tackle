import builtins
import collections
import contextlib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
ZERO = '0' * 64
ACCESS_NAMES = ('lstat', 'stat', 'exists', 'iterdir', 'read_bytes', 'open')
OWNER_STATE_PATHS = ('source', 'checkpoint', 'candidate', 'original_backup', 'adopted_backup', 'restore_stage')
OPENED = ('read_bytes', 'open', 'builtins.open', 'os.open')


def load_compact():
    spec = importlib.util.spec_from_file_location('compact_owner_confinement', ROOT / 'skills/tackle/scripts/migrate/compact.py')
    compact = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(compact)
    return compact


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True) + '\n', encoding='utf-8')


def build_lab(temporary):
    lab = Path(temporary).resolve()
    work, job, source, outside = lab / 'work', lab / 'job', lab / 'source', lab / 'work-outside'
    for directory in (work, job, source, outside): directory.mkdir()
    return lab, work, job, source, outside


def caller_state(job, source, phase='prepared'):
    return dict(source=str(source), original_backup=str(job / 'original-backup'), phase=phase)


def make_owner(compact, work, name, owner_source, state_overrides=None, manifest_source=None):
    owner = work / name
    (owner / 'checkpoint').mkdir(parents=True)
    paths = dict(source=str(owner_source),
                 checkpoint=str(owner / 'checkpoint'),
                 candidate=str(owner / 'candidate-project' / 'docs' / 'plans' / owner_source.name),
                 original_backup=str(owner / 'original-backup'),
                 adopted_backup=str(owner / 'adopted-backup'),
                 restore_stage=str(owner / 'restore-stage'))
    paths.update(state_overrides or {})
    state = dict(schema=compact.JOB_SCHEMA, operation_id='1' * 64, operation='adopt', phase='prepared',
                 source_sha256=ZERO, candidate_sha256=ZERO, checkpoint_sha256=ZERO, install_sha256=ZERO,
                 catalog_sha256=ZERO, context_sha256=ZERO, boundary_sha256=ZERO, receipts=[], **paths)
    write_json(owner / 'state.json', state)
    write_json(owner / 'manifest.json', {'source': {'path': str(manifest_source or owner_source)}})
    return owner


def review_value():
    return dict(schema='tackle-migration-review/1', reviewer='reviewer', candidate_sha256=ZERO,
                source_sha256=ZERO, catalog_sha256=ZERO, decisions=[])


@contextlib.contextmanager
def recorded_access():
    seen = collections.defaultdict(list)

    def method(name):
        original = getattr(Path, name)

        def spy(self, *args, **kwargs):
            seen[name].append(os.fspath(self))
            return original(self, *args, **kwargs)
        return spy

    def function(name, owner, attribute):
        original = getattr(owner, attribute)

        def spy(path='.', *args, **kwargs):
            if isinstance(path, (str, os.PathLike)): seen[name].append(os.fspath(path))
            return original(path, *args, **kwargs)
        return spy

    with contextlib.ExitStack() as stack:
        for name in ACCESS_NAMES:
            stack.enter_context(mock.patch.object(Path, name, method(name)))
        stack.enter_context(mock.patch.object(os, 'scandir', function('scandir', os, 'scandir')))
        stack.enter_context(mock.patch.object(os, 'open', function('os.open', os, 'open')))
        stack.enter_context(mock.patch.object(builtins, 'open', function('builtins.open', builtins, 'open')))
        yield seen


def touched(seen, directory):
    prefix = str(directory)
    return [path for names in seen.values() for path in names if path == prefix or path.startswith(prefix + os.sep)]


def opened(seen, path):
    return [name for name in OPENED for recorded in seen[name] if recorded == str(path)]


class OwnerConfinementTests(unittest.TestCase):
    def test_owner_state_paths_outside_roots_are_refused_before_access(self):
        compact = load_compact()
        with tempfile.TemporaryDirectory(prefix='tackle-owner-state-') as temporary:
            lab, work, job, source, outside = build_lab(temporary)
            owner_source = work / 'owner-source'
            owner_source.mkdir()
            caller = caller_state(job, source)
            previous = os.getcwd()
            os.chdir(work)
            try:
                for key in OWNER_STATE_PATHS:
                    owner = make_owner(compact, work, 'owner-' + key, owner_source, {key: str(outside)})
                    with recorded_access() as seen:
                        with self.assertRaisesRegex(compact.MigrationError, '^external-review-owner-outside-root$'):
                            compact._external_receipt_context(owner / 'semantic-review.json', review_value(), job, caller)
                    self.assertEqual(touched(seen, outside), [], key)
            finally:
                os.chdir(previous)

    def test_owner_manifest_source_outside_roots_is_refused_before_access(self):
        compact = load_compact()
        with tempfile.TemporaryDirectory(prefix='tackle-owner-manifest-') as temporary:
            lab, work, job, source, outside = build_lab(temporary)
            owner_source = work / 'owner-source'
            owner_source.mkdir()
            manifest_source = outside / 'owner-source'
            manifest_source.mkdir()
            caller = caller_state(job, source)
            previous = os.getcwd()
            os.chdir(work)
            try:
                valid = make_owner(compact, work, 'owner-valid', owner_source)
                try:
                    compact._external_receipt_context(valid / 'semantic-review.json', review_value(), job, caller)
                except compact.MigrationError as exc:
                    self.assertNotEqual(str(exc), 'external-review-owner-outside-root')
                owner = make_owner(compact, work, 'owner-outside', owner_source, manifest_source=manifest_source)
                with recorded_access() as seen:
                    with self.assertRaisesRegex(compact.MigrationError, '^external-review-owner-outside-root$'):
                        compact._external_receipt_context(owner / 'semantic-review.json', review_value(), job, caller)
                self.assertEqual(touched(seen, outside), [])
            finally:
                os.chdir(previous)

    def test_working_directory_root_is_not_an_admitted_root(self):
        compact = load_compact()
        with tempfile.TemporaryDirectory(prefix='tackle-root-work-') as temporary:
            lab, work, job, source, outside = build_lab(temporary)
            cited = outside / 'evidence.json'
            write_json(cited, {'evidence': 'outside'})
            state = caller_state(job, source)
            previous = os.getcwd()
            os.chdir('/')
            try:
                with self.assertRaisesRegex(compact.MigrationError, '^filesystem-root-authority$'):
                    compact._evidence_path(job, state, str(cited))
            finally:
                os.chdir(previous)

    def test_job_root_is_not_an_admitted_root(self):
        compact = load_compact()
        with tempfile.TemporaryDirectory(prefix='tackle-root-job-') as temporary:
            lab, work, job, source, outside = build_lab(temporary)
            cited = outside / 'evidence.json'
            write_json(cited, {'evidence': 'outside'})
            previous = os.getcwd()
            os.chdir(work)
            try:
                with self.assertRaisesRegex(compact.MigrationError, '^filesystem-root-authority$'):
                    compact._evidence_path(Path('/'), caller_state(Path('/'), source), str(cited))
                root_source = caller_state(job, Path('/'))
                with self.assertRaisesRegex(compact.MigrationError, '^filesystem-root-authority$'):
                    compact._evidence_path(job, root_source, str(cited))
                spelled = caller_state(Path('//'), source)
                with self.assertRaisesRegex(compact.MigrationError, '^filesystem-root-authority$'):
                    compact._evidence_path(Path('//'), spelled, str(cited))
            finally:
                os.chdir(previous)

    def test_absolute_hardlinked_evidence_is_refused_before_read(self):
        compact = load_compact()
        with tempfile.TemporaryDirectory(prefix='tackle-hardlink-') as temporary:
            lab, work, job, source, outside = build_lab(temporary)
            evidence = work / 'evidence.json'
            write_json(evidence, {'evidence': 'linked'})
            os.link(evidence, outside / 'alias.json')
            state = caller_state(job, source)
            ref = dict(path=str(evidence), sha256=digest(evidence.read_bytes()))
            previous = os.getcwd()
            os.chdir(work)
            try:
                with recorded_access() as seen:
                    with self.assertRaisesRegex(compact.MigrationError, '^hardlinked-external-evidence$'):
                        compact._evidence_ref(job, state, ref)
                self.assertEqual(opened(seen, evidence), [])
            finally:
                os.chdir(previous)

    def test_redirected_backup_hardlinked_evidence_is_refused_before_read(self):
        compact = load_compact()
        with tempfile.TemporaryDirectory(prefix='tackle-redirect-') as temporary:
            lab, work, job, source, outside = build_lab(temporary)
            backup = job / 'original-backup'
            backup.mkdir()
            redirected = backup / 'evidence.json'
            write_json(redirected, {'evidence': 'redirected'})
            os.link(redirected, outside / 'alias.json')
            state = dict(caller_state(job, source, 'adopted'))
            cited = source / 'evidence.json'
            ref = dict(path=str(cited), sha256=digest(redirected.read_bytes()))
            previous = os.getcwd()
            os.chdir(work)
            try:
                with recorded_access() as seen:
                    with self.assertRaisesRegex(compact.MigrationError, '^hardlinked-external-evidence$'):
                        compact._evidence_ref(job, state, ref)
                self.assertEqual(opened(seen, redirected), [])
            finally:
                os.chdir(previous)

    def test_single_link_absolute_evidence_is_accepted(self):
        compact = load_compact()
        with tempfile.TemporaryDirectory(prefix='tackle-single-link-') as temporary:
            lab, work, job, source, outside = build_lab(temporary)
            evidence = work / 'evidence.json'
            write_json(evidence, {'evidence': 'single'})
            state = caller_state(job, source)
            ref = dict(path=str(evidence), sha256=digest(evidence.read_bytes()))
            redirected = job / 'original-backup' / 'single.json'
            write_json(redirected, {'evidence': 'redirected'})
            cited = source / 'single.json'
            redirect_ref = dict(path=str(cited), sha256=digest(redirected.read_bytes()))
            previous = os.getcwd()
            os.chdir(work)
            try:
                try:
                    self.assertEqual(compact._evidence_ref(job, state, ref), ref)
                    self.assertEqual(compact._evidence_ref(job, dict(state, phase='adopted'), redirect_ref), redirect_ref)
                except compact.MigrationError as exc:
                    self.fail(str(exc))
            finally:
                os.chdir(previous)

    def test_relative_hardlinked_job_evidence_keeps_its_contract(self):
        compact = load_compact()
        with tempfile.TemporaryDirectory(prefix='tackle-relative-link-') as temporary:
            lab, work, job, source, outside = build_lab(temporary)
            evidence = job / 'evidence.json'
            write_json(evidence, {'evidence': 'relative'})
            os.link(evidence, job / 'alias.json')
            state = caller_state(job, source)
            ref = dict(path='evidence.json', sha256=digest(evidence.read_bytes()))
            previous = os.getcwd()
            os.chdir(work)
            try:
                try:
                    self.assertEqual(compact._evidence_ref(job, state, ref), ref)
                except compact.MigrationError as exc:
                    self.fail(str(exc))
            finally:
                os.chdir(previous)

    def test_reference_graph_parses_the_checked_bytes(self):
        compact = load_compact()
        with tempfile.TemporaryDirectory(prefix='tackle-graph-') as temporary:
            lab, work, job, source, outside = build_lab(temporary)
            cited = work / 'cited.json'
            valid = b'{"note": "checked"}\n'
            write_json(cited, {'reference': {'path': str(work / 'missing.json'), 'sha256': ZERO}})
            state = caller_state(job, source)
            ref = dict(path=str(cited), sha256=digest(valid))
            original = Path.read_bytes
            served = []

            def first_read(self):
                if self == cited and not served:
                    served.append(self)
                    return valid
                return original(self)
            previous = os.getcwd()
            os.chdir(work)
            try:
                with mock.patch.object(Path, 'read_bytes', first_read):
                    try:
                        compact._validate_reference_graph(job, state, ref)
                    except compact.MigrationError as exc:
                        self.fail(str(exc))
            finally:
                os.chdir(previous)


if __name__ == '__main__':
    unittest.main()
