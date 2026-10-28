"""Typed nested links through the real compact pipeline; temporary synthetic data only."""
from pathlib import Path
import contextlib, functools, hashlib, importlib.util, json, os, shutil, sys, tempfile, threading, unittest, errno
from unittest import mock
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from eval.tests.product.migration import test_compact_migration as fixture
spec = importlib.util.spec_from_file_location('compact_content_links', ROOT / 'skills/tackle/scripts/migrate/compact.py')
compact = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compact)

def fixture_phase(number):
    return 'P-' + str(number).zfill(2)
FIXTURE_PHASE_1 = fixture_phase(1)
FIXTURE_PHASE_3 = fixture_phase(3)

def fixture_task(number):
    return 'T-' + str(number).zfill(2)
FIXTURE_TASK_6 = fixture_task(6)

def harness():
    return fixture.CompactMigrationTests('runTest')

def nanoid(root):
    parent = root / f'verification-records/{FIXTURE_TASK_6}/baseline/node_modules'
    (parent / '.bin').mkdir(parents=True)
    (parent / 'nanoid/bin').mkdir(parents=True)
    (parent / 'nanoid/bin/nanoid.cjs').write_bytes(b'export const fixture = true;\n')
    link = parent / '.bin/nanoid'
    link.symlink_to('../nanoid/bin/nanoid.cjs')
    return link.relative_to(root).as_posix()

def inert_links(root, outside):
    raw = root / 'raw'
    raw.mkdir(exist_ok=True)
    links = {'absolute': str(outside), 'broken': 'missing-target', 'cycle': 'cycle', 'chain-a': 'chain-b', 'chain-b': str(outside), 'directory': str(outside.parent), 'literal': '../do-not-normalize/./state.json'}
    for (name, target) in links.items():
        (raw / name).symlink_to(target)
    return {'raw/' + name: target for (name, target) in links.items()}

@contextlib.contextmanager
def case(**labels):
    """Name the failing case without unittest sub-tests."""
    try:
        yield
    except AssertionError as exc:
        raise AssertionError(repr(labels) + ': ' + str(exc)) from exc

def failure_not_error(test):
    """Report an unexpected exception as a failed expectation, not a test error."""
    @functools.wraps(test)
    def wrapper(self):
        try:
            test(self)
        except (AssertionError, unittest.SkipTest):
            raise
        except Exception as exc:
            self.fail(type(exc).__name__ + ': ' + str(exc))
    return wrapper

class ContentSymlinkTests(unittest.TestCase):

    @failure_not_error
    def test_nanoid_diagnose_is_read_only_and_keeps_typed_identity(self):
        h = harness()
        with h.lab() as lab:
            installed = h.install(lab)
            (project, source) = h.fixture(lab, 'nanoid')
            agents = source / 'AGENTS.md'
            agents.write_bytes(agents.read_bytes().replace(b'Tackle 10.1.0', b'Tackle 10.0.0'))
            rel = nanoid(source)
            before = fixture.inventory(source)
            (manifest, plan, _) = h.plan(installed, source, lab / 'job')
            self.assertEqual(fixture.inventory(source), before)
            self.assertEqual(plan['source']['inventory'][rel], before[rel])
            self.assertEqual(plan['source']['inventory'][rel]['target'], '../nanoid/bin/nanoid.cjs')
            self.assertNotIn(rel, compact._tree(source).files)

    @failure_not_error
    def test_inert_target_classes_survive_checkpoint_copy_and_restore_copy(self):
        with tempfile.TemporaryDirectory(prefix='tackle-link-copy-') as raw:
            lab = Path(raw).resolve()
            source = lab / 'source'
            source.mkdir()
            outside = lab / 'outside/state.json'
            outside.parent.mkdir()
            outside.write_bytes(b'outside\n')
            expected = inert_links(source, outside)
            rel = nanoid(source)
            before = fixture.inventory(source)
            for dest in (lab / 'checkpoint', lab / 'candidate-copy'):
                compact._copy_bytes(source, dest)
                self.assertEqual(fixture.inventory(dest), before)
                for (path, target) in expected.items():
                    self.assertEqual(os.readlink(dest / path), target)
            compact._copy_bytes(lab / 'checkpoint', lab / 'restored')
            self.assertEqual(fixture.inventory(lab / 'restored'), before)
            self.assertEqual(outside.read_bytes(), b'outside\n')

    @failure_not_error
    def test_type_target_and_deletion_are_part_of_tree_identity(self):
        with tempfile.TemporaryDirectory(prefix='tackle-link-identity-') as raw:
            root = Path(raw).resolve()
            (root / 'raw').mkdir()
            link = root / 'raw/object'
            link.symlink_to('missing')
            before = compact._inventory(root)
            digest = compact._inventory_sha(before)
            mode = before['raw/object']['mode']
            link.unlink()
            link.symlink_to('./missing')
            self.assertNotEqual(compact._inventory_sha(compact._inventory(root)), digest)
            link.unlink()
            link.write_bytes(b'missing')
            link.chmod(mode)
            self.assertNotEqual(compact._inventory_sha(compact._inventory(root)), digest)
            link.unlink()
            self.assertNotEqual(compact._inventory_sha(compact._inventory(root)), digest)
            regular = {'raw': before['raw'], 'raw/object': {'type': 'file', 'mode': mode, 'sha256': hashlib.sha256(b'missing').hexdigest()}}
            self.assertNotEqual(compact._inventory_sha(regular), digest)

    @failure_not_error
    def test_live_fifo_and_directory_canaries_observe_actual_target_access(self):
        with tempfile.TemporaryDirectory(prefix='tackle-link-no-follow-') as raw:
            lab = Path(raw).resolve()
            root = lab / 'source'
            root.mkdir()
            outside = lab / 'outside'
            outside.mkdir()
            fifo = outside / 'state.json'
            os.mkfifo(fifo)
            inert_links(root, fifo)
            outside_id = (outside.stat().st_dev, outside.stat().st_ino)
            traversals = []
            metadata = []
            read_opens = []
            fifo_id = (fifo.stat().st_dev, fifo.stat().st_ino)
            (real_listdir, real_scandir, real_stat, real_lstat, real_open) = (os.listdir, os.scandir, os.stat, os.lstat, os.open)
            link_names = {'absolute', 'broken', 'cycle', 'chain-a', 'chain-b', 'directory', 'literal'}

            def is_outside(path):
                return isinstance(path, (str, bytes, Path)) and Path(os.fsdecode(path)).is_absolute() and Path(os.fsdecode(path)).is_relative_to(outside)

            def observed_stat(path, *args, **kwargs):
                if is_outside(path) or (isinstance(path, (str, bytes, Path)) and Path(os.fsdecode(path)).name in link_names and kwargs.get('follow_symlinks', True)):
                    metadata.append(True)
                return real_stat(path, *args, **kwargs)

            def observed_lstat(path, *args, **kwargs):
                if is_outside(path):
                    metadata.append(True)
                return real_lstat(path, *args, **kwargs)

            def observed_open(path, flags, *args, **kwargs):
                fd = real_open(path, flags, *args, **kwargs)
                info = os.fstat(fd)
                if (info.st_dev, info.st_ino) in (outside_id, fifo_id) and flags & os.O_ACCMODE != os.O_WRONLY:
                    read_opens.append(True)
                return fd

            def listdir(path):
                info = os.fstat(path) if isinstance(path, int) else real_stat(path)
                if (info.st_dev, info.st_ino) == outside_id:
                    traversals.append(True)
                return real_listdir(path)

            def scandir(path):
                info = os.fstat(path) if isinstance(path, int) else real_stat(path)
                if (info.st_dev, info.st_ino) == outside_id:
                    traversals.append(True)
                return real_scandir(path)

            def observe(action, forbidden=False):
                stop = threading.Event()
                opens = []
                errors = []
                failure = None

                def writer():
                    while not stop.is_set():
                        try:
                            fd = os.open(fifo, os.O_WRONLY | os.O_NONBLOCK)
                            try:
                                opens.append(True)
                                try:
                                    os.write(fd, b'outside\n')
                                except BrokenPipeError:
                                    pass
                            finally:
                                os.close(fd)
                        except OSError as error:
                            if error.errno not in (errno.ENXIO, errno.ENOENT):
                                errors.append(repr(error))
                                return
                        stop.wait(0.01)
                thread = threading.Thread(target=writer)
                thread.start()
                try:
                    action()
                except BaseException as error:
                    failure = error
                finally:
                    stop.set()
                    thread.join(timeout=1)
                self.assertFalse(thread.is_alive())
                self.assertEqual(errors, [])
                if forbidden:
                    self.assertFalse(opens, 'consumer opened external FIFO')
                if failure:
                    raise failure
                return bool(opens)
            with mock.patch.object(compact.os, 'listdir', listdir), mock.patch.object(compact.os, 'scandir', scandir), mock.patch.object(compact.os, 'stat', observed_stat), mock.patch.object(compact.os, 'lstat', observed_lstat), mock.patch.object(compact.os, 'open', observed_open):
                self.assertFalse(observe(lambda : compact._tree(root), forbidden=True))
                self.assertFalse(observe(lambda : compact._inventory(root), forbidden=True))
                self.assertEqual((traversals, metadata, read_opens), ([], [], []))
                fd = os.open(outside, os.O_RDONLY | os.O_DIRECTORY)
                try:
                    compact.os.listdir(fd)
                    with compact.os.scandir(fd):
                        pass
                finally:
                    os.close(fd)
                self.assertTrue(traversals, 'directory observer must detect its live control')
                self.assertTrue(read_opens, 'descriptor observer must detect its live control')
                os.stat(root / 'raw/absolute')
                self.assertTrue(metadata, 'metadata observer must detect its live control')
            self.assertTrue(observe(lambda : fifo.read_bytes()), 'FIFO witness must detect its live control')

    @failure_not_error
    def test_path_substitution_cannot_open_an_outside_file_or_directory(self):
        for kind in ('file', 'directory'):
            with case(kind=kind), tempfile.TemporaryDirectory(prefix='tackle-link-race-') as raw:
                lab = Path(raw).resolve()
                root = lab / 'source'
                (root / 'raw').mkdir(parents=True)
                victim = root / 'raw/value'
                outside = lab / 'outside'
                if kind == 'file':
                    victim.write_bytes(b'inside')
                    outside.write_bytes(b'outside')
                else:
                    victim.mkdir()
                    outside.mkdir()
                    (outside / 'sentinel').write_bytes(b'outside')
                outside_id = (outside.stat().st_dev, outside.stat().st_ino)
                real_open = os.open
                opened = []
                swapped = []

                def replacing(path, flags, *args, **kwargs):
                    if os.fspath(path) == 'value' and 'dir_fd' in kwargs and (not swapped):
                        swapped.append(True)
                        victim.unlink() if kind == 'file' else victim.rmdir()
                        victim.symlink_to(outside)
                    fd = real_open(path, flags, *args, **kwargs)
                    info = os.fstat(fd)
                    if (info.st_dev, info.st_ino) == outside_id:
                        opened.append(True)
                    return fd
                with mock.patch.object(compact.os, 'open', replacing):
                    with self.assertRaises((OSError, compact.MigrationError)):
                        compact._tree(root)
                self.assertTrue(swapped)
                self.assertEqual(opened, [])

    @failure_not_error
    def test_materialization_validates_prefix_payload_and_alias_collisions_before_effects(self):
        with tempfile.TemporaryDirectory(prefix='tackle-link-collisions-') as raw:
            lab = Path(raw).resolve()
            outside = lab / 'outside'
            outside.mkdir()
            carrier = lab / 'carrier'
            carrier.symlink_to(outside)
            mode = carrier.lstat().st_mode & 4095
            link = {'type': 'symlink', 'mode': mode, 'sha256': None, 'target': str(outside)}
            file = {'type': 'file', 'mode': 420, 'sha256': compact._sha(b'x')}
            cases = [({'a/b': b'x'}, {'a': link, 'a/b': file}), ({'a': b'x', 'a/b': b'x'}, None), ({'a/../b': b'x'}, None), ({'a': b'x'}, {'a': link}), ({'a': b'x'}, {'a': dict(file, sha256='0' * 64)})]
            for (number, (files, inventory)) in enumerate(cases):
                dest = lab / ('dest-' + str(number))
                with self.assertRaises(compact.MigrationError):
                    compact._materialize(files, dest, inventory)
                self.assertFalse(dest.exists())
                self.assertEqual(list(outside.iterdir()), [])
            parent = lab / 'parent'
            parent.symlink_to(outside, target_is_directory=True)
            held = False
            try:
                compact._materialize({'x': b'x'}, parent / 'copy')
            except (OSError, compact.MigrationError):
                held = True
            self.assertEqual(list(outside.iterdir()), [], 'materializer wrote through an alias')
            self.assertTrue(held)
            compact._materialize({'a/b': b'x'}, lab / 'regular-stage')
            self.assertEqual((lab / 'regular-stage/a/b').read_bytes(), b'x')
            outside_file = outside / 'mode-target'
            outside_file.write_bytes(b'outside mode sentinel')
            outside_file.chmod(416)
            requested = mode ^ 64
            inventory = {'raw': {'type': 'directory', 'mode': 493, 'sha256': None}, 'raw/link': dict(link, target=str(outside_file), mode=requested)}
            rejected = None
            try:
                compact._materialize({}, lab / 'mode-stage', inventory)
            except compact.MigrationError as error:
                rejected = str(error)
            self.assertEqual(outside_file.stat().st_mode & 4095, 416, 'link chmod touched an outside target')
            self.assertEqual(outside_file.read_bytes(), b'outside mode sentinel')
            if rejected:
                self.assertIn('unsupported-link-mode:', rejected)
            else:
                made = compact._inventory(lab / 'mode-stage')['raw/link']
                self.assertEqual((made['type'], made['mode'], made['target']), ('symlink', requested, str(outside_file)))

    @failure_not_error
    def test_actual_required_inputs_refuse_links_including_citations_and_event_sources(self):
        for kind in ('root', 'brief', 'citation', 'case-citation', 'event-source', 'history-segment'):
            with case(kind=kind):
                h = harness()
                with h.lab() as lab:
                    (project, source) = h.fixture(lab, kind)
                    outside = lab / 'outside.md'
                    outside.write_text('# Outside\n')
                    if kind == 'root':
                        path = source / 'plan.md'
                        path.unlink()
                    elif kind == 'brief':
                        path = next((source / 'tasks').glob('*.md'))
                        path.unlink()
                    else:
                        path = source / 'raw/cited.md'
                        path.parent.mkdir()
                        if kind in ('citation', 'case-citation'):
                            spelling = 'raw/cited.md' if kind == 'citation' else 'RAW/cited.md'
                            with (source / 'plan.md').open('a') as stream:
                                stream.write('\n' + spelling + ':1 — "Outside"\n')
                        elif kind == 'event-source':
                            with (source / 'resource-usage.md').open('a') as stream:
                                stream.write('| run | finish | T-0002 | executor | host | fast | model | low | n/a | failed | 1 | n/a | n/a | raw/cited.md#event-x |\n')
                        else:
                            index = source / 'history/index.md'
                            index.parent.mkdir()
                            index.write_text('# Index\n\n```json\n' + json.dumps({'schema': 'tackle-history/1', 'segments': [{'path': 'raw/cited.md'}]}) + '\n```\n')
                    path.symlink_to(outside)
                    before = fixture.inventory(source)
                    with self.assertRaisesRegex(compact.MigrationError, 'root-link-refused|required-regular-link'):
                        compact._tree(source)
                    self.assertEqual(fixture.inventory(source), before)

    @failure_not_error
    def test_control_job_install_lock_and_receipt_aliases_remain_held(self):
        h = harness()
        with h.lab() as lab:
            installed = h.install(lab)
            (project, source) = h.fixture(lab, 'controls')
            nanoid(source)
            job = lab / 'job'
            (plan, candidate, frozen) = h.ready(installed, source, job)
            before = fixture.inventory(source)
            for path in (job / 'state.json', job / 'receipts/admission.json', candidate / '.context-lock', installed / 'SKILL.md'):
                with case(path=path.name):
                    saved = path.read_bytes()
                    mode = path.stat().st_mode & 4095
                    outside = lab / ('saved-' + path.name)
                    outside.write_bytes(saved)
                    path.unlink()
                    path.symlink_to(outside)
                    if path.name == 'state.json':
                        with self.assertRaises(compact.PendingError):
                            compact._load_state(job)
                    else:
                        h.cli(installed, 'adopt', ['--job', job], 1)
                    path.unlink()
                    path.write_bytes(saved)
                    path.chmod(mode)
                    self.assertEqual(outside.read_bytes(), saved)
                    self.assertEqual(fixture.inventory(source), before)
            alias = lab / 'job-alias'
            alias.symlink_to(job, target_is_directory=True)
            h.cli(installed, 'adopt', ['--job', alias], 2)

    @failure_not_error
    def test_all_structural_adapters_project_link_entries_and_legacy_snapshots(self):
        h = harness()
        with h.lab() as lab:
            installed = h.install(lab)
            for (name, fixture_name, old, new) in [('pre-3', 'pre3-to-3', f'evidence/{FIXTURE_PHASE_3}/link', f'verification-records/{FIXTURE_PHASE_3}/link'), ('3', '3-to-4', f'evidence/{FIXTURE_PHASE_1}/link', f'verification-records/{FIXTURE_PHASE_1}/link'), ('4', '4-to-5', 'raw/link', 'raw/link')]:
                source = lab / ('project-' + name) / 'docs/plans/demo'
                shutil.copytree(ROOT / 'eval/migration/fixtures' / fixture_name / 'before', source)
                path = source / old
                path.parent.mkdir(parents=True, exist_ok=True)
                path.symlink_to('../literal/./target')
                before = fixture.inventory(source)
                job = lab / ('job-' + name)
                (manifest, plan, _) = h.plan(installed, source, job, next_wave=False)
                h.cli(installed, 'prepare', ['--manifest', manifest, '--job', job], 0)
                candidate = job / 'candidate-project/docs/plans/demo'
                after = fixture.inventory(candidate)
                self.assertEqual(after[new], before[old])
                self.assertEqual(fixture.inventory(job / 'checkpoint'), before)
                copies = [meta for (path, meta) in after.items() if path.startswith('legacy-') and path.endswith('/' + old)]
                self.assertIn(before[old], copies)
                self.assertEqual(fixture.inventory(source), before)

    @failure_not_error
    def test_full_lifecycle_preserves_links_and_repeats_are_exact_noops(self):
        h = harness()
        with h.lab() as lab:
            installed = h.install(lab)
            (project, source) = h.fixture(lab, 'lifecycle')
            rel = nanoid(source)
            inert_links(source, project / 'neighbor-sentinel')
            before = fixture.inventory(source)
            job = lab / 'job'
            (plan, candidate, frozen) = h.ready(installed, source, job)
            h.cli(installed, 'prepare', ['--manifest', job / 'manifest.json', '--job', job], 0)
            self.assertEqual(fixture.inventory(job / 'checkpoint'), before)
            h.cli(installed, 'adopt', ['--job', job], 0)
            adopted = fixture.inventory(source)
            self.assertEqual(adopted[rel], before[rel])
            h.cli(installed, 'adopt', ['--job', job], 0)
            self.assertEqual(fixture.inventory(source), adopted)
            h.cli(installed, 'restore', ['--job', job], 0)
            self.assertEqual(fixture.inventory(source), before)
            state = fixture.inventory(job)
            h.cli(installed, 'restore', ['--job', job], 0)
            self.assertEqual(fixture.inventory(job), state)
            self.assertEqual(fixture.inventory(source), before)
            self.assertEqual((project / 'neighbor-sentinel').read_bytes(), b'neighbor\n')

    @failure_not_error
    def test_link_drift_blocks_real_adoption(self):
        for fault in ('target', 'file', 'delete'):
            with case(fault=fault):
                h = harness()
                with h.lab() as lab:
                    installed = h.install(lab)
                    (project, source) = h.fixture(lab, fault)
                    rel = nanoid(source)
                    before = fixture.inventory(source)
                    job = lab / 'job'
                    (plan, candidate, frozen) = h.ready(installed, source, job)
                    path = candidate / rel
                    target = os.readlink(path)
                    path.unlink()
                    if fault == 'target':
                        path.symlink_to('./' + target)
                    if fault == 'file':
                        path.write_bytes(target.encode())
                    h.cli(installed, 'adopt', ['--job', job], 1)
                    self.assertEqual(fixture.inventory(source), before)
                    self.assertEqual((project / 'neighbor-sentinel').read_bytes(), b'neighbor\n')

    @failure_not_error
    def test_interrupted_adopt_and_restore_recover_with_exact_links(self):
        h = harness()
        with h.lab() as lab:
            installed = h.install(lab)
            for direction in ('adopt', 'restore'):
                for count in (1, 2):
                    for mode in ('before', 'after'):
                        label = direction + '-' + str(count) + '-' + mode
                        (project, source) = h.fixture(lab, label)
                        nanoid(source)
                        job = lab / ('job-' + label)
                        (plan, candidate, frozen) = h.ready(installed, source, job)
                        original = fixture.inventory(job / 'checkpoint')
                        if direction == 'restore':
                            h.cli(installed, 'adopt', ['--job', job], 0)
                        boot = lab / (label + '.py')
                        boot.write_text(fixture.INTERRUPT)
                        signal = lab / (label + '.signal')
                        h.run_child([sys.executable, '-I', '-B', boot, installed / 'scripts/migrate/compact.py', direction, job, str(count), mode, signal], lab, 99)
                        self.assertEqual(signal.read_bytes(), (mode + '\n').encode())
                        h.cli(installed, direction, ['--job', job], 0)
                        self.assertEqual(fixture.tree_sha(source), frozen if direction == 'adopt' else fixture.tree_sha(job / 'checkpoint'))
                        if direction == 'restore':
                            self.assertEqual(fixture.inventory(source), original)
                        after = fixture.inventory(job)
                        h.cli(installed, direction, ['--job', job], 0)
                        self.assertEqual(fixture.inventory(job), after)

    @failure_not_error
    def test_actual_native_checker_refuses_link_inputs_without_opening_targets(self):
        for parent in ('raw', 'reference-docs'):
            h = harness()
            with case(parent=parent), h.lab() as lab:
                installed = h.install(lab)
                (project, source) = h.fixture(lab, old=False)
                job = lab / 'job'
                job.mkdir()
                outside = lab / 'external.md'
                os.mkfifo(outside)
                target = source / parent
                target.mkdir(exist_ok=True)
                (target / 'evidence.md').symlink_to(outside)
                stop = threading.Event()
                opens = []
                errors = []

                def writer():
                    while not stop.is_set():
                        try:
                            fd = os.open(outside, os.O_WRONLY | os.O_NONBLOCK)
                            try:
                                opens.append(True)
                                try:
                                    os.write(fd, b'outside payload\n')
                                except BrokenPipeError:
                                    pass
                            finally:
                                os.close(fd)
                        except OSError as error:
                            if error.errno not in (errno.ENXIO, errno.ENOENT):
                                errors.append(str(error))
                                return
                        stop.wait(0.01)
                thread = threading.Thread(target=writer)
                thread.start()
                try:
                    with self.assertRaisesRegex(compact.MigrationError, 'required-regular-link'):
                        compact._check_native(installed, project, source.name, job, 'candidate', source, 'a' * 64, 'b' * 64, compact._install_identity(installed))
                finally:
                    stop.set()
                    thread.join(timeout=1)
                    self.assertFalse(opens, 'native lint read an uncited external target; live FIFO connection observed')
                self.assertFalse(thread.is_alive())
                self.assertEqual(errors, [])
                (target / 'evidence.md').unlink()
                (target / 'evidence.md').write_bytes(b'ordinary retained evidence\n')
                nanoid(source)
                checks = compact._check_native(installed, project, source.name, job, 'candidate', source, 'a' * 64, 'b' * 64, compact._install_identity(installed))
                self.assertEqual([row['row'] for row in checks], list(range(1, 20)))
if __name__ == '__main__':
    unittest.main()
