"""Reversible workspace relocation, closure qualification and retained-reader guarantees."""
import base64
from contextlib import contextmanager
from datetime import datetime, timezone
import errno
import fcntl
import hashlib
import importlib.util
import json
import locale
import os
from pathlib import Path
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import uuid

ROOT = Path(__file__).resolve().parents[4]
MODULE = ROOT / 'skills/tackle/scripts/workspace_archive.py'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(',', ':'), allow_nan=False) + '\n').encode()


def inventory(root):
    """Independent no-follow preservation observation, including the root and empty dirs."""
    result = {}

    def visit(path, name):
        info = path.lstat()
        row = {'kind': None, 'mode': stat.S_IMODE(info.st_mode), 'sha256': None, 'link': None}
        if stat.S_ISLNK(info.st_mode):
            row.update(kind='symlink', link=os.readlink(path))
        elif stat.S_ISDIR(info.st_mode):
            row['kind'] = 'directory'
        elif stat.S_ISREG(info.st_mode):
            row.update(kind='file', sha256=digest(path.read_bytes()))
        else:
            raise AssertionError('unexpected fixture object: ' + str(path))
        result[name] = row
        if row['kind'] == 'directory':
            for child in sorted(path.iterdir(), key=lambda p: p.name):
                visit(child, child.name if name == '.' else name + '/' + child.name)

    visit(root, '.')
    return result


BOOTSTRAP = r'''
import base64, builtins, importlib.util, io, json, os, stat, sys
from pathlib import Path
module_path, request_path = map(Path, sys.argv[1:3])
request = json.loads(request_path.read_bytes())
spec = importlib.util.spec_from_file_location('archive_under_test', module_path)
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)

def encode(value):
    if isinstance(value, bytes):
        return {'$fixture_bytes': base64.b64encode(value).decode('ascii')}
    if isinstance(value, Path):
        return str(value)
    raise TypeError(type(value).__name__)

deny = [str(Path(p).resolve()) for p in request.get('deny_reads', [])]
def audit(event, args):
    if event in ('open', 'os.scandir', 'os.listdir') and args:
        try:
            value = os.fspath(args[0])
        except TypeError:
            return
        if isinstance(value, bytes):
            value = os.fsdecode(value)
        value = os.path.abspath(value)
        if any(value == p or value.startswith(p + os.sep) for p in deny):
            raise AssertionError('forbidden fixture read: ' + value)
sys.addaudithook(audit)

phase = request.get('interrupt')
if request.get('hold_before_rename'):
    import time
    origin, destination = map(Path, request['move'])
    ready, release = map(Path, request['hold_before_rename'])
    real_rename, real_replace = os.rename, os.replace
    def held_call(function, src, dst, *args, **kwargs):
        if Path(src) == origin and Path(dst) == destination:
            ready.write_bytes(b'locks held before actual rename\n')
            deadline = time.monotonic() + 20
            while not release.exists():
                if time.monotonic() >= deadline:
                    raise TimeoutError('fixture controller did not release held operation')
                time.sleep(0.01)
        return function(src, dst, *args, **kwargs)
    os.rename = lambda src, dst, *args, **kwargs: held_call(real_rename, src, dst, *args, **kwargs)
    os.replace = lambda src, dst, *args, **kwargs: held_call(real_replace, src, dst, *args, **kwargs)
if phase:
    origin, destination = map(Path, request['move'])
    repo = Path(request['args'][0])
    journal = repo / 'docs/plans/.archive/transaction.json'
    catalog = repo / 'docs/plans/.archive/catalog.json'
    index = repo / 'docs/plans/archive-index.md'
    real_rename, real_replace, real_fsync = os.rename, os.replace, os.fsync
    moved = [False]
    published = set()
    synced = set()
    parents = {(p.stat().st_dev, p.stat().st_ino) for p in
               (origin.parent, destination.parent) if p.exists()}

    def renamed(src, dst, *args, **kwargs):
        result = real_rename(src, dst, *args, **kwargs)
        observed(src, dst)
        return result

    def replaced(src, dst, *args, **kwargs):
        result = real_replace(src, dst, *args, **kwargs)
        observed(src, dst)
        return result

    def observed(src, dst):
        src, dst = Path(src), Path(dst)
        if src == origin and dst == destination:
            moved[0] = True
            parents.update((p.stat().st_dev, p.stat().st_ino) for p in
                           (origin.parent, destination.parent))
        if dst == catalog:
            published.add('catalog')
        if dst == index:
            published.add('index')

    def synced_fd(fd):
        result = real_fsync(fd)
        info = os.fstat(fd)
        if not stat.S_ISDIR(info.st_mode):
            return result
        identity = (info.st_dev, info.st_ino)
        def is_parent(path):
            s = path.parent.stat()
            return identity == (s.st_dev, s.st_ino)
        if phase == 'journal' and journal.is_file() and not moved[0] and is_parent(journal):
            os._exit(99)
        if moved[0] and identity in parents:
            synced.add(identity)
        if phase == 'rename' and moved[0] and parents <= synced:
            os._exit(99)
        if phase == 'catalog' and 'catalog' in published and is_parent(catalog):
            os._exit(99)
        if phase == 'index' and 'index' in published and is_parent(index):
            os._exit(99)
        return result
    os.rename, os.replace, os.fsync = renamed, replaced, synced_fd

try:
    result = getattr(api, request['operation'])(*request['args'], **request.get('kwargs', {}))
except (ValueError, PermissionError, FileNotFoundError) as error:
    print(json.dumps({'error_type': type(error).__name__, 'message': str(error)}))
    sys.exit(2)
else:
    print(json.dumps({'result': result}, default=encode, ensure_ascii=False))
'''


class WorkspaceArchiveTests(unittest.TestCase):
    @contextmanager
    def lab(self):
        with tempfile.TemporaryDirectory(prefix='workspace-archive-public-') as temporary:
            root = Path(temporary).resolve(strict=True)
            self.lab_root = root
            try:
                yield root
            finally:
                selected = os.environ.get('TACKLE_ARCHIVE_RECORD_DIR')
                if selected:
                    destination = Path(selected)
                    if destination.is_symlink() or not destination.is_dir():
                        raise ValueError('record controller root must be an existing real directory')
                    destination = destination.resolve(strict=True)
                    if destination == root or root in destination.parents:
                        raise ValueError('record controller root overlaps temporary fixture')
                    shutil.copytree(root, destination / (self._testMethodName + '-' + uuid.uuid4().hex),
                                    symlinks=True)

    def native(self, label, argv, cwd, timeout=30):
        capture = self.lab_root / 'captures' / (label + '-' + uuid.uuid4().hex)
        capture.mkdir(parents=True)
        started = datetime.now(timezone.utc).isoformat()
        timed_out = False
        child = None
        try:
            with (capture / 'stdout.bin').open('wb') as stdout, (capture / 'stderr.bin').open('wb') as stderr:
                child = subprocess.Popen(argv, cwd=cwd, stdout=stdout, stderr=stderr,
                                         start_new_session=True)
                try:
                    child.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    timed_out = True
                    try:
                        os.killpg(child.pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
                    try:
                        child.wait(timeout=0.5)
                    except subprocess.TimeoutExpired:
                        try:
                            os.killpg(child.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                        child.wait(timeout=0.5)
        finally:
            receipt = {'argv': list(map(str, argv)), 'cwd': str(cwd), 'started': started,
                       'finished': datetime.now(timezone.utc).isoformat(), 'timeout_seconds': timeout,
                       'python': sys.version, 'executable': sys.executable,
                       'timed_out': timed_out, 'exit': child.returncode if child else None,
                       'signal': -child.returncode if child and child.returncode is not None and child.returncode < 0 else None}
            for stream in ('stdout', 'stderr'):
                path = capture / (stream + '.bin')
                receipt[stream + '_sha256'] = digest(path.read_bytes()) if path.exists() else None
            (capture / 'result.json').write_bytes(canonical(receipt))
        return receipt, (capture / 'stdout.bin').read_bytes(), (capture / 'stderr.bin').read_bytes()

    def call(self, world, operation, *args, refusal=False, interrupt=None, deny_reads=(),
             error_types=('ValueError', 'PermissionError'), child_timeout=30, **kwargs):
        request = {'operation': operation, 'args': [str(world['repo']), *args], 'kwargs': kwargs,
                   'deny_reads': list(map(str, deny_reads))}
        if interrupt:
            request.update(interrupt=interrupt, move=list(map(str, world['move'])))
        request_file = self.lab_root / ('request-' + uuid.uuid4().hex + '.json')
        request_file.write_bytes(canonical(request))
        argv = [sys.executable, '-I', '-B', '-c', BOOTSTRAP, str(MODULE), str(request_file)]
        receipt, stdout, stderr = self.native(operation, argv, world['repo'], timeout=child_timeout)
        self.assertFalse(receipt['timed_out'], (receipt, stdout, stderr))
        if interrupt:
            self.assertEqual(receipt['exit'], 99, (receipt, stdout, stderr))
            return None
        self.assertEqual(receipt['exit'], 2 if refusal else 0, (receipt, stdout, stderr))
        envelope = json.loads(stdout)
        if refusal:
            self.assertIn(envelope['error_type'], error_types)
            return envelope
        return envelope['result']

    def world(self, parent, shape='5', state='Complete', disposition='accepted', skipped=False):
        repo = parent / ('repo-' + uuid.uuid4().hex)
        source = repo / 'docs/plans/closed'
        source.mkdir(parents=True)
        (repo / 'docs/plans/neighbor').mkdir()
        (repo / 'docs/plans/neighbor/plan.md').write_bytes(b'# Neighbor\n\nIndependent active work.\n')
        (repo / 'docs/plans/neighbor/history.md').write_bytes(b'not a card-query input\n' * 4096)
        outside = parent / ('outside-sentinel-' + uuid.uuid4().hex)
        outside.mkdir()
        (outside / 'preserve.bin').write_bytes(b'outside the selected repository\x00\xff')
        authority = repo / '.fixture-authority'
        authority.mkdir()
        (authority / 'owner.md').write_bytes(b'Fixture controller authorizes archive/recover/restore for closed only.\n')
        plan = b'Gate: Lite\n\n# Closed fixture\n\nUseful bytes.\n' if shape in ('lite', 'ambiguous') else b'# Closed fixture\n\nUseful bytes.\n\n[Neighbor](../neighbor/plan.md)\n'
        if shape == 'bad-lite':
            plan = b'Gate: Unknown\n\n# Closed fixture\n'
        (source / 'plan.md').write_bytes(plan)
        tasks = []
        if shape not in ('lite', 'bad-lite'):
            schema = '4' if shape == 'ambiguous' else shape
            head = '# Task board\n\nSchema: tackle-workspace/' + schema + '\n\n'
            head += '| Task | What | Brief | Depends on | Status | Verification |\n|---|---|---|---|---|---|\n'
            head += '| T-0001 | Closed work | tasks/T-0001-closed.md | none | ' + state + ' | records/closure.md |\n'
            tasks.append({'id': 'T-0001', 'state': state, 'disposition': disposition})
            if skipped:
                head += '| T-0002 | Accepted exclusion | tasks/T-0002-skipped.md | none | Skipped | records/closure.md |\n'
                tasks.append({'id': 'T-0002', 'state': 'Skipped', 'disposition': 'accepted-exclusion'})
            (source / 'task-board.md').write_bytes(head.encode())
            (source / 'tasks').mkdir()
            for task in tasks:
                (source / ('tasks/' + task['id'] + '-closed.md')).write_bytes(
                    ('# Task ' + task['id'] + '\n\nClosed fixture work.\n').encode())
            if skipped:
                (source / 'tasks/T-0002-closed.md').rename(source / 'tasks/T-0002-skipped.md')
        (source / 'records').mkdir()
        (source / 'records/closure.md').write_bytes(
            b'# Accepted closure\n\nDelivery accepted. Remains: none. Effects settled. Maintenance settled.\n'
            b'Closed work is accepted; skipped scope and explicit withdrawn obligations are exclusions.\n')
        (source / 'records/binary.bin').write_bytes(b'\x00\xffretained\r\n')
        (source / 'records/alias').symlink_to('closure.md')
        (source / 'history.md').write_bytes(b'# History\r\n\r\nFailed attempt retained; cycles spent2/3.\r\nAccepted closure.\r\n')
        (source / 'empty').mkdir()
        (source / '.context-lock').write_bytes(b'')
        (source / 'records/binary.bin').chmod(0o640)
        return {'repo': repo, 'source': source, 'id': 'closed', 'tasks': tasks,
                'original': inventory(source), 'neighbor': inventory(repo / 'docs/plans/neighbor'),
                'outside': outside, 'outside_inventory': inventory(outside)}

    def ref(self, world, path):
        return {'path': str(path.relative_to(world['repo'])), 'sha256': digest(path.read_bytes())}

    def qualification(self, world):
        source, repo = world['source'], world['repo']
        closure = self.ref(world, source / 'records/closure.md')
        card = {'title': 'Closed fixture', 'purpose': 'Useful bytes', 'accepted_result': 'Accepted bounded fixture work',
                'exclusions': ['Accepted skipped or explicitly withdrawn scope'], 'reusable_decisions': ['Retain evidence bytes'],
                'closed_at': None, 'delivery_state': 'unknown', 'delivery_links': [dict(label='Closure', **closure)],
                'verification_links': [dict(label='Verification', **closure)]}
        return {'schema': 'tackle-archive-qualification/1', 'id': world['id'],
                'source_revision': digest(canonical(inventory(source))),
                'sources': [dict(claim=claim, **closure) for claim in
                            ('closure', 'obligations', 'effects', 'maintenance', 'references')],
                'tasks': [dict(task, receipt=closure) for task in world['tasks']],
                'accepted_delivery': True, 'obligations_resolved': True, 'effects_settled': True,
                'maintenance_settled': True, 'references': [],
                'reference_scope': {'inputs': [self.ref(world, source / 'plan.md')],
                                    'diagnostic': 'Selected fixture has no other required active direct readers.'},
                'reviewer': 'fixture-controller', 'observed_at': datetime.now(timezone.utc).isoformat(), 'card': card}

    def scope(self, world):
        return {'schema': 'tackle-archive-scope/1', 'repo': str(world['repo']), 'ids': [world['id']],
                'operations': ['archive', 'recover', 'restore'],
                'authorization_source': self.ref(world, world['repo'] / '.fixture-authority/owner.md')}

    def writer(self, world, revision):
        carrier = world['source'] if world['source'].exists() else world['repo'] / 'docs/plans/.archive' / world['id']
        source_refs = [self.ref(world, world['repo'] / '.fixture-authority/owner.md')]
        journal = world['repo'] / 'docs/plans/.archive/transaction.json'
        if journal.exists():
            source_refs.append(self.ref(world, journal))
            if carrier.exists():
                revision = digest(canonical(inventory(carrier)))
        return {'schema': 'tackle-archive-writers/1', 'repo': str(world['repo']), 'ids': [world['id']],
                'source_revisions': {world['id']: revision}, 'observer': 'fixture-controller',
                'observed_at': datetime.now(timezone.utc).isoformat(),
                'cooperating_locks': ([{'path': str((carrier / '.context-lock').relative_to(world['repo'])), 'protocol': 'flock'}]
                                      if (carrier / '.context-lock').is_file() and not (carrier / '.context-lock').is_symlink() else []),
                'remaining_limits': ['Only the selected owned fixture and cooperating writers are observed.'],
                'source_refs': source_refs}

    def preview(self, world, qualification=None, refusal=False):
        return self.call(world, 'preview', world['id'], qualification or self.qualification(world), refusal=refusal)

    def apply(self, world, preview, **extra):
        world['move'] = (world['source'], world['repo'] / 'docs/plans/.archive' / world['id'])
        return self.call(world, 'apply', preview, scope=self.scope(world),
                         writer_receipt=self.writer(world, preview['source_revision']), **extra)

    def restore(self, world, revision, **extra):
        world['move'] = (world['repo'] / 'docs/plans/.archive' / world['id'], world['source'])
        return self.call(world, 'restore', world['id'], revision, scope=self.scope(world),
                         writer_receipt=self.writer(world, revision), **extra)

    def preserved(self, expected, actual):
        self.assertEqual(inventory(actual), expected)
        for name, row in expected.items():
            if row['kind'] == 'symlink':
                path = actual / name
                target = path.resolve(strict=True)
                target.relative_to(actual.resolve(strict=True))
                target_name = str(target.relative_to(actual.resolve(strict=True)))
                if expected[target_name]['kind'] == 'file':
                    self.assertEqual(digest(path.read_bytes()), expected[target_name]['sha256'])

    def test_closed_workspace_archive_lookup_recover_restore(self):
        with self.lab() as lab:
            for shape, existing_lock, declared_task in (('5', True, False), ('4', True, False),
                    ('lite', True, False), ('4', False, False), ('lite', False, False), ('lite', True, True)):
                with self.subTest(shape=shape, existing_lock=existing_lock, declared_task=declared_task):
                    world = self.world(lab, shape, skipped=shape == '5')
                    if declared_task:
                        with (world['source'] / 'plan.md').open('ab') as stream:
                            stream.write(b'\n## Task T-0001\n\nState: Complete. Accepted closed fixture work.\n')
                        world['tasks'].append({'id': 'T-0001', 'state': 'Complete', 'disposition': 'accepted'})
                        world['original'] = inventory(world['source'])
                    if not existing_lock:
                        (world['source'] / '.context-lock').unlink()
                        world['original'] = inventory(world['source'])
                    original = world['original']
                    preview = self.preview(world)
                    self.assertEqual(preview['inventory'], original)
                    self.assertEqual(preview['source_revision'], digest(canonical(original)))
                    self.assertFalse((world['repo'] / 'docs/plans/.archive').exists())
                    self.apply(world, preview, interrupt='rename' if shape == '5' else None)
                    archived = world['repo'] / 'docs/plans/.archive/closed'
                    if shape == '5':
                        before_query = inventory(world['repo'])
                        pending = self.call(world, 'list_workspaces', state='all')
                        self.assertTrue(pending['pending'])
                        self.assertEqual(inventory(world['repo']), before_query)
                        recovered = self.call(world, 'recover', scope=self.scope(world),
                                              writer_receipt=self.writer(world, preview['source_revision']))
                        self.assertEqual(recovered['status'], 'recovered')
                    self.assertFalse(world['source'].exists())
                    self.preserved(original, archived)
                    active = self.call(world, 'list_workspaces', state='active')
                    self.assertNotIn('closed', [e['id'] for e in active['entries']])
                    self.assertIn('neighbor', [e['id'] for e in active['entries']])
                    found = self.call(world, 'list_workspaces', state='archived', query='UsEfUl', deny_reads=[archived])
                    self.assertEqual([e['id'] for e in found['entries']], ['closed'])
                    self.assertIsNone(found['entries'][0]['card']['closed_at'])
                    self.assertEqual(found['entries'][0]['card']['delivery_state'], 'unknown')
                    self.assertTrue(found['entries'][0]['card']['exclusions'])
                    member = 'plan.md' if shape == 'lite' else 'task-board.md'
                    for relative in (member, 'records/closure.md', 'records/alias'):
                        actual = self.call(world, 'resolve', 'closed', relative)
                        data = base64.b64decode(actual['bytes']['$fixture_bytes'])
                        self.assertEqual(data, (archived / relative).read_bytes())
                        self.assertEqual(actual['sha256'], digest(data))
                        self.assertEqual(Path(actual['path']).resolve(), (archived / relative).resolve())
                    before_repeat = inventory(world['repo'])
                    self.assertEqual(self.apply(world, preview)['status'], 'already-applied')
                    self.assertEqual(inventory(world['repo']), before_repeat)
                    restored = self.restore(world, preview['source_revision'])
                    self.assertEqual(restored['status'], 'restored')
                    self.preserved(original, world['source'])
                    self.assertEqual(inventory(world['repo'] / 'docs/plans/neighbor'), world['neighbor'])
                    self.assertEqual(inventory(world['outside']), world['outside_inventory'])
                    if shape == '4':
                        self.assertIn(b'Schema: tackle-workspace/4\n', (world['source'] / member).read_bytes())
                        self.assertNotIn(b'tackle-workspace/5', (world['source'] / member).read_bytes())
                    if shape == 'lite':
                        self.assertEqual((world['source'] / 'plan.md').read_bytes().splitlines()[0], b'Gate: Lite')
                        self.assertFalse((world['source'] / 'task-board.md').exists())
                        self.assertFalse((world['source'] / 'board.md').exists())

    def test_closure_qualification_refuses_unresolved_work(self):
        with self.lab() as lab:
            failures = [('5', 'obligations_resolved'), ('5', 'maintenance_settled'),
                        ('5', 'effects_settled'), ('5', 'missing-closure'),
                        ('99', None), ('bad-lite', None), ('ambiguous', None),
                        ('4', 'missing-closure'), ('lite', 'missing-closure'),
                        ('4', 'accepted_delivery'), ('lite', 'accepted_delivery')]
            for shape, fault in failures:
                with self.subTest(shape=shape, fault=fault):
                    world = self.world(lab, shape)
                    if fault in ('obligations_resolved', 'maintenance_settled', 'effects_settled', 'accepted_delivery'):
                        descriptions = {
                            'obligations_resolved': b'Delivery accepted. Remains: O-open. Effects and maintenance settled.\n',
                            'maintenance_settled': b'Delivery accepted. Required publication and maintenance remain pending.\n',
                            'effects_settled': b'Delivery accepted. An external effect is running and unresolved.\n',
                            'accepted_delivery': b'Delivery acceptance is absent or unresolved.\n',
                        }
                        (world['source'] / 'records/closure.md').write_bytes(descriptions[fault])
                    q = self.qualification(world)
                    if fault == 'missing-closure':
                        (world['source'] / 'records/alias').unlink()
                        (world['source'] / 'records/closure.md').unlink()
                        q['source_revision'] = digest(canonical(inventory(world['source'])))
                    elif fault:
                        q[fault] = False
                    snapshot = inventory(world['repo'])
                    self.preview(world, q, refusal=True)
                    self.assertEqual(inventory(world['repo']), snapshot)
                    self.assertEqual(inventory(world['outside']), world['outside_inventory'])
                    self.assertFalse((world['repo'] / 'docs/plans/.archive').exists())
                    self.assertFalse((world['repo'] / 'docs/plans/archive-index.md').exists())
            for state, disposition in [('Unverifiable', 'pending'), ('Skipped', 'accepted-exclusion'),
                                       ('Unverifiable', 'accepted-withdrawal')]:
                with self.subTest(state=state, disposition=disposition):
                    world = self.world(lab, state=state, disposition=disposition)
                    q = self.qualification(world)
                    q['obligations_resolved'] = disposition != 'pending'
                    snapshot = inventory(world['repo'])
                    preview = self.preview(world, q, refusal=disposition == 'pending')
                    if disposition == 'pending':
                        self.assertEqual(inventory(world['repo']), snapshot)
                    else:
                        self.apply(world, preview)
                        self.restore(world, preview['source_revision'])
                        self.preserved(world['original'], world['source'])

    def test_reference_consumers_preserve_access_or_refuse_move(self):
        from test_plan_siblings import build, run
        with self.lab() as lab:
            alpha, beta = build(lab)
            world = self.world(lab)
            shutil.rmtree(world['source'])
            world['source'] = beta
            world['repo'] = beta.parents[2]
            world['id'] = 'beta'
            authority = world['repo'] / '.fixture-authority'
            authority.mkdir()
            (authority / 'owner.md').write_bytes(b'Fixture controller authorizes selected beta fixture only.\n')
            board = (beta / 'task-board.md').read_bytes().replace(b'In progress', b'Complete').replace(b'Draft', b'Complete')
            (beta / 'task-board.md').write_bytes(board)
            (beta / 'records').mkdir()
            (beta / 'records/closure.md').write_bytes(b'All three fixture tasks accepted; Remains: none; effects and maintenance settled.\n')
            (beta / 'plan.md').write_bytes(b'# Closed sibling fixture\n\nUseful bytes.\n')
            (beta / 'task-board.md').write_bytes((beta / 'task-board.md').read_bytes().replace(b'| v |', b'| records/closure.md |'))
            world['tasks'] = [{'id': 'T-0007', 'state': 'Complete', 'disposition': 'accepted'},
                              {'id': 'T-0008', 'state': 'Complete', 'disposition': 'accepted'},
                              {'id': 'T-0009', 'state': 'Complete', 'disposition': 'accepted'}]
            q = self.qualification(world)
            pinned = self.ref(world, alpha / 'task-board.md')
            q['reference_scope'] = {'inputs': [pinned, self.ref(world, alpha / 'AGENTS.md')],
                                    'diagnostic': 'Declared active sibling view requires the original beta path.'}
            q['references'] = [{'consumer': 'plan_view', 'path': 'docs/plans/beta',
                                'sha256': digest(canonical(inventory(beta))), 'required': True,
                                'mode': 'direct', 'disposition': 'refused', 'evidence': [pinned]}]
            snapshot = inventory(world['repo'])
            self.preview(world, q, refusal=True)
            self.assertEqual(inventory(world['repo']), snapshot)
            old_run = subprocess.run
            def observed_run(argv, **options):
                self.assertEqual(options, {'capture_output': True, 'text': True, 'timeout': 60})
                receipt, stdout, stderr = self.native('sibling-reader', argv, lab, timeout=60)
                if receipt['timed_out']:
                    raise subprocess.TimeoutExpired(argv, 60, output=stdout, stderr=stderr)
                encoding = locale.getpreferredencoding(False)
                return subprocess.CompletedProcess(argv, receipt['exit'], stdout.decode(encoding), stderr.decode(encoding))
            try:
                subprocess.run = observed_run
                result, page = run(lab, alpha)
            finally:
                subprocess.run = old_run
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(page.is_file())
            self.assertTrue(beta.is_dir())
            self.assertEqual(inventory(world['repo']), snapshot)
            other = self.world(lab)
            preview = self.preview(other)
            original_plan = (other['source'] / 'plan.md').read_bytes()
            self.apply(other, preview)
            detail = self.call(other, 'resolve', 'closed', 'plan.md')
            self.assertEqual(base64.b64decode(detail['bytes']['$fixture_bytes']), original_plan)
            prefix_detail = self.call(other, 'resolve', 'docs/plans/closed', 'plan.md')
            self.assertEqual(base64.b64decode(prefix_detail['bytes']['$fixture_bytes']), original_plan)
            target = self.call(other, 'resolve', 'neighbor', 'plan.md')
            self.assertEqual(base64.b64decode(target['bytes']['$fixture_bytes']),
                             (other['repo'] / 'docs/plans/neighbor/plan.md').read_bytes())
            self.restore(other, preview['source_revision'])
            self.preserved(other['original'], other['source'])

    def test_transaction_recovery_is_idempotent_and_conflict_safe(self):
        with self.lab() as lab:
            for direction in ('archive', 'restore'):
                for phase in ('journal', 'rename', 'catalog', 'index'):
                    with self.subTest(direction=direction, phase=phase):
                        world = self.world(lab)
                        preview = self.preview(world)
                        if direction == 'archive':
                            self.apply(world, preview, interrupt=phase)
                        else:
                            self.apply(world, preview)
                            self.restore(world, preview['source_revision'], interrupt=phase)
                        transaction = json.loads((world['repo'] / 'docs/plans/.archive/transaction.json').read_bytes())
                        self.assertEqual(transaction['operation'], direction)
                        origin, destination = world['move']
                        self.assertEqual(origin.exists(), phase == 'journal')
                        self.assertEqual(destination.exists(), phase != 'journal')
                        self.preserved(world['original'], origin if phase == 'journal' else destination)
                        catalog = world['repo'] / 'docs/plans/.archive/catalog.json'
                        index = world['repo'] / 'docs/plans/archive-index.md'
                        if phase in ('journal', 'rename'):
                            self.assertEqual(digest(catalog.read_bytes()) if catalog.exists() else None,
                                             transaction['old_catalog_sha256'])
                        else:
                            self.assertEqual(catalog.read_bytes(), canonical(transaction['next_catalog']))
                        if phase == 'index':
                            self.assertEqual(index.read_bytes(), transaction['next_index'].encode('utf-8'))
                        else:
                            self.assertEqual(digest(index.read_bytes()) if index.exists() else None,
                                             transaction['old_index_sha256'])
                        snapshot = inventory(world['repo'])
                        self.assertTrue(self.call(world, 'list_workspaces', state='all')['pending'])
                        self.call(world, 'resolve', 'closed', refusal=True)
                        self.assertEqual(inventory(world['repo']), snapshot)
                        result = self.call(world, 'recover', scope=self.scope(world),
                                           writer_receipt=self.writer(world, preview['source_revision']))
                        self.assertEqual(result['status'], 'recovered')
                        final = world['repo'] / 'docs/plans/.archive/closed' if direction == 'archive' else world['source']
                        self.preserved(world['original'], final)
                        repeated = inventory(world['repo'])
                        self.assertEqual(self.call(world, 'recover', scope=self.scope(world),
                                                  writer_receipt=self.writer(world, preview['source_revision']))['status'], 'no-op')
                        self.assertEqual(inventory(world['repo']), repeated)
                        if direction == 'archive':
                            self.restore(world, preview['source_revision'])
                        else:
                            self.assertEqual(self.restore(world, preview['source_revision'])['status'], 'already-restored')
            for fault in ('both', 'neither', 'catalog-conflict', 'occupied-restore'):
                with self.subTest(fault=fault):
                    world = self.world(lab)
                    preview = self.preview(world)
                    self.apply(world, preview, interrupt=None if fault == 'occupied-restore' else 'rename')
                    archived = world['repo'] / 'docs/plans/.archive/closed'
                    if fault == 'both':
                        shutil.copytree(archived, world['source'], symlinks=True)
                    elif fault == 'neither':
                        archived.rename(lab / ('retained-lost-location-' + uuid.uuid4().hex))
                    elif fault == 'catalog-conflict':
                        (archived.parent / 'catalog.json').write_bytes(b'{"schema":"unknown","entries":{}}\n')
                    else:
                        world['source'].mkdir()
                        (world['source'] / 'occupied').write_bytes(b'preserve this concurrent destination\n')
                    snapshot = inventory(world['repo'])
                    if fault == 'occupied-restore':
                        self.restore(world, preview['source_revision'], refusal=True)
                    else:
                        self.call(world, 'recover', scope=self.scope(world),
                                  writer_receipt=self.writer(world, preview['source_revision']), refusal=True)
                    self.assertEqual(inventory(world['repo']), snapshot)
                    self.assertEqual(inventory(world['outside']), world['outside_inventory'])

    def test_boundary_and_writer_guards_preserve_sentinels(self):
        with self.lab() as lab:
            for fault in ('traversal', 'cross-root', 'external-link', 'dangling-link', 'lease', 'context-lock',
                          'stale-source', 'stale-qualification', 'stale-catalog', 'duplicate-id'):
                with self.subTest(fault=fault):
                    world = self.world(lab)
                    q = self.qualification(world)
                    if fault in ('external-link', 'dangling-link'):
                        target = world['outside'] / ('preserve.bin' if fault == 'external-link' else 'missing.bin')
                        (world['source'] / 'unsafe-alias').symlink_to(target)
                        q['source_revision'] = digest(canonical(inventory(world['source'])))
                    if fault == 'lease':
                        lease = world['source'] / 'verification-records/store/.lock'
                        lease.mkdir(parents=True)
                        (lease / 'owner.json').write_bytes(b'{"owner":"fixture-live-writer"}\n')
                        q['source_revision'] = digest(canonical(inventory(world['source'])))
                    if fault == 'stale-qualification':
                        q['source_revision'] = '0' * 64
                    snapshot = inventory(world['repo'])
                    source_snapshot = inventory(world['source'])
                    if fault in ('traversal', 'cross-root'):
                        self.call(world, 'preview', '../closed' if fault == 'traversal' else str(lab / 'outside'), q, refusal=True)
                    elif fault in ('external-link', 'dangling-link', 'lease', 'stale-qualification'):
                        self.preview(world, q, refusal=True)
                    else:
                        preview = self.preview(world, q)
                        if fault == 'context-lock':
                            with (world['source'] / '.context-lock').open('rb') as stream:
                                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                                self.assertEqual(self.apply(world, preview, refusal=True)['message'], 'writer-active')
                                fcntl.flock(stream, fcntl.LOCK_UN)
                        elif fault == 'stale-source':
                            (world['source'] / 'history.md').write_bytes(b'concurrent retained edit\n')
                            snapshot = inventory(world['repo'])
                            source_snapshot = inventory(world['source'])
                            self.apply(world, preview, refusal=True)
                        elif fault == 'stale-catalog':
                            archive = world['repo'] / 'docs/plans/.archive'
                            archive.mkdir()
                            (archive / 'catalog.json').write_bytes(canonical({'schema': 'tackle-workspace-archive/1', 'entries': {}}))
                            snapshot = inventory(world['repo'])
                            self.apply(world, preview, refusal=True)
                        else:
                            self.apply(world, preview)
                            shutil.copytree(world['repo'] / 'docs/plans/.archive/closed', world['source'], symlinks=True)
                            snapshot = inventory(world['repo'])
                            self.preview(world, self.qualification(world), refusal=True)
                            source_snapshot = inventory(world['source'])
                    if fault in ('context-lock', 'stale-source', 'stale-catalog'):
                        self.assertEqual(inventory(world['source']), source_snapshot)
                        self.assertEqual(inventory(world['repo'] / 'docs/plans/neighbor'), world['neighbor'])
                        current = inventory(world['repo'])
                        for name in ('docs/plans/.archive/catalog.json', 'docs/plans/archive-index.md',
                                     'docs/plans/.archive/transaction.json'):
                            self.assertEqual(current.get(name), snapshot.get(name))
                    else:
                        self.assertEqual(inventory(world['repo']), snapshot)
                    self.assertEqual(inventory(world['outside']), world['outside_inventory'])
            valid = self.world(lab)
            preview = self.preview(valid)
            self.apply(valid, preview)
            self.restore(valid, preview['source_revision'])
            self.preserved(valid['original'], valid['source'])
            concurrent = self.world(lab)
            preview = self.preview(concurrent)
            destination = concurrent['repo'] / 'docs/plans/.archive/closed'
            ready, release = lab / 'writer-ready', lab / 'writer-release'
            request = {'operation': 'apply', 'args': [str(concurrent['repo']), preview],
                       'kwargs': {'scope': self.scope(concurrent),
                                  'writer_receipt': self.writer(concurrent, preview['source_revision'])},
                       'move': [str(concurrent['source']), str(destination)],
                       'hold_before_rename': [str(ready), str(release)]}
            request_path = lab / 'concurrent-request.json'
            request_path.write_bytes(canonical(request))
            capture = lab / 'concurrent-writer'
            capture.mkdir()
            argv = [sys.executable, '-I', '-B', '-c', BOOTSTRAP, str(MODULE), str(request_path)]
            started = datetime.now(timezone.utc).isoformat()
            deadline = time.monotonic() + 30
            child = None
            timed_out = False
            try:
                with (capture / 'stdout.bin').open('wb') as stdout, (capture / 'stderr.bin').open('wb') as stderr:
                    child = subprocess.Popen(argv, cwd=concurrent['repo'], stdout=stdout, stderr=stderr,
                                             start_new_session=True)
                    while not ready.exists() and child.poll() is None and time.monotonic() < deadline:
                        time.sleep(0.01)
                    self.assertTrue(ready.is_file(), (child.poll(), (capture / 'stderr.bin').read_bytes()))
                    held = inventory(concurrent['repo'])
                    self.assertEqual(self.apply(concurrent, preview, refusal=True,
                                                child_timeout=max(0.001, deadline - time.monotonic()))['message'], 'writer-active')
                    self.assertEqual(inventory(concurrent['repo']), held)
                    release.write_bytes(b'finish once\n')
                    child.wait(timeout=max(0.001, deadline - time.monotonic()))
            finally:
                if child and child.poll() is None:
                    timed_out = time.monotonic() >= deadline
                    try:
                        os.killpg(child.pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
                    try:
                        child.wait(timeout=0.5)
                    except subprocess.TimeoutExpired:
                        os.killpg(child.pid, signal.SIGKILL)
                        child.wait(timeout=0.5)
                (capture / 'result.json').write_bytes(canonical(
                    {'argv': argv, 'cwd': str(concurrent['repo']), 'started': started,
                     'finished': datetime.now(timezone.utc).isoformat(), 'timeout_seconds': 30,
                     'python': sys.version, 'executable': sys.executable,
                     'timed_out': timed_out, 'exit': child.returncode if child else None,
                     'signal': -child.returncode if child and child.returncode is not None and child.returncode < 0 else None,
                     'stdout_sha256': digest((capture / 'stdout.bin').read_bytes()),
                     'stderr_sha256': digest((capture / 'stderr.bin').read_bytes())}))
            self.assertFalse(timed_out)
            self.assertEqual(child.returncode, 0, (capture / 'stderr.bin').read_bytes())
            self.assertEqual(json.loads((capture / 'stdout.bin').read_bytes())['result']['status'], 'applied')
            self.preserved(concurrent['original'], destination)
            self.restore(concurrent, preview['source_revision'])
            self.preserved(concurrent['original'], concurrent['source'])

    def test_archive_queries_are_read_only_and_bounded(self):
        with self.lab() as lab:
            world = self.world(lab)
            preview = self.preview(world)
            self.apply(world, preview)
            archived = world['repo'] / 'docs/plans/.archive/closed'
            snapshot = inventory(world['repo'])
            for state, query in [('active', None), ('archived', None), ('all', 'UsEfUl'), ('archived', 'no-match[.*]')]:
                result = self.call(world, 'list_workspaces', state=state, query=query,
                                   deny_reads=[archived, world['repo'] / 'docs/plans/neighbor/history.md'])
                if query == 'no-match[.*]':
                    self.assertEqual(result['entries'], [])
                self.assertEqual(inventory(world['repo']), snapshot)
            detail = self.call(world, 'resolve', 'closed', 'records/closure.md',
                               deny_reads=[archived / 'history.md', archived / 'records/binary.bin'])
            self.assertEqual(base64.b64decode(detail['bytes']['$fixture_bytes']), (archived / 'records/closure.md').read_bytes())
            self.call(world, 'resolve', 'closed', 'missing.md', refusal=True,
                      error_types=('ValueError', 'FileNotFoundError'))
            self.assertEqual(inventory(world['repo']), snapshot)
            world['source'].mkdir()
            (world['source'] / 'plan.md').write_bytes(b'# Independent replacement at the original path\n')
            occupied = inventory(world['repo'])
            for state, query in (('active', None), ('all', 'no-match')):
                result = self.call(world, 'list_workspaces', state=state, query=query, deny_reads=[archived])
                self.assertTrue(any(row['id'] == 'closed' and row['code'] != 'unqualified-active-name'
                                    for row in result['diagnostics']))
                self.assertEqual(inventory(world['repo']), occupied)
            (world['source'] / 'plan.md').unlink()
            world['source'].rmdir()
            repaired = self.call(world, 'list_workspaces', state='active', deny_reads=[archived])
            self.assertFalse(any(row['id'] == 'closed' for row in repaired['diagnostics']))
            self.assertEqual(inventory(world['repo']), snapshot)
            index = world['repo'] / 'docs/plans/archive-index.md'
            index.write_bytes(index.read_bytes() + b'conflicting projection\n')
            conflict = inventory(world['repo'])
            self.call(world, 'list_workspaces', state='archived', refusal=True)
            self.assertEqual(inventory(world['repo']), conflict)
            fresh = self.world(lab)
            pending = self.preview(fresh)
            self.apply(fresh, pending, interrupt='journal')
            unchanged = inventory(fresh['repo'])
            self.assertTrue(self.call(fresh, 'list_workspaces', state='all')['pending'])
            self.call(fresh, 'resolve', 'closed', refusal=True)
            self.assertEqual(inventory(fresh['repo']), unchanged)

    def test_member_symlink_loop_is_the_same_refusal_on_every_python(self):
        # Python before 3.13 raises RuntimeError for a symlink loop in resolve(strict=True); 3.13 and later
        # raise OSError(ELOOP). Both must reach the member-link-conflict refusal; other errors keep their type.
        spec = importlib.util.spec_from_file_location('workspace_archive_member_probe', MODULE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory(prefix='member loop ') as directory:
            base = Path(directory).resolve()
            (base / 'alias').symlink_to('alias')
            with self.assertRaises(ValueError) as real_loop:
                module._member_file(base, 'alias', None)
            self.assertEqual(str(real_loop.exception), 'member-link-conflict')
            for error in (RuntimeError('Symlink loop from ' + str(base / 'alias')),
                          OSError(errno.ELOOP, os.strerror(errno.ELOOP))):
                with self.subTest(error=type(error).__name__):
                    with patch.object(Path, 'resolve', side_effect=error):
                        with self.assertRaises(ValueError) as refused:
                            module._member_file(base, 'alias', None)
                    self.assertEqual(str(refused.exception), 'member-link-conflict')
            with patch.object(Path, 'resolve', side_effect=OSError(errno.EACCES, 'fixture denial')):
                with self.assertRaises(PermissionError):
                    module._member_file(base, 'alias', None)
            with self.assertRaises(FileNotFoundError):
                module._member_file(base, 'absent', None)

    def test_oracles_reject_loss_and_allow_intact_alternative(self):
        with self.lab() as lab:
            world = self.world(lab, skipped=True)
            preview = self.preview(world)
            self.apply(world, preview)
            archived = world['repo'] / 'docs/plans/.archive/closed'
            self.preserved(world['original'], archived)
            closure = archived / 'records/closure.md'
            original_closure = closure.read_bytes()
            intact = self.call(world, 'resolve', 'closed', 'records/alias')
            self.assertEqual(base64.b64decode(intact['bytes']['$fixture_bytes']), original_closure)
            closure.write_bytes(bytes([original_closure[0] ^ 1]) + original_closure[1:])
            corrupt = inventory(world['repo'])
            self.call(world, 'resolve', 'closed', 'records/alias', refusal=True)
            self.assertEqual(inventory(world['repo']), corrupt)
            self.assertEqual((archived / 'records/alias').readlink(), Path('closure.md'))
            closure.write_bytes(original_closure)
            repaired = self.call(world, 'resolve', 'closed', 'records/alias')
            self.assertEqual(base64.b64decode(repaired['bytes']['$fixture_bytes']), original_closure)
            alias = archived / 'records/alias'
            alias.unlink()
            alias.symlink_to('alias')
            looped = inventory(world['repo'])
            self.call(world, 'resolve', 'closed', 'records/alias', refusal=True)
            self.assertEqual(inventory(world['repo']), looped)
            self.assertEqual(alias.readlink(), Path('alias'))
            alias.unlink()
            alias.symlink_to('closure.md')
            repaired = self.call(world, 'resolve', 'closed', 'records/alias')
            self.assertEqual(base64.b64decode(repaired['bytes']['$fixture_bytes']), original_closure)
            for fault in ('history-byte', 'required-alias'):
                mutant = lab / ('mutant-' + fault)
                shutil.copytree(archived, mutant, symlinks=True)
                count = len(inventory(mutant))
                if fault == 'history-byte':
                    original = (mutant / 'history.md').read_bytes()
                    (mutant / 'history.md').write_bytes(bytes([original[0] ^ 1]) + original[1:])
                else:
                    (mutant / 'records/alias').unlink()
                    (mutant / 'records/alias').symlink_to('missing.md')
                self.assertEqual(len(inventory(mutant)), count)
                with self.assertRaises(AssertionError):
                    self.preserved(world['original'], mutant)
            self.restore(world, preview['source_revision'])
            self.preserved(world['original'], world['source'])


if __name__ == '__main__':
    unittest.main()
