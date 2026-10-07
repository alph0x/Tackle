"""Public offline guarantees: native fixture effects, bytes, and refusal witnesses.

These tests execute local fixtures only. They establish neither provider billing,
OS containment, real listener topology, private outcomes, nor agent behavior.
"""
import base64
import copy
from decimal import Decimal
import errno
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[5]
HARNESS = ROOT / 'eval/behavior/harness'
sys.path.insert(0, str(HARNESS))
import controlled_route as route
import gpt_route as legacy
import subscription_route as public
import jev_signal as signal_reader


def script(items, fault=None, chunk=0):
    return dict(schema='stub-responses-script/1', items=items, status='completed',
                fault=fault, chunk_bytes=chunk)


def text_item(text='Finished.', item_id='final'):
    return dict(type='message', id=item_id, role='assistant',
                content=[dict(type='output_text', text=text)])


def tool(name, arguments, identity='call'):
    return dict(type='function_call', id='item_' + identity, call_id=identity,
                name=name, arguments=arguments if isinstance(arguments, str) else json.dumps(arguments, ensure_ascii=False))


class ControlledRoute(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='controlled-public-')
        self.parent = Path(self.temporary.name).resolve()
        self.task = self.parent / 'task'
        self.config = route.create_config(self.task)
        self.serial = 0
        self.commands = []

    def tearDown(self):
        # Optional native-run instrumentation retains all synthetic artifacts,
        # including failed packets; the directory must be new for each test.
        capture = os.environ.get('TACKLE_CONTROLLED_CAPTURE_ROOT')
        if capture:
            destination = Path(capture) / self.id().rsplit('.', 1)[-1]
            shutil.copytree(self.parent, destination, symlinks=True)
            (destination / 'native-test-commands.json').write_bytes(route.encoded(self.commands))
        self.temporary.cleanup()

    def cli(self, command, config=None, episode=None, bundle=None, out=None):
        self.serial += 1
        configured = self.config if config is None else config
        path = self.task / ('config-%d.json' % self.serial)
        path.write_bytes(route.encoded(configured))
        out = Path(out) if out else self.task / 'evidence' / ('output-%d' % self.serial)
        argv = [sys.executable, '-B', str(HARNESS / 'gpt_route.py'), command,
                '--config', str(path), '--out', str(out)]
        if episode is not None:
            ep = self.task / ('episode-%d.json' % self.serial)
            ep.write_bytes(route.encoded(episode)); argv.extend(['--episode', str(ep)])
        if bundle is not None:
            argv.extend(['--bundle', str(bundle)])
        started = time.monotonic_ns()
        result = subprocess.run(argv, cwd=ROOT, capture_output=True, timeout=45,
            env=dict(PATH='/usr/bin:/bin', TMPDIR=tempfile.gettempdir(),
                     LANG='C.UTF-8', PYTHONDONTWRITEBYTECODE='1'))
        self.commands.append(dict(argv=argv, cwd=str(ROOT), started_ns=started,
            ended_ns=time.monotonic_ns(), native_exit=result.returncode,
            signal=-result.returncode if result.returncode < 0 else None, timeout=False,
            stdout_utf8_b64=base64.b64encode(result.stdout).decode(),
            stderr_utf8_b64=base64.b64encode(result.stderr).decode()))
        self.assertEqual(result.stderr, b'', result.stderr)
        return result.returncode, json.loads(result.stdout), out

    def episode(self, responses=None, eid='episode', sessions=None, stage='smoke', files=None):
        return dict(schema='tackle-controlled-offline-episode/1', episode_id=eid,
            arm='control', stage=stage, fixture_files=files or {}, install_files={},
            sessions=sessions or [dict(session_id='s1', prompt='Synthetic public task.',
                responses=responses or [script([text_item()])])],
            limits=dict(seconds=900, request_units=60), network=None)

    def completed(self, episode):
        code, packet, out = self.cli('controlled-run', episode=episode)
        self.assertEqual((code, packet['outcome']), (0, 'offline_completed'), packet)
        base = out / episode['episode_id']
        self.assertTrue((base / 'bundle.json').is_file())
        return base, json.loads((base / 'bundle.json').read_bytes())

    def journal(self):
        path = self.task / 'state/journal.jsonl'
        return [json.loads(line) for line in path.read_bytes().splitlines()] if path.exists() else []

    def no_dispatch(self, out):
        self.assertEqual(list(out.rglob('stub.stderr.jsonl')) if out.exists() else [], [])

    def carry(self, stage, amount, settled='n/a'):
        path = self.task / 'state/checkpoint.json'
        checkpoint = json.loads(path.read_bytes())
        raw = route.encoded(dict(kind='synthetic_non_inference', stage=stage,
                                 reserved_usd=amount, actual_usd=settled))
        source_path = self.task / 'state/carried.json'
        source_path.write_bytes(raw)
        source = route.record('raw_source', artifact='carried.json', sha256=route.digest(raw),
            byte_start=0, byte_end=len(raw), event_id='carried', producer='ledger')
        checkpoint['prior_claims'] = [route.record('checkpoint_claim', claim_id='carried',
            kind='non_inference', stage=stage, episode_id=None, attempt_id=None,
            admission_id=None, body_sha256=None, reservation_event_id=None,
            request_units=0, unit_state='not_inference', reserved_usd=amount,
            settled_usd=settled, settlement_status='unsettled' if settled == 'n/a' else 'settled', source=source)]
        raw = route.encoded(checkpoint); path.write_bytes(raw)
        self.config['checkpoint']['sha256'] = route.digest(raw)

    def local_worker(self, name, given):
        self.serial += 1
        work = self.task / 'runs' / ('direct-%d' % self.serial)
        work.mkdir()
        tmp = work / 'tmp'; tmp.mkdir()
        store_root = self.task / 'evidence' / ('direct-%d' % self.serial); store_root.mkdir()
        argument = route.encoded(given)
        source = route.record('raw_source', artifact='synthetic-argument.json', sha256=route.digest(argument),
            byte_start=0, byte_end=len(argument), event_id='direct', producer='stub')
        invocation = dict(schema=route.VERSIONS['invocation'], episode_id='direct', session_id='s1',
            attempt_id='a1', response_id='resp-one', item_index=0, item_id='i1', call_id='call-one',
            function_name=name, arguments_utf8_b64=base64.b64encode(argument).decode(),
            arguments_sha256=route.digest(argument), arguments_raw_span=source,
            parsed_input=given, worker_handle='w1', fingerprint=self.config['pins']['fingerprint'])
        result = route.execute_tool(invocation, dict(work=work, tmp=tmp, runtime=route.FIXTURE), route.Store(store_root))[0]
        return result, store_root

    def test_legacy_selector(self):
        before = copy.deepcopy((legacy.BINDING, legacy.MAPPING, legacy.CAPS))
        args = legacy.parser().parse_args(['preflight', '--config', 'x', '--out', 'y'])
        self.assertEqual(args.command, 'preflight')
        code, packet, _ = self.cli('controlled-preflight')
        self.assertEqual((code, packet['schema']), (0, 'tackle-controlled-route-packet/1'))
        self.assertEqual((legacy.BINDING, legacy.MAPPING, legacy.CAPS), before)
        code, packet, out = self.cli('preflight', config=dict(schema='tackle-controlled-route-config/1', mode='offline'))
        self.assertEqual(code, 2)
        self.assertFalse(out.exists())

    def test_strict_preflight(self):
        code, _, _ = self.cli('controlled-preflight')
        self.assertEqual(code, 0)
        for change in ('unknown', 'nested', 'count_bool', 'schema', 'binding', 'runtime', 'pin'):
            configured = copy.deepcopy(self.config)
            if change == 'unknown': configured['extra'] = True
            elif change == 'nested': configured['profiles']['extra'] = 'candidate'
            elif change == 'count_bool': configured['caps']['episode_request_units'] = True
            elif change == 'schema': configured['schema'] = 'unregistered/1'
            elif change == 'binding': configured['binding']['model'] = 'candidate'
            elif change == 'runtime': configured['pins']['interpreter']['path'] = str(self.parent / 'candidate')
            else: configured['pins']['fingerprint'] = 'f' * 64
            with self.subTest(change=change):
                code, packet, out = self.cli('controlled-preflight', config=configured)
                self.assertEqual((code, packet['outcome']), (2, 'malformed'))
                self.assertFalse(out.exists()); self.assertEqual(self.journal(), [])
        with self.assertRaises(route.Refusal): route.strict_json(b'{"a":1,"a":2}')
        with self.assertRaises(route.Refusal): route.strict_json(b'{"a":NaN}')
        existing = self.task / 'evidence/existing'; existing.mkdir()
        code, _, _ = self.cli('controlled-preflight', out=existing)
        self.assertEqual(code, 2); self.assertEqual(list(existing.iterdir()), [])
        dangling = self.task / 'evidence/dangling'; dangling.symlink_to(self.parent / 'absent')
        code, _, _ = self.cli('controlled-preflight', out=dangling)
        self.assertEqual(code, 2); self.assertTrue(dangling.is_symlink())

    def test_explicit_history(self):
        work = self.task / 'runs/history/work'
        first = tool('Write', dict(file_path=str(work / 'persist.txt'), content='persistent α'), 'write')
        second = tool('Read', dict(file_path=str(work / 'persist.txt'), byte_offset=0, max_bytes=100), 'read')
        sessions = [dict(session_id='first', prompt='First prompt', responses=[script([first], chunk=1), script([text_item('First done')])]),
                    dict(session_id='second', prompt='Fresh prompt', responses=[script([second], chunk=7), script([text_item('Second done')])])]
        base, _ = self.completed(self.episode(eid='history', sessions=sessions))
        pids = []
        for index, session in enumerate(sessions, 1):
            folder = base / ('sessions/%02d' % index)
            process = json.loads((folder / 'controller.process.json').read_bytes()); pids.append(process['pid'])
            self.assertEqual(process['exit_code'], 0)
            request1 = json.loads((folder / ('a_%s_1/request.json' % session['session_id'])).read_bytes())
            request2 = json.loads((folder / ('a_%s_2/request.json' % session['session_id'])).read_bytes())
            returned = json.loads((base / ('workers/w_%s_1_0/result.raw.jsonl' % session['session_id'])).read_bytes())
            output = base64.b64decode(returned['returned_output_utf8_b64']).decode()
            self.assertEqual(request1['input'], [dict(role='user', content=session['prompt'])])
            self.assertEqual(request2['input'], request1['input'] + session['responses'][0]['items'] +
                [dict(type='function_call_output', call_id=session['responses'][0]['items'][0]['call_id'], output=output)])
            self.assertEqual(set(request1), {'model', 'reasoning', 'instructions', 'input', 'tools', 'store', 'stream', 'parallel_tool_calls'})
            self.assertFalse(request1['store']); self.assertFalse(request1['parallel_tool_calls'])
        self.assertEqual(len(set(pids)), 2)
        self.assertEqual((work / 'persist.txt').read_text(), 'persistent α')
        returned = json.loads((base / 'workers/w_second_1_0/result.raw.jsonl').read_bytes())
        self.assertEqual(base64.b64decode(returned['returned_output_utf8_b64']), 'persistent α'.encode())
        oversized = self.episode(eid='overflow'); oversized['sessions'][0]['prompt'] = 'x' * route.IO['max_serialized_request_bytes']
        code, packet, out = self.cli('controlled-run', episode=oversized)
        self.assertEqual((code, packet['outcome']), (1, 'instrument_incomplete')); self.no_dispatch(out)

    def test_atomic_admission(self):
        self.carry('probe', '3.9')
        config_path = self.task / 'race-config.json'; config_path.write_bytes(route.encoded(self.config))
        children = []
        for index in range(2):
            ep = self.episode(eid='contender%d' % index, stage='probe')
            ep_path = self.task / ('race-episode%d.json' % index); ep_path.write_bytes(route.encoded(ep))
            out = self.task / 'evidence' / ('race%d' % index)
            argv = [sys.executable, '-B', str(HARNESS / 'gpt_route.py'), 'controlled-run', '--config', str(config_path), '--episode', str(ep_path), '--out', str(out)]
            children.append((subprocess.Popen(argv, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE), out))
        returns = []
        for child, out in children:
            stdout, stderr = child.communicate(timeout=45); self.assertEqual(stderr, b'')
            returns.append(child.returncode)
            (out / 'native-cli.stdout').write_bytes(stdout); (out / 'native-cli.stderr').write_bytes(stderr)
        self.assertEqual(sorted(returns), [0, 1])
        events = self.journal(); reservations = [e for e in events if e['kind'] == 'reserve']
        self.assertEqual(len(reservations), 1)
        self.assertEqual(Decimal('3.9') + sum(Decimal(e['reserved_usd']) for e in reservations), Decimal('4'))
        acks = list((self.task / 'evidence').rglob('stub.stderr.jsonl')); self.assertEqual(len(acks), 1)
        ack = json.loads(acks[0].read_bytes()); admission = reservations[0]
        self.assertEqual((ack['attempt_id'], ack['body_sha256']), (admission['attempt_id'], admission['body_sha256']))
        matching = [e for e in events if e['attempt_id'] == ack['attempt_id']]
        self.assertEqual([e['kind'] for e in matching], ['reserve', 'consume', 'dispatch_ack'])
        self.assertTrue(all(Decimal(e['reserved_usd']) > 0 and e['actual_usd'] == 'n/a' for e in matching))

    def test_retry_uncertainty(self):
        ep = self.episode(eid='uncertain', responses=[script([text_item()], fault='drop_ack')])
        code, packet, out = self.cli('controlled-run', episode=ep)
        self.assertEqual((code, packet['outcome']), (1, 'instrument_incomplete'))
        events = self.journal(); self.assertEqual([e['kind'] for e in events], ['episode_open', 'reserve', 'consume', 'uncertain'])
        self.assertEqual(sum(Decimal(e['reserved_usd']) for e in events if e['kind'] == 'reserve'), Decimal('0.1'))
        original = (self.task / 'state/journal.jsonl').read_bytes()
        code, _, denied = self.cli('controlled-run', episode=ep)
        self.assertEqual(code, 1); self.no_dispatch(denied)
        self.assertEqual((self.task / 'state/journal.jsonl').read_bytes(), original)
        self.completed(self.episode(eid='fresh_attempt'))
        _, checkpoint = route.validate_config(self.config)
        ledger = route.Ledger(self.config, checkpoint, self.episode(eid='permit_test'))
        try:
            permit, bound = ledger.reserve('s1', 'a1', b'request')
            self.assertFalse(bound['provider_applicable']); self.assertGreater(Decimal(bound['maximum_usd']), 0)
            before = ledger.path.read_bytes()
            for altered in (dict(permit, session_id='wrong'), dict(permit, fingerprint='f' * 64), dict(permit, episode_origin_event_id='wrong')):
                with self.assertRaises(route.Refusal): ledger.consume(altered, b'request')
                self.assertEqual(ledger.path.read_bytes(), before)
            ledger.consume(permit, b'request'); before = ledger.path.read_bytes()
            with self.assertRaises(route.Refusal): ledger.consume(permit, b'request')
            with self.assertRaises(route.Refusal): ledger.reserve('s1', 'a1', b'request')
            self.assertEqual(ledger.path.read_bytes(), before)
        finally: ledger.close()

    def test_journal_integrity(self):
        self.completed(self.episode())
        path = self.task / 'state/journal.jsonl'; good = path.read_bytes()
        events = self.journal()
        for raw in (good[:-1], good.replace(b'"prev_sha256":"', b'"prev_sha256":"f', 1)):
            path.write_bytes(raw); before = path.stat()
            code, packet, out = self.cli('controlled-preflight')
            self.assertEqual((code, packet['outcome']), (2, 'malformed'))
            self.assertFalse(out.exists()); self.assertEqual(path.read_bytes(), raw)
            self.assertEqual(path.stat().st_mtime_ns, before.st_mtime_ns)
        path.write_bytes(good)
        code, _, _ = self.cli('controlled-preflight'); self.assertEqual(code, 0)
        replay = object.__new__(route.Ledger); _, replay.checkpoint = route.validate_config(self.config)
        replay.config = self.config; replay.authority = replay.checkpoint['authority_binding']; replay.events = events
        settlement = dict(events[-1], sequence=len(events) + 1, prev_sha256=route.digest(route.encoded(events[-1]) + b'\n'),
            event_id='settled', kind='settle', actual_usd='0.04')
        replay.events = events + [settlement]; replay.verify()
        self.assertEqual(sum(c[3] for c in replay.usage()), Decimal('0.04'))
        settlement['actual_usd'] = '0.11'
        with self.assertRaises(route.Refusal): replay.verify()
        self.assertEqual(path.read_bytes(), good)

    def test_file_tools(self):
        outside = self.parent / 'outside.txt'; outside.write_text('sentinel α')
        for name, given in (('Read', dict(file_path=str(outside), byte_offset=0, max_bytes=100)),
                            ('Write', dict(file_path=str(outside), content='changed')),
                            ('Bash', dict(command='cat ' + str(outside), cwd=str(outside.parent)))):
            with self.subTest(name=name):
                result, _ = self.local_worker(name, given)
                self.assertEqual(result['kind'], 'refused')
                self.assertIsNone(result['facts']['errno']); self.assertFalse(result['facts']['effect_started'])
                self.assertEqual(outside.read_text(), 'sentinel α')
        work = self.task / 'runs/tools/work'
        actions = [tool('Read', dict(file_path=str(work / 'own.txt'), byte_offset=0, max_bytes=100), 'read'),
                   tool('Write', dict(file_path=str(work / 'written.txt'), content='written β'), 'write'),
                   tool('Bash', dict(command=route.command('stdout_stderr'), cwd=str(work)), 'bash')]
        base, _ = self.completed(self.episode(eid='tools', files={'own.txt': 'own α'}, responses=[script(actions), script([text_item()])]))
        facts = json.loads((base / 'mapping.json').read_bytes())['facts']
        self.assertEqual([f['exact_result']['kind'] for f in facts[:3]], ['Read', 'Write', 'Bash'])
        self.assertEqual((work / 'written.txt').read_text(), 'written β')
        # Each file pathway independently refuses traversal, symbolic and hard links.
        import controlled_worker as worker
        fd = os.open(work, os.O_RDONLY | os.O_DIRECTORY)
        try:
            (work / 'symbolic').symlink_to(outside); os.link(outside, work / 'hard')
            for write in (False, True):
                for path in (work / '../escape', work / 'symbolic', work / 'hard'):
                    with self.subTest(write=write, path=path.name):
                        with self.assertRaises((route.Refusal, OSError)): worker.open_file(str(path), {'work': fd}, write=write)
            self.assertEqual(outside.read_text(), 'sentinel α')
        finally: os.close(fd)

        # A real worker creates a parent before an overlong final name fails.
        failed_work = self.task / 'runs/failed_write/work'
        target = failed_work / 'created-parent' / ('n' * (os.pathconf(work, 'PC_NAME_MAX') + 1))
        failed_base, _ = self.completed(self.episode(eid='failed_write', responses=[
            script([tool('Write', dict(file_path=str(target), content='new data'))]),
            script([text_item()])]))
        failed = json.loads((failed_base / 'mapping.json').read_bytes())['facts'][0]['exact_result']
        self.assertEqual(failed['kind'], 'refused')
        self.assertEqual(failed['facts']['errno'], errno.ENAMETOOLONG)
        self.assertIs(failed['facts']['effect_started'], True)
        self.assertEqual(list((failed_work / 'created-parent').iterdir()), [])

        # Inject late failures into the public main with real own-file operations.
        # Root authority is supplied directly here; this is not a kernel-boundary test.
        envelope = json.loads((base / 'workers/w_s1_1_1/invocation.json').read_bytes())
        written = work / 'written.txt'
        proof = self.task / 'late-write-observations'; proof.mkdir()
        fd = os.open(work, os.O_RDONLY | os.O_DIRECTORY)
        original_require = route.require
        def fail_ack(condition, code, detail=''):
            if code == 'write_ack': raise route.Refusal(code)
            return original_require(condition, code, detail)
        try:
            for phase in ('fsync', 'ack'):
                with self.subTest(late_failure=phase):
                    written.write_bytes(b'previous contents')
                    incoming, stdout, stderr = io.BytesIO(route.encoded(envelope)), io.BytesIO(), io.BytesIO()
                    fault = (mock.patch.object(worker.os, 'fsync', side_effect=OSError(errno.EIO, 'synthetic fsync fault'))
                             if phase == 'fsync' else mock.patch.object(route, 'require', side_effect=fail_ack))
                    with mock.patch.object(worker, 'roots', return_value={'work': fd}), \
                         mock.patch.object(sys, 'stdin', SimpleNamespace(buffer=incoming)), \
                         mock.patch.object(sys, 'stdout', SimpleNamespace(buffer=stdout)), \
                         mock.patch.object(sys, 'stderr', SimpleNamespace(buffer=stderr)), fault:
                        exit_code = worker.main()
                    self.assertEqual(exit_code, 0)
                    observed = json.loads(stdout.getvalue())
                    route.validate_result(observed, envelope['invocation'])
                    self.assertEqual(observed['kind'], 'refused')
                    self.assertIs(observed['facts']['effect_started'], True)
                    self.assertEqual(observed['facts']['errno'], errno.EIO if phase == 'fsync' else None)
                    self.assertEqual(observed['facts']['mechanism'], 'observed_os_error' if phase == 'fsync' else 'fixture_policy')
                    self.assertEqual(written.read_bytes(), 'written β'.encode())
                    (proof / (phase + '-input.json')).write_bytes(route.encoded(envelope))
                    (proof / (phase + '-stdout.jsonl')).write_bytes(stdout.getvalue())
                    (proof / (phase + '-stderr.jsonl')).write_bytes(stderr.getvalue())
                    (proof / (phase + '-consumer.json')).write_bytes(route.encoded(dict(
                        method='direct controlled_worker.main', returned_exit=exit_code,
                        authority='test-supplied own directory descriptor', fault=phase,
                        before_utf8='previous contents', after_utf8=written.read_text())))
        finally: os.close(fd)

    def test_complete_command(self):
        work = self.task / 'runs/command/work'
        actions = [tool('Bash', dict(command=route.command(mode), cwd=str(work)), mode) for mode in ('stdout_stderr', 'nonzero')]
        base, _ = self.completed(self.episode(eid='command', responses=[script(actions), script([text_item()])]))
        calls = public.tool_calls((base / 'transcript.jsonl').read_text())
        self.assertEqual([(c['text'], c['is_error']) for c in calls], [('out α\nerr β\n', False), ('observed\nfailed command\n', True)])
        for index, (stdout, stderr, exit_code) in enumerate(((b'out \xce\xb1\n', b'err \xce\xb2\n', 0), (b'observed\n', b'failed command\n', 7))):
            prefix = base / ('workers/w_s1_1_%d' % index)
            result = json.loads((prefix / 'result.raw.jsonl').read_bytes())['facts']
            self.assertEqual((prefix / 'stdout.bin').read_bytes(), stdout); self.assertEqual((prefix / 'stderr.bin').read_bytes(), stderr)
            self.assertEqual(result['exit_code'], exit_code)
            self.assertEqual(result['argv'], ['/bin/sh', '-c', actions[index]['arguments'] and json.loads(actions[index]['arguments'])['command']])
            self.assertEqual(result['cwd'], str(work)); self.assertFalse(result['timeout']); self.assertIsNone(result['signal'])
        observed = route.captured([route.PYTHON, '-B', str(route.FIXTURE / 'command_fixture.py'), 'delay'], b'', self.task,
            route.fresh_environment(self.task, self.task), timeout=.001)
        self.assertTrue(observed['timeout']); self.assertIsNotNone(observed['signal'])
        observed = route.captured([route.PYTHON, '-B', str(route.FIXTURE / 'command_fixture.py'), 'stdout_stderr'], b'', self.task,
            route.fresh_environment(self.task, self.task), maximum=2)
        self.assertTrue(observed['overflow']); self.assertFalse(observed['capture_complete'])
        (self.task / 'capture-incomplete.json').write_bytes(route.encoded({k:v for k,v in observed.items() if k!='streams'}))

    def test_source_spans(self):
        work = self.task / 'runs/spans/work'
        argument = '{ "max_bytes" : 100, "file_path" : ' + json.dumps(str(work / 'unicode.txt')) + ', "byte_offset": 0 }'
        item = tool('Read', argument, 'exact')
        base, bundle = self.completed(self.episode(eid='spans', files={'unicode.txt': 'α text'}, responses=[script([item], chunk=1), script([text_item('β final')], chunk=3)]))
        mapping = json.loads((base / 'mapping.json').read_bytes()); fact = mapping['facts'][0]
        self.assertEqual(base64.b64decode(fact['exact_argument_utf8_b64']), argument.encode())
        source = fact['sources'][1]; raw = (base / source['artifact']).read_bytes()
        self.assertEqual(route.digest(raw), source['sha256'])
        self.assertEqual(json.loads(raw[source['byte_start']:source['byte_end']]), argument)
        self.assertEqual(fact['exact_input'], json.loads(argument))
        raw_components = b''.join((base / c['artifact_ref']['artifact']).read_bytes() for c in bundle['raw_transcript_components'])
        self.assertEqual(bundle['raw_transcript_sha256'], hashlib.sha256(raw_components).hexdigest())
        self.assertNotEqual(bundle['raw_transcript_sha256'], bundle['canonical_sha256'])
        code, packet, _ = self.cli('controlled-verify', bundle=base / 'bundle.json')
        self.assertEqual((code, packet['outcome']), (0, 'offline_completed'))

    def test_archive_bytes(self):
        work = self.task / 'runs/archive/work'; archive = 'αβγ\n' + 'x' * 200
        actions = [tool('Read', dict(file_path=str(work / 'history-archive.md'), byte_offset=2, max_bytes=4), 'prefix'),
                   tool('Bash', dict(command=route.command('read_archive_prefix'), cwd=str(work)), 'command')]
        base, _ = self.completed(self.episode(eid='archive', files={'history-archive.md': archive}, responses=[script(actions), script([text_item()])]))
        raw = (base / 'transcript.jsonl').read_text()
        self.assertEqual(public.archive_bytes_read(raw), len('βγ'.encode()) + len(archive.encode()[:128]))
        self.assertEqual(public.tool_calls(raw)[0]['text'], 'βγ')
        broken_work = self.task / 'runs/split/work'
        split = tool('Read', dict(file_path=str(broken_work / 'history-archive.md'), byte_offset=1, max_bytes=1))
        code, packet, out = self.cli('controlled-run', episode=self.episode(eid='split', files={'history-archive.md': 'α'}, responses=[script([split]), script([text_item()])]))
        self.assertEqual((code, packet['outcome']), (1, 'instrument_incomplete'))
        self.assertFalse((out / 'split/bundle.json').exists())
        self.assertTrue((out / 'split/workers/w_s1_1_0/result.raw.jsonl').is_file())

    def test_pairing_duplicates(self):
        for fault in ('missing_completion', 'conflict_item', 'duplicate_event', 'nonzero'):
            with self.subTest(fault=fault):
                code, packet, out = self.cli('controlled-run', episode=self.episode(eid=fault, responses=[script([text_item()], fault=fault)]))
                self.assertEqual((code, packet['outcome']), (1, 'instrument_incomplete'))
                self.assertFalse((out / fault / 'bundle.json').exists())
        # A compatible update is deduplicated from independent raw event bytes.
        base, _ = self.completed(self.episode(eid='pair'))
        path = base / 'sessions/01/a_s1_1/response.raw.jsonl'
        lines = path.read_bytes().splitlines(); repeated = json.loads(lines[1]); repeated['event_id'] = 'compatible_update'
        raw = b'\n'.join(lines[:2] + [route.encoded(repeated)] + lines[2:]) + b'\n'
        store_root = self.task / 'evidence/compatible'; store_root.mkdir(); store = route.Store(store_root)
        ref = store.put('response.raw.jsonl', raw)
        _, items, _, _ = route.parse_response(raw, ref, store, 's1', 'a_s1_1')
        self.assertEqual(items, [text_item()])
        unknown = copy.deepcopy(self.episode(eid='unknown')); unknown['sessions'][0]['responses'][0]['items'][0]['type']='unknown'
        code, _, out = self.cli('controlled-run', episode=unknown); self.assertEqual(code, 2); self.no_dispatch(out)

    def test_final_text_claims(self):
        final = 'I read the archive, wrote a report and reviewed everything. α'
        base, bundle = self.completed(self.episode(eid='claims', responses=[script([text_item(final)])]))
        read = signal_reader.participant_output(base.parent, 'claims')
        self.assertEqual(read, (final, []))
        self.assertEqual(public.tool_calls((base / 'transcript.jsonl').read_text()), [])
        self.assertEqual(bundle['counts']['tool_invocation_count'], 0)

    def test_fixture_supervisor(self):
        work = self.task / 'runs/owned/work'
        item = tool('Bash', dict(command=route.command('owned_helper'), cwd=str(work)))
        base, bundle = self.completed(self.episode(eid='owned', responses=[script([item]), script([text_item('Done')])]))
        prefix = base / 'workers/w_s1_1_0'
        owned = json.loads((prefix / 'native.stderr.jsonl').read_bytes())
        self.assertEqual(len(owned['handles']), 2); self.assertEqual(owned['remaining_handle_ids'], [])
        self.assertTrue(all(h['exit_code'] == 0 and h['exited_ns'] >= h['started_ns'] for h in owned['handles']))
        events = json.loads((prefix / 'supervisor/events.json').read_bytes())
        self.assertEqual([e['kind'] for e in events], ['spawn_ack','main_exit','tracked_fixture_handles_empty','stdout_eof','stderr_eof','snapshot_observed','offline_finalized'])
        snapshot = events[5]['facts']['snapshot']
        self.assertGreater(snapshot['observed_monotonic_ns'], max(h['exited_ns'] for h in owned['handles']))
        self.assertTrue({'delayed.txt', 'owned-helper.txt'} <= {e['relative_path'] for e in snapshot['entries']})
        for ref in bundle['supervisor_receipts']:
            receipt = json.loads((base / ref['artifact_ref']['artifact']).read_bytes())
            self.assertIs(receipt['kernel_boundary_accepted'], False); self.assertIs(receipt['complete'], True)
            refs = {item['artifact']: item for item in bundle['artifacts']}
            self.assertEqual(route.verify_supervisor(base, ref, refs), receipt)
            variants = [('int-zero', 0, 'invalid_type'), ('float-zero', 0.0, 'invalid_type'),
                        ('null', None, 'invalid_type'), ('string', 'false', 'invalid_type'),
                        ('array', [], 'invalid_type'), ('object', {}, 'invalid_type'),
                        ('true', True, 'invalid_constant')]
            for label, value, expected in variants:
                with self.subTest(boolean=label):
                    variant_base = self.task / 'boolean-fixtures' / ref['worker_handle'] / label
                    shutil.copytree(base, variant_base)
                    mutated = copy.deepcopy(receipt); mutated['kernel_boundary_accepted'] = value
                    raw = route.encoded(mutated)
                    target = variant_base / ref['artifact_ref']['artifact']; target.write_bytes(raw)
                    supplied = copy.deepcopy(ref)
                    supplied['artifact_ref'].update(sha256=route.digest(raw), byte_length=len(raw))
                    variant_refs = copy.deepcopy(refs)
                    variant_refs[supplied['artifact_ref']['artifact']] = supplied['artifact_ref']
                    with self.assertRaises(route.Refusal) as rejected:
                        route.verify_supervisor(variant_base, supplied, variant_refs)
                    self.assertEqual(rejected.exception.code, expected)
                    (variant_base.parent / (label + '-consumer.json')).write_bytes(route.encoded(dict(
                        method='controlled_route.verify_supervisor', base=str(variant_base),
                        reference=supplied, refs=variant_refs, observed_refusal=rejected.exception.code)))
        observation = dict(capture_complete=False, overflow=False, timeout=False, exit_code=0, signal=None)
        with self.assertRaises(route.Refusal): route.finalize('x','s1','w',self.config['pins']['fingerprint'],observation,[],work,route.Store(self.task),'unused',{},None)

    def test_network_inactive(self):
        ep = self.episode(); ep['network'] = dict(topology='task_owned_loopback', listener_receipt=True)
        code, packet, out = self.cli('controlled-run', episode=ep)
        self.assertEqual((code, packet['outcome'], packet['reason']), (1, 'unsupported', 'network_unsupported'))
        self.assertFalse(out.exists()); self.assertEqual(self.journal(), [])
        self.completed(self.episode())

    def test_public_consumer_argv(self):
        code, packet, evidence = self.cli('controlled-run', episode=self.episode(eid='protocol_error', responses=[script([text_item()], fault='missing_completion')]))
        self.assertEqual((code, packet['outcome']), (1, 'instrument_incomplete'))
        raw_response = (evidence / 'protocol_error/sessions/01/a_s1_1/response.raw.jsonl').read_bytes()
        self.assertFalse((evidence / 'protocol_error/bundle.json').exists())
        cohort = self.task / 'synthetic-cohort'; cohort.mkdir()
        executor = dict(harness='offline-public-fixture', model='n/a', effort='n/a')
        variant = dict(scenario_id='synthetic-shape', variant_id='public', split='development', **{'class':'procedure'}, fixture_sha256='a'*64)
        order = [dict(episode_id='unobserved', scenario_id='synthetic-shape', variant_id='public', arm='control', seed=1)]
        manifest = dict(schema='tackle-cohort/1', cohort_id='public-shape', hypothesis='Unobserved record shape only',
            primary_metric='shape', decision_rule='No behavioral verdict', n_min=1, seeds=[1], variants=[variant],
            arms=['control'], comparisons=[], executor=executor, judge=dict(model_family='n/a', blinded=False),
            artifacts=dict(baseline_sha256='b'*64,candidate_sha256='c'*64), oracle_sha256='d'*64,
            order=order, created_at='2026-01-01T00:00:00Z')
        manifest['seal_sha256']=hashlib.sha256(json.dumps(manifest, sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
        record=dict(schema='tackle-episode/1', cohort_id='public-shape', prev_sha256='0'*64, split='development',
            order_index=0, artifact_sha256=None, executor=executor, roles=[], judge=dict(kind='mechanical',model_family='n/a',blinded=False),
            rule_exposure=False,outcome='unobserved',invalid_reason=None,
            scores={k:None for k in ('correct_action','evidence','verification_honesty','report_quality')},
            cost={k:'n/a' for k in ('tokens_in','tokens_out','wall_seconds','tool_calls','files_written')},
            transcript_sha256=None,started_at='n/a',finished_at='n/a',**order[0])
        (cohort/'manifest.json').write_bytes(route.encoded(manifest)); (cohort/'episodes.jsonl').write_bytes(route.encoded(record)+b'\n')
        argv=[sys.executable,'-B',str(ROOT/'eval/protocol-v2/check.py'),str(cohort)]
        result=subprocess.run(argv,cwd=ROOT,capture_output=True,timeout=30)
        (cohort/'native.stdout').write_bytes(result.stdout);(cohort/'native.stderr').write_bytes(result.stderr)
        (cohort/'native.json').write_bytes(route.encoded(dict(argv=argv,cwd=str(ROOT),native_exit=result.returncode,timeout=False,signal=None)))
        self.assertEqual(result.returncode,0,result.stderr);self.assertEqual(result.stderr,b'')
        record['outcome']='error'; record['transcript_sha256']=hashlib.sha256(raw_response).hexdigest()
        self.assertEqual(record['transcript_sha256'], route.digest(raw_response))
        (cohort/'episodes.jsonl').write_bytes(route.encoded(record)+b'\n')
        observed=subprocess.run(argv,cwd=ROOT,capture_output=True,timeout=30)
        (cohort/'error.stdout').write_bytes(observed.stdout);(cohort/'error.stderr').write_bytes(observed.stderr)
        (cohort/'error-native.json').write_bytes(route.encoded(dict(argv=argv,cwd=str(ROOT),native_exit=observed.returncode,timeout=False,signal=None)))
        self.assertEqual(observed.returncode,0,observed.stderr)
        record['transcript_sha256']=None; (cohort/'episodes.jsonl').write_bytes(route.encoded(record)+b'\n')
        bad=subprocess.run(argv,cwd=ROOT,capture_output=True,timeout=30)
        (cohort/'invalid.stdout').write_bytes(bad.stdout);(cohort/'invalid.stderr').write_bytes(bad.stderr)
        self.assertEqual(bad.returncode,1)

    def test_bundle_and_capabilities(self):
        base, _ = self.completed(self.episode())
        original = (base / 'transcript.jsonl').read_bytes()
        code, _, _ = self.cli('controlled-verify', bundle=base/'bundle.json');self.assertEqual(code,0)
        for path in ('transcript.jsonl','mapping.json','checkpoint.json','sessions/01/a_s1_1/response.raw.jsonl','sessions/01/controller/supervisor/receipt.json'):
            target=base/path;good=target.read_bytes();target.write_bytes(good+b' ')
            code,packet,out=self.cli('controlled-verify',bundle=base/'bundle.json')
            self.assertEqual((code,packet['outcome']),(2,'malformed'));self.assertFalse(out.exists())
            self.assertEqual(target.read_bytes(),good+b' ');target.write_bytes(good)
        self.assertEqual((base/'transcript.jsonl').read_bytes(),original)
        live=dict(mode='live',pins=dict(fingerprint='candidate'),capabilities={'kernel_boundary':True,'provider_billable_bound':True},roots={'task_root':'do-not-open'})
        code,packet,out=self.cli('controlled-preflight',config=live)
        self.assertEqual((code,packet['outcome']),(1,'unsupported'));self.assertFalse(out.exists())
        self.assertEqual(packet['actual_provider_telemetry'],dict(model='n/a',effort='n/a',tokens_in='n/a',tokens_out='n/a',cost_usd='n/a'))
        self.assertTrue(packet['missing_capabilities'])
        self.assertFalse(packet['live_ready']);self.assertFalse(packet['task_complete']);self.assertFalse(packet['private_consumer_accepted'])


class IsolatedToolAdapter(unittest.TestCase):
    """Real source helper/CLI simulation; no Docker, kernel or provider evidence."""
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix='isolated-tools-')
        self.parent=Path(self.temporary.name).resolve()
        self.root=self.parent/'component';self.root.mkdir()
        self.roots={'component_root':self.root}
        for role in ('work','tmp','runtime','evidence_parent','cli_home','cli_config'):
            self.roots[role]=self.root/role;self.roots[role].mkdir()
        policy=route.isolated_policy();runtime=self.roots['runtime']
        sources={'controlled_route.py':HARNESS/'controlled_route.py','controlled_worker.py':HARNESS/'controlled_worker.py',
            'streams.json':route.FIXTURE/'streams.json','isolated_adapter.json':route.FIXTURE/'isolated_adapter.json'}
        for name,path in sources.items():
            target=runtime/'harness'/('fixtures/controlled-route/'+name if name.endswith('.json') else name)
            target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(path.read_bytes())
        for name,text in policy['engine_files'].items():
            target=runtime/'engine-files'/name;target.parent.mkdir(exist_ok=True);target.write_bytes(text.encode())
        for parent,dirs,names in os.walk(runtime):
            for name in names:(Path(parent)/name).chmod(0o444)
            Path(parent).chmod(0o555)
        spec=importlib.util.spec_from_file_location('isolated_fixture',route.FIXTURE/'isolated_engine_fixture.py')
        self.fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.fixture)
        image=self.fixture.encoded(self.fixture.image_record())+b'\n'
        self.config=dict(schema='tackle-isolated-component-config/1',mode='component-offline',adapter=policy['adapter'],
            docker_cli={k:v.removeprefix('const ') for k,v in policy['docker_cli'].items()},image_id=policy['image_id'],
            roots={k:str(v) for k,v in self.roots.items()},caps=copy.deepcopy(policy['caps']),
            policy_sha256=route.digest((route.FIXTURE/'isolated_adapter.json').read_bytes()),network='none',seccomp='docker-default',
            provider_requests=0,pins=dict(source_files={k:route.digest(v.read_bytes()) for k,v in sources.items()},
                runtime_tree_sha256=route.isolated_tree(runtime),image_config_sha256=route.digest(image),
                engine_files={k:route.digest(v.encode()) for k,v in policy['engine_files'].items()},fingerprint='0'*64))
        self.config['pins']['fingerprint']=route.isolated_fingerprint(self.config)
        self.serial=0

    def tearDown(self):
        for parent,dirs,names in os.walk(self.roots['runtime']):
            Path(parent).chmod(0o755)
            for name in names:(Path(parent)/name).chmod(0o644)
        self.temporary.cleanup()

    def invocation(self,name='Bash',arguments=None):
        value=arguments or dict(command='printf general-command',cwd='/work')
        raw=route.encoded(value)
        source=route.record('raw_source',artifact='arguments.json',sha256=route.digest(raw),byte_start=0,byte_end=len(raw),event_id='input',producer='stub')
        return dict(schema=route.VERSIONS['invocation'],episode_id='isolated',session_id='session',attempt_id='attempt',
            response_id='response',item_index=0,item_id='item',call_id='call',function_name=name,
            arguments_utf8_b64=base64.b64encode(raw).decode(),arguments_sha256=route.digest(raw),arguments_raw_span=source,
            parsed_input=value,worker_handle='worker',fingerprint=self.config['pins']['fingerprint'])

    def make_one_responses_state(self,stdout=b'own \xce\xb1\n',stderr=b'error \xce\xb2\n',exit_code=0,read=b'read control'):
        """Own public positive source-simulation data; no command interpretation."""
        self.serial+=1
        state=self.root/('one-responses-state-%d.json'%self.serial)
        state.write_bytes(route.encoded(dict(fault=None,stdout_b64=base64.b64encode(stdout).decode(),
            stderr_b64=base64.b64encode(stderr).decode(),exit_code=exit_code,
            read_b64=base64.b64encode(read).decode())))
        return state

    def run_case(self,invocation=None,fault=None,stdout=b'own \xce\xb1\n',stderr=b'error \xce\xb2\n',exit_code=0):
        self.serial+=1
        state=self.root/('simulation-%d.json'%self.serial)
        state.write_bytes(route.encoded(dict(fault=fault,stdout_b64=base64.b64encode(stdout).decode(),
            stderr_b64=base64.b64encode(stderr).decode(),exit_code=exit_code,read_b64=base64.b64encode(b'read control').decode())))
        output=self.roots['evidence_parent']/('run-%d'%self.serial)
        call=invocation or self.invocation()
        original_capture=route.isolated_watchdog_capture;frames=[]
        def observe(argv,payload,deadline,environment):
            frame=dict(argv=argv,payload=payload,deadline=deadline,environment=environment)
            frames.append(frame)
            frame['observed']=original_capture(argv,payload,deadline,environment)
            return frame['observed']
        try:
            with mock.patch.object(route,'isolated_watchdog_capture',side_effect=observe):
                observation=route.isolated_run(self.config,call,output,_simulation=dict(state_path=str(state)))
        except Exception as failure:
            retained=self.retain_case(output,state,call,frames)
            self.last_case_evidence,self.last_watchdog_frames=retained,frames
            print(json.dumps(dict(failure_code=getattr(failure,'code',type(failure).__name__),
                evidence=str(retained)),sort_keys=True),flush=True)
            raise
        self.observation_path(output).write_bytes(route.encoded(observation))
        retained=self.retain_case(output,state,call,frames)
        self.last_case_evidence,self.last_watchdog_frames=retained,frames
        if not (output/'receipt.json').exists():
            raise AssertionError('missing inner receipt; observation='+json.dumps(observation)+' evidence='+str(retained))
        receipt=json.loads((output/'receipt.json').read_bytes())
        print(json.dumps(dict(failure_codes=receipt['failure_codes'],evidence=str(retained)),sort_keys=True),flush=True)
        bundle=json.loads((output/'bundle.json').read_bytes())
        return bundle,receipt,output,json.loads(state.read_bytes())

    def file_claim(self,name,arguments,fsync_fault=False):
        import controlled_worker as worker
        descriptors={role:os.open(self.roots[role],os.O_RDONLY|os.O_DIRECTORY) for role in ('work','tmp','runtime')}
        request=route.isolated_record('FileRequest',request_id='0abcdef',function_name=name,arguments=arguments)
        incoming,stdout,stderr=io.BytesIO(route.encoded(request)),io.BytesIO(),io.BytesIO()
        fault=mock.patch.object(worker.os,'fsync',side_effect=OSError(errno.EIO,'public fault')) if fsync_fault else mock.patch.dict({}, {})
        with mock.patch.dict(os.environ,dict(os.environ),clear=True),mock.patch.object(worker,'isolated_file_roots',return_value=descriptors), \
                mock.patch.object(sys,'stdin',SimpleNamespace(buffer=incoming)),mock.patch.object(sys,'stdout',SimpleNamespace(buffer=stdout)), \
                mock.patch.object(sys,'stderr',SimpleNamespace(buffer=stderr)),fault:
            code=worker.isolated_file_main()
        self.serial+=1;output=self.roots['evidence_parent']/('file-helper-'+str(self.serial));output.mkdir()
        for name,data in [('input.bin',incoming.getvalue()),('stdout.bin',stdout.getvalue()),('stderr.bin',stderr.getvalue())]:
            (output/name).write_bytes(data)
        (output/'kind.json').write_bytes(route.encoded(dict(kind='inprocess_public_immutable_file_helper',exit_code=code,source_simulation_only=True)))
        self.retain_case(output)
        return code,json.loads(stdout.getvalue()),stderr.getvalue()

    def mutate_receipt(self,bundle,output,change):
        original=copy.deepcopy(bundle)
        receipt=json.loads((output/'receipt.json').read_bytes());change(receipt)
        raw=route.encoded(receipt);(output/'receipt.json').write_bytes(raw)
        ref=dict(original['receipt_ref'],sha256=route.digest(raw),byte_length=len(raw))
        original['receipt_ref']=ref
        original['artifacts']=[ref if x['artifact']==ref['artifact'] else x for x in original['artifacts']]
        (output/'bundle.json').write_bytes(route.encoded(original))
        self.refresh_observation(output);self.retain_case(output)

    def observation_path(self,output):
        return self.roots['evidence_parent']/(output.name+'.observation.json')

    def retain_case(self,output,state=None,invocation=None,watchdog_frames=None):
        """Capture public own evidence before assertions and own temporary teardown."""
        import stat
        value=os.environ.get('TACKLE_ISOLATED_TEST_EVIDENCE_ROOT')
        root=Path(value) if value else self.root/'retained'
        if value and not root.is_absolute():raise AssertionError('evidence root must be absolute')
        for component in (root,*root.parents):
            if component.is_symlink():raise AssertionError('linked evidence root')
        root.mkdir(parents=True,exist_ok=True)
        existing=[]
        for parent,dirs,names in os.walk(root,followlinks=False):
            if any((Path(parent)/name).is_symlink() for name in dirs):raise AssertionError('linked evidence directory')
            existing.extend(Path(parent)/name for name in names)
        total=0
        for path in existing:
            info=path.lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1:raise AssertionError('unsafe evidence file')
            total+=info.st_size
        count=len(existing)
        destination=root/(self._testMethodName+'-'+os.urandom(8).hex());destination.mkdir()
        inputs=[]
        if state is not None:
            if state.parent!=self.root:raise AssertionError('foreign simulation state')
            inputs.append((state,'simulation-state.json',None))
        if self.observation_path(output).exists():inputs.append((self.observation_path(output),'run-observation.json',None))
        for parent,dirs,names in os.walk(output,followlinks=False):
            if any((Path(parent)/name).is_symlink() for name in dirs):raise AssertionError('linked source evidence directory')
            inputs.extend((Path(parent)/name,'component/'+(Path(parent)/name).relative_to(output).as_posix(),None) for name in names)
        config_bytes=route.encoded(self.config)
        inputs.append((None,'config.json',config_bytes))
        if invocation is not None:inputs.append((None,'invocation.json',route.encoded(invocation)))
        if watchdog_frames is not None:
            if len(watchdog_frames)>1:raise AssertionError('multiple watchdog captures')
            metadata=dict(record_kind='original_watchdog_capture',source_simulation_only=True,
                capture_calls=len(watchdog_frames),capture_returned=False)
            if watchdog_frames:
                frame=watchdog_frames[0];wire=frame['payload']
                if type(wire) is not bytes or len(wire)>4194304:raise AssertionError('watchdog wire cap')
                inputs.append((None,'controller/input.bin',wire))
                metadata['launch']=dict(argv=frame['argv'],deadline=frame['deadline'],environment=frame['environment'])
                if 'observed' in frame:
                    observed=frame['observed'];metadata['capture_returned']=True
                    metadata['facts']={k:v for k,v in observed.items() if k!='streams'}
                    metadata['streams']={}
                    for channel in ('stdout','stderr'):
                        data=observed['streams'][channel]
                        if type(data) is not bytes or len(data)>4194304:raise AssertionError('watchdog stream cap')
                        inputs.append((None,'controller/'+channel+'.bin',data))
                        metadata['streams'][channel]=dict(bytes=len(data),sha256=route.digest(data))
            inputs.append((None,'controller/capture.json',route.encoded(metadata)))
        for source,relative,memory in inputs:
            if source is None:data=memory
            else:
                fd=os.open(source,os.O_RDONLY|os.O_NOFOLLOW)
                try:
                    info=os.fstat(fd)
                    if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1:raise AssertionError('unsafe source evidence')
                    if total+info.st_size>1073741824 or count+1>4096:raise AssertionError('evidence cap')
                    with os.fdopen(fd,'rb',closefd=False) as stream:data=stream.read(info.st_size+1)
                    if len(data)!=info.st_size:raise AssertionError('source evidence changed')
                finally:os.close(fd)
            if total+len(data)>1073741824 or count+1>4096:raise AssertionError('evidence cap')
            target=destination/relative;target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('xb') as stream:stream.write(data)
            target.chmod(0o444);total+=len(data);count+=1
        return destination

    def retain_capture(self,label,observed):
        self.serial+=1;output=self.roots['evidence_parent']/(label+'-'+str(self.serial));output.mkdir()
        for channel,data in observed['streams'].items():(output/(channel+'.bin')).write_bytes(data)
        (output/'observation.json').write_bytes(route.encoded(dict(
            source_unit_mechanism_only=True,**{k:v for k,v in observed.items() if k!='streams'})))
        return self.retain_case(output)

    def refresh_observation(self,output):
        # Synthetic counterfault bridge only: a forged observation is not host proof.
        path=self.observation_path(output);observed=json.loads(path.read_bytes())
        raw=(output/'bundle.json').read_bytes();bundle=json.loads(raw)
        reference=route.isolated_record('Artifact',artifact=output.name+'/bundle.json',sha256=route.digest(raw),byte_length=len(raw))
        observed['bundle_ref']=reference;observed['outcome']=bundle['outcome']
        observed['exit_code']=0 if bundle['outcome']=='component_completed' else 6
        summary=dict(request_id=observed['request_id'],fingerprint=observed['fingerprint'],bundle_ref=reference,
            outcome=bundle['outcome'],retained_bytes=sum(r['byte_length'] for r in bundle['artifacts'])+len(raw))
        observed['stdout_utf8_b64']=base64.b64encode(json.dumps(summary,sort_keys=True).encode()+b'\n').decode()
        path.write_bytes(route.encoded(observed))

    def repack(self,output,updates=None,change=None):
        bundle=json.loads((output/'bundle.json').read_bytes())
        receipt=json.loads((output/'receipt.json').read_bytes())
        replacements={}
        for name,data in (updates or {}).items():
            path=output/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
            replacements[name]=route.isolated_record('Artifact',artifact=name,sha256=route.digest(data),byte_length=len(data))
        def visit(value):
            if type(value) is dict:
                if value.get('schema')=='tackle-isolated-artifact/1' and value.get('artifact') in replacements:return replacements[value['artifact']]
                return {k:visit(v) for k,v in value.items()}
            if type(value) is list:return [visit(v) for v in value]
            return value
        receipt=visit(receipt)
        if change:change(receipt)
        raw=route.encoded(receipt);(output/'receipt.json').write_bytes(raw)
        replacements['receipt.json']=route.isolated_record('Artifact',artifact='receipt.json',sha256=route.digest(raw),byte_length=len(raw))
        bundle=visit(bundle)
        for name,ref in replacements.items():
            if not any(r['artifact']==name for r in bundle['artifacts']):bundle['artifacts'].append(ref)
        (output/'bundle.json').write_bytes(route.encoded(bundle));self.refresh_observation(output)
        self.retain_case(output)

    def check_closed_arguments(self):
        value=dict(file_path='/work/read.txt',byte_offset=True,max_bytes=3)
        call=self.invocation('Read',value);call['parsed_input']=dict(value,byte_offset=1)
        with self.assertRaises(route.Refusal):route.validate_isolated_invocation(call)
        good=self.invocation('Read',dict(value,byte_offset=1));route.validate_isolated_invocation(good)
        # Different lexical JSON whitespace/order remains valid and exactly retained.
        raw=json.dumps(good['parsed_input'],indent=2).encode();good['arguments_utf8_b64']=base64.b64encode(raw).decode()
        good['arguments_sha256']=route.digest(raw);good['arguments_raw_span'].update(sha256=route.digest(raw),byte_end=len(raw))
        route.validate_isolated_invocation(good)

    def check_bash_discriminant(self):
        _,receipt,out,_=self.run_case(exit_code=7)
        self.assertEqual(route.verify_isolated_bundle(self.config,out/'bundle.json',self.observation_path(out)),receipt)
        result=json.loads((out/'result.json').read_bytes())
        facts=dict(error_code='invented',errno=None,mechanism='path_policy',effect_started=False)
        result.update(kind='refused',facts=facts,returned_utf8_b64=base64.b64encode(route.encoded(facts)).decode(),returned_sha256=route.digest(route.encoded(facts)))
        self.repack(out,{'result.json':route.encoded(result)})
        with self.assertRaises(route.Refusal) as failure:route.verify_isolated_bundle(self.config,out/'bundle.json',self.observation_path(out))
        self.assertEqual(failure.exception.code,'isolated_result_kind')

    def check_incomplete_claims(self):
        _,receipt,out,_=self.run_case(fault='create_uncertain')
        self.assertEqual(route.verify_isolated_bundle(self.config,out/'bundle.json',self.observation_path(out)),receipt)
        self.repack(out,change=lambda value:value.update(native_commands=[],container_created=None,container_stopped=None))
        with self.assertRaises(route.Refusal) as failure:route.verify_isolated_bundle(self.config,out/'bundle.json',self.observation_path(out))
        self.assertEqual(failure.exception.code,'isolated_lifecycle_unproven')
        _,receipt,out,_=self.run_case(fault='create_uncertain')
        row=next(r for r in receipt['native_commands'] if r['phase']=='cleanup_remove');name=row['stdout_ref']['artifact'];data=b'corrupt cleanup\n'
        def change(value):
            next(r for r in value['native_commands'] if r['phase']=='cleanup_remove')['stdout_received_bytes']=len(data)
        self.repack(out,{name:data},change)
        with self.assertRaises(route.Refusal) as failure:route.verify_isolated_bundle(self.config,out/'bundle.json',self.observation_path(out))
        self.assertEqual(failure.exception.code,'isolated_cleanup_unproven')

    def check_stream_caps(self):
        for phase,channel,cap in [('start_attached','stdout',1048576),('start_attached','stderr',1048576),('image_inspect','stdout',4194304)]:
            with self.subTest(phase=phase,channel=channel):
                _,receipt,out,_=self.run_case()
                self.assertEqual(route.verify_isolated_bundle(self.config,out/'bundle.json',self.observation_path(out)),receipt)
                row=next(r for r in receipt['native_commands'] if r['phase']==phase)
                data=b'x'*(cap+1);name=row[channel+'_ref']['artifact']
                updates={name:data}
                if phase=='start_attached':
                    result=json.loads((out/'result.json').read_bytes())
                    result['facts'][channel+'_utf8']=data.decode()
                    result['facts'][channel+'_ref']=route.isolated_record('Artifact',artifact=name,sha256=route.digest(data),byte_length=len(data))
                    returned=route.encoded([dict(type='text',text=result['facts']['stdout_utf8']),dict(type='text',text=result['facts']['stderr_utf8'])])
                    result.update(returned_utf8_b64=base64.b64encode(returned).decode(),returned_sha256=route.digest(returned))
                    updates['result.json']=route.encoded(result)
                def change(value):
                    next(r for r in value['native_commands'] if r['phase']==phase)[channel+'_received_bytes']=len(data)
                self.repack(out,updates,change)
                with self.assertRaises(route.Refusal) as failure:route.verify_isolated_bundle(self.config,out/'bundle.json',self.observation_path(out))
                self.assertEqual(failure.exception.code,'isolated_stream_cap')
        # Aggregate boundary uses actual own public data, not a weakened configured cap.
        _,_,out,_=self.run_case();data=b'z'*(67108864+1)
        self.repack(out,{'snapshot/aggregate.bin':data})
        with self.assertRaises(route.Refusal) as failure:route.verify_isolated_bundle(self.config,out/'bundle.json',self.observation_path(out))
        self.assertEqual(failure.exception.code,'isolated_retention_cap')
        ref=route.isolated_record('Artifact',artifact='own.bin',sha256=route.digest(b'abc'),byte_length=3)
        self.assertEqual(route.isolated_retention_total([ref],b'{}',b'{}',7),7)
        with self.assertRaises(route.Refusal):route.isolated_retention_total([ref],b'{}',b'{}',6)

    def check_time_order(self):
        for fault in ('snapshot_before_eof','cross_command','phase_duration','run_duration'):
            with self.subTest(fault=fault):
                _,receipt,out,_=self.run_case()
                self.assertEqual(route.verify_isolated_bundle(self.config,out/'bundle.json',self.observation_path(out)),receipt)
                if fault=='run_duration':
                    path=self.observation_path(out);observed=json.loads(path.read_bytes())
                    observed['ended_ns']=observed['started_ns']+91000000000;path.write_bytes(route.encoded(observed));self.retain_case(out)
                else:
                    def change(value):
                        if fault=='snapshot_before_eof':value['snapshot']['observed_ns']=value['native_commands'][3]['ended_ns']-1
                        elif fault=='cross_command':
                            row=value['native_commands'][2];row['started_ns']=value['native_commands'][1]['started_ns']
                            row['phase_deadline_ns']=min(row['phase_deadline_ns'],row['started_ns']+8000000000)
                        else:value['native_commands'][3]['ended_ns']=value['native_commands'][3]['started_ns']+31000000000
                    self.repack(out,change=change)
                with self.assertRaises(route.Refusal) as failure:route.verify_isolated_bundle(self.config,out/'bundle.json',self.observation_path(out))
                self.assertEqual(failure.exception.code,dict(snapshot_before_eof='isolated_snapshot_order',
                    cross_command='isolated_chronology',phase_duration='isolated_phase_deadline',run_duration='isolated_controller_incomplete')[fault])
        _,_,out,_=self.run_case()
        with self.assertRaises(route.Refusal):route.verify_isolated_bundle(self.config,out/'bundle.json',self.roots['evidence_parent']/'absent-observation.json')

    def check_finalization_mechanism(self):
        # Small absolute budgets exercise the actual watchdog capture mechanism only.
        # They are not canonical90s completed component runs or native kernel proof.
        environment=dict(PATH='/usr/bin:/bin',LANG='C.UTF-8')
        for mode in ('fast','stall'):
            observed=route.isolated_watchdog_capture([route.PYTHON,'-B',str(route.FIXTURE/'isolated_engine_fixture.py'),
                '--finalization-control='+mode],b'',time.monotonic()+(5 if mode=='fast' else .02),environment)
            self.serial+=1;out=self.roots['evidence_parent']/('mechanism-'+str(self.serial));out.mkdir()
            for channel,data in observed['streams'].items():(out/(channel+'.bin')).write_bytes(data)
            (out/'observation.json').write_bytes(route.encoded({k:v for k,v in observed.items() if k!='streams'}))
            self.retain_case(out)
            if mode=='fast':self.assertTrue(observed['capture_complete']);self.assertEqual(observed['exit_code'],0)
            else:self.assertTrue(observed['timeout']);self.assertFalse(observed['capture_complete']);self.assertIsNotNone(observed['signal'])

    def check_claim_types(self):
        call=self.invocation('Read',dict(file_path='/work/read.txt',byte_offset=1,max_bytes=3))
        _,receipt,out,_=self.run_case(call)
        self.assertEqual(route.verify_isolated_bundle(self.config,out/'bundle.json',self.observation_path(out)),receipt)
        raw=json.loads((out/receipt['native_commands'][3]['stdout_ref']['artifact']).read_bytes())
        route.isolated_validate_file_claim(raw,call,receipt['request_id'])
        for field in ('byte_offset','eof'):
            bad=copy.deepcopy(raw)
            bad['facts'][field]=True if field=='byte_offset' else int(bad['facts']['eof'])
            with self.assertRaises(route.Refusal):route.isolated_validate_file_claim(bad,call,receipt['request_id'])
        bad=copy.deepcopy(raw);bad['complete']=1
        with self.assertRaises(route.Refusal):route.isolated_validate_file_claim(bad,call,receipt['request_id'])
        # Re-pin the raw claim and result claim_ref, preserving typed component facts.
        bad=copy.deepcopy(raw);bad['facts']['byte_offset']=True
        name=receipt['native_commands'][3]['stdout_ref']['artifact'];data=route.encoded(bad)+b'\n'
        result=json.loads((out/'result.json').read_bytes())
        result['claim_ref']=route.isolated_record('Artifact',artifact=name,sha256=route.digest(data),byte_length=len(data))
        def change(value):value['native_commands'][3]['stdout_received_bytes']=len(data)
        self.repack(out,{name:data,'result.json':route.encoded(result)},change)
        with self.assertRaises(route.Refusal) as failure:route.verify_isolated_bundle(self.config,out/'bundle.json',self.observation_path(out))
        self.assertEqual(failure.exception.code,'invalid_integer')

    def check_temporary_environment(self):
        fixed=dict(PATH='/usr/bin:/bin',LANG='C.UTF-8')
        alternatives=[({},fixed),({'TMPDIR':'','TEMP':'','TMP':''},fixed),
            (dict(TMPDIR='/public own//',TEMP='/public-temp/',TMP='/public-tmp',HOME='/ignored-public'),
                dict(fixed,TMPDIR='/public own//',TEMP='/public-temp/',TMP='/public-tmp')),
            ({'TMPDIR':'/'+'a'*4095},dict(fixed,TMPDIR='/'+'a'*4095)),
            ({'TMPDIR':'/'+'α'*2047},dict(fixed,TMPDIR='/'+'α'*2047))]
        invalid=[True,1,'relative','/public/./tmp','/public/../tmp','/public/\x00tmp','/public/\ntmp',
            '/public/\rtmp','/public/\x7ftmp','/'+'a'*4096,'/'+'α'*2048,'/public/\ud800tmp']
        with mock.patch.object(route,'artifact_read',side_effect=AssertionError('prelaunch artifact IO')), \
                mock.patch.object(route,'directory',side_effect=AssertionError('prelaunch directory IO')), \
                mock.patch.object(route,'isolated_tree',side_effect=AssertionError('prelaunch tree IO')), \
                mock.patch.object(route,'Store',side_effect=AssertionError('prelaunch Store IO')), \
                mock.patch.object(route.tempfile,'gettempdir',side_effect=AssertionError('prelaunch temp IO')), \
                mock.patch.object(Path,'resolve',side_effect=AssertionError('prelaunch resolve IO')), \
                mock.patch.object(Path,'stat',side_effect=AssertionError('prelaunch stat IO')), \
                mock.patch.object(Path,'lstat',side_effect=AssertionError('prelaunch lstat IO')), \
                mock.patch.object(os,'open',side_effect=AssertionError('prelaunch open IO')), \
                mock.patch.object(os,'walk',side_effect=AssertionError('prelaunch walk IO')):
            for values,expected in alternatives:
                with self.subTest(environment=values),mock.patch.object(route.os,'environ',values):
                    self.assertEqual(route.isolated_controller_environment(),expected)
            for key in ('TMPDIR','TEMP','TMP'):
                for value in invalid:
                    with self.subTest(key=key,value=value),mock.patch.object(route.os,'environ',{key:value}), \
                            mock.patch.object(route,'isolated_watchdog_capture') as capture:
                        with self.assertRaises(route.Refusal) as failure:
                            route.isolated_run(self.config,self.invocation(),self.roots['evidence_parent']/'unlaunched')
                        self.assertEqual(failure.exception.code,'isolated_temporary_environment')
                        capture.assert_not_called()
        with mock.patch.dict(os.environ,dict(TMPDIR=str(self.parent.parent),TEMP='',TMP='')):
            _,receipt,out,_=self.run_case()
            self.assertEqual(route.verify_isolated_bundle(self.config,out/'bundle.json',self.observation_path(out)),receipt)
            self.assertTrue(receipt['complete'])

    def check_fatal_capture_retention(self):
        bad=copy.deepcopy(self.config);bad['provider_requests']=True
        with mock.patch.object(self,'config',bad):
            with self.assertRaises(route.Refusal) as failure:self.run_case()
        self.assertEqual(failure.exception.code,'isolated_controller_malformed')
        retained=self.last_case_evidence;frames=self.last_watchdog_frames
        self.assertEqual(len(frames),1)
        frame=frames[0];observed=frame['observed']
        self.assertEqual(frame['argv'],route.isolated_controller_argv())
        self.assertEqual((retained/'controller/input.bin').read_bytes(),frame['payload'])
        payload=route.strict_json(frame['payload'])
        self.assertIs(payload['config']['provider_requests'],True)
        self.assertEqual(frame['deadline'],payload['run_deadline_ns']/1000000000)
        self.assertEqual(frame['environment'],route.isolated_controller_environment())
        metadata=json.loads((retained/'controller/capture.json').read_bytes())
        self.assertTrue(metadata['capture_returned']);self.assertEqual(metadata['capture_calls'],1)
        self.assertEqual(metadata['facts'],{k:v for k,v in observed.items() if k!='streams'})
        self.assertEqual(metadata['launch'],dict(argv=frame['argv'],deadline=frame['deadline'],environment=frame['environment']))
        for channel,expected in [('stdout',b''),('stderr',b'isolated_provider_absent\n')]:
            raw=(retained/('controller/'+channel+'.bin')).read_bytes()
            self.assertEqual(raw,expected);self.assertEqual(raw,observed['streams'][channel])
            self.assertEqual(metadata['streams'][channel],dict(bytes=len(raw),sha256=route.digest(raw)))
        self.assertTrue(observed['capture_complete']);self.assertEqual(observed['exit_code'],2)
        self.assertFalse(observed['timeout']);self.assertFalse(observed['overflow']);self.assertIsNone(observed['signal'])
        self.assertEqual(set(observed['eof_channels']),{'stdout','stderr'})
        self.assertEqual(observed['input_bytes_total'],len(frame['payload']))
        self.assertEqual(observed['input_bytes_written'],len(frame['payload']))
        self.assertIs(json.loads((retained/'config.json').read_bytes())['provider_requests'],True)
        self.assertEqual(json.loads((retained/'invocation.json').read_bytes()),payload['invocation'])
        self.assertFalse((retained/'run-observation.json').exists())
        self.assertFalse((Path(payload['output'])/'bundle.json').exists())
        _,receipt,out,_=self.run_case()
        self.assertTrue(receipt['complete'])
        self.assertEqual(route.verify_isolated_bundle(self.config,out/'bundle.json',self.observation_path(out)),receipt)

    def check_image_volume_shapes(self):
        # Public fixture matrix through the literal image guard; no Docker/kernel proof.
        base = self.fixture.image_record()
        expected = dict(value.split('=', 1) for value in base[0]['Config']['Env'])
        omitted = object()
        for label, volumes in [('omitted', omitted), ('null', None), ('empty-object', {})]:
            image = copy.deepcopy(base)
            if volumes is omitted:
                image[0]['Config'].pop('Volumes')
            else:
                image[0]['Config']['Volumes'] = volumes
            raw = self.fixture.encoded(image) + b'\n'
            configured = copy.deepcopy(self.config)
            configured['pins']['image_config_sha256'] = route.digest(raw)
            with self.subTest(image_volumes=label):
                self.assertEqual(route.isolated_image(raw, configured), expected)
        for label, volumes in [('declared', {'/declared': {}}), ('list', []),
                               ('string', ''), ('bool', False), ('number', 0)]:
            image = copy.deepcopy(base)
            image[0]['Config']['Volumes'] = volumes
            raw = self.fixture.encoded(image) + b'\n'
            configured = copy.deepcopy(self.config)
            configured['pins']['image_config_sha256'] = route.digest(raw)
            with self.subTest(rejected_volumes=label):
                with self.assertRaises(route.Refusal) as failure:
                    route.isolated_image(raw, configured)
                self.assertEqual(failure.exception.code, 'isolated_image_volume')
        for label, image_config in [('omitted', omitted), ('null', None), ('list', []),
                                    ('string', ''), ('bool', False), ('number', 0)]:
            image = copy.deepcopy(base)
            if image_config is omitted:
                image[0].pop('Config')
            else:
                image[0]['Config'] = image_config
            raw = self.fixture.encoded(image) + b'\n'
            configured = copy.deepcopy(self.config)
            configured['pins']['image_config_sha256'] = route.digest(raw)
            with self.subTest(rejected_config=label):
                with self.assertRaises(route.Refusal) as failure:
                    route.isolated_image(raw, configured)
                self.assertEqual(failure.exception.code, 'isolated_image_config')
        image = copy.deepcopy(base)
        image[0]['Config'].pop('Volumes')
        raw = self.fixture.encoded(image) + b'\n'
        configured = copy.deepcopy(self.config)
        configured['pins']['image_config_sha256'] = '0' * 64
        with self.assertRaises(route.Refusal) as failure:
            route.isolated_image(raw, configured)
        self.assertEqual(failure.exception.code, 'isolated_image_config_pin')
        for label, environment in [('null', None), ('string', 'PATH=/usr/bin'),
                                   ('element-type', [0]), ('entry-format', ['PATH']),
                                   ('duplicate', ['PATH=/usr/bin', 'PATH=/bin']),
                                   ('unlisted', ['PUBLIC_UNLISTED_NAME=own'])]:
            image = copy.deepcopy(base)
            image[0]['Config'].pop('Volumes')
            image[0]['Config']['Env'] = environment
            raw = self.fixture.encoded(image) + b'\n'
            configured = copy.deepcopy(self.config)
            configured['pins']['image_config_sha256'] = route.digest(raw)
            with self.subTest(rejected_image_env=label):
                with self.assertRaises(route.Refusal) as failure:
                    route.isolated_image(raw, configured)
                self.assertEqual(failure.exception.code, 'isolated_image_env')

    def test_isolated_authority_plan_and_inspect(self):
        self.check_temporary_environment()
        self.check_closed_arguments()
        self.check_image_volume_shapes()
        with self.assertRaises(route.Refusal):route.isolated_record('ContainerFacts',record_type='extra')
        plan=route.isolated_plan(self.config,self.invocation(),'a'*32)
        self.assertEqual(len(plan['mounts']),6)
        self.assertEqual([m['destination'] for m in plan['mounts'] if m['writable']],['/work','/tmp'])
        self.assertFalse(any(str(self.roots['evidence_parent'])==m['source'] or 'docker.sock' in m['source'] for m in plan['mounts']))
        self.assertIn('--pull=never',plan['create_argv']);self.assertNotIn('--security-opt=seccomp=unconfined',plan['create_argv'])
        good,receipt,out,_=self.run_case()
        self.assertEqual(good['outcome'],'component_completed')
        self.assertEqual(route.verify_isolated_bundle(self.config,out/'bundle.json',self.observation_path(out)),receipt)
        bad,receipt,_,state=self.run_case(fault='extra_mount')
        self.assertEqual(bad['outcome'],'instrument_incomplete');self.assertFalse(receipt['complete'])
        self.assertFalse(any(row[:2]==['rm','--force'] for row in state['commands']))

    def test_isolated_general_bash_plan(self):
        self.check_bash_discriminant()
        (self.roots['work']/'nested').mkdir()
        host_target=self.root/'never-executed'
        command='printf "arbitrary"; touch '+str(host_target)+'; exit 7'
        call=self.invocation(arguments=dict(command=command,cwd='/work/nested'))
        bundle,receipt,out,state=self.run_case(call,exit_code=7)
        self.assertEqual(bundle['outcome'],'component_completed');self.assertFalse(host_target.exists())
        result=json.loads((out/'result.json').read_bytes())
        self.assertEqual(result['facts']['argv'],['/bin/sh','-c',command]);self.assertEqual(result['facts']['exit_code'],7)
        self.assertIsNone(result['facts']['signal']);self.assertEqual(result['facts']['cwd'],'/work/nested')
        self.assertEqual((out/result['facts']['stdout_ref']['artifact']).read_bytes(),'own α\n'.encode())
        self.assertEqual((out/result['facts']['stderr_ref']['artifact']).read_bytes(),'error β\n'.encode())
        self.assertEqual(sum(row[0]=='create' for row in state['commands']),1)
        self.assertEqual(sum(row[0]=='start' for row in state['commands']),1)
        self.assertEqual(route.verify_isolated_bundle(self.config,out/'bundle.json',self.observation_path(out)),receipt)

    def test_isolated_file_boundary_and_effects(self):
        work=self.roots['work'];tmp=self.roots['tmp'];runtime=self.roots['runtime']
        own=work/'own.txt';value='own α\n'
        code,claim,_=self.file_claim('Write',dict(file_path=str(own),content=value))
        self.assertEqual((code,claim['kind']),(0,'Write'));self.assertEqual(own.read_bytes(),value.encode())
        code,claim,_=self.file_claim('Read',dict(file_path=str(own),byte_offset=0,max_bytes=100))
        self.assertEqual((code,claim['kind']),(0,'Read'));self.assertEqual(base64.b64decode(claim['returned_utf8_b64']),value.encode())
        code,claim,_=self.file_claim('Write',dict(file_path=str(tmp/'tmp.txt'),content='tmp'))
        self.assertEqual((code,claim['kind']),(0,'Write'))
        outside=self.parent/'outside.txt';outside.write_text('sentinel')
        (work/'link').symlink_to(outside);os.link(outside,work/'hard')
        for name in ('Read','Write'):
            for path in (outside,work/'link',work/'hard',runtime/'engine-files/hosts'):
                if name=='Read' and path==runtime/'engine-files/hosts':continue
                given=dict(file_path=str(path),**(dict(byte_offset=0,max_bytes=100) if name=='Read' else dict(content='bad')))
                _,observed,_=self.file_claim(name,given)
                self.assertEqual(observed['kind'],'refused');self.assertFalse(observed['facts']['effect_started'])
        self.assertEqual(outside.read_text(),'sentinel')
        import controlled_worker as worker
        with self.assertRaises(route.Refusal):
            worker.isolated_file_request(route.encoded(route.isolated_record('FileRequest',request_id='traversal',
                function_name='Read',arguments=dict(file_path=str(work/'../escape'),byte_offset=0,max_bytes=100))))
        _,claim,_=self.file_claim('Write',dict(file_path=str(own),content='new'),fsync_fault=True)
        self.assertEqual(claim['kind'],'refused');self.assertTrue(claim['facts']['effect_started']);self.assertEqual(own.read_bytes(),b'new')
        invalid=work/'invalid';invalid.write_bytes(b'\xff')
        code,claim,raw=self.file_claim('Read',dict(file_path=str(invalid),byte_offset=0,max_bytes=2))
        self.assertEqual(code,6);self.assertFalse(claim['complete']);self.assertEqual(raw,b'\xff')

    def test_isolated_untrusted_payload_and_host_lifecycle(self):
        self.check_fatal_capture_retention()
        forged=b'{"complete":true,"remaining_handle_ids":[],"sourceReady":true}\n'
        bundle,receipt,out,_=self.run_case(stdout=forged)
        self.assertEqual(bundle['outcome'],'component_completed')
        self.assertFalse(receipt['component_boundary_observed']);self.assertEqual(receipt['proof_scope'],'source_simulation')
        self.assertFalse(receipt['sourceReady']);self.assertFalse(receipt['C07_accepted']);self.assertFalse(receipt['C20_accepted'])
        self.assertEqual(json.loads((out/'result.json').read_bytes())['facts']['stdout_utf8'].encode(),forged)
        self.assertEqual(route.verify_isolated_bundle(self.config,out/'bundle.json',self.observation_path(out)),receipt)
        self.mutate_receipt(bundle,out,lambda value:value['container_stopped'].__setitem__('running',0))
        with self.assertRaises(route.Refusal):route.verify_isolated_bundle(self.config,out/'bundle.json',self.observation_path(out))
        _,receipt,_,state=self.run_case(fault='live_after_start',stdout=forged)
        self.assertFalse(receipt['complete']);self.assertTrue(receipt['cleanup_confirmed']);self.assertIsNone(receipt['snapshot'])
        self.assertTrue(any(row[0]=='kill' for row in state['commands']))

    def check_capture_native_exit(self):
        # Actual finite own processes: channel EOF may precede native process exit.
        program="import os;os.close(0);os.write(1,b'public stdout\\n');os.write(2,b'public stderr\\n');os.close(1);os.close(2);__import__('time').sleep(0.2);raise SystemExit(7)"
        argv=[route.PYTHON,'-I','-B','-c',program]
        environment=dict(PATH='/usr/bin:/bin',LANG='C.UTF-8')
        for kind,seconds in [('natural',8),('deadline',.1)]:
            with self.subTest(native_exit=kind):
                observed=route.isolated_capture(argv,b'',time.monotonic()+seconds,
                    dict(stdout=128,stderr=128),dict(environment=environment))
                self.retain_capture('native-exit-'+kind,observed)
                self.assertEqual(observed['argv'],argv)
                self.assertEqual(observed['input_bytes_total'],0);self.assertEqual(observed['input_bytes_written'],0)
                self.assertFalse(observed['overflow'])
                if kind=='natural':
                    self.assertEqual(observed['exit_code'],7);self.assertIsNone(observed['signal'])
                    self.assertFalse(observed['timeout']);self.assertTrue(observed['capture_complete'])
                    self.assertEqual(set(observed['eof_channels']),{'stdout','stderr'})
                    self.assertEqual(observed['streams'],dict(stdout=b'public stdout\n',stderr=b'public stderr\n'))
                    self.assertEqual(observed['stdout_received_bytes'],14);self.assertEqual(observed['stderr_received_bytes'],14)
                else:
                    self.assertTrue(observed['timeout']);self.assertFalse(observed['capture_complete'])
                    self.assertIsNone(observed['exit_code']);self.assertIsNotNone(observed['signal'])
                    self.assertGreaterEqual(observed['ended_ns'],observed['phase_deadline_ns'])

    def test_isolated_capture_completeness_and_caps(self):
        self.check_capture_native_exit()
        self.check_stream_caps();self.check_time_order();self.check_finalization_mechanism()
        environment=dict(PATH='/usr/bin:/bin',HOME=str(self.roots['cli_home']),LANG='C.UTF-8')
        observed=route.isolated_capture([route.PYTHON,'-c','import sys;sys.stdout.buffer.write(b"abcdef");sys.stderr.write("e")'],b'',
            time.monotonic()+5,dict(stdout=2,stderr=10),dict(environment=environment))
        self.retain_capture('channel-cap-control',observed)
        self.assertTrue(observed['overflow']);self.assertFalse(observed['capture_complete']);self.assertEqual(observed['streams']['stdout'],b'ab')
        observed=route.isolated_capture([route.PYTHON,'-c','import time;time.sleep(.2)'],b'',time.monotonic()+.01,
            dict(stdout=10,stderr=10),dict(environment=environment))
        self.retain_capture('timeout-control',observed)
        self.assertTrue(observed['timeout']);self.assertFalse(observed['capture_complete']);self.assertIsNotNone(observed['signal'])
        _,receipt,out,_=self.run_case(stdout=b'\xff')
        self.assertFalse(receipt['complete']);self.assertTrue(receipt['cleanup_confirmed']);self.assertIsNone(receipt['result_ref'])
        self.assertEqual((out/receipt['native_commands'][3]['stdout_ref']['artifact']).read_bytes(),b'\xff')
        _,receipt,_,_=self.run_case(exit_code=7,fault='wrong_exit')
        self.assertFalse(receipt['complete']);self.assertIn('isolated_exit',receipt['failure_codes'])

    def test_isolated_uncertain_create_and_exact_cleanup(self):
        self.check_incomplete_claims()
        bundle,receipt,out,state=self.run_case(fault='create_uncertain')
        self.assertEqual(bundle['outcome'],'instrument_incomplete');self.assertTrue(receipt['cleanup_confirmed'])
        self.assertIsNone(receipt['snapshot']);self.assertIsNone(receipt['result_ref'])
        self.assertEqual(sum(row[0]=='create' for row in state['commands']),1);self.assertFalse(any(row[0]=='start' for row in state['commands']))
        removed=[row for row in state['commands'] if row[:2]==['rm','--force']]
        self.assertEqual(removed,[['rm','--force',receipt['owned_cid']]])
        self.assertEqual(route.verify_isolated_bundle(self.config,out/'bundle.json',self.observation_path(out)),receipt)
        _,receipt,_,state=self.run_case(fault='cid_conflict')
        self.assertFalse(receipt['cleanup_confirmed']);self.assertFalse(any(row[0] in ('kill','rm') for row in state['commands']))
        _,receipt,_,_=self.run_case(fault='bad_absence')
        self.assertFalse(receipt['complete']);self.assertFalse(receipt['cleanup_confirmed'])

    def test_isolated_network_and_pin_limits(self):
        self.check_claim_types()
        for field,value in [('network','bridge'),('seccomp','unconfined'),('provider_requests',True)]:
            bad=copy.deepcopy(self.config);bad[field]=value
            with self.assertRaises(route.Refusal):route.validate_isolated_config(bad)
        bad=copy.deepcopy(self.config);bad['pins']['source_files']['controlled_worker.py']='0'*64
        with self.assertRaises(route.Refusal):route.validate_isolated_config(bad)
        bad=copy.deepcopy(self.config);bad['controller_authority']='forbidden'
        with self.assertRaises(route.Refusal):route.validate_isolated_config(bad)
        bundle,receipt,out,_=self.run_case(self.invocation('Read',dict(file_path='/work/read.txt',byte_offset=1,max_bytes=3)))
        self.assertEqual(bundle['outcome'],'component_completed')
        self.assertEqual(json.loads((out/'result.json').read_bytes())['facts']['content_utf8'],'ead')
        config_path=self.root/'component.json';config_path.write_bytes(route.encoded(self.config))
        result=subprocess.run([route.PYTHON,'-B',str(HARNESS/'controlled_route.py'),'isolated-verify','--config',str(config_path),
            '--bundle',str(out/'bundle.json'),'--run-observation',str(self.observation_path(out)),'--out',str(self.roots['evidence_parent']/'verified')],capture_output=True,check=False)
        self.retain_capture('verify-cli',dict(streams=dict(stdout=result.stdout,stderr=result.stderr),exit_code=result.returncode))
        self.assertEqual(result.returncode,0,result.stderr+result.stdout)
        self.assertEqual(json.loads(result.stdout)['outcome'],'component_completed')
        self.assertFalse(receipt['cgroup_empty_observed']);self.assertEqual(receipt['descendant_census'],'n/a')
        with self.assertRaises(route.Refusal):route.isolated_run(self.config,self.invocation(),out,_simulation=dict(state_path=str(self.root/'not-used.json')))


if __name__ == '__main__':
    unittest.main()
