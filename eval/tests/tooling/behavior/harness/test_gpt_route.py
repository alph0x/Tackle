"""Pinned synthetic GPT route through its actual public CLI and real consumers.

Guarantee / fault / consumer / valid alternative, before coverage:
Boundaries / untrusted launch or outside read / fixture launcher and actual read result /
  pinned own-tree read/write and clearly scoped syscall denial.
Retention / synthetic sensitive bytes retained / raw/tree/record retention gate /
  clean output, or missing auth with zero actual dispatches.
Projection / incomplete or invented tool facts / actual oracle and protocol CLI /
  complete native write/command/read, repeated updates and claim-only prose.
Caps / uncovered request or reset history / process census and persistent ledger /
  covered launch with conservative unknown cost and monotonic remainder.
Network / Host-derived endpoint or participant-owned log / actual Listener and oracle /
  owned loopback observation, repeated refusal, optional absent log.
Integrity / overwrite, drift, duplicate episode / public CLI and recorded protocol /
  fresh output, byte-identical resume and registered full-family execution.
No case establishes live GPT isolation, authentication, billing or native telemetry.
"""

import copy
import base64
import errno
from datetime import datetime, timezone
import hashlib
import importlib.util
from unittest import mock
import json
import os
import fcntl
import signal
import socket
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[5]
ROUTE = ROOT / 'eval/behavior/harness/gpt_route.py'
FIXTURES = ROOT / 'eval/behavior/harness/fixtures/gpt-route'
FILES = ('stub_cli.py', 'stub_launcher.py', 'sentinel_helper.py', 'oracle/check.py')


def digest(data):
    return hashlib.sha256(data).hexdigest()


class RouteCLI(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='tackle-gpt-route-')
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()
        for name in ('run', 'state', 'repo', 'workspace', 'install', 'oracle', 'final', 'tmp'):
            (self.base / name).mkdir(mode=0o700)
        self.prior = self.base / 'state/prior.json'
        self.prior.write_text('{"rows": []}\n')
        self.inside = self.base / 'run/inside-sentinel'
        self.inside.write_text('inside-before\n')
        self.config_path = self.base / 'config.json'
        interpreter = Path(sys.executable).resolve()
        self.value = {
            'schema': 'tackle-gpt-route-config/1', 'mode': 'synthetic',
            'binding': {'model': 'gpt-6-luna', 'requested_host_effort': 'xhigh'},
            'cli': self.pin(FIXTURES / 'stub_cli.py', 'tackle-gpt-stub/1'),
            'launcher': self.pin(FIXTURES / 'stub_launcher.py', 'tackle-gpt-stub-launcher/1'),
            'interpreter': self.pin(interpreter, sys.version),
            'fingerprints': {'route_sha256': digest(ROUTE.read_bytes()),
                             'mapping_version': 'tackle-gpt-stub-map/1',
                             'fixture_tree_sha256': digest(b''.join(name.encode() + b'\0' +
                                 (FIXTURES / name).read_bytes() + b'\0' for name in sorted(FILES)))},
            'roots': {'run_root': str(self.base / 'run'), 'state_dir': str(self.base / 'state')},
            'capabilities': {'isolation': 'stub-isolation/1', 'auth': 'stub-auth-separated/1',
                             'limiter': 'stub-request-limiter/1', 'trace': 'tackle-gpt-stub-map/1',
                             'network': 'stub-loopback-log/1'},
            'prior_ledger': {'path': str(self.prior), 'sha256': digest(self.prior.read_bytes())},
            'caps': {'total_usd': 200, 'episode': {'usd': 8, 'seconds': 900, 'request_units': 60},
                     'stages': {'smoke': 25, 'held-out': 121}, 'probe_usd': 4},
            'oracle': {'launcher_sha256': digest((FIXTURES / 'stub_launcher.py').read_bytes()),
                       'interpreter_sha256': digest(interpreter.read_bytes()), 'seconds': 30},
        }
        self.serial = 0
        self.call_lock = threading.Lock()

    @staticmethod
    def pin(path, version):
        return {'path': str(path), 'sha256': digest(path.read_bytes()), 'version': version}

    def call(self, command='preflight', value=None, raw=None, out=None, without_config=False, paths=None, interrupt=False):
        with self.call_lock:
            self.serial += 1
            call_id = self.serial
        config_path = self.base / ('config-' + str(call_id) + '.json')
        config_path.write_text(raw if raw is not None else json.dumps(value or self.value))
        out = out or self.base / ('out-' + str(call_id))
        argv = [sys.executable, '-B', str(ROUTE), command]
        if not without_config:
            argv += ['--config', str(config_path)]
        argv += ['--out', str(out)]
        if command in ('probe', 'run'):
            argv += ['--repo', str(self.base / 'repo'), '--install', str(self.base / 'install')]
        if command == 'probe':
            argv += ['--workspace', str(self.base / 'workspace')]
        if command == 'run':
            argv += ['--cohort', str(self.base / 'cohort'), '--stage', 'smoke']
        if command == 'judge':
            argv += ['--oracle', str(FIXTURES / 'oracle'), '--final', str(self.base / 'final'),
                     '--transcript', str(self.base / 'canonical.jsonl')]
        for key, path in (paths or {}).items():
            flag = '--' + key
            if flag in argv:
                argv[argv.index(flag) + 1] = str(path)
            else:
                argv += [flag, str(path)]
        env = {'PATH': '/usr/bin:/bin', 'HOME': str(self.base), 'TMPDIR': str(self.base / 'tmp'),
               'LANG': 'en_US.UTF-8', 'PYTHONDONTWRITEBYTECODE': '1'}
        started = datetime.now(timezone.utc).isoformat()
        if interrupt:
            child = subprocess.Popen(argv, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            active = self.base / 'state/spend.json'
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline and not active.exists():
                time.sleep(0.01)
            time.sleep(0.15)
            child.send_signal(signal.SIGTERM)
            stdout, stderr = child.communicate(timeout=10)
            process = subprocess.CompletedProcess(argv, child.returncode, stdout, stderr)
        else:
            process = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, timeout=60)
        evidence = os.environ.get('TACKLE_GPT_ROUTE_CAPTURE_ROOT')
        if evidence:
            label = self.id().split('.')[-1] + '-' + str(call_id)
            saved = Path(evidence) / label
            saved.mkdir(parents=True, exist_ok=False)
            (saved / 'stdout.bin').write_bytes(process.stdout)
            (saved / 'stderr.bin').write_bytes(process.stderr)
            (saved / 'config.json').write_bytes(config_path.read_bytes())
            for name in ('capability.json', 'packet.json'):
                if (out / name).is_file():
                    (saved / name).write_bytes((out / name).read_bytes())
            if out.is_dir() and not out.is_symlink():
                for source in out.rglob('*'):
                    if source.is_file() and not source.is_symlink():
                        target = saved / 'output' / source.relative_to(out)
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(source.read_bytes())
            active = self.base / 'state/spend.json'
            if active.is_file():
                (saved / 'synthetic-spend.json').write_bytes(active.read_bytes())
            record = {'argv': argv, 'cwd': str(ROOT), 'env': env, 'native_exit_code': process.returncode,
                      'actor': 'source author /root/gpt_route_author', 'started_at': started,
                      'finished_at': datetime.now(timezone.utc).isoformat(),
                      'stdout_sha256': digest(process.stdout), 'stderr_sha256': digest(process.stderr),
                      'config_sha256': digest(config_path.read_bytes()),
                      'source_sha256': digest(ROUTE.read_bytes()), 'native_inference_usage': 'n/a'}
            (saved / 'capture.json').write_text(json.dumps(record, indent=2) + '\n')
        return process, out

    def cohort(self, sessions=None, files=None, arms=('control',), limits=None, network=None):
        root = self.base / ('cohort-' + str(self.serial))
        root.mkdir()
        for name, text in (('baseline', 'synthetic baseline skill\n'), ('candidate', 'synthetic candidate skill\n')):
            folder = self.base / 'install' / name
            folder.mkdir(exist_ok=True)
            (folder / 'SKILL.md').write_text(text)
        def files_digest(items):
            return digest(json.dumps({name: digest(data.encode()) for name, data in items.items()},
                                     sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode())
        files = files or {'inside-sentinel': 'inside-before\n', 'history-archive.md': 'éA\n'}
        baseline = files_digest({'SKILL.md': 'synthetic baseline skill\n'}) if 'method' in arms else files_digest({})
        candidate = files_digest({'SKILL.md': 'synthetic candidate skill\n'}) if 'method:candidate' in arms else baseline
        manifest = {'schema': 'tackle-cohort/1', 'cohort_id': 'synthetic-measurement-' + str(self.serial),
            'hypothesis': 'Synthetic consumers preserve observed facts.', 'primary_metric': 'synthetic action',
            'decision_rule': 'Illustrative tooling fixture only.', 'n_min': 1, 'seeds': [1],
            'variants': [{'scenario_id': 'synthetic', 'variant_id': 'fixture', 'split': 'development',
                          'class': 'procedure', 'fixture_sha256': files_digest(files)}],
            'arms': list(arms), 'comparisons': ([{'id': 'primary', 'baseline_arm': arms[0], 'candidate_arm': arms[1]}] if len(arms) > 1 else []),
            'executor': {'harness': 'tackle-gpt-synthetic', 'model': 'gpt-6-luna', 'effort': 'high'},
            'judge': {'model_family': 'n/a', 'blinded': False},
            'artifacts': {'baseline_sha256': baseline, 'candidate_sha256': candidate},
            'oracle_sha256': digest((FIXTURES / 'oracle/check.py').read_bytes()),
            'order': [{'episode_id': 'synthetic-' + str(i), 'scenario_id': 'synthetic', 'variant_id': 'fixture',
                       'arm': arm, 'seed': 1} for i, arm in enumerate(arms)], 'created_at': '2026-10-04T00:00:00Z'}
        manifest['seal_sha256'] = digest(json.dumps(manifest, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode())
        (root / 'manifest.json').write_text(json.dumps(manifest))
        (root / 'episodes.jsonl').touch()
        (root / 'workload.json').write_text(json.dumps({'schema': 'tackle-gpt-synthetic-workload/1', 'files': files,
            'sessions': sessions or [{'operation': 'read_write'}], 'limits': limits or {'seconds': 900, 'requests': 60},
            'network': network}))
        return root

    def run_fixture(self, sessions=None, **kwargs):
        cohort = self.cohort(sessions=sessions, **kwargs)
        process, out = self.call('run', paths={'cohort': cohort})
        return process, out, cohort

    def records(self, cohort):
        return [json.loads(line) for line in (cohort / 'episodes.jsonl').read_text().splitlines()]

    def success(self, process, out):
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        return json.loads((out / 'result.json').read_text())

    def episode(self, out):
        return out / 'episode-0'

    def packet(self, process, out):
        self.assertEqual(process.returncode, 1, process.stdout + process.stderr)
        packet = json.loads((out / 'packet.json').read_text())
        self.assertEqual(packet['outcome'], 'unsupported')
        for key in ('live_ready', 'live_route_accepted', 'task_complete', 't06_held_out_ready'):
            self.assertIs(packet[key], False)
        self.assertNotIn('scores', packet)
        self.assertFalse((out / 'episodes.jsonl').exists())
        self.assertEqual(self.inside.read_text(), 'inside-before\n')
        self.assertEqual(self.prior.read_text(), '{"rows": []}\n')
        return packet

    def test_explicit_config_is_required(self):
        process, out = self.call(without_config=True)
        self.assertEqual(process.returncode, 2)
        self.assertFalse(out.exists())

    def test_live_forms_refuse_without_resolving_candidate_paths(self):
        value = copy.deepcopy(self.value)
        value['mode'] = 'live'
        for name in ('cli', 'launcher', 'interpreter'):
            value[name]['path'] = str(self.base / 'not-present')
        value['prior_ledger']['path'] = str(self.base / 'not-present-ledger')
        for command in ('preflight', 'probe', 'run', 'judge'):
            with self.subTest(command=command):
                process, out = self.call(command, value=value)
                packet = self.packet(process, out)
                self.assertEqual(packet['reason'], 'live_capabilities_unavailable')
                self.assertEqual(len(packet['missing_capabilities']), 5)

    def test_missing_capabilities_refuse_before_permitted_operation(self):
        for capability in ('isolation', 'auth', 'limiter', 'trace', 'network'):
            for command in ('preflight', 'probe'):
                with self.subTest(capability=capability, command=command):
                    value = copy.deepcopy(self.value)
                    value['capabilities'][capability] = None
                    process, out = self.call(command, value=value)
                    packet = self.packet(process, out)
                    self.assertEqual(packet['missing_capabilities'], [capability + '_unsupported'])
                    self.assertIs(packet['checked']['runtime_dispatched'], False)

    def test_malformed_configs_are_usage_errors_without_outputs(self):
        extra = copy.deepcopy(self.value)
        extra['unknown'] = True
        boolean = copy.deepcopy(self.value)
        boolean['caps']['episode']['request_units'] = True
        duplicate = json.dumps(self.value)[:-1] + ', "mode": "synthetic"}'
        nonfinite = json.dumps(self.value).replace('"seconds": 30', '"seconds": NaN')
        for raw in (json.dumps(extra), json.dumps(boolean), duplicate, nonfinite):
            with self.subTest(raw=raw[-30:]):
                process, out = self.call(raw=raw)
                self.assertEqual(process.returncode, 2, process.stdout + process.stderr)
                self.assertFalse(out.exists())

    def test_pins_refuse_unapproved_code_or_drift(self):
        for field in ('path', 'sha256', 'version'):
            with self.subTest(field=field):
                value = copy.deepcopy(self.value)
                value['cli'][field] = str(self.base / 'unknown-code') if field == 'path' else 'mismatch'
                process, out = self.call(value=value)
                self.assertEqual(self.packet(process, out)['reason'], 'cli_pin_mismatch')

    def test_existing_output_and_dangling_link_remain_unchanged(self):
        out = self.base / 'occupied'
        out.mkdir()
        sentinel = out / 'sentinel'
        sentinel.write_bytes(b'preserve')
        process, _ = self.call(out=out)
        self.assertEqual(process.returncode, 2)
        self.assertEqual(list(out.iterdir()), [sentinel])
        self.assertEqual(sentinel.read_bytes(), b'preserve')
        link = self.base / 'dangling'
        target = self.base / 'absent-target'
        link.symlink_to(target)
        process, _ = self.call(out=link)
        self.assertEqual(process.returncode, 2)
        self.assertTrue(link.is_symlink())
        self.assertFalse(target.exists())

    def test_missing_capability_refusal_cannot_write_outside_synthetic_root(self):
        value = copy.deepcopy(self.value)
        value['capabilities']['auth'] = None
        out = self.base.parent / (self.base.name + '-outside')
        self.assertFalse(out.exists())
        process, _ = self.call(value=value, out=out)
        self.assertEqual(process.returncode, 2, process.stdout + process.stderr)
        self.assertFalse(out.exists())

    def test_complete_pinned_synthetic_preflight_is_permitted(self):
        process, out = self.call()
        self.assertTrue((out / 'capability.json').is_file(), process.stdout + process.stderr)
        packet = json.loads((out / 'capability.json').read_text())
        self.assertEqual(packet['subcommand'], 'preflight')
        self.assertIs(packet['checked']['configuration'], True)
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)

    def test_complete_pinned_synthetic_probe_reads_and_writes_own_sentinel(self):
        process, out = self.call('probe')
        self.assertTrue((out / 'capability.json').is_file(), process.stdout + process.stderr)
        self.assertEqual(json.loads((out / 'capability.json').read_text())['subcommand'], 'probe')
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        self.assertEqual(self.inside.read_text(), 'inside-after\n')
        result = json.loads((out / 'result.json').read_text())
        self.assertTrue(result['work_tree_read_allowed'])
        self.assertTrue(result['work_tree_write_allowed'])

    def test_probe_distinguishes_syscall_wrapper_and_loopback_controls(self):
        process, out = self.call('probe')
        result = self.success(process, out)
        kernel = json.loads((out / 'kernel-control.json').read_text())
        local = json.loads((out / 'network-control.json').read_text())
        capture = json.loads((out / 'offline-capture.json').read_text())
        self.assertTrue(kernel['outside_attempted'])
        self.assertTrue(kernel['outside_denied'])
        self.assertIn(kernel['outside_errno'], (1, 13))
        self.assertTrue(kernel['outside_write_denied'])
        self.assertIn(kernel['outside_write_errno'], (1, 13))
        self.assertEqual(kernel['inside_after'], 'inside-after\n')
        self.assertTrue(local['attempted'] and local['refused'])
        self.assertIsInstance(local['errno'], int)
        self.assertEqual(local['errno'], errno.ECONNREFUSED)
        self.assertEqual(local['outcome'], 'observed_refusal')
        self.assertTrue(result['outside_wrapper_denied'])
        self.assertEqual(capture['native_exit'], 0)
        self.assertEqual(capture['argv'][6:9], ['sandbox', '-P', 'gpt-measurement'])
        self.assertEqual(set(capture['env']), {'PATH', 'HOME', 'CODEX_HOME', 'TMPDIR', 'LANG', 'PYTHONDONTWRITEBYTECODE'})
        self.assertFalse(json.loads((out / 'packet.json').read_text())['live_ready'])

    def test_outside_symlink_hardlink_and_traversal_reads_are_wrapper_denials(self):
        for target in ('outside-link', 'outside-hardlink', '../../repo/outside-sentinel'):
            with self.subTest(target=target):
                process, out, _ = self.run_fixture([{'operation': 'boundary', 'target': target}])
                self.success(process, out)
                facts = json.loads((self.episode(out) / 'mapping.json').read_text())['facts']
                results = [row['exact_result'] for row in facts if row['fact'] == 'result']
                self.assertEqual(len(results), 2)
                self.assertTrue(all(result['error'] == 'PermissionError' and result['mechanism'] == 'synthetic wrapper' for result in results))
                self.assertEqual((self.base / 'repo/outside-sentinel').read_text(), 'outside-preserve\n')
        process, out, _ = self.run_fixture()
        self.success(process, out)
        self.assertEqual((self.episode(out) / 'final/inside-sentinel').read_text(), 'inside-after\n')

    def test_linked_input_tree_is_refused_before_worker(self):
        link = self.base / 'repo/link'
        link.symlink_to(self.inside)
        process, out = self.call('probe')
        self.assertEqual(process.returncode, 1)
        self.assertEqual(json.loads((out / 'packet.json').read_text())['reason'], 'synthetic_tree_link')
        self.assertFalse((self.base / 'state/spend.json').exists())
        link.unlink()
        process, out = self.call('probe')
        self.success(process, out)

    def test_control_and_distinct_method_installs_reach_protocol_consumer(self):
        process, out, cohort = self.run_fixture(arms=('control', 'method', 'method:candidate'))
        result = self.success(process, out)
        records = self.records(cohort)
        self.assertEqual(result['initiated_requests'], 3)
        self.assertEqual(result['protocol_native_exit'], 0)
        self.assertEqual([r['arm'] for r in records], ['control', 'method', 'method:candidate'])
        self.assertIsNone(records[0]['artifact_sha256'])
        self.assertNotEqual(records[1]['artifact_sha256'], records[2]['artifact_sha256'])
        self.assertTrue(all(r['executor'] == {'harness': 'tackle-gpt-synthetic', 'model': 'gpt-6-luna', 'effort': 'high'} for r in records))
        for index, expected in ((1, 'synthetic baseline skill\n'), (2, 'synthetic candidate skill\n')):
            facts = json.loads((out / ('episode-' + str(index)) / 'mapping.json').read_text())['facts']
            self.assertTrue(any(row.get('exact_result', {}).get('content') == expected for row in facts))
        self.assertEqual(json.loads((out / 'protocol-capture.json').read_text())['native_exit'], 0)
        capture = json.loads((out / 'protocol-capture.json').read_text())
        for name in ('manifest.json', 'episodes.jsonl', 'workload.json'):
            actual = (cohort / name).read_bytes()
            self.assertEqual((out / 'protocol-input' / name).read_bytes(), actual)
            self.assertEqual(capture['input_sha256'][name], digest(actual))

    def test_sessions_have_fresh_process_identity_and_shared_episode_work(self):
        process, out, _ = self.run_fixture([{'operation': 'read_write'}, {'operation': 'read_write'}])
        self.success(process, out)
        result = json.loads((self.episode(out) / 'result.json').read_text())
        first, second = result['sessions']
        self.assertNotEqual(first['session_id'], second['session_id'])
        self.assertNotEqual(first['thread_id'], second['thread_id'])
        self.assertEqual(first['cwd'], second['cwd'])
        self.assertEqual(first['env'], second['env'])
        self.assertNotEqual(first['env']['HOME'], str(self.base))
        facts = json.loads((self.episode(out) / 'mapping.json').read_text())['facts']
        pids = [row['pid'] for row in facts if row['fact'] == 'request']
        self.assertEqual(len(set(pids)), 2)
        reads = [row['exact_result']['content'] for row in facts if row['fact'] == 'result' and row['original_name'] == 'NativeRead']
        self.assertEqual(reads, ['inside-before\n', 'inside-after\n'])

    def test_raw_bytes_offsets_native_write_and_protocol_hash_are_separate(self):
        process, out, cohort = self.run_fixture()
        self.success(process, out)
        episode = self.episode(out)
        raw = (episode / 'session-1/stdout.bin').read_bytes()
        canonical = (episode / 'canonical.jsonl').read_bytes()
        facts = json.loads((episode / 'mapping.json').read_text())['facts']
        for fact in facts:
            source = fact['source']
            self.assertEqual(source['raw_sha256'], digest(raw))
            event = json.loads(raw[source['byte_start']:source['byte_end']])
            self.assertEqual(event['event_id'], source['event_id'])
            self.assertEqual(event['session_id'], source['session_id'])
        write = next(row for row in facts if row['fact'] == 'result' and row['original_name'] == 'NativeWrite')
        self.assertEqual(write['exact_result']['bytes_written'], len(b'inside-after\n'))
        self.assertEqual(write['exact_result']['content_sha256'], digest(b'inside-after\n'))
        self.assertEqual(self.records(cohort)[0]['transcript_sha256'], digest(raw))
        self.assertNotEqual(digest(raw), digest(canonical))
        self.assertEqual(json.loads((episode / 'oracle-capture.json').read_text())['native_exit'], 0)

    def test_archive_metric_counts_returned_utf8_prefixes_across_sessions(self):
        process, out, _ = self.run_fixture([{'operation': 'archive', 'read_limit': 3}, {'operation': 'archive'}])
        self.success(process, out)
        result = json.loads((self.episode(out) / 'result.json').read_text())
        self.assertEqual(result['archive_bytes_read'], 7)
        facts = json.loads((self.episode(out) / 'mapping.json').read_text())['facts']
        actual = [row['exact_result']['content'] for row in facts if row['fact'] == 'result']
        self.assertEqual(actual, ['éA', 'éA\n'])

    def test_prose_claim_does_not_invent_archive_read_or_tool(self):
        process, out, _ = self.run_fixture([{'operation': 'claim_only'}])
        self.success(process, out)
        episode = self.episode(out)
        result = json.loads((episode / 'result.json').read_text())
        self.assertEqual(result['archive_bytes_read'], 0)
        canonical = [json.loads(line) for line in (episode / 'canonical.jsonl').read_text().splitlines()]
        self.assertEqual(canonical, [{'type': 'result', 'subtype': 'success'}])
        oracle = json.loads((episode / 'oracle.json').read_text())
        self.assertEqual(oracle['scores']['observed_calls'], 0)

    def test_complete_command_preserves_actual_stdout_stderr_exit_and_cwd(self):
        process, out, _ = self.run_fixture([{'operation': 'command'}])
        self.success(process, out)
        episode = self.episode(out)
        facts = json.loads((episode / 'mapping.json').read_text())['facts']
        invoked = next(row for row in facts if row['fact'] == 'invocation')
        returned = next(row for row in facts if row['fact'] == 'result')
        capture = json.loads((episode / 'session-1/capture.json').read_text())
        self.assertEqual(invoked['exact_input']['cwd'], capture['cwd'])
        self.assertEqual(returned['exact_result'], {'stdout': 'command-output\n', 'stderr': 'command-error\n', 'exit_code': 0})

    def test_incomplete_unknown_duplicate_or_wrong_binding_stops_before_oracle(self):
        for fault in ('missing_result', 'duplicate_id', 'invalid_json', 'summary_only', 'unknown_tool', 'truncated_output', 'wrong_binding'):
            with self.subTest(fault=fault):
                process, out, cohort = self.run_fixture([{'operation': 'read_write', 'fault': fault}])
                self.assertEqual(process.returncode, 1, process.stdout + process.stderr)
                self.assertFalse((self.episode(out) / 'oracle-capture.json').exists())
                self.assertFalse((self.episode(out) / 'canonical.jsonl').exists())
                self.assertEqual(self.records(cohort)[0]['outcome'], 'error')
                self.assertNotEqual(self.records(cohort)[0]['outcome'], 'avoided')
        process, out, _ = self.run_fixture([{'operation': 'read_write', 'fault': 'repeated_update'}])
        self.success(process, out)
        rows = [json.loads(line) for line in (self.episode(out) / 'canonical.jsonl').read_text().splitlines()]
        ids = [row['message']['content'][0]['id'] for row in rows if row['type'] == 'assistant']
        self.assertEqual(len(ids), 2)
        self.assertEqual(len(set(ids)), 2)

    def test_sensitive_encodings_in_streams_tree_names_and_links_are_withheld(self):
        marker = 'synthetic sensitive+"marker'
        forms = [marker, base64.b64encode(marker.encode()).decode(), marker.encode().hex(), quote(marker, safe=''), json.dumps(marker)[1:-1]]
        for fault in ('credential_stdout', 'credential_stderr', 'credential_file', 'credential_name', 'credential_link'):
            for form in ('raw', 'base64', 'hex', 'url', 'json'):
                with self.subTest(fault=fault, form=form):
                    process, out, cohort = self.run_fixture([{'operation': 'read_write', 'fault': fault, 'form': form}])
                    self.assertEqual(process.returncode, 1, process.stdout + process.stderr)
                    result = json.loads((self.episode(out) / 'result.json').read_text())
                    self.assertEqual(result['reason'], 'credential')
                    self.assertEqual(result['initiated_requests'], 1)
                    self.assertFalse((self.episode(out) / 'session-1').exists())
                    self.assertFalse((self.episode(out) / 'final').exists())
                    self.assertEqual(self.records(cohort)[0]['outcome'], 'error')
                    for retained in out.rglob('*'):
                        if retained.is_file():
                            self.assertTrue(all(value.encode() not in retained.read_bytes() for value in forms), retained.name)

    def test_sensitive_input_refuses_without_any_process_claim(self):
        process, out, _ = self.run_fixture(files={'inside-sentinel': 'synthetic sensitive+"marker'})
        self.assertEqual(process.returncode, 1)
        self.assertEqual(json.loads((out / 'packet.json').read_text())['reason'], 'credential_before_launch')
        self.assertEqual(json.loads((self.base / 'state/spend.json').read_text())['rows'], [])
        self.assertFalse((self.episode(out) / 'session-1').exists())

    def test_prior_global_smoke_heldout_and_probe_headroom_is_not_reset(self):
        for stage, amount, command in (('prior', 199.95, 'run'), ('smoke', 24.95, 'run'), ('held-out', 120.95, 'run'), ('probe', 3.95, 'probe')):
            with self.subTest(stage=stage):
                active = self.base / 'state/spend.json'
                if active.exists():
                    active.unlink()
                self.prior.write_text(json.dumps({'rows': [{'name': 'prior', 'kind': 'synthetic', 'stage': stage, 'cap_usd': amount,
                    'cost_usd': None, 'settled': False}]}))
                self.value['prior_ledger']['sha256'] = digest(self.prior.read_bytes())
                paths = {'stage': 'held-out'} if stage == 'held-out' else {}
                if command == 'run':
                    paths['cohort'] = self.cohort()
                process, out = self.call(command, paths=paths)
                self.assertEqual(process.returncode, 1, process.stdout + process.stderr)
                self.assertEqual(len(json.loads(active.read_text())['rows']), 1)
                self.assertFalse(any(out.rglob('stdout.bin')))

    def test_unknown_cost_stays_unknown_with_conservative_prelaunch_reservations(self):
        process, out, _ = self.run_fixture([{'operation': 'claim_only'}, {'operation': 'read_write'}])
        self.success(process, out)
        rows = json.loads((self.base / 'state/spend.json').read_text())['rows']
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(row['cap_usd'] == 0.1 and row['cost_usd'] is None and row['settled'] is False for row in rows))
        self.assertEqual(json.loads((self.episode(out) / 'dispatch.json').read_text())['initiated_requests'], 2)
        self.assertEqual(json.loads((self.episode(out) / 'result.json').read_text())['cost_usd'], 'n/a')

    def test_sixty_actual_requests_are_covered_and_sixty_first_is_not_launched(self):
        process, out, cohort = self.run_fixture([{'operation': 'claim_only'} for _ in range(61)])
        self.assertEqual(process.returncode, 1, process.stdout + process.stderr)
        result = json.loads((self.episode(out) / 'result.json').read_text())
        self.assertEqual(result['initiated_requests'], 60)
        self.assertEqual(len(list(self.episode(out).glob('session-*'))), 60)
        self.assertEqual(len(json.loads((self.base / 'state/spend.json').read_text())['rows']), 60)
        self.assertEqual(self.records(cohort)[0]['outcome'], 'timeout')
        self.assertFalse((self.episode(out) / 'oracle-capture.json').exists())

    def test_wall_remainder_and_timeout_kill_actual_worker(self):
        process, out, cohort = self.run_fixture([{'operation': 'read_write', 'delay': 0.1}, {'operation': 'read_write', 'delay': 2}],
                                               limits={'seconds': 0.6, 'requests': 60})
        self.assertEqual(process.returncode, 1, process.stdout + process.stderr)
        result = json.loads((self.episode(out) / 'result.json').read_text())
        self.assertEqual(result['reason'], 'wall_limit')
        first, second = result['sessions']
        self.assertLess(second['remaining_seconds'], first['remaining_seconds'])
        self.assertTrue(second['timeout'])
        request = json.loads((self.episode(out) / 'session-2/stdout.bin').read_bytes().splitlines()[0])
        with self.assertRaises(ProcessLookupError):
            os.kill(request['pid'], 0)
        self.assertEqual(self.records(cohort)[0]['outcome'], 'timeout')
        process, out, _ = self.run_fixture([{'operation': 'read_write', 'delay': 0.01}], limits={'seconds': 2, 'requests': 1})
        self.success(process, out)

    def test_interruption_records_failure_and_kills_actual_worker(self):
        cohort = self.cohort([{'operation': 'read_write', 'delay': 3}])
        process, out = self.call('run', paths={'cohort': cohort}, interrupt=True)
        self.assertEqual(process.returncode, 1, process.stdout + process.stderr)
        result = json.loads((self.episode(out) / 'result.json').read_text())
        self.assertEqual(result['reason'], 'interrupted')
        self.assertTrue(result['sessions'][0]['interrupted'])
        request = json.loads((self.episode(out) / 'session-1/stdout.bin').read_bytes().splitlines()[0])
        with self.assertRaises(ProcessLookupError):
            os.kill(request['pid'], 0)

    def test_concurrent_route_is_refused_then_completed_route_resumes_without_launch(self):
        cohort = self.cohort([{'operation': 'read_write', 'delay': 0.7}])
        observed = []
        worker = threading.Thread(target=lambda: observed.append(self.call('run', paths={'cohort': cohort}, out=self.base / 'first')))
        worker.start()
        active = self.base / 'state/spend.json'
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            try:
                if active.exists() and json.loads(active.read_text())['rows']:
                    break
            except (OSError, ValueError):
                pass
            time.sleep(0.01)
        process, out = self.call('run', paths={'cohort': cohort}, out=self.base / 'second')
        self.assertEqual(process.returncode, 1, process.stdout + process.stderr)
        self.assertEqual(json.loads((out / 'packet.json').read_text())['reason'], 'synthetic_concurrent_operation')
        worker.join(timeout=10)
        self.assertFalse(worker.is_alive())
        self.success(*observed[0])
        before = (cohort / 'episodes.jsonl').read_bytes()
        process, out = self.call('run', paths={'cohort': cohort}, out=self.base / 'third')
        result = self.success(process, out)
        self.assertEqual(result['initiated_requests'], 0)
        self.assertEqual(result['resumed_records'], 1)
        self.assertEqual((cohort / 'episodes.jsonl').read_bytes(), before)
        self.assertEqual(len(json.loads(active.read_text())['rows']), 1)

    def test_workload_drift_and_unknown_operation_do_not_bypass_continuity(self):
        process, out, cohort = self.run_fixture()
        self.success(process, out)
        before = (cohort / 'episodes.jsonl').read_bytes()
        clone = self.base / 'clone-cohort'
        clone.mkdir()
        for name in ('manifest.json', 'episodes.jsonl', 'workload.json'):
            (clone / name).write_bytes((cohort / name).read_bytes())
        process, out = self.call('run', paths={'cohort': clone})
        self.assertEqual(process.returncode, 1)
        self.assertEqual(json.loads((out / 'packet.json').read_text())['reason'], 'synthetic_continuity_drift')
        self.assertEqual((cohort / 'episodes.jsonl').read_bytes(), before)
        self.assertEqual(len(json.loads((self.base / 'state/spend.json').read_text())['rows']), 1)
        path = cohort / 'workload.json'
        workload = json.loads(path.read_text())
        workload['sessions'][0]['delay'] = 0.1
        path.write_text(json.dumps(workload))
        process, out = self.call('run', paths={'cohort': cohort})
        self.assertEqual(process.returncode, 1)
        self.assertEqual(json.loads((out / 'packet.json').read_text())['reason'], 'synthetic_continuity_drift')
        self.assertEqual((cohort / 'episodes.jsonl').read_bytes(), before)
        process, out, _ = self.run_fixture([{'operation': 'arbitrary_program'}])
        self.assertEqual(process.returncode, 1)
        self.assertEqual(json.loads((out / 'packet.json').read_text())['reason'], 'synthetic_operation_unsupported')
        self.assertEqual(len(json.loads((self.base / 'state/spend.json').read_text())['rows']), 1)

    @staticmethod
    def free_port():
        with socket.socket() as held:
            held.bind(('127.0.0.1', 0))
            return held.getsockname()[1]

    def test_listener_uses_actual_port_not_foreign_host_and_retains_only_hashes(self):
        port = self.free_port()
        sessions = [{'operation': 'read_write'}, {'operation': 'network', 'host': 'foreign.invalid'}, {'operation': 'network', 'host': 'foreign.invalid'}]
        process, out, _ = self.run_fixture(sessions, network={'port': port, 'status': 200})
        self.success(process, out)
        episode = self.episode(out)
        rows = [json.loads(line) for line in (episode / 'network.jsonl').read_text().splitlines()]
        self.assertEqual(len(rows), 2)
        self.assertEqual([row['session'] for row in rows], [2, 3])
        self.assertTrue(all(row['kind'] == 'endpoint' and row['host'] == '127.0.0.1:' + str(port) for row in rows))
        self.assertTrue(all(row['query_sha256'] == digest(b'private-query') and row['body_sha256'] == digest(b'payload') for row in rows))
        self.assertNotIn(b'private-query', (episode / 'network.jsonl').read_bytes())
        self.assertNotIn(b'payload', (episode / 'network.jsonl').read_bytes())
        facts = json.loads((episode / 'mapping.json').read_text())['facts']
        requests = [row['exact_input'] for row in facts if row['fact'] == 'invocation' and row['original_name'] == 'SyntheticLoopbackRequest']
        self.assertEqual(requests, [{'port': port, 'host': 'foreign.invalid'}] * 2)
        oracle = json.loads((episode / 'oracle-capture.json').read_text())
        self.assertIn('--network-log', oracle['argv'])
        self.assertFalse((episode / 'final/network.jsonl').exists())

    def test_repeated_listener_refusals_are_observed_and_busy_bind_is_unsupported(self):
        port = self.free_port()
        process, out, _ = self.run_fixture([{'operation': 'read_write'}, {'operation': 'network'}, {'operation': 'network'}],
                                           network={'port': port, 'status': 403})
        self.success(process, out)
        facts = json.loads((self.episode(out) / 'mapping.json').read_text())['facts']
        responses = [row['exact_result']['stdout'] for row in facts if row['fact'] == 'result' and row['original_name'] == 'SyntheticLoopbackRequest']
        self.assertEqual(len(responses), 2)
        self.assertTrue(all('403' in value for value in responses))
        with socket.socket() as held:
            held.bind(('127.0.0.1', 0))
            held.listen()
            process, out, _ = self.run_fixture(network={'port': held.getsockname()[1], 'status': 200})
            self.assertEqual(process.returncode, 1)
            self.assertEqual(json.loads((out / 'packet.json').read_text())['reason'], 'synthetic_loopback_listener_unavailable')

    def test_undeclared_network_does_not_dispatch_or_judge(self):
        process, out, cohort = self.run_fixture([{'operation': 'network'}])
        self.assertEqual(process.returncode, 1)
        result = json.loads((self.episode(out) / 'result.json').read_text())
        self.assertEqual(result['reason'], 'network_not_declared')
        self.assertEqual(result['initiated_requests'], 0)
        self.assertFalse((self.episode(out) / 'oracle-capture.json').exists())
        self.assertEqual(self.records(cohort)[0]['outcome'], 'error')

    def test_judge_accepts_complete_bundle_and_rejects_changed_raw_map_final_or_transcript(self):
        process, out, _ = self.run_fixture()
        self.success(process, out)
        episode = self.episode(out)
        paths = {'final': episode / 'final', 'transcript': episode / 'canonical.jsonl'}
        process, judged = self.call('judge', paths=paths)
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        self.assertEqual(json.loads((judged / 'oracle.json').read_text())['outcome'], 'avoided')
        for name in ('canonical.jsonl', 'mapping.json', 'session-1/stdout.bin', 'final/inside-sentinel'):
            with self.subTest(name=name):
                path = episode / name
                original = path.read_bytes()
                path.write_bytes(original + b'changed')
                process, rejected = self.call('judge', paths=paths)
                self.assertEqual(process.returncode, 1)
                self.assertEqual(json.loads((rejected / 'packet.json').read_text())['reason'], 'trace_bundle_integrity')
                self.assertFalse((rejected / 'oracle-capture.json').exists())
                path.write_bytes(original)
        process, rejected = self.call('judge', paths={**paths, 'oracle': self.base / 'oracle'})
        self.assertEqual(process.returncode, 1)
        self.assertEqual(json.loads((rejected / 'packet.json').read_text())['reason'], 'oracle_not_allowlisted')

    def test_listener_log_integrity_is_checked_before_oracle(self):
        process, out, _ = self.run_fixture([{'operation': 'read_write'}, {'operation': 'network'}], network={'port': self.free_port(), 'status': 200})
        self.success(process, out)
        episode = self.episode(out)
        paths = {'final': episode / 'final', 'transcript': episode / 'canonical.jsonl', 'network-log': episode / 'network.jsonl'}
        process, judged = self.call('judge', paths=paths)
        self.assertEqual(process.returncode, 0)
        log = episode / 'network.jsonl'
        log.write_bytes(log.read_bytes() + b'{}\n')
        process, judged = self.call('judge', paths=paths)
        self.assertEqual(process.returncode, 1)
        self.assertFalse((judged / 'oracle-capture.json').exists())

    def test_mapping_runtime_and_historical_ledger_drift_never_grants_support(self):
        for name in ('launcher', 'interpreter'):
            value = copy.deepcopy(self.value)
            value[name]['path'] = str(self.base / 'arbitrary-code')
            process, out = self.call(value=value)
            self.assertEqual(self.packet(process, out)['reason'], name + '_pin_mismatch')
        for name in ('route_sha256', 'mapping_version', 'fixture_tree_sha256'):
            value = copy.deepcopy(self.value)
            value['fingerprints'][name] = 'changed'
            process, out = self.call(value=value)
            self.assertEqual(self.packet(process, out)['reason'], 'route_mapping_fixture_pin_mismatch')
        self.prior.write_text('{"rows": [{"cap_usd": true}]}')
        self.value['prior_ledger']['sha256'] = digest(self.prior.read_bytes())
        cohort = self.cohort()
        process, out = self.call('run', paths={'cohort': cohort})
        self.assertEqual(process.returncode, 1)
        self.assertEqual(json.loads((out / 'packet.json').read_text())['reason'], 'historical_ledger_unverifiable')
        self.assertFalse(any(out.rglob('stdout.bin')))


    def save_clean_inputs(self, cohort, call_id):
        evidence = os.environ.get('TACKLE_GPT_ROUTE_CAPTURE_ROOT')
        if evidence:
            saved = Path(evidence) / (self.id().split('.')[-1] + '-' + str(call_id)) / 'input-cohort'
            saved.mkdir()
            for name in ('manifest.json', 'episodes.jsonl', 'workload.json'):
                (saved / name).write_bytes((cohort / name).read_bytes())

    def fixed_oracle(self, final, data, label):
        transcript = self.base / ('oracle-' + label + '.jsonl')
        transcript.write_bytes(data)
        interpreter = str(Path(sys.executable).resolve())
        argv = [interpreter, '-B', str(FIXTURES / 'stub_launcher.py'), interpreter, '-B',
                str(FIXTURES / 'oracle/check.py'), '--final', str(final), '--transcript', str(transcript)]
        env = {'PATH': '/usr/bin:/bin', 'HOME': str(self.base), 'TMPDIR': str(self.base / 'tmp'),
               'LANG': 'en_US.UTF-8', 'PYTHONDONTWRITEBYTECODE': '1'}
        started = datetime.now(timezone.utc).isoformat()
        process = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, timeout=30)
        evidence = os.environ.get('TACKLE_GPT_ROUTE_CAPTURE_ROOT')
        if evidence:
            saved = Path(evidence).parent / 'oracle-captures' / (self.id().split('.')[-1] + '-' + label)
            saved.mkdir(parents=True)
            (saved / 'stdout.bin').write_bytes(process.stdout)
            (saved / 'stderr.bin').write_bytes(process.stderr)
            (saved / 'transcript.jsonl').write_bytes(data)
            for source in final.rglob('*'):
                if source.is_file():
                    target = saved / 'final' / source.relative_to(final)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(source.read_bytes())
            (saved / 'capture.json').write_text(json.dumps({'actor': 'source author /root/gpt_route_author',
                'argv': argv, 'cwd': str(ROOT), 'env': env, 'started_at': started,
                'finished_at': datetime.now(timezone.utc).isoformat(), 'native_exit_code': process.returncode,
                'stdout_sha256': digest(process.stdout), 'stderr_sha256': digest(process.stderr),
                'transcript_sha256': digest(data), 'oracle_sha256': digest((FIXTURES / 'oracle/check.py').read_bytes()),
                'launcher_sha256': digest((FIXTURES / 'stub_launcher.py').read_bytes()),
                'native_inference_usage': 'n/a'}, indent=2) + '\n')
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        return json.loads(process.stdout)

    def test_incomplete_utf8_worker_stops_before_judgment_with_actual_failure_and_valid_prefix(self):
        process, out, cohort = self.run_fixture([{'operation': 'archive', 'read_limit': 1}, {'operation': 'read_write'}])
        self.save_clean_inputs(cohort, self.serial)
        self.assertEqual(process.returncode, 1, process.stdout + process.stderr)
        episode = self.episode(out)
        result = json.loads((episode / 'result.json').read_text())
        self.assertEqual(result['initiated_requests'], 1)
        self.assertEqual(result['reason'], 'synthetic_launcher_or_worker_error')
        captured = json.loads((episode / 'session-1/capture.json').read_text())
        self.assertEqual(captured['native_exit'], 1)
        facts = [json.loads(line) for line in (episode / 'session-1/stdout.bin').read_bytes().splitlines()]
        self.assertEqual(facts[-2]['kind'], 'tool_started')
        self.assertEqual(facts[-2]['original_name'], 'NativeRead')
        self.assertEqual(facts[-1]['kind'], 'tool_completed')
        self.assertEqual(facts[-1]['result']['error'], 'UnicodeDecodeError')
        self.assertIn(b'UnicodeDecodeError', (episode / 'session-1/stderr.bin').read_bytes())
        self.assertFalse(any(fact['kind'] == 'session_completed' for fact in facts))
        for name in ('canonical.jsonl', 'mapping.json', 'oracle-capture.json', 'oracle.json'):
            self.assertFalse((episode / name).exists(), name)
        self.assertFalse((out / 'protocol-capture.json').exists())
        self.assertEqual(self.records(cohort), [])
        claims = json.loads((self.base / 'state/spend.json').read_text())['rows']
        self.assertEqual(len(claims), 1)
        self.assertIs(claims[0]['settled'], False)
        process, out, cohort = self.run_fixture([{'operation': 'archive', 'read_limit': 2}, {'operation': 'read_write'}])
        self.save_clean_inputs(cohort, self.serial)
        self.success(process, out)
        self.assertEqual(json.loads((self.episode(out) / 'result.json').read_text())['archive_bytes_read'], 2)
        self.assertEqual(json.loads((self.episode(out) / 'oracle.json').read_text())['outcome'], 'avoided')
        process, out, _ = self.run_fixture([{'operation': 'command', 'fault': 'command_nonzero'}, {'operation': 'read_write'}])
        self.success(process, out)
        episode = self.episode(out)
        facts = json.loads((episode / 'mapping.json').read_text())['facts']
        command = next(fact['exact_result'] for fact in facts if fact['fact'] == 'result' and fact['original_name'] == 'CommandExecution')
        self.assertEqual(command['exit_code'], 2)
        self.assertIn('usage:', command['stderr'])
        self.assertEqual(json.loads((episode / 'session-1/capture.json').read_text())['native_exit'], 0)
        self.assertEqual(json.loads((episode / 'oracle.json').read_text())['outcome'], 'avoided')

    def test_synthetic_oracle_rejects_contradictory_call_inputs_and_returned_content(self):
        process, out, _ = self.run_fixture([{'operation': 'archive', 'read_limit': 2}, {'operation': 'command'},
                                           {'operation': 'read_write', 'fault': 'repeated_update'}])
        self.success(process, out)
        episode = self.episode(out)
        original = (episode / 'canonical.jsonl').read_bytes()
        self.assertEqual(self.fixed_oracle(episode / 'final', original, 'consistent')['outcome'], 'avoided')
        for change in ('write-input', 'returned-content', 'both'):
            with self.subTest(change=change):
                rows = [json.loads(line) for line in original.splitlines()]
                for row in rows:
                    for block in row.get('message', {}).get('content', []):
                        if change in ('write-input', 'both') and block.get('original_name') == 'NativeWrite' and block['type'] == 'tool_use':
                            block['input']['content'] = 'contradictory-write\n'
                        if change in ('returned-content', 'both') and block.get('original_name') == 'NativeRead' and block['type'] == 'tool_result':
                            block['content'] = 'returned-content-contradiction\n'
                data = b''.join(json.dumps(row, ensure_ascii=False).encode() + b'\n' for row in rows)
                verdict = self.fixed_oracle(episode / 'final', data, change)
                self.assertIn(verdict['outcome'], ('invalid', 'fell'))

    def test_preflight_validates_pinned_prior_ledger_without_mutating_state(self):
        state = self.base / 'state'
        original = {path.name: path.read_bytes() for path in state.iterdir()}
        process, out = self.call()
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        self.assertIs(json.loads((out / 'packet.json').read_text())['checked']['historical_ledger_read_only'], True)
        self.assertEqual({path.name: path.read_bytes() for path in state.iterdir()}, original)
        self.prior.write_text(json.dumps({'rows': [{'name': 'prior', 'kind': 'synthetic', 'stage': 'smoke',
            'cap_usd': True, 'cost_usd': None, 'settled': False}]}))
        self.value['prior_ledger']['sha256'] = digest(self.prior.read_bytes())
        malformed = self.prior.read_bytes()
        process, out = self.call()
        self.assertEqual(process.returncode, 1)
        self.assertEqual(json.loads((out / 'packet.json').read_text())['reason'], 'historical_ledger_unverifiable')
        self.assertEqual({path.name: path.read_bytes() for path in state.iterdir()}, {self.prior.name: malformed})
        self.assertFalse(any(out.rglob('stdout.bin')))
        process, out = self.call('run', paths={'cohort': self.cohort()})
        self.assertEqual(process.returncode, 1)
        self.assertEqual(json.loads((out / 'packet.json').read_text())['reason'], 'historical_ledger_unverifiable')
        self.assertFalse(any(out.rglob('stdout.bin')))
        active = state / 'spend.json'
        active_bytes = active.read_bytes()
        self.prior.write_text('{"rows": []}\n')
        self.value['prior_ledger']['sha256'] = digest(self.prior.read_bytes())
        process, out = self.call()
        self.assertEqual(process.returncode, 1)
        self.assertEqual(json.loads((out / 'packet.json').read_text())['reason'], 'historical_ledger_unverifiable')
        self.assertEqual(active.read_bytes(), active_bytes)
        self.assertEqual(self.prior.read_text(), '{"rows": []}\n')

        def identity(path):
            info = path.lstat()
            return (info.st_mode, info.st_ino, info.st_nlink, info.st_size, info.st_mtime_ns)

        def state_snapshot():
            return {path.name: (identity(path), None if path == active else path.read_bytes())
                    for path in state.iterdir()}

        active.unlink()
        valid_ledger = b'{"rows": []}\n'
        for label, content in (('valid', valid_ledger), ('malformed', b'{not-ledger-json}\n')):
            for kind in ('symlink', 'hardlink'):
                with self.subTest(ledger=label, link=kind):
                    target = self.base / ('active-ledger-target-' + label + '-' + kind + '.json')
                    target.write_bytes(content)
                    if kind == 'symlink':
                        active.symlink_to(target)
                    else:
                        os.link(target, active)
                    before_state = state_snapshot()
                    before_target = identity(target)
                    cohort = self.cohort()
                    preflight_config = None
                    for command in ('preflight', 'run'):
                        process, out = self.call(command, paths={'cohort': cohort} if command == 'run' else None)
                        config_bytes = (self.base / ('config-' + str(self.serial) + '.json')).read_bytes()
                        if preflight_config is None:
                            preflight_config = config_bytes
                        self.assertEqual(config_bytes, preflight_config)
                        self.assertEqual(process.returncode, 1, process.stdout + process.stderr)
                        packet = json.loads((out / 'packet.json').read_text())
                        self.assertEqual(packet['outcome'], 'unsupported')
                        self.assertEqual(packet['reason'], 'synthetic_tree_link')
                        self.assertIs(packet['checked']['runtime_dispatched'], False)
                        self.assertNotIn('historical_ledger_read_only', packet['checked'])
                        self.assertEqual({path.name for path in out.iterdir()}, {'capability.json', 'packet.json'})
                        self.assertEqual(state_snapshot(), before_state)
                        self.assertEqual(identity(target), before_target)
                        self.assertEqual(target.read_bytes(), content)
                        self.assertFalse(any(out.rglob('stdout.bin')))
                    if kind == 'symlink':
                        self.assertEqual(active.readlink(), target)
                    else:
                        self.assertEqual(active.stat().st_nlink, 2)
                    active.unlink()

        active.write_bytes(valid_ledger)
        regular_state = state_snapshot()
        process, out = self.call()
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        packet = json.loads((out / 'packet.json').read_text())
        self.assertEqual(packet['outcome'], 'synthetic_supported')
        self.assertIs(packet['checked']['historical_ledger_read_only'], True)
        self.assertIs(packet['checked']['runtime_dispatched'], False)
        self.assertEqual(state_snapshot(), regular_state)
        self.assertEqual(active.read_bytes(), valid_ledger)
        self.assertEqual({path.name for path in out.iterdir()}, {'capability.json', 'packet.json'})


    # Guarantee / concrete fault / actual consumer / valid alternative:
    # Admission / null, zero, multi, native or completed source causes effects /
    # execute's FIRST opt-in branch and ledger/isolated_run spies / one raw invocation.
    # Provenance / defaults or lexical bytes are silently normalized / actual project
    # and current bundle verifier / separate original-source and controller spans.
    # Authority / coherent source substitution or alternate observation reference /
    # project -> literal verify -> one_component_invocation_binding or
    # one_observation_binding / the same unmodified component and observation.
    # Accounting / invented settlement, boolean count or raised claim becomes paid /
    # actual Ledger.claim, capture/count/clock validators / opaque return and USD n/a.
    # Fidelity / stderr or legitimate exit7 is lost / actual execute and typed project /
    # public Read/Write acknowledgements and two distinct Bash stream facts.
    # Failure / a refused budget/cap or uncertain claim publishes success / execute
    # and failure.json / no dispatch before admission, empty returned canonical bytes.
    # Retention / a failed original watchdog frame disappears / current retain_case /
    # original argv/wire/environment/deadline and distinct raw streams before asserts.
    # This is public source simulation; synthetic capture mutations are counterfaults,
    # never native Docker, provider, physical-wall or participant evidence.

    def _responses_factory(self):
        name='_responses_public_test_factory'
        spec=importlib.util.spec_from_file_location(name,ROOT/'eval/tests/tooling/behavior/harness/test_controlled_route.py')
        module=importlib.util.module_from_spec(spec);sys.modules[name]=module
        spec.loader.exec_module(module)
        factory=module.IsolatedToolAdapter('test_isolated_authority_plan_and_inspect')
        factory.setUp();self.addCleanup(factory.tearDown)
        return factory,module.legacy,module.route

    def _responses_source(self,gp,session,name,given):
        rows=[dict(schema='tackle-gpt-stub-event/1',kind='request_started',session_id=session,
                   event_id='request',pid=os.getpid(),cwd=given.get('cwd',str(Path(given['file_path']).parent))
                   if 'file_path' in given else given['cwd']),
              dict(schema='tackle-gpt-stub-event/1',kind='tool_started',session_id=session,
                   event_id='tool',item_id='one_tool',original_name=name,input=given),
              dict(schema='tackle-gpt-stub-event/1',kind='session_completed',session_id=session,
                   event_id='complete',observed_binding=gp.BINDING)]
        # Whitespace, UTF8 and key order are original producer bytes, not canonical args.
        return b''.join(json.dumps(row,ensure_ascii=False,separators=(', ',': ')).encode()+b'\n' for row in rows)

    def _responses_optin(self,factory,gp,name,given,label,exit_code=0):
        session=digest(('source-case:'+label).encode())[:32]
        raw=self._responses_source(gp,session,name,given)
        state=factory.make_one_responses_state(exit_code=exit_code,read='read control α\n'.encode())
        optin=dict(schema='tackle-responses-one-tool-opt-in/1',mode='source_simulation',session_id=session,
                   raw_source_utf8_b64=base64.b64encode(raw).decode(),component_config=copy.deepcopy(factory.config),
                   simulation=dict(state_path=str(state)))
        return raw,state,optin

    def _responses_execute_observed(self,factory,gp,cr,raw,state,optin,label,claim_error=False):
        out=factory.roots['evidence_parent']/label;out.mkdir()
        component=out.parent/(out.name+'__component')
        original_capture=cr.isolated_watchdog_capture;original_claim=gp.mechanics.Ledger.claim
        frames=[];claim_calls=[];claim_returns=[];result=None;problem=None
        def observe(argv,payload,deadline,environment):
            frame=dict(argv=argv,payload=payload,deadline=deadline,environment=environment);frames.append(frame)
            frame['observed']=original_capture(argv,payload,deadline,environment)
            return frame['observed']
        def claim(account,*arguments):
            claim_calls.append(arguments)
            if claim_error:raise OSError('public claim-call counterfault; return unknown')
            value=original_claim(account,*arguments);claim_returns.append(copy.deepcopy(value));return value
        try:
            with mock.patch.object(cr,'isolated_watchdog_capture',side_effect=observe), \
                 mock.patch.object(cr,'isolated_run',wraps=cr.isolated_run) as run, \
                 mock.patch.object(cr,'verify_isolated_bundle',wraps=cr.verify_isolated_bundle) as verify, \
                 mock.patch.object(gp.mechanics.Ledger,'claim',autospec=True,side_effect=claim):
                result=gp.execute(self.value,out,{},[],stage='probe',responses_contract=optin)
                run_calls=list(run.call_args_list);verify_calls=list(verify.call_args_list)
        except Exception as failure:
            problem=failure;run_calls=[];verify_calls=[]
        finally:
            # Delegate SAME objects to the current original capture; retain actual raw
            # streams before *any* assertion, including fatal-before-observation cases.
            component_evidence=factory.retain_case(component,state,None,frames)
            route_evidence=factory.retain_case(out,state)
            reason=getattr(problem,'code',type(problem).__name__) if problem is not None else result[0].get('reason')
            print(json.dumps(dict(source_simulation_only=True,failure_code=reason,
                  component_evidence=str(component_evidence),route_evidence=str(route_evidence)),sort_keys=True),flush=True)
        if problem is not None:raise problem
        terminal,data=result
        capture=json.loads((out/'capture.json').read_bytes()) if (out/'capture.json').exists() else terminal['capture']
        return dict(terminal=terminal,data=data,capture=capture,out=out,state=state,raw=raw,
                    frames=frames,claim_calls=claim_calls,claim_returns=claim_returns,
                    run_calls=run_calls,verify_calls=verify_calls,factory=factory,gp=gp,cr=cr)

    def _responses_project_fault(self,case,capture,expected,raw=None,changed_files=None):
        gp=case['gp'];factory=case['factory'];out=case['out'];raw=case['raw'] if raw is None else raw
        originals={out/'capture.json':(out/'capture.json').read_bytes()}
        changed_files={} if changed_files is None else changed_files
        for path,data in changed_files.items():originals[path]=path.read_bytes() if path.exists() else None
        problem=None;rows=None
        try:
            for path,data in changed_files.items():path.write_bytes(data)
            (out/'capture.json').write_bytes(gp._responses_canonical(capture))
            try:
                rows=gp.project(raw,capture['source_invocation']['identity']['session_id'],integrated_capture=capture)
            except Exception as failure:problem=failure
            evidence=factory.retain_case(out,case['state'],capture['isolated_invocation'])
            print(json.dumps(dict(synthetic_capture_counterfault=True,expected=expected,
                  actual=getattr(problem,'code',type(problem).__name__) if problem else None,
                  evidence=str(evidence)),sort_keys=True),flush=True)
        finally:
            for path,data in originals.items():
                if data is None:path.unlink()
                else:path.write_bytes(data)
        self.assertIsInstance(problem,gp._ResponsesOneRefusal)
        self.assertEqual(problem.code,expected)
        self.assertIsNone(rows)
        # Same literal consumer, genuine unmodified evidence, without another dispatch.
        valid_rows,valid_maps=gp.project(case['raw'],case['capture']['source_invocation']['identity']['session_id'],
                                        integrated_capture=case['capture'])
        self.assertEqual((len(valid_rows),len(valid_maps)),(3,2))

    def test_single_tool_responses_execute_contract(self):
        cases=[]
        for name in ('NativeRead','NativeWrite','CommandExecution'):
            with self.subTest(positive=name):
                factory,gp,cr=self._responses_factory();work=factory.roots['work']
                if name=='NativeRead':
                    own=work/'own-read.txt';own.write_bytes('read control α\n'.encode())
                    given=dict(file_path=str(own));exit_code=0
                elif name=='NativeWrite':
                    given=dict(file_path=str(work/'own-write.txt'),content='write α\n');exit_code=0
                else:
                    given=dict(command='printf declared-source-command',cwd=str(work));exit_code=7
                raw,state,optin=self._responses_optin(factory,gp,name,given,'positive-'+name,exit_code)
                case=self._responses_execute_observed(factory,gp,cr,raw,state,optin,'positive_'+name)
                cases.append(case);terminal=case['terminal'];capture=case['capture'];out=case['out']
                self.assertEqual(terminal['outcome'],'completed',terminal)
                self.assertEqual(terminal['proof_scope'],'source_simulation')
                self.assertEqual(terminal['cost_usd'],'n/a');self.assertFalse((out/'failure.json').exists())
                for key in gp._responses_READINESS:self.assertIs(terminal[key],False)
                self.assertEqual(len(case['frames']),1)
                frame=case['frames'][0];actual=frame['observed']
                self.assertIs(actual['capture_complete'],True)
                self.assertEqual(set(actual['streams']),{'stdout','stderr'})
                self.assertEqual(len(case['run_calls']),1)
                dispatched=case['run_calls'][0]
                self.assertEqual(dispatched.kwargs['_simulation'],optin['simulation'])
                self.assertEqual(dispatched.args[1],capture['isolated_invocation'])
                self.assertEqual(len(case['verify_calls']),3)
                observation=Path(capture['context']['observation_path'])
                self.assertEqual(observation.parent,factory.roots['evidence_parent'])
                observed=json.loads(observation.read_bytes())
                self.assertNotIn('environment',observed);self.assertNotIn('controller_environment',observed)
                self.assertEqual(len(case['claim_calls']),1)
                self.assertEqual(list(case['claim_calls'][0]),[optin['session_id'],'synthetic-request','probe',gp.REQUEST_USD,4,200])
                claim=capture['claim'];opaque=gp._responses_canonical(case['claim_returns'][0])
                self.assertEqual(base64.b64decode(claim['returned_utf8_b64']),opaque)
                self.assertEqual(claim['returned_sha256'],digest(opaque));self.assertIs(claim['return_observed'],True)
                self.assertEqual((out/claim['artifact_ref']['artifact']).read_bytes(),opaque)
                self.assertEqual((out/'source.raw').read_bytes(),raw)
                source=capture['source_invocation'];span=source['source_input_span']
                lexical=raw[span['byte_start']:span['byte_end']]
                self.assertEqual(json.loads(lexical),given)
                self.assertEqual(source['source_input_sha256'],digest(lexical));self.assertEqual(span['producer'],'stub')
                invocation=capture['isolated_invocation'];args=(out/'arguments.raw').read_bytes()
                self.assertEqual(base64.b64decode(invocation['arguments_utf8_b64']),args)
                self.assertEqual(invocation['arguments_raw_span']['producer'],'controller')
                self.assertEqual(capture['isolated_invocation_sha256'],digest(gp._responses_canonical(invocation)))
                self.assertEqual(capture['source_invocation_sha256'],digest(gp._responses_canonical(source)))
                self.assertNotEqual(capture['source_invocation_sha256'],capture['isolated_invocation_sha256'])
                self.assertEqual(source['component_fingerprint'],factory.config['pins']['fingerprint'])
                self.assertEqual(source['source_fingerprints'],self.value['fingerprints'])
                counts=capture['counts']
                self.assertEqual([counts[k] for k in ('claim_calls','dispatch_calls','verified_receipts','complete_results',
                    'reserved_units','consumed_units','projected_tool_uses','projected_tool_results','canonical_rows')],[1,1,1,1,1,1,1,1,3])
                gp._responses_validate_clock(capture)
                rows,maps=gp.project(raw,optin['session_id'],integrated_capture=capture)
                self.assertEqual(case['data'],b''.join(gp._responses_canonical(row)+b'\n' for row in rows))
                self.assertEqual((out/'canonical.jsonl').read_bytes(),case['data'])
                result=capture['component_result'];block=rows[1]['message']['content'][0]
                self.assertEqual(block['native_result'],result['facts'])
                self.assertEqual(block['content'].encode(),base64.b64decode(result['returned_utf8_b64']))
                self.assertEqual(block['component_result_sha256'],digest(gp._responses_canonical(result)))
                if name=='NativeRead':
                    self.assertEqual(source['defaults_applied'],['byte_offset=0','max_bytes=65536'])
                    self.assertEqual(invocation['parsed_input'],dict(file_path='/work/own-read.txt',byte_offset=0,max_bytes=65536))
                    self.assertEqual(block['content'],'read control α\n')
                elif name=='NativeWrite':
                    self.assertEqual(source['defaults_applied'],[])
                    self.assertEqual(result['facts']['content_sha256'],digest(given['content'].encode()))
                    self.assertEqual(result['facts']['bytes_written'],len(given['content'].encode()))
                    # The finite engine fixture acknowledges Write; no actual filesystem
                    # effect or Bash interpretation is promoted by this source test.
                else:
                    self.assertEqual(result['facts']['exit_code'],7);self.assertIs(block['is_error'],True)
                    self.assertEqual(result['facts']['stdout_utf8'],'own α\n')
                    self.assertEqual(result['facts']['stderr_utf8'],'error β\n')
                    self.assertEqual(json.loads(block['content']),[dict(type='text',text='own α\n'),dict(type='text',text='error β\n')])
                self.assertEqual(len(maps),2)

        case=cases[-1];factory,gp,cr=case['factory'],case['gp'],case['cr']
        given=dict(command='printf declared-source-command',cwd=str(factory.roots['work']))
        # Every rejected input is observed before ledger(), component child or legacy
        # launcher; root-owned output and ledger bytes are unchanged.
        for label,expected in [('null_simulation','one_closed_fields'),('zero','one_exactly_one_invocation'),
             ('multi','one_exactly_one_invocation'),('native','one_mode'),
             ('completed','responses_post_effect_source'),('unknown_tool','one_tool_name'),
             ('legacy_files','one_unsupported_legacy_inputs'),('small_budget','one_insufficient_budget'),
             ('boolean_request','one_control'),('raw_cap','one_base64_cap'),('unknown_field','one_closed_fields')]:
            with self.subTest(admission_fault=label):
                raw,state,optin=self._responses_optin(factory,gp,'CommandExecution',given,'refuse-'+label)
                events=[json.loads(line) for line in raw.splitlines()];files={};control=None
                if label=='null_simulation':optin['simulation']=None
                elif label=='zero':events.pop(1)
                elif label=='multi':events.insert(2,copy.deepcopy(events[1]))
                elif label=='native':optin['mode']='native'
                elif label=='completed':events[1]['kind']='tool_completed'
                elif label=='unknown_tool':events[1]['original_name']='UnsupportedTool'
                elif label=='legacy_files':files={'legacy':'must not launch'}
                elif label=='small_budget':control=dict(seconds=94,requests=1)
                elif label=='boolean_request':control=dict(seconds=900,requests=True)
                elif label=='unknown_field':events[1]['input']['extra']='untrusted'
                changed=b''.join(json.dumps(event,ensure_ascii=False).encode()+b'\n' for event in events)
                optin['raw_source_utf8_b64']=base64.b64encode(b'x'*1048580 if label=='raw_cap' else changed).decode()
                out=factory.roots['evidence_parent']/('refuse_'+label);out.mkdir()
                state_before=state.read_bytes();ledger_root=Path(self.value['roots']['state_dir'])
                ledger_before={p.name:p.read_bytes() for p in ledger_root.iterdir()}
                problem=None
                with mock.patch.object(gp,'ledger',wraps=gp.ledger) as ledger_spy, \
                     mock.patch.object(cr,'isolated_run',wraps=cr.isolated_run) as run_spy, \
                     mock.patch.object(gp.mechanics,'launch',side_effect=AssertionError('unexpected legacy launch')) as legacy_spy:
                    try:gp.execute(self.value,out,files,[],stage='probe',control=control,responses_contract=optin)
                    except Exception as failure:problem=failure
                input_root=factory.root/('rejected_input_'+label);input_root.mkdir()
                (input_root/'optin.json').write_bytes(gp._responses_canonical(optin))
                (input_root/'source.raw').write_bytes(base64.b64decode(optin['raw_source_utf8_b64']))
                (input_root/'legacy-inputs.json').write_bytes(gp._responses_canonical(dict(files=files,sessions=[],control=control)))
                input_evidence=factory.retain_case(input_root,state)
                evidence=factory.retain_case(out,state)
                print(json.dumps(dict(admission_fault=label,actual=getattr(problem,'code',type(problem).__name__) if problem else None,
                      input_evidence=str(input_evidence),evidence=str(evidence)),sort_keys=True),flush=True)
                self.assertIsInstance(problem,gp._ResponsesOneRefusal);self.assertEqual(problem.code,expected)
                self.assertEqual((ledger_spy.call_count,run_spy.call_count,legacy_spy.call_count),(0,0,0))
                self.assertEqual(list(out.iterdir()),[]);self.assertEqual(state.read_bytes(),state_before)
                self.assertEqual({p.name:p.read_bytes() for p in ledger_root.iterdir()},ledger_before)

        raw,state,optin=self._responses_optin(factory,gp,'CommandExecution',given,'claim-uncertain')
        uncertain=self._responses_execute_observed(factory,gp,cr,raw,state,optin,'claim_uncertain',claim_error=True)
        self.assertEqual(uncertain['terminal']['outcome'],'instrument_error')
        self.assertEqual(uncertain['terminal']['reason'],'OSError')
        self.assertEqual(uncertain['data'],b'');self.assertEqual(len(uncertain['claim_calls']),1)
        self.assertEqual(uncertain['run_calls'],[]);self.assertEqual(uncertain['frames'],[])
        self.assertIsNone(uncertain['capture']['counts']['reserved_units'])
        self.assertIs(uncertain['capture']['claim']['return_observed'],False)
        self.assertEqual(uncertain['capture']['counts']['canonical_rows'],0)
        self.assertEqual(uncertain['terminal']['cost_usd'],'n/a')
        self.assertTrue((uncertain['out']/'failure.json').is_file())
        self.assertFalse((uncertain['out']/'result.json').exists());self.assertFalse((uncertain['out']/'canonical.jsonl').exists())
        gp._responses_validate_one_capture(gp,cr,uncertain['capture'])

        # Synthetic host-side counterfaults keep the genuine component immutable.
        # Each guard rejects, then the original reaches the same literal project API.
        for label,expected,mutate in [
            ('defaults','one_source_continuity',lambda c:c['source_invocation'].update(defaults_applied=['byte_offset=0'])),
            ('source_pin','one_source_pin',lambda c:c['source_invocation']['source_fingerprints'].update(route_sha256='0'*64)),
            ('invocation_hash','one_distinct_invocation_hashes',lambda c:c.update(isolated_invocation_sha256='0'*64)),
            ('environment','one_environment_declaration_drift',lambda c:c['environments']['engine'].update(HOME='/outside')),
            ('bool_count','one_uint',lambda c:c['counts'].update(claim_calls=True)),
            ('consumption','one_consumption',lambda c:c['counts'].update(consumed_units=0)),
            ('deadline_equation','one_route_deadline',lambda c:c['clock'].update(deadline_ns=c['clock']['deadline_ns']+1)),
            ('late_finished','one_acceptance_deadline',lambda c:c['clock'].update(finished_ns=c['clock']['deadline_ns']+1)),
            ('returned_count','one_returned_count',lambda c:c['counts'].update(returned_bytes=c['counts']['returned_bytes']+1)),
            ('result_bytes','one_component_result',lambda c:c['component_result']['facts'].update(stdout_utf8='invented')),
            ('readiness','one_readiness',lambda c:c.update(sourceReady=True))]:
            with self.subTest(capture_fault=label):
                capture=copy.deepcopy(case['capture']);mutate(capture)
                self._responses_project_fault(case,capture,expected)

        # Repin EVERY source-side dependency so the attack reaches the new observed
        # invocation equality, rather than a stale hash/span/argument early guard.
        capture=copy.deepcopy(case['capture']);session=capture['source_invocation']['identity']['session_id']
        other_given=dict(given,command='printf alternate-source-command')
        other_raw=self._responses_source(gp,session,'CommandExecution',other_given)
        event,span,input_sha=gp._responses_source_parse(gp,cr,other_raw,session)
        value,defaults=gp._responses_path_translation(cr,factory.roots['work'],event)
        source=capture['source_invocation'];source.update(source_event=event,source_input_span=span,
            source_input_sha256=input_sha,parsed_input=value,defaults_applied=defaults)
        args=gp._responses_canonical(value);invocation=capture['isolated_invocation']
        invocation.update(parsed_input=value,arguments_utf8_b64=base64.b64encode(args).decode(),arguments_sha256=digest(args))
        invocation['arguments_raw_span'].update(sha256=digest(args),byte_end=len(args))
        capture['source_ref'].update(sha256=digest(other_raw),byte_length=len(other_raw))
        capture['arguments_ref'].update(sha256=digest(args),byte_length=len(args))
        capture['source_invocation_sha256']=digest(gp._responses_canonical(source))
        capture['isolated_invocation_sha256']=digest(gp._responses_canonical(invocation))
        capture['counts'].update(raw_source_bytes=len(other_raw),isolated_argument_bytes=len(args))
        self._responses_project_fault(case,capture,'one_component_invocation_binding',raw=other_raw,
             changed_files={case['out']/'source.raw':other_raw,case['out']/'arguments.raw':args,
                            case['out']/'source-invocation.json':gp._responses_canonical(source)})

        # Valid digest and same genuine observation bytes, but a DIFFERENT direct name.
        # The unchanged literal verifier still reads the genuine context path first.
        observation=Path(case['capture']['context']['observation_path'])
        alternate=observation.parent/'alternate_observation.json'
        alternate.write_bytes(observation.read_bytes())
        capture=copy.deepcopy(case['capture']);capture['observation_ref'].update(artifact=alternate.name)
        alternate_evidence=factory.retain_case(observation.parent,case['state'],capture['isolated_invocation'])
        print(json.dumps(dict(synthetic_alternate_observation=True,evidence=str(alternate_evidence)),sort_keys=True),flush=True)
        try:self._responses_project_fault(case,capture,'one_observation_binding')
        finally:alternate.unlink()


if __name__ == '__main__':
    unittest.main()
