"""Pinned synthetic measurement route. Live GPT transport always fails closed.

The fixed fixture launcher is a tool-wrapper control, not an OS sandbox claim.
"""

import argparse
import base64
import stat
from decimal import Decimal
import controlled_route
import hashlib
import json
import os
from pathlib import Path
import fcntl
import math
import re
import shutil
import signal
import sys
import time
import uuid
from types import SimpleNamespace

import harness
import subscription_route as mechanics
import network_listener


HERE = Path(__file__).resolve().parent
FIXTURES = HERE / 'fixtures' / 'gpt-route'
MAPPING = 'tackle-gpt-stub-map/1'
CAPABILITIES = {
    'isolation': 'stub-isolation/1',
    'auth': 'stub-auth-separated/1',
    'limiter': 'stub-request-limiter/1',
    'trace': MAPPING,
    'network': 'stub-loopback-log/1',
}
CAPS = {'total_usd': 200, 'episode': {'usd': 8, 'seconds': 900, 'request_units': 60},
        'stages': {'smoke': 25, 'held-out': 121}, 'probe_usd': 4}
BINDING = {'model': 'gpt-6-luna', 'requested_host_effort': 'xhigh'}
FILES = ('stub_cli.py', 'stub_launcher.py', 'sentinel_helper.py', 'oracle/check.py')
TRUSTED = {'oracle/check.py': 'aff0b5f2af644826bbb4b439176e359ba4c5ed50cc6a5f5cd38d27698c473211', 'sentinel_helper.py': 'c5a9149e2bb34fbe12332a66b34c8c1d72573c6b26421353deb171462f6e3bd2', 'stub_cli.py': 'd0c1673bf9f20e4c03deb32cf0dec1038795aaf884e54e795dadfda6aac47699', 'stub_launcher.py': 'f43979db6b2dfb3e83ed07334ce805a41e27f59932c72c66462f3a0e3fc7e141'}
REQUEST_USD = 0.1  # Fixed synthetic reservation; not provider pricing or observed billing.
MARKER = 'synthetic sensitive+"marker'
NA = 'n/a'


class Refused(Exception):
    pass


class StopEpisode(Exception):
    def __init__(self, reason, outcome='error'):
        self.reason, self.outcome = reason, outcome


class Malformed(Exception):
    pass


def sha(data):
    return hashlib.sha256(data).hexdigest()


def unique(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise Malformed('duplicate_config_key')
        value[key] = item
    return value


def reject_constant(value):
    raise Malformed('nonfinite_config_number')


def closed(value, names):
    if not isinstance(value, dict) or set(value) != set(names):
        raise Malformed('config_fields')


def same_numbers(actual, expected):
    if isinstance(expected, dict):
        closed(actual, expected)
        return all(same_numbers(actual[key], item) for key, item in expected.items())
    return type(actual) in (int, float) and actual == expected


def config(path):
    try:
        value = json.loads(Path(path).read_bytes(), object_pairs_hook=unique, parse_constant=reject_constant)
    except (OSError, ValueError, UnicodeDecodeError):
        raise Malformed('config_unreadable') from None
    closed(value, ('schema', 'mode', 'binding', 'cli', 'launcher', 'interpreter', 'fingerprints',
                   'roots', 'capabilities', 'prior_ledger', 'caps', 'oracle'))
    if value['schema'] != 'tackle-gpt-route-config/1' or value['mode'] not in ('synthetic', 'live'):
        raise Malformed('config_schema')
    closed(value['binding'], BINDING)
    if value['binding'] != BINDING:
        raise Malformed('requested_binding')
    for name in ('cli', 'launcher', 'interpreter'):
        closed(value[name], ('path', 'sha256', 'version'))
        if not all(isinstance(item, str) and item for item in value[name].values()):
            raise Malformed('config_pin_fields')
    closed(value['fingerprints'], ('route_sha256', 'mapping_version', 'fixture_tree_sha256'))
    closed(value['roots'], ('run_root', 'state_dir'))
    closed(value['capabilities'], CAPABILITIES)
    if not all(item is None or isinstance(item, str) for item in value['capabilities'].values()):
        raise Malformed('config_capability_fields')
    closed(value['prior_ledger'], ('path', 'sha256'))
    closed(value['oracle'], ('launcher_sha256', 'interpreter_sha256', 'seconds'))
    if not same_numbers(value['caps'], CAPS) or type(value['oracle']['seconds']) not in (int, float):
        raise Malformed('config_caps')
    if not 0 < value['oracle']['seconds'] <= 900:
        raise Malformed('config_oracle_seconds')
    return value


def canonical(path):
    if not isinstance(path, str):
        raise Malformed('config_path')
    given = Path(path)
    if not given.is_absolute() or given != given.resolve() or given.is_symlink():
        raise Malformed('config_path')
    return given


def fixture_digest():
    return sha(b''.join(name.encode() + b'\0' + (FIXTURES / name).read_bytes() + b'\0'
                        for name in sorted(FILES)))


def safe_output(configured, out):
    run_root, state_dir = [canonical(configured['roots'][key]) for key in ('run_root', 'state_dir')]
    parent = run_root.parent
    if (parent != state_dir.parent or not parent.name.startswith('tackle-gpt-route-')
            or run_root == state_dir or not run_root.is_dir() or not state_dir.is_dir()
            or not out.is_relative_to(parent) or out.is_relative_to(state_dir) or out == run_root):
        raise Malformed('synthetic_output_scope')


def missing(configured):
    if configured['mode'] == 'live':
        return ['G1_read_native_isolation', 'G2_separated_auth', 'G3_complete_native_trace',
                'G4_pre_request_billable_limiter', 'G5_gpt_network_observation']
    absent = [name + '_unsupported' for name, expected in CAPABILITIES.items()
              if configured['capabilities'][name] != expected]
    if absent:
        return absent
    pinned = {'cli': (FIXTURES / 'stub_cli.py', 'tackle-gpt-stub/1'),
              'launcher': (FIXTURES / 'stub_launcher.py', 'tackle-gpt-stub-launcher/1'),
              'interpreter': (Path(sys.executable).resolve(), sys.version)}
    for name, (expected_path, expected_version) in pinned.items():
        record = configured[name]
        # Check the fixed allowlist before opening a candidate-supplied path.
        if record['path'] != str(expected_path) or record['version'] != expected_version:
            return [name + '_pin_mismatch']
        path = canonical(record['path'])
        if not path.is_file() or sha(path.read_bytes()) != record['sha256']:
            return [name + '_pin_mismatch']
    for name in FILES:
        path = FIXTURES / name
        if path.is_symlink() or not path.is_file() or sha(path.read_bytes()) != TRUSTED.get(name):
            return ['packaged_fixture_pin_mismatch']
    fingerprints = configured['fingerprints']
    if fingerprints != {'route_sha256': sha(Path(__file__).read_bytes()), 'mapping_version': MAPPING,
                        'fixture_tree_sha256': fixture_digest()}:
        return ['route_mapping_fixture_pin_mismatch']
    state_dir = canonical(configured['roots']['state_dir'])
    prior = canonical(configured['prior_ledger']['path'])
    if not prior.is_relative_to(state_dir) or not prior.is_file():
        return ['prior_ledger_unsupported']
    if sha(prior.read_bytes()) != configured['prior_ledger']['sha256']:
        return ['prior_ledger_pin_mismatch']
    if configured['oracle']['launcher_sha256'] != configured['launcher']['sha256']:
        return ['oracle_launcher_pin_mismatch']
    if configured['oracle']['interpreter_sha256'] != configured['interpreter']['sha256']:
        return ['oracle_interpreter_pin_mismatch']
    return []


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def has_sensitive(data):
    """Scan exact bytes and decoded JSON strings without changing retained bytes."""
    found = mechanics.needles(MARKER)
    if mechanics.contains(data, found):
        return True

    def walk(value, depth=0):
        if depth > 64:
            raise Refused('retention_json_depth_unverifiable')
        if isinstance(value, str):
            if mechanics.contains(value.encode('utf-8'), found):
                return True
            if value[:1] in ('{', '[', '"'):
                try:
                    nested = json.loads(value)
                except (ValueError, RecursionError):
                    return False
                return walk(nested, depth + 1)
        elif isinstance(value, dict):
            return any(walk(key, depth + 1) or walk(item, depth + 1) for key, item in value.items())
        elif isinstance(value, list):
            return any(walk(item, depth + 1) for item in value)
        return False

    for line in data.splitlines():
        try:
            value = json.loads(line)
        except (ValueError, UnicodeDecodeError):
            continue
        except RecursionError:
            raise Refused('retention_json_depth_unverifiable') from None
        if walk(value):
            return True
    return False


def tree_sensitive(root):
    if mechanics.token_hits(root, MARKER):
        return True
    return any(has_sensitive(path.read_bytes()) for path in root.rglob('*')
               if not path.is_symlink() and path.is_file())


def scoped(configured, path):
    given = canonical(str(path))
    parent = canonical(configured['roots']['run_root']).parent
    if not given.is_relative_to(parent):
        raise Refused('synthetic_input_outside_root')
    return given


def tree(path):
    files = {}
    for item in sorted(path.rglob('*')):
        if item.is_symlink() or item.is_file() and item.stat().st_nlink != 1:
            raise Refused('synthetic_tree_link')
        if item.is_file():
            files[item.relative_to(path).as_posix()] = item.read_bytes()
    return files


def write_files(root, files):
    for name, data in files.items():
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise Refused('synthetic_tree_path')
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)


def validate_ledger(path):
    """Read the strict synthetic ledger format without creating or changing state."""
    try:
        data = json.loads(path.read_bytes(), object_pairs_hook=unique, parse_constant=reject_constant)
        closed(data, ('rows',))
        if not isinstance(data['rows'], list):
            raise ValueError()
        for row in data['rows']:
            if not isinstance(row, dict) or not all(key in row for key in
                    ('name', 'kind', 'stage', 'cap_usd', 'cost_usd', 'settled')):
                raise ValueError()
            if not all(isinstance(row[k], str) for k in ('name', 'kind', 'stage')) or type(row['settled']) is not bool:
                raise ValueError()
            for key in ('cap_usd', 'cost_usd'):
                value = row[key]
                if value is None and key == 'cost_usd' and not row['settled']:
                    continue
                if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                    raise ValueError()
    except (OSError, ValueError, Malformed):
        raise Refused('historical_ledger_unverifiable') from None


def ledger(configured):
    state = canonical(configured['roots']['state_dir'])
    prior = canonical(configured['prior_ledger']['path'])
    active = state / 'spend.json'
    if not active.exists():
        active.write_bytes(prior.read_bytes())
    validate_ledger(active)
    return mechanics.Ledger(state)


def process_env(episode):
    return {'PATH': '/usr/bin:/bin', 'HOME': str(episode / 'home'), 'CODEX_HOME': str(episode / 'codex'),
            'TMPDIR': str(episode / 'tmp'), 'LANG': 'en_US.UTF-8', 'PYTHONDONTWRITEBYTECODE': '1'}


def fixed_argv(configured, name, *arguments):
    return [configured['interpreter']['path'], '-B', configured['launcher']['path'],
            configured['interpreter']['path'], '-B', str(FIXTURES / name), *map(str, arguments)]


def project(raw, session, integrated_capture=None):
    """Validate complete synthetic facts before producing canonical tool blocks."""
    if integrated_capture is not None:
        return _responses_responses_project_one(sys.modules[__name__], controlled_route, raw, session, integrated_capture)
    pending, complete, event_ids, mappings, canonical_rows = {}, set(), set(), [], []
    offset, finished = 0, False
    raw_digest = sha(raw)
    for number, line in enumerate(raw.splitlines(keepends=True), 1):
        start, offset = offset, offset + len(line)
        try:
            event = json.loads(line, object_pairs_hook=unique, parse_constant=reject_constant)
        except (ValueError, UnicodeDecodeError, Malformed):
            raise StopEpisode('trace_invalid_json') from None
        if not isinstance(event, dict) or event.get('schema') != 'tackle-gpt-stub-event/1':
            raise StopEpisode('trace_schema')
        if event.get('session_id') != session or not isinstance(event.get('event_id'), str) or event['event_id'] in event_ids:
            raise StopEpisode('trace_event_identity')
        event_ids.add(event['event_id'])
        source = {'session_id': session, 'event_id': event['event_id'], 'item_id': event.get('item_id'),
                  'line': number, 'byte_start': start, 'byte_end': offset, 'raw_sha256': raw_digest}
        kind = event.get('kind')
        if finished:
            raise StopEpisode('trace_after_completion')
        if kind == 'request_started':
            closed(event, ('schema', 'kind', 'session_id', 'event_id', 'pid', 'cwd'))
            if type(event['pid']) is not int or event['pid'] <= 0 or not isinstance(event['cwd'], str):
                raise StopEpisode('trace_request_metadata')
            mappings.append({'canonical_id': None, 'fact': 'request', 'source': source,
                             'original_name': None, 'pid': event['pid'], 'cwd': event['cwd']})
        elif kind == 'tool_started':
            closed(event, ('schema', 'kind', 'session_id', 'event_id', 'item_id', 'original_name', 'input'))
            item, name, given = event['item_id'], event['original_name'], event['input']
            if not isinstance(item, str) or not isinstance(given, dict) or item in complete:
                raise StopEpisode('trace_invocation_identity')
            if item in pending:
                if pending[item][0:2] != (name, given):
                    raise StopEpisode('trace_conflicting_update')
                continue
            names = {'NativeRead': 'Read', 'NativeWrite': 'Write', 'CommandExecution': 'Bash',
                     'SyntheticLoopbackRequest': 'SyntheticLoopbackRequest'}
            if name not in names:
                raise StopEpisode('trace_unknown_tool')
            required = {'NativeRead': ('file_path',), 'NativeWrite': ('file_path', 'content'),
                        'CommandExecution': ('command', 'cwd'), 'SyntheticLoopbackRequest': ('port', 'host')}[name]
            closed(given, required)
            use_id = session + ':' + item
            block = {'type': 'tool_use', 'id': use_id, 'name': names[name], 'input': given,
                     'source': source, 'original_name': name}
            canonical_rows.append({'type': 'assistant', 'message': {'content': [block]}})
            pending[item] = (name, given, use_id)
            mappings.append({'canonical_id': use_id, 'fact': 'invocation', 'source': source,
                             'original_name': name, 'exact_input': given})
        elif kind == 'tool_completed':
            closed(event, ('schema', 'kind', 'session_id', 'event_id', 'item_id', 'result'))
            item, result = event['item_id'], event['result']
            if item not in pending or item in complete or not isinstance(result, dict):
                raise StopEpisode('trace_unmatched_result')
            name, given, use_id = pending.pop(item)
            failed = 'error' in result
            if failed:
                closed(result, ('error', 'errno', 'mechanism'))
                content = ''
            elif name == 'NativeRead':
                closed(result, ('content', 'returned_bytes'))
                content = result['content']
                if not isinstance(content, str) or type(result['returned_bytes']) is not int or len(content.encode()) != result['returned_bytes']:
                    raise StopEpisode('trace_returned_bytes')
            elif name == 'NativeWrite':
                closed(result, ('path', 'bytes_written', 'content_sha256'))
                if result['path'] != given['file_path'] or result['bytes_written'] != len(given['content'].encode()) or result['content_sha256'] != sha(given['content'].encode()):
                    raise StopEpisode('trace_write_payload')
                content = json.dumps(result, sort_keys=True)
            else:
                closed(result, ('stdout', 'stderr', 'exit_code'))
                if not isinstance(result['stdout'], str) or not isinstance(result['stderr'], str) or type(result['exit_code']) is not int:
                    raise StopEpisode('trace_command_result')
                content = result['stdout']
            block = {'type': 'tool_result', 'tool_use_id': use_id, 'content': content, 'is_error': failed,
                     'source': source, 'original_name': name, 'native_result': result}
            canonical_rows.append({'type': 'user', 'message': {'content': [block]}})
            mappings.append({'canonical_id': use_id, 'fact': 'result', 'source': source,
                             'original_name': name, 'exact_result': result})
            complete.add(item)
        elif kind == 'claim':
            closed(event, ('schema', 'kind', 'session_id', 'event_id', 'text'))
        elif kind == 'session_completed':
            closed(event, ('schema', 'kind', 'session_id', 'event_id', 'observed_binding'))
            if event['observed_binding'] != BINDING:
                raise StopEpisode('observed_binding_mismatch')
            if pending:
                raise StopEpisode('trace_missing_result')
            finished = True
        else:
            raise StopEpisode('trace_unknown_semantics')
    if not finished:
        raise StopEpisode('trace_missing_completion')
    return canonical_rows, mappings


def operation(value):
    if not isinstance(value, dict):
        raise Refused('synthetic_operation_schema')
    permitted = {'operation', 'fault', 'delay', 'read_limit', 'host', 'port', 'target', 'form'}
    if set(value) - permitted or value.get('operation', 'read_write') not in (
            'read_write', 'probe', 'archive', 'command', 'network', 'boundary', 'claim_only'):
        raise Refused('synthetic_operation_unsupported')
    for name in ('delay', 'read_limit'):
        if name in value and (type(value[name]) not in (int, float) or not math.isfinite(value[name]) or value[name] < 0):
            raise Refused('synthetic_operation_bounds')
    if 'read_limit' in value and type(value['read_limit']) is not int:
        raise Refused('synthetic_operation_bounds')
    faults = {'repeated_update', 'duplicate_id', 'missing_result', 'invalid_json', 'summary_only',
              'unknown_tool', 'truncated_output', 'wrong_binding', 'credential_stdout',
              'credential_stderr', 'credential_file', 'credential_name', 'credential_link', 'command_nonzero'}
    if value.get('fault') is not None and value['fault'] not in faults:
        raise Refused('synthetic_fault_unsupported')
    if any(name in value and not isinstance(value[name], str) for name in ('host', 'target', 'form')):
        raise Refused('synthetic_operation_schema')
    if 'host' in value and (value['host'] != 'foreign.invalid'):
        raise Refused('synthetic_host_unsupported')
    if 'port' in value:
        raise Refused('synthetic_port_owned_by_listener')
    if value.get('form', 'raw') not in ('raw', 'base64', 'hex', 'url', 'json'):
        raise Refused('synthetic_encoding_unsupported')
    return value


_responses_SCHEMAS = {'optin': {'schema': 'const tackle-responses-one-tool-opt-in/1', 'mode': 'const source_simulation', 'session_id': 'hex32', 'raw_source_utf8_b64': 'canonical-base64<=1048576 decoded bytes', 'component_config': 'existing ComponentConfig', 'simulation': 'NONNULL exact {state_path:absolute UTF8 path}'}, 'route_identity': {'episode_id': 'hex32', 'session_id': 'hex32', 'attempt_id': 'hex32', 'response_id': 'hex32', 'item_index': 'const integer 0', 'item_id': 'existing identifier', 'call_id': 'hex32', 'worker_handle': 'hex32'}, 'source_event': {'session_id': 'hex32', 'event_id': 'existing identifier', 'item_id': 'existing identifier', 'line': 'const integer 2', 'byte_start': 'uint', 'byte_end': 'uint', 'raw_sha256': 'sha256', 'original_name': 'NativeRead|NativeWrite|CommandExecution', 'exact_input': 'closed original tool-specific object'}, 'source_invocation': {'schema': 'const tackle-responses-one-tool-source-invocation/1', 'identity': 'route_identity', 'source_event': 'source_event', 'source_input_span': 'existing raw_source, producer=stub', 'source_input_sha256': 'sha256 of exact lexical input object bytes', 'source_fingerprints': 'exact {route_sha256:sha256,mapping_version:const tackle-gpt-stub-map/1,fixture_tree_sha256:sha256}', 'component_fingerprint': 'sha256', 'source_root': 'absolute work root', 'function_name': 'Read|Write|Bash', 'parsed_input': 'current isolated tool arguments', 'defaults_applied': 'Read:[byte_offset=0,max_bytes=65536]; otherwise []'}, 'context': {'route_root': 'absolute empty existing direct evidence_parent child', 'component_output': 'absolute absent direct evidence_parent child', 'observation_path': 'absolute absent direct evidence_parent file', 'source_root': 'absolute component_config.roots.work', 'simulation': 'NONNULL exact {state_path:absolute existing single-link own file}', 'stage': 'probe|smoke|held-out', 'seconds_ns': 'positive_int<=900000000000', 'requests': 'positive_int<=60'}, 'claim': {'call': 'exact six-argument JSON array', 'returned_utf8_b64': 'nullable<canonical-base64 of canonical actual claim return JSON>', 'returned_sha256': 'nullable<sha256>', 'artifact_ref': 'nullable<existing isolated Artifact relative to route_root>', 'return_observed': 'bool', 'reserved_usd': 'const 0.1 string', 'actual_usd': 'const n/a string'}, 'environments': {'kind': 'const declarations_not_observed_environment', 'watchdog': 'exact PATH=/usr/bin:/bin,LANG=C.UTF-8; optional TMPDIR/TEMP/TMP under existing trusted guard', 'engine': 'exact PATH=/usr/bin:/bin,LANG=C.UTF-8,HOME=roots.cli_home,DOCKER_CONFIG=roots.cli_config,DOCKER_HOST=config.docker_cli.endpoint'}, 'clock': {'origin_ns': 'uint', 'admitted_ns': 'uint', 'deadline_ns': 'uint', 'dispatch_ns': 'nullable<uint>', 'run_return_ns': 'nullable<uint>', 'verified_ns': 'nullable<uint>', 'projected_ns': 'nullable<uint>', 'finished_ns': 'nullable<uint>'}, 'counts': {'claim_calls': 'uint<=1', 'dispatch_calls': 'uint<=1', 'verified_receipts': 'uint<=1', 'complete_results': 'uint<=1', 'projected_tool_uses': 'uint<=1', 'projected_tool_results': 'uint<=1', 'canonical_rows': 'uint<=3', 'reserved_units': 'nullable<uint<=1>; null if claim call raises', 'consumed_units': 'uint<=1', 'raw_source_bytes': 'uint<=1048576', 'isolated_argument_bytes': 'uint<=1048576', 'returned_bytes': 'uint<=3145728', 'stdout_bytes': 'uint<=1048576', 'stderr_bytes': 'uint<=1048576'}, 'capture': {'schema': 'const tackle-responses-one-tool-capture/1', 'status': 'verified|instrument_incomplete', 'reason': 'nullable<error-code>', 'context': 'context', 'component_config': 'existing ComponentConfig', 'source_invocation': 'source_invocation', 'isolated_invocation': 'existing invocation', 'source_invocation_sha256': 'sha256', 'isolated_invocation_sha256': 'sha256', 'source_ref': 'existing isolated Artifact relative to route_root', 'arguments_ref': 'existing isolated Artifact relative to route_root', 'claim': 'nullable<claim>', 'environments': 'environments', 'clock': 'clock', 'counts': 'counts', 'observation_ref': 'nullable<isolated Artifact relative to evidence_parent>', 'bundle_ref': 'nullable<isolated Artifact relative to evidence_parent>', 'receipt_ref': 'nullable<isolated Artifact relative to component_output>', 'result_ref': 'nullable<isolated Artifact relative to component_output>', 'component_result': 'nullable<existing ComponentResult>', 'publication_scope': 'const component_verify_and_projection_only', 'sourceReady': 'const false bool', 'liveReady': 'const false bool', 'T12Ready': 'const false bool', 'T17Complete': 'const false bool', 'C07_accepted': 'const false bool', 'C20_accepted': 'const false bool', 'fullroute': 'const false bool'}}

_responses_SOURCE_NAMES = {'NativeRead': 'Read', 'NativeWrite': 'Write', 'CommandExecution': 'Bash'}

_responses_SOURCE_FIELDS = {'NativeRead': ('file_path',), 'NativeWrite': ('file_path', 'content'), 'CommandExecution': ('command', 'cwd')}

_responses_READINESS = ('sourceReady', 'liveReady', 'T12Ready', 'T17Complete', 'C07_accepted', 'C20_accepted', 'fullroute')

_responses_SCHEMAS['terminal'] = {'schema': 'const tackle-responses-one-tool-terminal/1', 'outcome': 'const completed', 'reason': 'const null', 'capture_ref': 'existing isolated Artifact relative route_root', 'canonical_sha256': 'sha256', 'mapping_sha256': 'sha256', 'initiated_requests': 'const 1 integer', 'cost_usd': 'const n/a', 'proof_scope': 'const source_simulation', 'finished_check_ns': 'uint', 'sourceReady': 'const false bool', 'liveReady': 'const false bool', 'T12Ready': 'const false bool', 'T17Complete': 'const false bool', 'C07_accepted': 'const false bool', 'C20_accepted': 'const false bool', 'fullroute': 'const false bool'}

_responses_SCHEMAS['failure'] = {'schema': 'const tackle-responses-one-tool-failure/1', 'outcome': 'const instrument_error', 'reason': 'error-code', 'capture': 'capture', 'cost_usd': 'const n/a', 'proof_scope': 'const source_simulation', 'sourceReady': 'const false bool', 'liveReady': 'const false bool', 'T12Ready': 'const false bool', 'T17Complete': 'const false bool', 'C07_accepted': 'const false bool', 'C20_accepted': 'const false bool', 'fullroute': 'const false bool'}

_responses_MIN_DISPATCH_REMAINING_NS = 95000000000

class _ResponsesOneRefusal(Exception):

    def __init__(self, code):
        self.code = code
        super().__init__(code)

def _responses_need(condition, code):
    if not condition:
        raise _ResponsesOneRefusal(code)

def _responses_closed(value, names):
    _responses_need(type(value) is dict and set(value) == set(names), 'one_closed_fields')

def _responses_canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')

def _responses_sha(raw):
    return hashlib.sha256(raw).hexdigest()

def _responses_decode(raw):

    def pairs(items):
        result = {}
        for (key, value) in items:
            _responses_need(key not in result, 'one_duplicate_key')
            result[key] = value
        return result

    def constant(_):
        raise _ResponsesOneRefusal('one_nonfinite')
    try:
        return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs, parse_constant=constant)
    except (UnicodeError, ValueError, RecursionError):
        raise _ResponsesOneRefusal('one_invalid_json') from None

def _responses_b64(raw):
    return base64.b64encode(raw).decode('ascii')

def _responses_unb64(text, maximum):
    _responses_need(type(text) is str and len(text) <= 4 * ((maximum + 2) // 3), 'one_base64_cap')
    try:
        raw = base64.b64decode(text, validate=True)
    except (ValueError, TypeError):
        raise _ResponsesOneRefusal('one_base64') from None
    _responses_need(_responses_b64(raw) == text and len(raw) <= maximum, 'one_base64')
    return raw

def _responses_uint(value, maximum=None):
    _responses_need(type(value) is int and value >= 0 and (maximum is None or value <= maximum), 'one_uint')

def _responses_digest_field(value):
    _responses_need(type(value) is str and re.fullmatch('[0-9a-f]{64}', value), 'one_sha256')

def _responses_absolute(value):
    _responses_need(type(value) is str and value.startswith('/') and ('\\' not in value) and ('\x00' not in value) and (len(value.encode('utf-8')) <= 4096), 'one_absolute_path')
    parts = value.split('/')[1:]
    _responses_need(parts and all((part not in ('', '.', '..') for part in parts)), 'one_absolute_path')
    return Path(value)

def _responses_safe_chain(path):
    for item in (path, *path.parents):
        _responses_need(not item.is_symlink(), 'one_path_link')

def _responses_regular(path):
    _responses_safe_chain(path)
    info = path.stat()
    _responses_need(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, 'one_regular_single_link')

def _responses_fingerprints(gp, configured):
    value = configured['fingerprints']
    _responses_closed(value, ('route_sha256', 'mapping_version', 'fixture_tree_sha256'))
    _responses_digest_field(value['route_sha256'])
    _responses_digest_field(value['fixture_tree_sha256'])
    _responses_need(value['mapping_version'] == gp.MAPPING == 'tackle-gpt-stub-map/1', 'one_mapping_pin')
    _responses_need(value['route_sha256'] == _responses_sha((gp.HERE / 'gpt_route.py').read_bytes()) and value['fixture_tree_sha256'] == gp.fixture_digest(), 'one_source_pin')
    _responses_need(configured['mode'] == 'synthetic' and configured['binding'] == gp.BINDING and (_responses_canonical(configured['caps']) == _responses_canonical(gp.CAPS)), 'one_source_config')
    return _responses_decode(_responses_canonical(value))

def _responses_control_limits(control):
    value = {'seconds': 900, 'requests': 60} if control is None else control
    _responses_closed(value, ('seconds', 'requests'))
    (seconds, requests) = (value['seconds'], value['requests'])
    _responses_need(type(seconds) in (int, float) and math.isfinite(seconds) and (0 < seconds <= 900), 'one_control')
    _responses_need(type(requests) is int and 1 <= requests <= 60, 'one_control')
    nanoseconds = int(Decimal(str(seconds)) * 1000000000)
    _responses_need(nanoseconds >= _responses_MIN_DISPATCH_REMAINING_NS, 'one_insufficient_budget')
    return (nanoseconds, requests)

def _responses_source_parse(gp, cr, raw, session):
    _responses_need(type(raw) is bytes and 0 < len(raw) <= 1048576 and raw.endswith(b'\n'), 'one_source_size')
    lines = raw.splitlines(keepends=True)
    events = [_responses_decode(line) for line in lines]
    _responses_need(not any((type(e) is dict and e.get('kind') == 'tool_completed' for e in events)), 'responses_post_effect_source')
    _responses_need(len(events) == 3, 'one_exactly_one_invocation')
    kinds = ('request_started', 'tool_started', 'session_completed')
    extras = (('pid', 'cwd'), ('item_id', 'original_name', 'input'), ('observed_binding',))
    seen = set()
    for (event, kind, more) in zip(events, kinds, extras):
        _responses_closed(event, ('schema', 'kind', 'session_id', 'event_id') + more)
        _responses_need(event['schema'] == 'tackle-gpt-stub-event/1' and event['kind'] == kind and (event['session_id'] == session), 'one_event_order')
        cr.identifier(event['event_id'])
        _responses_need(event['event_id'] not in seen, 'one_event_identity')
        seen.add(event['event_id'])
    _responses_need(type(events[0]['pid']) is int and events[0]['pid'] > 0 and (type(events[0]['cwd']) is str), 'one_source_metadata')
    _responses_need(_responses_canonical(events[2]['observed_binding']) == _responses_canonical(gp.BINDING), 'one_declared_binding')
    tool = events[1]
    cr.identifier(tool['item_id'])
    _responses_need(tool['original_name'] in _responses_SOURCE_NAMES, 'one_tool_name')
    _responses_closed(tool['input'], _responses_SOURCE_FIELDS[tool['original_name']])
    _responses_need(all((type(v) is str for v in tool['input'].values())), 'one_input_string')
    _responses_need(all((len(v.encode('utf-8')) <= 1048576 for v in tool['input'].values())), 'one_input_size')
    _responses_need(not gp.has_sensitive(raw), 'one_sensitive_source')
    start = len(lines[0])
    end = start + len(lines[1])
    (a, z) = cr.lexical_span(lines[1], ('input',))
    source = dict(session_id=session, event_id=tool['event_id'], item_id=tool['item_id'], line=2, byte_start=start, byte_end=end, raw_sha256=_responses_sha(raw), original_name=tool['original_name'], exact_input=tool['input'])
    span = cr.record('raw_source', artifact='source.raw', sha256=_responses_sha(raw), byte_start=start + a, byte_end=start + z, event_id=tool['event_id'], producer='stub')
    _responses_need(_responses_canonical(_responses_decode(raw[start + a:start + z])) == _responses_canonical(tool['input']), 'one_input_span')
    return (source, span, _responses_sha(raw[start + a:start + z]))

def _responses_path_translation(cr, source_root, source):
    (given, name) = (source['exact_input'], source['original_name'])
    key = 'cwd' if name == 'CommandExecution' else 'file_path'
    host = _responses_absolute(given[key])
    _responses_safe_chain(host)
    _responses_need(host.is_relative_to(source_root), 'one_outside_work')
    relative = host.relative_to(source_root).as_posix()
    if relative == '.':
        _responses_need(name == 'CommandExecution', 'one_work_root_alias')
        mapped = '/work'
    else:
        cr.relative(relative)
        mapped = '/work/' + relative
    if name == 'NativeRead':
        _responses_regular(host)
        value = dict(file_path=mapped, byte_offset=0, max_bytes=65536)
        defaults = ['byte_offset=0', 'max_bytes=65536']
    elif name == 'NativeWrite':
        _responses_need(host.parent.is_dir(), 'one_write_parent')
        if host.exists():
            _responses_regular(host)
        value = dict(file_path=mapped, content=given['content'])
        defaults = []
    else:
        _responses_need(host.is_dir(), 'one_cwd')
        value = dict(command=given['command'], cwd=mapped)
        defaults = []
    cr.validate_tool(_responses_SOURCE_NAMES[name], value)
    return (value, defaults)

def _responses_admitted(gp, cr, configured, out, files, sessions, install, stage, network, control, optin, origin):
    _responses_closed(optin, _responses_SCHEMAS['optin'])
    _responses_need(optin['schema'] == 'tackle-responses-one-tool-opt-in/1' and optin['mode'] == 'source_simulation', 'one_mode')
    _responses_need(type(optin['session_id']) is str and re.fullmatch('[0-9a-f]{32}', optin['session_id']), 'one_session')
    _responses_closed(optin['simulation'], ('state_path',))
    state = _responses_absolute(optin['simulation']['state_path'])
    _responses_need(files == {} and type(files) is dict and (sessions == []) and (type(sessions) is list) and (install is None) and (network is None) and (stage in ('probe', 'smoke', 'held-out')), 'one_unsupported_legacy_inputs')
    (seconds, requests) = _responses_control_limits(control)
    raw = _responses_unb64(optin['raw_source_utf8_b64'], 1048576)
    (source, span, source_input_sha) = _responses_source_parse(gp, cr, raw, optin['session_id'])
    fp = _responses_fingerprints(gp, configured)
    config = _responses_decode(_responses_canonical(optin['component_config']))
    roots = cr.validate_isolated_config(config)
    work = roots['work']
    route_root = _responses_absolute(str(out))
    _responses_safe_chain(route_root)
    _responses_need(route_root.parent == roots['evidence_parent'] and route_root.is_dir() and (not list(route_root.iterdir())), 'one_route_output')
    cr.identifier(route_root.name)
    component_output = roots['evidence_parent'] / (route_root.name + '__component')
    observation_path = roots['evidence_parent'] / (component_output.name + '.observation.json')
    _responses_need(not component_output.exists() and (not component_output.is_symlink()) and (not observation_path.exists()) and (not observation_path.is_symlink()), 'one_component_output')
    _responses_regular(state)
    _responses_need(state.parent == roots['component_root'], 'one_simulation_owner')
    state_raw = cr.artifact_read(state, 1048576)
    state_value = _responses_decode(state_raw)
    _responses_closed(state_value, ('fault', 'stdout_b64', 'stderr_b64', 'exit_code', 'read_b64'))
    _responses_need(state_value['fault'] is None and type(state_value['exit_code']) is int and (0 <= state_value['exit_code'] <= 255), 'one_simulation_state')
    for key in ('stdout_b64', 'stderr_b64', 'read_b64'):
        _responses_unb64(state_value[key], 1048576)
    (value, defaults) = _responses_path_translation(cr, work, source)
    session = optin['session_id']

    def generated(domain):
        return _responses_sha(_responses_canonical([domain, session, source['item_id'], 0]))[:32]
    identity = dict(episode_id=generated('episode'), session_id=session, attempt_id=generated('attempt'), response_id=generated('response'), item_index=0, item_id=source['item_id'], call_id=generated('call'), worker_handle=generated('worker'))
    source_inv = dict(schema='tackle-responses-one-tool-source-invocation/1', identity=identity, source_event=source, source_input_span=span, source_input_sha256=source_input_sha, source_fingerprints=fp, component_fingerprint=config['pins']['fingerprint'], source_root=str(work), function_name=_responses_SOURCE_NAMES[source['original_name']], parsed_input=value, defaults_applied=defaults)
    arguments = _responses_canonical(value)
    argument_span = cr.record('raw_source', artifact='arguments.raw', sha256=_responses_sha(arguments), byte_start=0, byte_end=len(arguments), event_id=generated('translated_arguments'), producer='controller')
    invocation = dict(schema=cr.VERSIONS['invocation'], **identity, function_name=source_inv['function_name'], arguments_utf8_b64=_responses_b64(arguments), arguments_sha256=_responses_sha(arguments), arguments_raw_span=argument_span, parsed_input=value, fingerprint=config['pins']['fingerprint'])
    cr.validate_isolated_invocation(invocation)
    now = gp.time.monotonic_ns()
    _responses_need(now - origin + _responses_MIN_DISPATCH_REMAINING_NS <= seconds, 'one_insufficient_budget')
    context = dict(route_root=str(route_root), component_output=str(component_output), observation_path=str(observation_path), source_root=str(work), simulation=dict(state_path=str(state)), stage=stage, seconds_ns=seconds, requests=requests)
    return (raw, arguments, source_inv, invocation, config, context, now)

class _ResponsesRouteStore:
    """Only fixed new direct files under the already-admitted own route output."""
    NAMES = ('source.raw', 'arguments.raw', 'source-invocation.json', 'claim.json', 'capture.json', 'canonical.jsonl', 'mapping.json', 'result.json', 'failure.json')

    def __init__(self, cr, root, maximum):
        (self.cr, self.root, self.maximum, self.total) = (cr, root, maximum, 0)

    def put(self, name, raw):
        _responses_need(name in self.NAMES and type(raw) is bytes and (self.total + len(raw) <= self.maximum), 'one_retention_cap')
        _responses_safe_chain(self.root)
        target = self.root / name
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 384)
        try:
            info = os.fstat(fd)
            _responses_need(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, 'one_retention_file')
            position = 0
            while position < len(raw):
                amount = os.write(fd, raw[position:position + 65536])
                _responses_need(amount > 0, 'one_retention_write')
                position += amount
            os.fsync(fd)
        finally:
            os.close(fd)
        self.total += len(raw)
        return self.cr.isolated_record('Artifact', artifact=name, sha256=_responses_sha(raw), byte_length=len(raw))

def _responses_read_ref(cr, base, reference, cap):
    cr.isolated_validate_artifact(reference)
    path = base / reference['artifact']
    _responses_safe_chain(path)
    _responses_regular(path)
    raw = cr.artifact_read(path, cap)
    _responses_need(len(raw) == reference['byte_length'] and _responses_sha(raw) == reference['sha256'], 'one_artifact_pin')
    return raw

def _responses_environment_declarations(cr, config):
    return dict(kind='declarations_not_observed_environment', watchdog=cr.isolated_controller_environment(), engine=dict(PATH='/usr/bin:/bin', LANG='C.UTF-8', HOME=config['roots']['cli_home'], DOCKER_CONFIG=config['roots']['cli_config'], DOCKER_HOST=config['docker_cli']['endpoint']))

def _responses_validate_environments(cr, config, value):
    _responses_closed(value, _responses_SCHEMAS['environments'])
    _responses_need(value['kind'] == 'declarations_not_observed_environment', 'one_environment_authority')
    expected = _responses_environment_declarations(cr, config)
    _responses_need(_responses_canonical(value) == _responses_canonical(expected), 'one_environment_declaration_drift')
    _responses_need(set(value['watchdog']) <= {'PATH', 'LANG', 'TMPDIR', 'TEMP', 'TMP'} and {'PATH', 'LANG'} <= set(value['watchdog']), 'one_watchdog_environment')
    _responses_closed(value['engine'], ('PATH', 'LANG', 'HOME', 'DOCKER_CONFIG', 'DOCKER_HOST'))

def _responses_validate_counts(capture, rows=None):
    c = capture['counts']
    _responses_closed(c, _responses_SCHEMAS['counts'])
    for (key, value) in c.items():
        limit = 1 if key in ('claim_calls', 'dispatch_calls', 'verified_receipts', 'complete_results', 'projected_tool_uses', 'projected_tool_results', 'reserved_units', 'consumed_units') else None
        if key == 'reserved_units' and value is None:
            continue
        _responses_uint(value, limit)
    _responses_need(c['claim_calls'] == int(capture['claim'] is not None), 'one_claim_count')
    expected_reserved = 0 if capture['claim'] is None else 1 if capture['claim']['return_observed'] else None
    _responses_need(_responses_canonical(c['reserved_units']) == _responses_canonical(expected_reserved), 'one_claim_count')
    _responses_need(c['complete_results'] <= c['verified_receipts'] <= c['dispatch_calls'] <= c['claim_calls'], 'one_count_order')
    _responses_need(c['consumed_units'] == c['complete_results'], 'one_consumption')
    raw = _responses_unb64(capture['isolated_invocation']['arguments_utf8_b64'], 1048576)
    _responses_need(c['raw_source_bytes'] == capture['source_ref']['byte_length'] and c['isolated_argument_bytes'] == len(raw), 'one_byte_counts')
    result = capture['component_result']
    returned = b'' if result is None else _responses_unb64(result['returned_utf8_b64'], 3145728)
    _responses_need(c['returned_bytes'] == len(returned), 'one_returned_count')
    for key in ('stdout', 'stderr'):
        expected = len(result['facts'][key + '_utf8'].encode('utf-8')) if result is not None and result['kind'] == 'Bash' else 0
        _responses_need(c[key + '_bytes'] == expected and expected <= 1048576, 'one_stream_count')
    if capture['status'] == 'verified':
        _responses_need(all((c[k] == 1 for k in ('claim_calls', 'dispatch_calls', 'verified_receipts', 'complete_results', 'reserved_units', 'consumed_units', 'projected_tool_uses', 'projected_tool_results'))) and c['canonical_rows'] == 3, 'one_complete_counts')
    else:
        _responses_need(c['projected_tool_uses'] == c['projected_tool_results'] == c['canonical_rows'] == 0, 'one_incomplete_counts')
    if rows is not None:
        _responses_need(len(rows) == c['canonical_rows'], 'one_projection_count')
        content = [r['message']['content'][0] for r in rows if r['type'] in ('assistant', 'user')]
        _responses_need(sum((b['type'] == 'tool_use' for b in content)) == c['projected_tool_uses'] and sum((b['type'] == 'tool_result' for b in content)) == c['projected_tool_results'], 'one_projection_count')
    return c

def _responses_validate_clock(capture):
    clock = capture['clock']
    _responses_closed(clock, _responses_SCHEMAS['clock'])
    for key in ('origin_ns', 'admitted_ns', 'deadline_ns'):
        _responses_uint(clock[key])
    _responses_need(clock['deadline_ns'] == clock['origin_ns'] + capture['context']['seconds_ns'], 'one_route_deadline')
    previous = clock['origin_ns']
    for key in ('admitted_ns', 'dispatch_ns', 'run_return_ns', 'verified_ns', 'projected_ns', 'finished_ns'):
        value = clock[key]
        if value is None:
            continue
        _responses_uint(value)
        _responses_need(previous <= value, 'one_clock_order')
        previous = value
    if clock['dispatch_ns'] is not None:
        _responses_need(clock['dispatch_ns'] + _responses_MIN_DISPATCH_REMAINING_NS <= clock['deadline_ns'], 'one_dispatch_budget')
    if capture['status'] == 'verified':
        _responses_need(all((clock[k] is not None for k in _responses_SCHEMAS['clock'])) and clock['finished_ns'] <= clock['deadline_ns'], 'one_acceptance_deadline')
    return clock

def _responses_validate_one_capture(gp, cr, capture, actual_claim=None, rows=None):
    """One authoritative signature. Files/claims are host inputs, never worker assertions."""
    _responses_closed(capture, _responses_SCHEMAS['capture'])
    _responses_need(capture['schema'] == 'tackle-responses-one-tool-capture/1' and capture['status'] in ('verified', 'instrument_incomplete') and (capture['publication_scope'] == 'component_verify_and_projection_only'), 'one_capture_schema')
    for key in _responses_READINESS:
        _responses_need(type(capture[key]) is bool and capture[key] is False, 'one_readiness')
    _responses_need(capture['reason'] is None if capture['status'] == 'verified' else type(capture['reason']) is str and bool(re.fullmatch('[A-Za-z0-9_.:-]{1,128}', capture['reason'])), 'one_reason')
    context = capture['context']
    _responses_closed(context, _responses_SCHEMAS['context'])
    _responses_need(context['stage'] in ('probe', 'smoke', 'held-out'), 'one_stage')
    _responses_closed(context['simulation'], ('state_path',))
    _responses_absolute(context['simulation']['state_path'])
    _responses_need(type(context['requests']) is int and 1 <= context['requests'] <= 60, 'one_control')
    _responses_uint(context['seconds_ns'], 900000000000)
    _responses_need(context['seconds_ns'] >= _responses_MIN_DISPATCH_REMAINING_NS, 'one_control')
    config = capture['component_config']
    roots = cr.validate_isolated_config(config)
    (route_root, output, observation_path) = [_responses_absolute(context[k]) for k in ('route_root', 'component_output', 'observation_path')]
    _responses_need(route_root.parent == output.parent == observation_path.parent == roots['evidence_parent'] and output.name == route_root.name + '__component' and (observation_path.name == output.name + '.observation.json') and (context['source_root'] == str(roots['work'])) and (Path(context['simulation']['state_path']).parent == roots['component_root']), 'one_context_binding')
    source = capture['source_invocation']
    _responses_closed(source, _responses_SCHEMAS['source_invocation'])
    _responses_need(source['schema'] == 'tackle-responses-one-tool-source-invocation/1', 'one_source_schema')
    _responses_closed(source['identity'], _responses_SCHEMAS['route_identity'])
    _responses_closed(source['source_event'], _responses_SCHEMAS['source_event'])
    raw = _responses_read_ref(cr, route_root, capture['source_ref'], 1048576)
    session = source['identity']['session_id']
    _responses_need(type(session) is str and re.fullmatch('[0-9a-f]{32}', session), 'one_session')
    (event, span, input_sha) = _responses_source_parse(gp, cr, raw, session)
    (value, defaults) = _responses_path_translation(cr, roots['work'], event)
    _responses_need(_responses_canonical(event) == _responses_canonical(source['source_event']) and _responses_canonical(span) == _responses_canonical(source['source_input_span']) and (input_sha == source['source_input_sha256']) and (value == source['parsed_input']) and (_responses_canonical(value) == _responses_canonical(source['parsed_input'])) and (defaults == source['defaults_applied']) and (source['source_root'] == str(roots['work'])) and (source['function_name'] == _responses_SOURCE_NAMES[event['original_name']]) and (source['component_fingerprint'] == config['pins']['fingerprint']), 'one_source_continuity')
    for (key, domain) in (('episode_id', 'episode'), ('attempt_id', 'attempt'), ('response_id', 'response'), ('call_id', 'call'), ('worker_handle', 'worker')):
        _responses_need(source['identity'][key] == _responses_sha(_responses_canonical([domain, session, event['item_id'], 0]))[:32], 'one_derived_identity')
    _responses_need(source['identity']['item_index'] == 0 and type(source['identity']['item_index']) is int and (source['identity']['item_id'] == event['item_id']), 'one_item_identity')
    fp = source['source_fingerprints']
    _responses_closed(fp, ('route_sha256', 'mapping_version', 'fixture_tree_sha256'))
    _responses_need(fp['route_sha256'] == _responses_sha((gp.HERE / 'gpt_route.py').read_bytes()) and fp['mapping_version'] == gp.MAPPING and (fp['fixture_tree_sha256'] == gp.fixture_digest()), 'one_source_pin')
    arguments = _responses_read_ref(cr, route_root, capture['arguments_ref'], 1048576)
    invocation = capture['isolated_invocation']
    cr.validate_isolated_invocation(invocation)
    expected_span = cr.record('raw_source', artifact='arguments.raw', sha256=_responses_sha(arguments), byte_start=0, byte_end=len(arguments), event_id=_responses_sha(_responses_canonical(['translated_arguments', session, event['item_id'], 0]))[:32], producer='controller')
    _responses_need(arguments == _responses_canonical(value) and _responses_unb64(invocation['arguments_utf8_b64'], 1048576) == arguments and (_responses_canonical(invocation['arguments_raw_span']) == _responses_canonical(expected_span)) and all((_responses_canonical(invocation[k]) == _responses_canonical(v) for (k, v) in source['identity'].items())) and (invocation['function_name'] == source['function_name']) and (invocation['fingerprint'] == config['pins']['fingerprint']), 'one_isolated_continuity')
    _responses_need(capture['source_invocation_sha256'] == _responses_sha(_responses_canonical(source)) and capture['isolated_invocation_sha256'] == _responses_sha(_responses_canonical(invocation)), 'one_distinct_invocation_hashes')
    _responses_validate_environments(cr, config, capture['environments'])
    _responses_validate_clock(capture)
    claim = capture['claim']
    if claim is not None:
        _responses_closed(claim, _responses_SCHEMAS['claim'])
        expected_call = [session, 'synthetic-request', context['stage'], gp.REQUEST_USD, gp.CAPS['probe_usd'] if context['stage'] == 'probe' else gp.CAPS['stages'][context['stage']], gp.CAPS['total_usd']]
        _responses_need(type(claim['return_observed']) is bool, 'one_claim_return_type')
        if not claim['return_observed']:
            _responses_need(claim['returned_utf8_b64'] is None and claim['returned_sha256'] is None and (claim['artifact_ref'] is None) and (capture['status'] == 'instrument_incomplete'), 'one_claim_uncertain')
            _responses_need(claim['call'] == expected_call and _responses_canonical(claim['call']) == _responses_canonical(expected_call), 'one_actual_claim_call')
            _responses_validate_counts(capture, rows)
            return capture
        claim_bytes = _responses_unb64(claim['returned_utf8_b64'], 1048576)
        _responses_need(claim['call'] == expected_call and _responses_canonical(claim['call']) == _responses_canonical(expected_call) and (claim['reserved_usd'] == '0.1') and (claim['actual_usd'] == 'n/a') and (_responses_sha(claim_bytes) == claim['returned_sha256']) and (_responses_canonical(_responses_decode(claim_bytes)) == claim_bytes) and (claim['artifact_ref'] is None or _responses_read_ref(cr, route_root, claim['artifact_ref'], 1048576) == claim_bytes), 'one_actual_claim')
        if capture['status'] == 'verified':
            _responses_need(claim['artifact_ref'] is not None, 'one_actual_claim_retention')
        if actual_claim is not None:
            _responses_need(claim_bytes == _responses_canonical(actual_claim), 'one_actual_claim_return')
    if capture['status'] == 'verified':
        receipt = cr.verify_isolated_bundle(config, output / 'bundle.json', observation_path)
        observed_invocation = _responses_decode(_responses_read_ref(cr, output, receipt['invocation_ref'], config['caps']['max_retained_bytes']))
        _responses_need(cr.encoded(observed_invocation) == cr.encoded(invocation), 'one_component_invocation_binding')
        observation_raw = _responses_read_ref(cr, roots['evidence_parent'], capture['observation_ref'], config['caps']['max_engine_command_stream_bytes'] * 3)
        _responses_need(capture['observation_ref']['artifact'] == observation_path.name and observation_raw == cr.artifact_read(observation_path, config['caps']['max_engine_command_stream_bytes'] * 3), 'one_observation_binding')
        observation = _responses_decode(observation_raw)
        _responses_need(observation['proof_scope'] == 'source_simulation' and observation['component_boundary_observed'] is False and (capture['clock']['dispatch_ns'] <= observation['started_ns']) and (observation['ended_ns'] <= capture['clock']['run_return_ns']), 'one_actual_observation')
        _responses_need(receipt['complete'] is True and receipt['proof_scope'] == 'source_simulation' and (receipt['component_boundary_observed'] is False), 'one_verified_complete')
        bundle_raw = _responses_read_ref(cr, roots['evidence_parent'], capture['bundle_ref'], config['caps']['max_retained_bytes'])
        bundle = _responses_decode(bundle_raw)
        _responses_need(_responses_canonical(capture['bundle_ref']) == _responses_canonical(observation['bundle_ref']) and _responses_canonical(capture['receipt_ref']) == _responses_canonical(bundle['receipt_ref']) and (_responses_canonical(capture['result_ref']) == _responses_canonical(receipt['result_ref'])), 'one_component_refs')
        _responses_need(_responses_canonical(_responses_decode(_responses_read_ref(cr, output, capture['receipt_ref'], config['caps']['max_retained_bytes']))) == _responses_canonical(receipt), 'one_receipt_bytes')
        result = _responses_decode(_responses_read_ref(cr, output, capture['result_ref'], config['caps']['max_retained_bytes']))
        expected_identity = {key: invocation[key] for key in cr.isolated_policy()['record_fields']['InvocationIdentity']}
        _responses_need(result['invocation_sha256'] == cr.digest(cr.encoded(invocation)) and cr.encoded(result['identity']) == cr.encoded(expected_identity), 'one_component_result_binding')
        _responses_need(_responses_canonical(result) == _responses_canonical(capture['component_result']) and result['complete'] is True and (result['request_id'] == receipt['request_id']), 'one_component_result')
        _responses_need(not gp.has_sensitive(_responses_canonical(result)), 'one_sensitive_result')
    _responses_validate_counts(capture, rows)
    return capture

def _responses_responses_project_one(gp, cr, raw, session, capture):
    _responses_validate_one_capture(gp, cr, capture)
    source = capture['source_invocation']['source_event']
    result = capture['component_result']
    _responses_need(capture['status'] == 'verified' and source['session_id'] == session and (source['raw_sha256'] == _responses_sha(raw)), 'one_project_source')
    use_id = session + ':' + source['item_id']
    kind = result['kind']
    facts = result['facts']
    mapping_source = {k: source[k] for k in ('session_id', 'event_id', 'item_id', 'line', 'byte_start', 'byte_end', 'raw_sha256')}
    use = dict(type='tool_use', id=use_id, name=capture['isolated_invocation']['function_name'], input=source['exact_input'], source=mapping_source, original_name=source['original_name'])
    returned = _responses_unb64(result['returned_utf8_b64'], 3145728)
    content = returned.decode('utf-8')
    is_error = kind == 'refused' or (kind == 'Bash' and facts['exit_code'] != 0)
    block = dict(type='tool_result', tool_use_id=use_id, content=content, is_error=is_error, source=mapping_source, original_name=source['original_name'], native_result=facts, component_result_sha256=_responses_sha(_responses_canonical(result)), component_result_ref=capture['result_ref'])
    rows = [{'type': 'assistant', 'message': {'content': [use]}}, {'type': 'user', 'message': {'content': [block]}}, {'type': 'result', 'subtype': 'success'}]
    maps = [dict(canonical_id=use_id, fact='invocation', source=mapping_source, original_name=source['original_name'], exact_input=source['exact_input']), dict(canonical_id=use_id, fact='result', source=mapping_source, original_name=source['original_name'], exact_result=facts)]
    _responses_validate_counts(capture, rows)
    return (rows, maps)

def _responses_responses_execute_single(gp, cr, configured, out, files, sessions, install, stage, network, control, optin):
    """Concrete source-only effectful adapter; NEVER run this inactive author artifact."""
    origin = gp.time.monotonic_ns()
    (raw, args, source, invocation, config, context, admitted_ns) = _responses_admitted(gp, cr, configured, out, files, sessions, install, stage, network, control, optin, origin)
    store = _ResponsesRouteStore(cr, Path(context['route_root']), config['caps']['max_retained_bytes'])
    raw_ref = store.put('source.raw', raw)
    args_ref = store.put('arguments.raw', args)
    store.put('source-invocation.json', _responses_canonical(source))
    capture = dict(schema='tackle-responses-one-tool-capture/1', status='instrument_incomplete', reason='one_not_dispatched', context=context, component_config=config, source_invocation=source, isolated_invocation=invocation, source_invocation_sha256=_responses_sha(_responses_canonical(source)), isolated_invocation_sha256=_responses_sha(_responses_canonical(invocation)), source_ref=raw_ref, arguments_ref=args_ref, claim=None, environments=_responses_environment_declarations(cr, config), clock=dict(origin_ns=origin, admitted_ns=admitted_ns, deadline_ns=origin + context['seconds_ns'], dispatch_ns=None, run_return_ns=None, verified_ns=None, projected_ns=None, finished_ns=None), counts={k: 0 for k in _responses_SCHEMAS['counts']}, observation_ref=None, bundle_ref=None, receipt_ref=None, result_ref=None, component_result=None, publication_scope='component_verify_and_projection_only', **{key: False for key in _responses_READINESS})
    capture['counts'].update(raw_source_bytes=len(raw), isolated_argument_bytes=len(args))
    actual_claim = None
    try:
        _responses_need(gp.time.monotonic_ns() + _responses_MIN_DISPATCH_REMAINING_NS <= capture['clock']['deadline_ns'], 'one_insufficient_budget')
        account = gp.ledger(configured)
        stage_cap = configured['caps']['probe_usd'] if stage == 'probe' else configured['caps']['stages'][stage]
        call = [source['identity']['session_id'], 'synthetic-request', stage, gp.REQUEST_USD, stage_cap, configured['caps']['total_usd']]
        capture['claim'] = dict(call=call, returned_utf8_b64=None, returned_sha256=None, artifact_ref=None, return_observed=False, reserved_usd='0.1', actual_usd='n/a')
        capture['counts'].update(claim_calls=1, reserved_units=None)
        actual_claim = account.claim(*call)
        returned = _responses_canonical(actual_claim)
        _responses_need(len(returned) <= 1048576, 'one_claim_size')
        capture['claim'].update(returned_utf8_b64=_responses_b64(returned), returned_sha256=_responses_sha(returned), return_observed=True)
        capture['counts']['reserved_units'] = 1
        capture['claim']['artifact_ref'] = store.put('claim.json', returned)
        dispatch = gp.time.monotonic_ns()
        _responses_need(dispatch + _responses_MIN_DISPATCH_REMAINING_NS <= capture['clock']['deadline_ns'], 'one_insufficient_budget')
        capture['clock']['dispatch_ns'] = dispatch
        capture['counts']['dispatch_calls'] = 1
        observation = cr.isolated_run(config, invocation, Path(context['component_output']), _simulation=context['simulation'])
        capture['clock']['run_return_ns'] = gp.time.monotonic_ns()
        observation_bytes = cr.encoded(observation)
        observation_path = Path(context['observation_path'])
        fd = os.open(observation_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 384)
        try:
            position = 0
            while position < len(observation_bytes):
                n = os.write(fd, observation_bytes[position:position + 65536])
                _responses_need(n > 0, 'one_observation_write')
                position += n
            os.fsync(fd)
        finally:
            os.close(fd)
        capture['observation_ref'] = cr.isolated_record('Artifact', artifact=observation_path.name, sha256=_responses_sha(observation_bytes), byte_length=len(observation_bytes))
        receipt = cr.verify_isolated_bundle(config, Path(context['component_output']) / 'bundle.json', observation_path)
        capture['clock']['verified_ns'] = gp.time.monotonic_ns()
        capture['counts']['verified_receipts'] = 1
        summary = _responses_decode(_responses_unb64(observation['stdout_utf8_b64'], config['caps']['max_engine_command_stream_bytes']))
        component_retained = summary['retained_bytes'] + len(observation_bytes)
        _responses_uint(component_retained, config['caps']['max_retained_bytes'])
        store.maximum = config['caps']['max_retained_bytes'] - component_retained
        _responses_need(store.total <= store.maximum, 'one_combined_retention_cap')
        bundle = _responses_decode(cr.artifact_read(Path(context['component_output']) / 'bundle.json', config['caps']['max_retained_bytes']))
        capture.update(bundle_ref=observation['bundle_ref'], receipt_ref=bundle['receipt_ref'], result_ref=receipt['result_ref'])
        _responses_need(receipt['complete'] is True, 'one_component_incomplete')
        result = _responses_decode(_responses_read_ref(cr, Path(context['component_output']), receipt['result_ref'], config['caps']['max_retained_bytes']))
        capture.update(bundle_ref=observation['bundle_ref'], receipt_ref=bundle['receipt_ref'], result_ref=receipt['result_ref'], component_result=result, status='verified', reason=None)
        returned = _responses_unb64(result['returned_utf8_b64'], 3145728)
        capture['counts'].update(complete_results=1, consumed_units=1, projected_tool_uses=1, projected_tool_results=1, canonical_rows=3, returned_bytes=len(returned))
        if result['kind'] == 'Bash':
            capture['counts'].update(stdout_bytes=len(result['facts']['stdout_utf8'].encode()), stderr_bytes=len(result['facts']['stderr_utf8'].encode()))
        capture['clock']['projected_ns'] = gp.time.monotonic_ns()
        capture['clock']['finished_ns'] = capture['clock']['projected_ns']
        (rows, maps) = gp.project(raw, source['identity']['session_id'], integrated_capture=capture)
        capture['clock']['projected_ns'] = gp.time.monotonic_ns()
        capture['clock']['finished_ns'] = capture['clock']['projected_ns']
        _responses_validate_one_capture(gp, cr, capture, actual_claim=actual_claim, rows=rows)
        capture['clock']['finished_ns'] = gp.time.monotonic_ns()
        _responses_validate_clock(capture)
        canonical_bytes = b''.join((_responses_canonical(row) + b'\n' for row in rows))
        mapping_bytes = _responses_canonical(dict(schema=gp.MAPPING, facts=maps))
        _responses_need(gp.time.monotonic_ns() <= capture['clock']['deadline_ns'], 'one_acceptance_deadline')
        capture_ref = store.put('capture.json', _responses_canonical(capture))
        store.put('canonical.jsonl', canonical_bytes)
        store.put('mapping.json', mapping_bytes)
        _responses_need(gp.time.monotonic_ns() <= capture['clock']['deadline_ns'], 'one_publication_deadline')
        terminal = dict(schema='tackle-responses-one-tool-terminal/1', outcome='completed', reason=None, capture_ref=capture_ref, canonical_sha256=_responses_sha(canonical_bytes), mapping_sha256=_responses_sha(mapping_bytes), initiated_requests=1, cost_usd='n/a', proof_scope='source_simulation', finished_check_ns=gp.time.monotonic_ns(), **{key: False for key in _responses_READINESS})
        store.put('result.json', _responses_canonical(terminal))
        _responses_need(gp.time.monotonic_ns() <= capture['clock']['deadline_ns'], 'one_publication_deadline')
        return (terminal, canonical_bytes)
    except Exception as problem:
        code = getattr(problem, 'code', type(problem).__name__)
        if not (type(code) is str and re.fullmatch('[A-Za-z0-9_.:-]{1,128}', code)):
            code = 'one_instrument_error'
        capture.update(status='instrument_incomplete', reason=code)
        capture['counts'].update(projected_tool_uses=0, projected_tool_results=0, canonical_rows=0)
        capture['clock']['finished_ns'] = gp.time.monotonic_ns()
        failure = dict(schema='tackle-responses-one-tool-failure/1', outcome='instrument_error', reason=code, capture=capture, cost_usd='n/a', proof_scope='source_simulation', **{key: False for key in _responses_READINESS})
        store.put('failure.json', _responses_canonical(failure))
        return (failure, b'')


def execute(configured, out, files, sessions, install=None, stage='smoke', network=None, control=None, responses_contract=None):
    if responses_contract is not None:
        return _responses_responses_execute_single(sys.modules[__name__], controlled_route, configured, out, files, sessions, install, stage, network, control, responses_contract)
    limits = {'seconds': 900, 'requests': 60, **(control or {})}
    if (set(limits) != {'seconds', 'requests'} or type(limits['requests']) is not int or
            not 0 < limits['requests'] <= 60 or type(limits['seconds']) not in (int, float) or
            not math.isfinite(limits['seconds']) or not 0 < limits['seconds'] <= 900):
        raise Refused('synthetic_workload_limits')
    account = ledger(configured)
    episode = canonical(configured['roots']['run_root']) / uuid.uuid4().hex
    for name in ('home', 'codex', 'work', 'tmp'):
        (episode / name).mkdir(mode=0o700, parents=True)
    write_files(episode / 'work', files)
    skill = episode / 'home/skill' if install else None
    if install:
        write_files(skill, install)
    if tree_sensitive(episode):
        shutil.rmtree(episode)
        raise Refused('credential_before_launch')
    begin = time.monotonic()
    protected = out / 'network.jsonl'
    listener = None
    if network:
        listener = network_listener.Listener(network['port'], network['status'], protected)
        try:
            listener.start()
        except (OSError, network_listener.PortUnavailable):
            raise Refused('synthetic_loopback_listener_unavailable') from None
    canonical_rows, maps, captures = [], [], []
    raw_hasher = hashlib.sha256()
    outside = canonical(configured['roots']['run_root']).parent / 'repo/outside-sentinel'
    outside.parent.mkdir(exist_ok=True)
    if not outside.exists():
        outside.write_text('outside-preserve\n')
    initiated = 0
    stop = None
    try:
        for index, supplied in enumerate(sessions, 1):
            payload = operation(supplied.copy())
            if payload.get('operation') == 'network':
                if not listener:
                    raise StopEpisode('network_not_declared')
                payload['port'] = network['port']
            session = uuid.uuid4().hex
            remainder = limits['seconds'] - (time.monotonic() - begin) - (2 if listener else 0)
            if initiated >= limits['requests'] or remainder <= 0 or (initiated + 1) * REQUEST_USD > CAPS['episode']['usd']:
                raise StopEpisode('episode_limit', 'timeout')
            try:
                claim = account.claim(session, 'synthetic-request', stage, REQUEST_USD,
                                      configured['caps']['probe_usd'] if stage == 'probe' else configured['caps']['stages'][stage],
                                      configured['caps']['total_usd'])
            except mechanics.CapReached:
                raise StopEpisode('stage_headroom_exhausted', 'unobserved') from None
            if listener:
                listener.session = index
            argv = fixed_argv(configured, 'stub_cli.py', '--work', episode / 'work', '--outside',
                              outside, '--session', session)
            if skill:
                argv += ['--skill', str(skill)]
            encoded = json.dumps(payload).encode()
            env = process_env(episode)
            if has_sensitive(encoded) or has_sensitive(json.dumps(argv).encode()) or has_sensitive(json.dumps(env).encode()):
                raise StopEpisode('credential')
            child = mechanics.launch(argv, episode / 'work', env, encoded, remainder)
            raw_hasher.update(child.stdout)
            if child.exit is not None:
                initiated += 1
            dump(out / 'dispatch.json', {'scope': 'synthetic process census', 'initiated_requests': initiated,
                                         'last_request_id': session, 'reserved_before_launch': True})
            capture = {'session_id': session, 'thread_id': session, 'request_id': session,
                       'claim': claim, 'argv': argv, 'cwd': str(episode / 'work'), 'env': env,
                       'native_exit': child.exit, 'seconds': child.seconds, 'remaining_seconds': remainder,
                       'stdout_sha256': sha(child.stdout), 'stderr_sha256': sha(child.stderr),
                       'cost_usd': NA, 'synthetic_reserved_usd': REQUEST_USD, 'timeout': child.timed_out,
                       'interrupted': child.interrupted, 'started_at': child.started, 'finished_at': child.ended}
            if has_sensitive(child.stdout) or has_sensitive(child.stderr) or tree_sensitive(episode):
                # Only this fresh, task-created root is removed; no input/source/state deletion.
                shutil.rmtree(episode)
                raise StopEpisode('credential')
            folder = out / ('session-' + str(index))
            folder.mkdir()
            (folder / 'stdout.bin').write_bytes(child.stdout)
            (folder / 'stderr.bin').write_bytes(child.stderr)
            dump(folder / 'capture.json', capture)
            captures.append(capture)
            if child.interrupted:
                raise StopEpisode('interrupted')
            if child.timed_out:
                raise StopEpisode('wall_limit', 'timeout')
            if child.exit != 0 or child.error:
                raise StopEpisode('synthetic_launcher_or_worker_error')
            rows, mappings = project(child.stdout, session)
            canonical_rows += rows
            maps += mappings
    except (StopEpisode, Malformed, Refused) as problem:
        stop = problem if isinstance(problem, StopEpisode) else StopEpisode(str(problem) if isinstance(problem, Refused) else 'trace_schema')
    finally:
        if listener:
            time.sleep(2)
            listener.stop()
    if protected.exists() and has_sensitive(protected.read_bytes()):
        protected.unlink()
        stop = StopEpisode('credential')
    canonical_rows.append({'type': 'result', 'subtype': 'success' if stop is None else 'instrument_error'})
    canonical_data = b''.join(json.dumps(row, ensure_ascii=False).encode() + b'\n' for row in canonical_rows)
    mapping_data = (json.dumps({'schema': MAPPING, 'facts': maps}, ensure_ascii=False, indent=2) + '\n').encode()
    if stop is None and (has_sensitive(canonical_data) or has_sensitive(mapping_data)):
        shutil.rmtree(episode)
        stop = StopEpisode('credential')
    if stop is None:
        (out / 'canonical.jsonl').write_bytes(canonical_data)
        (out / 'mapping.json').write_bytes(mapping_data)
        final = out / 'final'
        final.mkdir()
        write_files(final, tree(episode / 'work'))
        receipts = canonical(configured['roots']['state_dir']) / 'trace-receipts.json'
        existing = json.loads(receipts.read_text()) if receipts.exists() else {}
        existing[str(out / 'canonical.jsonl')] = {
            'canonical': sha(canonical_data), 'mapping': sha((out / 'mapping.json').read_bytes()),
            'final': harness.files_digest(tree(final)),
            'raw': {str(i): sha((out / ('session-' + str(i)) / 'stdout.bin').read_bytes()) for i in range(1, len(captures) + 1)},
            'network': sha(protected.read_bytes()) if protected.exists() else None,
            'fingerprints': configured['fingerprints']}
        dump(receipts, existing)
    own = {row['canonical_id']: row['original_name'] for row in maps if row['fact'] == 'invocation'
           and row['original_name'] in ('NativeRead', 'NativeWrite')
           and Path(row['exact_input']['file_path']).is_relative_to(episode / 'work')}
    completed_own = {own[row['canonical_id']] for row in maps if row['fact'] == 'result'
                     and row['canonical_id'] in own and 'error' not in row['exact_result']}
    result = {'scope': 'synthetic fixture/tool-wrapper controls only', 'initiated_requests': initiated,
              'sessions': captures, 'outcome': stop.outcome if stop else 'completed',
              'reason': stop.reason if stop else None, 'wall_seconds': time.monotonic() - begin,
              'cost_usd': NA, 'canonical_sha256': sha(canonical_data) if stop is None else None,
              'raw_sha256': raw_hasher.hexdigest(),
              'mapping_version': MAPPING, 'archive_bytes_read': mechanics.archive_bytes_read(canonical_data) if stop is None else NA,
              'work_tree_read_allowed': 'NativeRead' in completed_own,
              'work_tree_write_allowed': 'NativeWrite' in completed_own,
              'live_ready': False, 'live_route_accepted': False}
    dump(out / 'result.json', result)
    return result, canonical_data


def judge(configured, out, final, transcript, network=None):
    final = scoped(configured, final)
    transcript = scoped(configured, transcript)
    contents = tree(final)
    raw = transcript.read_bytes()
    receipt_path = canonical(configured['roots']['state_dir']) / 'trace-receipts.json'
    try:
        receipt = json.loads(receipt_path.read_text())[str(transcript)]
        if (receipt['fingerprints'] != configured['fingerprints'] or receipt['canonical'] != sha(raw)
                or receipt['final'] != harness.files_digest(contents)
                or receipt['mapping'] != sha((transcript.parent / 'mapping.json').read_bytes())):
            raise ValueError()
        for index, digest in receipt['raw'].items():
            if sha((transcript.parent / ('session-' + index) / 'stdout.bin').read_bytes()) != digest:
                raise ValueError()
        expected_network = transcript.parent / 'network.jsonl'
        if bool(network) != bool(receipt['network']) or network and (
                str(network) != str(expected_network) or sha(expected_network.read_bytes()) != receipt['network']):
            raise ValueError()
    except (OSError, ValueError, KeyError, TypeError):
        raise Refused('trace_bundle_integrity') from None
    try:
        events = [json.loads(line) for line in raw.splitlines()]
        if not events or events[-1] != {'type': 'result', 'subtype': 'success'}:
            raise ValueError()
        uses, completed = {}, set()
        for event in events[:-1]:
            blocks = event.get('message', {}).get('content')
            if event.get('type') not in ('assistant', 'user') or not isinstance(blocks, list) or len(blocks) != 1:
                raise ValueError()
            if 'source' not in blocks[0] or 'original_name' not in blocks[0]:
                raise ValueError()
            block = blocks[0]
            source = block['source']
            if not isinstance(source, dict) or set(source) != {'session_id', 'event_id', 'item_id', 'line', 'byte_start', 'byte_end', 'raw_sha256'}:
                raise ValueError()
            expected = source['session_id'] + ':' + source['item_id']
            if event['type'] == 'assistant':
                if block.get('type') != 'tool_use' or block.get('id') != expected or expected in uses:
                    raise ValueError()
                uses[expected] = block
            elif block.get('type') != 'tool_result' or block.get('tool_use_id') != expected or expected not in uses or expected in completed or block.get('original_name') != uses[expected]['original_name']:
                raise ValueError()
            else:
                completed.add(expected)
        if set(uses) != completed:
            raise ValueError()
    except (ValueError, TypeError, KeyError):
        raise Refused('canonical_trace_unverifiable') from None
    if has_sensitive(raw) or tree_sensitive(final):
        raise Refused('credential')
    scratch = out / 'judged'
    (scratch / 'final').mkdir(parents=True)
    (scratch / 'home').mkdir()
    (scratch / 'tmp').mkdir()
    (scratch / 'codex').mkdir()
    write_files(scratch / 'final', contents)
    (scratch / 'transcript.jsonl').write_bytes(raw)
    argv = fixed_argv(configured, 'oracle/check.py', '--final', scratch / 'final', '--transcript', scratch / 'transcript.jsonl')
    if network:
        network = scoped(configured, network)
        if network.is_relative_to(final) or has_sensitive(network.read_bytes()):
            raise Refused('network_log_untrusted')
        (scratch / 'network.jsonl').write_bytes(network.read_bytes())
        argv += ['--network-log', str(scratch / 'network.jsonl')]
    before = harness.files_digest(tree(scratch / 'final'))
    child = mechanics.launch(argv, scratch, process_env(scratch), b'', configured['oracle']['seconds'])
    dump(out / 'oracle-capture.json', {'argv': argv, 'cwd': str(scratch), 'native_exit': child.exit,
                                     'stdout_sha256': sha(child.stdout), 'stderr_sha256': sha(child.stderr),
                                     'scope': 'pinned synthetic wrapper; no OS sandbox proof'})
    if has_sensitive(child.stdout) or has_sensitive(child.stderr):
        raise Refused('credential')
    (out / 'oracle-stdout.bin').write_bytes(child.stdout)
    (out / 'oracle-stderr.bin').write_bytes(child.stderr)
    if child.exit != 0 or child.timed_out or child.interrupted or before != harness.files_digest(tree(scratch / 'final')):
        raise Refused('synthetic_oracle_error')
    verdict = mechanics.parse_verdict(child.stdout)
    dump(out / 'oracle.json', verdict)
    return verdict


def probe(configured, args, out):
    repo, workspace, install_root = [scoped(configured, value) for value in (args.repo, args.workspace, args.install)]
    tree(repo), tree(workspace), tree(install_root)
    root = canonical(configured['roots']['run_root'])
    scratch = root / uuid.uuid4().hex
    for name in ('home', 'codex', 'work', 'tmp'):
        (scratch / name).mkdir(parents=True, mode=0o700)
    inside, outside = scratch / 'work/inside-sentinel', scratch / 'outside-sentinel'
    inside.write_text('inside-before\n')
    outside.write_text('outside-preserve\n')
    outside.chmod(0)
    env = process_env(scratch)
    profile = {'scope': 'synthetic stub policy only', 'writable_roots': [str(scratch / 'work')], 'network': False}
    dump(scratch / 'codex/synthetic-profile.json', profile)
    argv = fixed_argv(configured, 'stub_cli.py', 'sandbox', '-P', 'gpt-measurement', '-C', scratch / 'work',
                      configured['interpreter']['path'], '-B', FIXTURES / 'sentinel_helper.py',
                      '--inside', inside, '--outside', outside, '--network-result', scratch / 'network-control.json',
                      '--out', scratch / 'kernel-control.json')
    account = ledger(configured)
    try:
        claim = account.claim(uuid.uuid4().hex, 'synthetic-offline-control', 'probe', REQUEST_USD,
                              CAPS['probe_usd'], CAPS['total_usd'])
    except mechanics.CapReached:
        raise Refused('probe_headroom_exhausted') from None
    try:
        child = mechanics.launch(argv, scratch / 'work', env, b'', 30)
    finally:
        outside.chmod(0o600)
    dump(out / 'offline-capture.json', {'argv': argv, 'cwd': str(scratch / 'work'), 'env': env,
                                      'claim': claim, 'native_exit': child.exit,
                                      'stdout_sha256': sha(child.stdout), 'stderr_sha256': sha(child.stderr),
                                      'scope': 'pinned stub sandbox argv; no Codex or kernel sandbox proof'})
    (out / 'offline-stdout.bin').write_bytes(child.stdout)
    (out / 'offline-stderr.bin').write_bytes(child.stderr)
    if child.exit != 0 or child.timed_out or child.interrupted:
        raise Refused('synthetic_offline_helper_unavailable')
    kernel = json.loads((scratch / 'kernel-control.json').read_text())
    local = json.loads((scratch / 'network-control.json').read_text())
    dump(out / 'kernel-control.json', kernel)
    dump(out / 'network-control.json', local)
    if not kernel['outside_denied'] or kernel['outside_errno'] is None or not kernel['outside_write_denied'] or kernel['outside_write_errno'] is None or not local['refused']:
        raise Refused('synthetic_offline_control_failed')
    installed = tree(install_root) or None
    if installed and 'SKILL.md' not in installed:
        raise Refused('synthetic_install_shape')
    result, _ = execute(configured, out, {'inside-sentinel': b'inside-before\n'}, [{'operation': 'probe'}],
                        install=installed, stage='probe')
    result['outside_wrapper_denied'] = False
    if result['outcome'] == 'completed':
        mapped = json.loads((out / 'mapping.json').read_text())['facts']
        result['outside_wrapper_denied'] = any(row['fact'] == 'result' and row['exact_result'].get('mechanism') == 'synthetic wrapper'
                                               and row['exact_result'].get('error') == 'PermissionError' for row in mapped)
        # The public synthetic sentinel is updated only from the actual completed write result.
        public_inside = root / 'inside-sentinel'
        if public_inside.exists() and not public_inside.is_symlink() and public_inside.stat().st_nlink == 1:
            public_inside.write_bytes((out / 'final/inside-sentinel').read_bytes())
    result['offline_control_scope'] = kernel['scope']
    result['offline_initiated_requests'] = 1
    dump(out / 'result.json', result)
    return result


def cohort_run(configured, args, out):
    repo, cohort, installs = [scoped(configured, value) for value in (args.repo, args.cohort, args.install)]
    tree(repo), tree(cohort), tree(installs)
    if args.stage not in ('smoke', 'held-out'):
        raise Refused('synthetic_stage_unsupported')
    check = harness.protocol()
    manifest_path, records_path = cohort / check.MANIFEST, cohort / check.EPISODES
    manifest = json.loads(manifest_path.read_bytes(), object_pairs_hook=unique, parse_constant=reject_constant)
    report = check.Report()
    context = check.check_manifest(manifest, report)
    if report.errors or manifest['executor'] != {'harness': 'tackle-gpt-synthetic', 'model': BINDING['model'], 'effort': 'high'}:
        raise Refused('synthetic_manifest_unverifiable')
    if set(manifest['arms']) - {'control', 'method', 'method:candidate'}:
        raise Refused('synthetic_arms_unsupported')
    workload = json.loads((cohort / 'workload.json').read_bytes(), object_pairs_hook=unique, parse_constant=reject_constant)
    closed(workload, ('schema', 'files', 'sessions', 'limits', 'network'))
    if workload['schema'] != 'tackle-gpt-synthetic-workload/1' or not isinstance(workload['files'], dict) or not isinstance(workload['sessions'], list) or not workload['sessions']:
        raise Refused('synthetic_workload_schema')
    if not all(isinstance(name, str) and isinstance(data, str) for name, data in workload['files'].items()):
        raise Refused('synthetic_workload_files')
    files = {name: data.encode() for name, data in workload['files'].items()}
    for session in workload['sessions']:
        operation(session)
    network = workload['network']
    if network is not None and (not isinstance(network, dict) or set(network) != {'port', 'status'}
            or type(network['port']) is not int or not 1024 <= network['port'] <= 65535
            or type(network['status']) is not int or network['status'] not in (200, 403)):
        raise Refused('synthetic_network_schema')
    artifacts = {}
    for arm, folder in (('method', 'baseline'), ('method:candidate', 'candidate')):
        if arm in manifest['arms']:
            artifacts[arm] = harness.read_install(installs / folder)
    baseline = harness.files_digest(artifacts.get('method', {}))
    candidate = harness.files_digest(artifacts.get('method:candidate', artifacts.get('method', {})))
    if manifest['artifacts'] != {'baseline_sha256': baseline, 'candidate_sha256': candidate}:
        raise Refused('synthetic_install_pin_mismatch')
    if 'method:candidate' in artifacts and baseline == candidate:
        raise Refused('synthetic_install_not_distinct')
    if any(v['fixture_sha256'] != harness.files_digest(files) for v in manifest['variants']) or manifest['oracle_sha256'] != TRUSTED['oracle/check.py']:
        raise Refused('synthetic_fixture_oracle_pin_mismatch')
    identity = sha(manifest_path.read_bytes())
    continuity = canonical(configured['roots']['state_dir']) / ('cohort-' + identity + '.json')
    pins = {'manifest': identity, 'cohort_path': str(cohort), 'workload': sha((cohort / 'workload.json').read_bytes()),
            'fingerprints': configured['fingerprints'], 'artifacts': manifest['artifacts'], 'stage': args.stage}
    lines = records_path.read_bytes().splitlines() if records_path.exists() else []
    if continuity.exists():
        if json.loads(continuity.read_text()) != pins:
            raise Refused('synthetic_continuity_drift')
    elif lines:
        raise Refused('synthetic_continuity_unverifiable')
    else:
        dump(continuity, pins)
        records_path.touch()
    by_id = {entry['episode_id']: (position, entry) for position, entry in enumerate(manifest['order'])}
    for position, raw in enumerate(lines):
        row = json.loads(raw)
        at = report.at(check.EPISODES, position + 1)
        if at.closed(row, check.EPISODE_FIELDS, 'record'):
            check.check_fields(row, at)
            check.check_against_manifest(row, context, by_id, at)
            at.expect(row['order_index'] == position and row['prev_sha256'] == (sha(lines[position - 1]) if position else '0' * 64), 'invalid recorded prefix')
    if report.errors or len(lines) > len(manifest['order']):
        raise Refused('synthetic_record_prefix_unverifiable')
    holder = SimpleNamespace(path=records_path, lines=lines, context=context, by_id=by_id)
    actual, outcomes, stop_remaining = 0, [], False
    for position, entry in enumerate(manifest['order'][len(lines):], len(lines)):
        episode_out = out / ('episode-' + str(position))
        episode_out.mkdir()
        if stop_remaining:
            result = {'outcome': 'unobserved', 'reason': 'prior_instrument_stop', 'initiated_requests': 0, 'sessions': [], 'wall_seconds': 0}
            raw_digest = None
        else:
            result, _ = execute(configured, episode_out, files, workload['sessions'], artifacts.get(entry['arm']),
                                args.stage, network, workload['limits'])
            actual += result['initiated_requests']
            raw_digest = result['raw_sha256']
        if result.get('reason') == 'synthetic_launcher_or_worker_error':
            # Raw failed tool facts and reservations remain; an incomplete worker has no judgment.
            stopped = {'scope': 'synthetic fixture only', 'initiated_requests': actual,
                       'resumed_records': len(lines), 'appended_records': len(outcomes),
                       'outcomes': outcomes + [result['outcome']], 'reason': result['reason'],
                       'protocol_native_exit': NA, 'cost_usd': NA,
                       'live_ready': False, 'live_route_accepted': False}
            dump(out / 'result.json', stopped)
            return stopped, 1
        verdict = None
        if result['outcome'] == 'completed':
            verdict = judge(configured, episode_out, episode_out / 'final', episode_out / 'canonical.jsonl',
                            episode_out / 'network.jsonl' if network else None)
        outcome = verdict['outcome'] if verdict else result['outcome']
        if outcome == 'unobserved':
            raw_digest = None
        scores = {key: None for key in check.SCORE_FIELDS}
        if verdict:
            scores['correct_action'] = verdict['scores'].get('synthetic_state')
            scores['evidence'] = verdict['scores'].get('observed_calls')
        line = {'schema': 'tackle-episode/1', 'cohort_id': manifest['cohort_id'], **entry,
                'split': context['variants'][(entry['scenario_id'], entry['variant_id'])]['split'],
                'order_index': position, 'artifact_sha256': harness.files_digest(artifacts[entry['arm']]) if entry['arm'] in artifacts else None,
                'executor': manifest['executor'], 'roles': [], 'judge': {'kind': 'mechanical', 'model_family': NA, 'blinded': False},
                'rule_exposure': False, 'outcome': outcome,
                'invalid_reason': verdict.get('invalid_reason') if verdict else result['reason'],
                'scores': scores, 'cost': {'tokens_in': NA, 'tokens_out': NA,
                    'wall_seconds': math.ceil(result['wall_seconds']), 'tool_calls': NA, 'files_written': NA},
                'transcript_sha256': raw_digest,
                'started_at': result['sessions'][0]['started_at'] if result['sessions'] else NA,
                'finished_at': result['sessions'][-1]['finished_at'] if result['sessions'] else NA}
        if has_sensitive(json.dumps(line).encode()):
            raise Refused('credential_protocol_record')
        mechanics.append_record(holder, line)
        outcomes.append(outcome)
        stop_remaining = stop_remaining or verdict is None
    # This is the actual unchanged protocol CLI, consuming the actual synthetic cohort records.
    argv = [configured['interpreter']['path'], '-B', str(harness.ROOT / 'eval/protocol-v2/check.py'), str(cohort)]
    protocol_inputs = {name: (cohort / name).read_bytes() for name in (check.MANIFEST, check.EPISODES, 'workload.json')}
    if any(has_sensitive(data) for data in protocol_inputs.values()):
        raise Refused('credential_protocol_input')
    input_root = out / 'protocol-input'
    input_root.mkdir()
    write_files(input_root, protocol_inputs)
    scratch = out / 'protocol-runtime'
    for name in ('home', 'codex', 'tmp'):
        (scratch / name).mkdir(parents=True)
    child = mechanics.launch(argv, cohort, process_env(scratch), b'', 30)
    if has_sensitive(child.stdout) or has_sensitive(child.stderr):
        raise Refused('credential_protocol_output')
    (out / 'protocol-stdout.bin').write_bytes(child.stdout)
    (out / 'protocol-stderr.bin').write_bytes(child.stderr)
    dump(out / 'protocol-capture.json', {'argv': argv, 'cwd': str(cohort), 'native_exit': child.exit,
                                        'input_sha256': {name: sha(data) for name, data in protocol_inputs.items()},
                                        'stdout_sha256': sha(child.stdout), 'stderr_sha256': sha(child.stderr)})
    if child.exit != 0 or child.timed_out or child.interrupted or any((cohort / name).read_bytes() != data for name, data in protocol_inputs.items()):
        raise Refused('synthetic_protocol_error')
    result = {'scope': 'synthetic fixture only', 'initiated_requests': actual, 'resumed_records': len(lines) - len(outcomes),
              'appended_records': len(outcomes), 'outcomes': outcomes, 'protocol_native_exit': child.exit,
              'cost_usd': NA, 'live_ready': False, 'live_route_accepted': False}
    dump(out / 'result.json', result)
    return result, 1 if any(outcome not in ('avoided', 'fell') for outcome in outcomes) else 0


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest='command', required=True)
    for command in ('preflight', 'probe', 'run', 'judge'):
        item = commands.add_parser(command)
        item.add_argument('--config', required=True)
        item.add_argument('--out', required=True)
        if command in ('probe', 'run'):
            item.add_argument('--repo', required=True)
            item.add_argument('--install', required=True)
        if command == 'probe':
            item.add_argument('--workspace', required=True)
        if command == 'run':
            item.add_argument('--cohort', required=True)
            item.add_argument('--stage', required=True)
        if command == 'judge':
            for name in ('oracle', 'final', 'transcript'):
                item.add_argument('--' + name, required=True)
            item.add_argument('--network-log')
    for command in ('controlled-preflight', 'controlled-run', 'controlled-verify'):
        item = commands.add_parser(command)
        item.add_argument('--config', required=True)
        item.add_argument('--out', required=True)
        if command == 'controlled-run':
            item.add_argument('--episode', required=True)
        if command == 'controlled-verify':
            item.add_argument('--bundle', required=True)
    return result


def main(argv=None):
    args = parser().parse_args(argv)
    if args.command.startswith('controlled-'):
        import controlled_route
        return controlled_route.main_parsed(args)
    mechanics.install_signal_handlers()
    out, configured, packet = None, None, None
    try:
        out = canonical(args.out)
        if os.path.lexists(out):
            raise Malformed('output_exists')
        configured = config(args.config)
        safe_output(configured, out)
        absent = missing(configured)
        reason = (absent[0] if configured['mode'] == 'synthetic' else 'live_capabilities_unavailable') if absent else None
        packet = {'schema': 'tackle-gpt-route-packet/1', 'subcommand': args.command,
                  'mode': configured['mode'], 'outcome': 'unsupported' if absent else 'synthetic_supported', 'reason': reason,
                  'missing_capabilities': absent, 'requested_binding': BINDING,
                  'source_sha256': sha(Path(__file__).read_bytes()), 'mapping_version': MAPPING,
                  'checked': {'configuration': True, 'runtime_dispatched': False},
                  'limitations': ['Pinned synthetic wrapper only; live isolation/auth/trace/limiter/network unobserved.'],
                  'live_ready': False, 'live_route_accepted': False, 'task_complete': False,
                  't06_held_out_ready': False}
        out.mkdir(mode=0o700, parents=True, exist_ok=False)
        code = 1 if absent else 0
        if not absent and args.command == 'preflight':
            state = canonical(configured['roots']['state_dir'])
            tree(state)
            validate_ledger(canonical(configured['prior_ledger']['path']))
            active = state / 'spend.json'
            if active.exists():
                validate_ledger(active)
            packet['checked']['historical_ledger_read_only'] = True
        if not absent and args.command != 'preflight':
            state = canonical(configured['roots']['state_dir'])
            tree(state)
            lock_path = state / 'route.lock'
            if lock_path.is_symlink() or lock_path.exists() and lock_path.stat().st_nlink != 1:
                raise Refused('state_lock_untrusted')
            with open(lock_path, 'a+') as handle:
                try:
                    fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    raise Refused('synthetic_concurrent_operation') from None
                if args.command == 'probe':
                    result = probe(configured, args, out)
                    code = 0 if result['outcome'] == 'completed' and result['outside_wrapper_denied'] else 1
                elif args.command == 'run':
                    result, code = cohort_run(configured, args, out)
                else:
                    oracle = canonical(args.oracle)
                    if oracle != FIXTURES / 'oracle':
                        raise Refused('oracle_not_allowlisted')
                    result = judge(configured, out, args.final, args.transcript, args.network_log)
                packet['checked']['runtime_dispatched'] = args.command != 'judge' or (out / 'oracle-capture.json').exists()
                if code:
                    packet.update(outcome='instrument_stop', reason=result.get('reason', 'synthetic_episode_not_observed'))
        for name in ('capability.json', 'packet.json'):
            dump(out / name, packet)
        print(json.dumps(packet))
        return code
    except (Refused, mechanics.Refusal, mechanics.CapReached, harness.Refusal) as error:
        if packet is not None and out is not None and out.is_dir():
            packet.update(outcome='unsupported', reason=str(error))
            for name in ('capability.json', 'packet.json'):
                dump(out / name, packet)
        print(json.dumps({'error': str(error)}))
        return 1
    except (Malformed, OSError) as error:
        reason = str(error) if isinstance(error, Malformed) else 'filesystem_error'
        print(json.dumps({'error': reason}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
