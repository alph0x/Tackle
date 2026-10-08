#!/usr/bin/env python3
"""Versioned local request, admission, worker and transcript route.

The only transport is a finite subprocess fixture. Live admission refuses.
Its complete capture and owned process claims apply to these fixtures only.
"""
import base64
import copy
from decimal import Decimal
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shlex
import signal
import stat
import subprocess
import sys
import tempfile
import time
import uuid

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / 'fixtures' / 'controlled-route'
POLICY = json.loads((FIXTURE / 'streams.json').read_text(encoding='utf-8'))
VERSIONS = POLICY['versions']
IO = POLICY['io']
INSTRUCTIONS = POLICY['instructions']
TOOLS = POLICY['tools']
MODEL = 'gpt-5.6-luna'
CAPS = dict(initiative_usd='200', episode_usd='8', episode_seconds=900,
            episode_request_units=60, smoke_usd='25', held_out_usd='121', probe_usd='4')
ZERO = '0' * 64
SHELL = '/bin/sh'
PYTHON = str(Path(sys.executable).resolve())
LIVE_MISSING = ('existing_opaque_single_attempt_auth', 'account_exact_binding_stateless_wire',
    'provider_applicable_complete_billable_bound', 'authoritative_carried_headroom',
    'accepted_worker_kernel_tool_boundary', 'accepted_supervisor_finalization',
    'accepted_C20_topology_if_declared', 'accepted_actual_unchanged_consumers',
    'fresh_instrument_and_readiness_receipts', 'explicit_bounded_activation')


class Refusal(Exception):
    def __init__(self, code, detail=''):
        self.code, self.detail = code, detail
        super().__init__(code + (': ' + detail if detail else ''))


def require(condition, code, detail=''):
    if not condition:
        raise Refusal(code, detail)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def strict_json(data):
    def pairs(items):
        answer = {}
        for key, value in items:
            require(key not in answer, 'duplicate_key', key)
            answer[key] = value
        return answer
    try:
        return json.loads(data, object_pairs_hook=pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(Refusal('nonfinite')))
    except (UnicodeError, ValueError) as exc:
        raise Refusal('invalid_json', str(exc)) from exc


def fields(value, names):
    require(type(value) is dict and set(value) == set(names), 'closed_fields')


def identifier(value):
    require(type(value) is str and re.fullmatch(r'[A-Za-z0-9_-]{1,128}', value), 'invalid_id')


def relative(value):
    require(type(value) is str and value and '\\' not in value and '\0' not in value,
            'unsafe_path')
    parts = value.split('/')
    require(not value.startswith('/') and all(p not in ('', '.', '..') for p in parts),
            'unsafe_path')
    return value


def usd(value):
    require(type(value) is str and re.fullmatch(r'(0|[1-9][0-9]*)(\.[0-9]{1,9})?', value),
            'invalid_usd')
    return Decimal(value)


def typed(value, spec):
    if type(spec) is dict:
        kind = spec.get('type')
        if kind == 'string':
            require(type(value) is str, 'invalid_type')
        elif kind in ('bool', 'boolean'):
            require(type(value) is bool, 'invalid_type')
        elif kind == 'integer':
            require(type(value) is int, 'invalid_type')
        else:
            raise Refusal('unknown_field_type', kind)
        require('const' not in spec or value == spec['const'], 'invalid_constant')
        require('enum' not in spec or value in spec['enum'], 'invalid_enum')
        return
    if spec.startswith('nullable<'):
        if value is not None:
            typed(value, spec[9:-1])
    elif spec.startswith('array<'):
        require(type(value) is list, 'invalid_type')
        for item in value:
            typed(item, spec[6:-1])
    elif spec in POLICY['records']:
        validate_record(spec, value)
    elif spec == 'id':
        identifier(value)
    elif spec == 'sha256':
        require(type(value) is str and re.fullmatch('[0-9a-f]{64}', value), 'invalid_hash')
    elif spec in ('uint', 'positive_int', 'int'):
        require(type(value) is int and (spec == 'int' or value >= (1 if spec == 'positive_int' else 0)),
                'invalid_integer')
    elif spec == 'bool':
        require(type(value) is bool, 'invalid_type')
    elif spec == 'usd':
        usd(value)
    elif spec == 'usd_or_na':
        if value != 'n/a':
            usd(value)
    elif spec == 'relative_path':
        relative(value)
    elif spec == 'absolute_task_path':
        require(type(value) is str and Path(value).is_absolute(), 'unsafe_path')
    elif spec == 'missing_fact_code':
        require(value in ('spawn_failed', 'main_exit_missing', 'owned_handles_live',
                'stdout_eof_missing', 'stderr_eof_missing', 'capture_incomplete',
                'snapshot_missing', 'source_mismatch', 'late_fact', 'authority_mismatch',
                'timer_continuity_unverifiable', 'unit_attribution_unverifiable'), 'invalid_enum')
    elif spec == 'config_caps':
        validate_caps(value)
    elif spec == 'existing_invocation':
        validate_invocation(value)
    elif spec == 'string':
        require(type(value) is str, 'invalid_type')
    else:
        raise Refusal('unknown_field_type', spec)


def record(name, **values):
    answer = dict(schema=POLICY['records'][name]['version'], **values)
    validate_record(name, answer)
    return answer


def validate_record(name, value):
    schema = POLICY['records'][name]
    properties = schema['properties']
    fields(value, properties)
    for key, spec in properties.items():
        if name == 'supervisor_event' and key == 'facts':
            discriminator = {'spawn_ack': 'supervisor_spawn_facts', 'main_exit': 'supervisor_exit_facts',
                'tracked_fixture_handles_empty': 'supervisor_empty_facts', 'stdout_eof': 'supervisor_eof_facts',
                'stderr_eof': 'supervisor_eof_facts', 'snapshot_observed': 'supervisor_snapshot_facts',
                'offline_finalized': 'supervisor_final_facts', 'instrument_incomplete': 'supervisor_incomplete_facts'}
            require(value['kind'] in discriminator, 'invalid_enum')
            validate_record(discriminator[value['kind']], value[key])
        else:
            typed(value[key], spec)


def artifact_read(path, maximum=IO['max_episode_retained_raw_bytes']):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, 'unsafe_file')
        require(info.st_size <= maximum, 'capture_overflow')
        with os.fdopen(os.dup(fd), 'rb') as stream:
            return stream.read(maximum + 1)
    finally:
        os.close(fd)


def directory(path):
    path = Path(path)
    require(path.is_absolute() and str(path) == str(path.resolve()), 'unsafe_root')
    for item in (path, *path.parents):
        require(not item.is_symlink(), 'unsafe_root')
    info = path.stat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid(), 'unsafe_root')
    return path


def identity(path):
    path = directory(path)
    info = path.stat()
    return record('root_identity', canonical_path=str(path), device=info.st_dev,
                  inode=info.st_ino, owner_uid=info.st_uid)


def tree_digest(root):
    entries = []
    for parent, dirs, names in os.walk(root, followlinks=False):
        for name in dirs:
            require(not (Path(parent) / name).is_symlink(), 'unsafe_file')
        for name in sorted(names):
            path = Path(parent) / name
            data = artifact_read(path)
            entries.append([str(path.relative_to(root)), len(data), digest(data)])
    return digest(encoded(sorted(entries)))


def pins():
    components = {name + '_sha256': digest(artifact_read(path)) for name, path in (
        ('gpt_route', HERE / 'gpt_route.py'), ('controlled_route', Path(__file__)),
        ('controlled_worker', HERE / 'controlled_worker.py'),
        ('stub_responses', FIXTURE / 'stub_responses.py'),
        ('command_fixture', FIXTURE / 'command_fixture.py'))}
    answer = dict(components=components,
                  interpreter=dict(path=PYTHON, version=platform.python_version(), sha256=digest(artifact_read(PYTHON))),
                  shell=dict(path=SHELL, version='posix-sh/1', sha256=digest(artifact_read(os.path.realpath(SHELL)))),
                  fixture_tree_sha256=tree_digest(FIXTURE), policy_sha256=digest(artifact_read(FIXTURE / 'streams.json')))
    answer['fingerprint'] = digest(encoded(dict(pins=answer, binding=MODEL, route=VERSIONS['route'])))
    return answer


def validate_caps(caps):
    fields(caps, CAPS)
    for key, fixed in CAPS.items():
        if key == 'probe_usd':
            require(0 < usd(caps[key]) <= Decimal(200), 'invalid_cap')
        else:
            require(type(caps[key]) is type(fixed) and caps[key] == fixed, 'invalid_cap')


def create_config(task_root):
    """Create a fresh synthetic authority tree for tests and local demonstrations."""
    task = Path(task_root).absolute()
    task.mkdir(mode=0o700, parents=False, exist_ok=False)
    for name in ('runs', 'state', 'evidence'):
        (task / name).mkdir(mode=0o700)
    roots = dict(task_root=str(task), run_root=str(task / 'runs'),
                 state_root=str(task / 'state'), evidence_root=str(task / 'evidence'))
    fixed = pins()
    authority = record('ledger_authority', authority_id='authority_' + uuid.uuid4().hex,
        initiative_id='synthetic_initiative', ledger_id='synthetic_ledger', checkpoint_id='checkpoint_0',
        task_root=identity(task), state_root=identity(task / 'state'),
        owner_handle='episode_owner', fingerprint=fixed['fingerprint'])
    checkpoint = dict(schema=VERSIONS['checkpoint'], proof_scope='synthetic_nonbillable',
        initiative_id=authority['initiative_id'], ledger_id=authority['ledger_id'],
        unit_policy='controlled-inference-attempt/1', caps=copy.deepcopy(CAPS), prior_claims=[],
        checkpoint_id=authority['checkpoint_id'], authority_binding=authority,
        journal_prefix=record('journal_prefix', cutoff_sequence=0, cutoff_sha256=ZERO), episode_anchors=[])
    checkpoint_path = task / 'state' / 'checkpoint.json'
    checkpoint_path.write_bytes(encoded(checkpoint))
    config = dict(schema=VERSIONS['config'], mode='offline',
        binding=dict(model=MODEL, requested_host_effort='xhigh', portable_effort='high'),
        profiles={key: VERSIONS[key] for key in ('wire', 'worker', 'history', 'scheduler', 'tools')},
        roots=roots, pins=fixed, policies=dict(neutral_instructions=INSTRUCTIONS, tool_schemas=TOOLS,
        history=VERSIONS['history'], scheduler=VERSIONS['scheduler'], io=IO),
        checkpoint=dict(path=str(checkpoint_path), sha256=digest(checkpoint_path.read_bytes())), caps=copy.deepcopy(CAPS))
    (task / 'config.json').write_bytes(encoded(config))
    return config


def validate_config(config):
    require(type(config) is dict, 'closed_fields')
    # This branch deliberately precedes any candidate capability or root access.
    require(config.get('mode') != 'live', 'live_unsupported')
    fields(config, ('schema', 'mode', 'binding', 'profiles', 'roots', 'pins', 'policies', 'checkpoint', 'caps'))
    require(config['schema'] == VERSIONS['config'] and config['mode'] == 'offline', 'invalid_version')
    require(config['binding'] == dict(model=MODEL, requested_host_effort='xhigh', portable_effort='high'), 'binding_mismatch')
    require(config['profiles'] == {k: VERSIONS[k] for k in ('wire', 'worker', 'history', 'scheduler', 'tools')}, 'profile_mismatch')
    require(config['policies'] == dict(neutral_instructions=INSTRUCTIONS, tool_schemas=TOOLS,
            history=VERSIONS['history'], scheduler=VERSIONS['scheduler'], io=IO), 'policy_mismatch')
    validate_caps(config['caps'])
    fields(config['roots'], ('task_root', 'run_root', 'state_root', 'evidence_root'))
    roots = {k: directory(v) for k, v in config['roots'].items()}
    task = roots['task_root']
    temporary = Path(tempfile.gettempdir()).resolve()
    require(task != temporary and temporary in task.parents, 'root_not_generated_temporary')
    require(len(set(roots.values())) == 4 and all(roots[k].parent == task for k in ('run_root', 'state_root', 'evidence_root')),
            'root_binding_mismatch')
    fields(config['pins'], ('components', 'interpreter', 'shell', 'fixture_tree_sha256', 'policy_sha256', 'fingerprint'))
    for name, path in (('interpreter', PYTHON), ('shell', SHELL)):
        fields(config['pins'][name], ('path', 'version', 'sha256'))
        require(config['pins'][name]['path'] == path, 'runtime_not_allowlisted')
    require(config['pins'] == pins(), 'pin_mismatch')
    fields(config['checkpoint'], ('path', 'sha256'))
    cp_path = Path(config['checkpoint']['path'])
    require(cp_path.parent == roots['state_root'] and cp_path.name == 'checkpoint.json', 'checkpoint_path')
    raw = artifact_read(cp_path)
    require(digest(raw) == config['checkpoint']['sha256'], 'checkpoint_pin')
    checkpoint = strict_json(raw)
    fields(checkpoint, POLICY['checkpoint_fields'])
    for key, spec in POLICY['checkpoint_fields'].items():
        typed(checkpoint[key], spec)
    require(checkpoint['caps'] == config['caps'], 'cap_mismatch')
    authority = checkpoint['authority_binding']
    require(authority['task_root'] == identity(task) and authority['state_root'] == identity(roots['state_root'])
            and authority['fingerprint'] == config['pins']['fingerprint']
            and authority['initiative_id'] == checkpoint['initiative_id']
            and authority['ledger_id'] == checkpoint['ledger_id']
            and authority['checkpoint_id'] == checkpoint['checkpoint_id']
            and authority['owner_handle'] == 'episode_owner', 'authority_mismatch')
    for claim in checkpoint['prior_claims']:
        source = claim['source']
        source_path = roots['state_root'] / source['artifact']
        for component in (source_path, *source_path.parents):
            if component == roots['state_root'].parent:
                break
            require(not component.is_symlink(), 'unsafe_artifact')
        source_bytes = artifact_read(source_path)
        require(digest(source_bytes) == source['sha256']
                and 0 <= source['byte_start'] < source['byte_end'] <= len(source_bytes), 'source_mismatch')
        inference = claim['kind'] == 'inference'
        require(claim['request_units'] == int(inference) and claim['unit_state'] == ('admitted' if inference else 'not_inference'),
                'unit_attribution_unverifiable')
        for key in ('attempt_id', 'admission_id', 'body_sha256', 'reservation_event_id'):
            require((claim[key] is not None) == inference, 'unit_attribution_unverifiable')
        require(not inference or claim['episode_id'] is not None, 'unit_attribution_unverifiable')
        require(claim['settlement_status'] == ('unsettled' if claim['settled_usd'] == 'n/a' else 'settled'), 'settlement_mismatch')
        if claim['settled_usd'] != 'n/a':
            require(usd(claim['settled_usd']) <= usd(claim['reserved_usd']), 'settlement_mismatch')
    identities = [c['admission_id'] for c in checkpoint['prior_claims'] if c['kind'] == 'inference']
    require(len(identities) == len(set(identities)), 'duplicate_admission')
    return roots, checkpoint


def validate_tool(name, value):
    schema = next((tool['parameters'] for tool in TOOLS if tool['name'] == name), None)
    require(schema is not None, 'unknown_tool')
    fields(value, schema['required'])
    for key, rule in schema['properties'].items():
        typed(value[key], rule)
        if rule['type'] == 'integer':
            require(value[key] >= rule.get('minimum', value[key]) and value[key] <= rule.get('maximum', value[key]), 'invalid_tool_argument')
        else:
            require(len(value[key]) >= rule.get('minLength', 0) and len(value[key]) <= rule.get('maxLength', len(value[key])), 'invalid_tool_argument')
    if name == 'Write':
        require(len(value['content'].encode('utf-8')) <= 1048576, 'write_overflow')


def validate_invocation(invocation):
    fields(invocation, ('schema', 'episode_id', 'session_id', 'attempt_id', 'response_id', 'item_index',
           'item_id', 'call_id', 'function_name', 'arguments_utf8_b64', 'arguments_sha256',
           'arguments_raw_span', 'parsed_input', 'worker_handle', 'fingerprint'))
    require(invocation['schema'] == VERSIONS['invocation'], 'invalid_version')
    for key in ('episode_id', 'session_id', 'attempt_id', 'response_id', 'item_id', 'call_id', 'worker_handle'):
        identifier(invocation[key])
    typed(invocation['item_index'], 'uint')
    for key in ('arguments_sha256', 'fingerprint'):
        typed(invocation[key], 'sha256')
    validate_record('raw_source', invocation['arguments_raw_span'])
    try:
        raw = base64.b64decode(invocation['arguments_utf8_b64'], validate=True)
    except (ValueError, TypeError) as exc:
        raise Refusal('invalid_base64') from exc
    require(digest(raw) == invocation['arguments_sha256'], 'argument_hash')
    require(strict_json(raw) == invocation['parsed_input'], 'argument_mismatch')
    validate_tool(invocation['function_name'], invocation['parsed_input'])


def validate_script(script):
    fields(script, POLICY['script']['fields'])
    require(script['schema'] == POLICY['script']['schema'] and script['status'] in POLICY['script']['status']
            and script['fault'] in POLICY['script']['faults'], 'invalid_script')
    typed(script['chunk_bytes'], 'uint')
    require(script['chunk_bytes'] <= IO['max_response_raw_bytes'] and type(script['items']) is list
            and len(script['items']) <= IO['max_response_items'], 'script_overflow')
    for item in script['items']:
        validate_item(item)


def validate_item(item):
    require(type(item) is dict, 'closed_fields')
    if item.get('type') == 'function_call':
        fields(item, ('type', 'id', 'call_id', 'name', 'arguments'))
        identifier(item['id']); identifier(item['call_id'])
        require(item['name'] in ('Read', 'Write', 'Bash') and type(item['arguments']) is str, 'invalid_item')
    else:
        fields(item, ('type', 'id', 'role', 'content'))
        require(item['type'] == 'message' and item['role'] == 'assistant' and type(item['content']) is list, 'invalid_item')
        identifier(item['id'])
        for part in item['content']:
            fields(part, ('type', 'text'))
            require(part['type'] == 'output_text' and type(part['text']) is str, 'invalid_item')


def validate_episode(episode):
    fields(episode, ('schema', 'episode_id', 'arm', 'stage', 'fixture_files', 'install_files', 'sessions', 'limits', 'network'))
    require(episode['schema'] == VERSIONS['episode'], 'invalid_version')
    identifier(episode['episode_id'])
    require(episode['network'] is None, 'network_unsupported')
    require(episode['arm'] in ('control', 'method', 'method:candidate') and episode['stage'] in ('probe', 'smoke', 'held-out'), 'invalid_episode')
    for kind in ('fixture_files', 'install_files'):
        require(type(episode[kind]) is dict, 'invalid_type')
        for path, text in episode[kind].items():
            relative(path)
            require(type(text) is str, 'invalid_type')
    require(episode['arm'] != 'control' or not episode['install_files'], 'control_install')
    fields(episode['limits'], ('seconds', 'request_units'))
    for key, ceiling in (('seconds', 900), ('request_units', 60)):
        typed(episode['limits'][key], 'positive_int')
        require(episode['limits'][key] <= ceiling, 'invalid_cap')
    require(type(episode['sessions']) is list and episode['sessions'], 'invalid_episode')
    sessions = set()
    for session in episode['sessions']:
        fields(session, ('session_id', 'prompt', 'responses'))
        identifier(session['session_id'])
        require(session['session_id'] not in sessions and type(session['prompt']) is str, 'duplicate_session')
        sessions.add(session['session_id'])
        require(type(session['responses']) is list and session['responses'], 'invalid_script')
        for script in session['responses']:
            validate_script(script)


def body(history):
    result = dict(model=MODEL, reasoning=dict(effort='xhigh'), instructions=INSTRUCTIONS,
        input=history, tools=TOOLS, store=False, stream=True, parallel_tool_calls=False)
    require(len(encoded(result)) <= IO['max_serialized_request_bytes'], 'request_overflow')
    return result


def command(mode):
    require(mode in POLICY['modes'], 'command_unsupported')
    argv = [PYTHON, '-B', str(FIXTURE / 'command_fixture.py'), mode]
    if mode == 'read_archive_prefix':
        argv.append('history-archive.md')
    return ' '.join(shlex.quote(part) for part in argv)


def fresh_environment(home, temporary):
    return dict(PATH='/usr/bin:/bin', HOME=str(home), TMPDIR=str(temporary), LANG='C.UTF-8', PYTHONDONTWRITEBYTECODE='1')


def session_controller():
    """Fresh process, explicit session-local history, no transport/worker authority."""
    initial = strict_json(sys.stdin.buffer.readline())
    fields(initial, ('session_id', 'prompt'))
    identifier(initial['session_id'])
    history = [dict(role='user', content=initial['prompt'])]
    while True:
        sys.stdout.buffer.write(encoded(dict(kind='request', body=body(history))) + b'\n')
        sys.stdout.buffer.flush()
        line = sys.stdin.buffer.readline(IO['max_response_raw_bytes'] + IO['max_worker_result_bytes'] + 1)
        require(bool(line), 'controller_eof')
        update = strict_json(line)
        fields(update, ('items', 'outputs', 'finished'))
        history.extend(update['items'])
        history.extend(update['outputs'])
        if update['finished']:
            return 0


class Store:
    def __init__(self, root):
        self.root, self.total, self.serial = Path(root), 0, 0

    def put(self, path, data):
        relative(path)
        require(type(data) is bytes, 'invalid_type')
        self.total += len(data)
        require(self.total <= IO['max_episode_retained_raw_bytes'], 'retention_overflow')
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        return record('artifact_reference', artifact=path, byte_length=len(data), sha256=digest(data))

    def json(self, path, value):
        return self.put(path, encoded(value) + b'\n')

    def source(self, reference, event_id, producer, start=0, end=None):
        return record('raw_source', artifact=reference['artifact'], sha256=reference['sha256'],
            byte_start=start, byte_end=reference['byte_length'] if end is None else end,
            event_id=event_id, producer=producer)

    def fact(self, prefix, producer, payload):
        self.serial += 1
        event_id = 'fact_' + str(self.serial)
        ref = self.json(prefix + '/fact-%04d.json' % self.serial,
                        dict(event_id=event_id, producer=producer, observed=payload))
        return self.source(ref, event_id, producer)


class Ledger:
    def __init__(self, config, checkpoint, episode):
        self.config, self.checkpoint, self.episode = config, checkpoint, episode
        self.authority = checkpoint['authority_binding']
        self.path = Path(config['roots']['state_root']) / 'journal.jsonl'
        self.fd = os.open(self.path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        require(stat.S_ISREG(os.fstat(self.fd).st_mode) and os.fstat(self.fd).st_nlink == 1, 'unsafe_journal')
        try:
            fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            os.close(self.fd); raise Refusal('ledger_busy') from exc
        try:
            self.events = self.read()
            self.verify()
            require(not any(e['episode_id'] == episode['episode_id'] for e in self.events)
                    and not any(a['episode_id'] == episode['episode_id'] for a in checkpoint['episode_anchors']),
                    'timer_continuity_unverifiable')
            self.origin = record('episode_origin', authority_id=self.authority['authority_id'],
                initiative_id=checkpoint['initiative_id'], ledger_id=checkpoint['ledger_id'],
                episode_id=episode['episode_id'], clock_owner_handle='episode_owner',
                clock_epoch_id='epoch_' + uuid.uuid4().hex, clock_basis='python-monotonic-owner-lifetime/1',
                origin_monotonic_ns=time.monotonic_ns(), origin_event_id='open_' + uuid.uuid4().hex)
            self.append('episode_open')
        except Exception:
            self.close()
            raise


    def read(self):
        os.lseek(self.fd, 0, os.SEEK_SET)
        data = os.read(self.fd, IO['max_episode_retained_raw_bytes'] + 1)
        require(len(data) <= IO['max_episode_retained_raw_bytes'] and (not data or data.endswith(b'\n')), 'journal_torn')
        return [strict_json(line) for line in data.splitlines()]

    def verify(self):
        previous, admissions, opened = ZERO, {}, {}
        event_ids = set()
        consumed, acknowledged, uncertain, settled = set(), set(), set(), set()
        elapsed = {}
        for index, event in enumerate(self.events, 1):
            fields(event, POLICY['ledger_fields'])
            for key, spec in POLICY['ledger_fields'].items(): typed(event[key], spec)
            require(event['sequence'] == index and event['prev_sha256'] == previous, 'journal_chain')
            require(event['event_id'] not in event_ids, 'duplicate_ledger_fact')
            event_ids.add(event['event_id'])
            require(event['ledger_id'] == self.checkpoint['ledger_id']
                    and event['initiative_id'] == self.checkpoint['initiative_id']
                    and event['authority_id'] == self.authority['authority_id']
                    and event['fingerprint'] == self.config['pins']['fingerprint'], 'authority_mismatch')
            previous = digest(encoded(event) + b'\n')
            eid = event['episode_id']
            if event['kind'] == 'episode_open':
                require(eid not in opened and event['episode_origin'] is not None, 'duplicate_origin')
                origin = event['episode_origin']
                require(origin['origin_event_id'] == event['event_id'] == event['episode_origin_event_id']
                        and origin['episode_id'] == eid and origin['authority_id'] == event['authority_id']
                        and origin['initiative_id'] == event['initiative_id'] and origin['ledger_id'] == event['ledger_id'], 'origin_mismatch')
                require(event['monotonic_elapsed_ns'] == event['request_units_delta'] == 0
                        and event['reserved_usd'] == '0' and event['actual_usd'] == 'n/a'
                        and all(event[k] is None for k in ('session_id', 'attempt_id', 'body_sha256', 'bound_receipt_sha256', 'permit_id')),
                        'origin_mismatch')
                opened[eid] = origin; elapsed[eid] = 0
            else:
                require(eid in opened and event['episode_origin'] is None
                        and event['episode_origin_event_id'] == opened[eid]['origin_event_id'], 'origin_mismatch')
                require(event['monotonic_elapsed_ns'] >= elapsed[eid], 'timer_rewind')
                elapsed[eid] = event['monotonic_elapsed_ns']
                key = (eid, event['attempt_id'])
                if event['kind'] == 'reserve':
                    require(key not in admissions and event['request_units_delta'] == 1 and event['actual_usd'] == 'n/a', 'duplicate_admission')
                    require(usd(event['reserved_usd']) > 0, 'nonpositive_reservation')
                    require(all(event[k] is not None for k in ('session_id', 'attempt_id', 'body_sha256', 'bound_receipt_sha256', 'permit_id')), 'admission_identity')
                    admissions[key] = event
                else:
                    require(key in admissions and event['request_units_delta'] == 0, 'admission_identity')
                    original = admissions[key]
                    require(all(event[k] == original[k] for k in ('session_id', 'attempt_id', 'body_sha256', 'bound_receipt_sha256',
                            'permit_id', 'reserved_usd', 'stage')), 'admission_identity')
                    group = {'consume': consumed, 'dispatch_ack': acknowledged, 'uncertain': uncertain, 'settle': settled}[event['kind']]
                    require(key not in group, 'duplicate_ledger_fact')
                    if event['kind'] in ('dispatch_ack', 'uncertain', 'settle'):
                        require(key in consumed, 'unconsumed_dispatch')
                    if event['kind'] == 'settle':
                        require(event['actual_usd'] != 'n/a' and usd(event['actual_usd']) <= usd(original['reserved_usd']), 'settlement_mismatch')
                    else:
                        require(event['actual_usd'] == 'n/a', 'settlement_mismatch')
                    group.add(key)
        prefix = self.checkpoint['journal_prefix']
        require(prefix['cutoff_sequence'] <= len(self.events), 'checkpoint_prefix')
        actual = ZERO if not prefix['cutoff_sequence'] else digest(encoded(self.events[prefix['cutoff_sequence'] - 1]) + b'\n')
        require(actual == prefix['cutoff_sha256'], 'checkpoint_prefix')
        claims = [c for c in self.checkpoint['prior_claims'] if c['kind'] == 'inference']
        prefix_reserves = [e for e in self.events[:prefix['cutoff_sequence']] if e['kind'] == 'reserve']
        require({c['reservation_event_id'] for c in claims} == {e['event_id'] for e in prefix_reserves}, 'checkpoint_admission_census')
        for claim in claims:
            original = next(e for e in prefix_reserves if e['event_id'] == claim['reservation_event_id'])
            require(claim['admission_id'] == original['permit_id'] and claim['attempt_id'] == original['attempt_id']
                    and claim['episode_id'] == original['episode_id'] and claim['body_sha256'] == original['body_sha256']
                    and claim['stage'] == original['stage'] and claim['reserved_usd'] == original['reserved_usd'], 'checkpoint_admission_census')
        origins = [e['episode_origin'] for e in self.events[:prefix['cutoff_sequence']] if e['kind'] == 'episode_open']
        require(self.checkpoint['episode_anchors'] == origins, 'checkpoint_origin_census')
        usage = self.usage()
        require(sum((c[3] for c in usage), Decimal(0)) <= usd(self.config['caps']['initiative_usd']), 'initiative_cap')
        for stage, cap in (('probe', 'probe_usd'), ('smoke', 'smoke_usd'), ('held-out', 'held_out_usd')):
            require(sum((c[3] for c in usage if c[0] == stage), Decimal(0)) <= usd(self.config['caps'][cap]), 'stage_cap')
        for eid in opened:
            own = [c for c in usage if c[1] == eid]
            require(sum(c[2] for c in own) <= self.config['caps']['episode_request_units'], 'request_unit_cap')
            require(sum((c[3] for c in own), Decimal(0)) <= usd(self.config['caps']['episode_usd']), 'episode_cap')
            require(elapsed[eid] < self.config['caps']['episode_seconds'] * 1000000000, 'episode_deadline')
        return admissions

    def elapsed(self):
        require(self.authority['task_root'] == identity(self.config['roots']['task_root'])
                and self.authority['state_root'] == identity(self.config['roots']['state_root']), 'authority_mismatch')
        answer = time.monotonic_ns() - self.origin['origin_monotonic_ns']
        require(answer >= 0, 'timer_rewind')
        return answer

    def append(self, kind, permit=None, evidence=ZERO):
        event = dict(schema=VERSIONS['ledger_event'], ledger_id=self.checkpoint['ledger_id'],
            initiative_id=self.checkpoint['initiative_id'], sequence=len(self.events) + 1,
            prev_sha256=digest(encoded(self.events[-1]) + b'\n') if self.events else ZERO,
            event_id=self.origin['origin_event_id'] if kind == 'episode_open' else kind + '_' + uuid.uuid4().hex,
            episode_id=self.episode['episode_id'], session_id=None, attempt_id=None, stage=self.episode['stage'],
            kind=kind, body_sha256=None, bound_receipt_sha256=None, fingerprint=self.config['pins']['fingerprint'],
            reserved_usd='0', actual_usd='n/a', monotonic_elapsed_ns=0 if kind == 'episode_open' else self.elapsed(),
            permit_id=None, evidence_sha256=evidence, authority_id=self.authority['authority_id'],
            episode_origin_event_id=self.origin['origin_event_id'], episode_origin=self.origin if kind == 'episode_open' else None,
            request_units_delta=1 if kind == 'reserve' else 0)
        if permit:
            for key in ('session_id', 'attempt_id', 'body_sha256', 'bound_receipt_sha256', 'permit_id', 'reserved_usd'):
                event[key] = permit[key]
        fields(event, POLICY['ledger_fields'])
        for key, spec in POLICY['ledger_fields'].items(): typed(event[key], spec)
        self.events.append(event)
        try:
            self.verify()
        except Exception:
            self.events.pop()
            raise
        raw = encoded(event) + b'\n'
        os.lseek(self.fd, 0, os.SEEK_END)
        require(os.write(self.fd, raw) == len(raw), 'journal_write')
        os.fsync(self.fd)
        return event

    def usage(self):
        cutoff = self.checkpoint['journal_prefix']['cutoff_sequence']
        claims = [(c['stage'], c['episode_id'], c['request_units'], usd(c['settled_usd'] if c['settlement_status'] == 'settled' else c['reserved_usd']))
                  for c in self.checkpoint['prior_claims']]
        settlements = {e['permit_id']: e['actual_usd'] for e in self.events if e['kind'] == 'settle'}
        claims.extend((e['stage'], e['episode_id'], 1, usd(settlements.get(e['permit_id'], e['reserved_usd'])))
                      for e in self.events[cutoff:] if e['kind'] == 'reserve')
        return claims

    def check_headroom(self, amount, units):
        require(self.elapsed() < self.episode['limits']['seconds'] * 1000000000, 'episode_deadline')
        claims = self.usage()
        own = [c for c in claims if c[1] == self.episode['episode_id']]
        require(sum(c[2] for c in own) + units <= self.episode['limits']['request_units'], 'request_unit_cap')
        require(sum((c[3] for c in claims), Decimal(0)) + amount <= usd(self.config['caps']['initiative_usd']), 'initiative_cap')
        require(sum((c[3] for c in own), Decimal(0)) + amount <= usd(self.config['caps']['episode_usd']), 'episode_cap')
        stage = self.episode['stage']
        cap = {'probe': 'probe_usd', 'smoke': 'smoke_usd', 'held-out': 'held_out_usd'}[stage]
        require(sum((c[3] for c in claims if c[0] == stage), Decimal(0)) + amount <= usd(self.config['caps'][cap]), 'stage_cap')

    def reserve(self, session, attempt, raw):
        identifier(session); identifier(attempt)
        require(not any(e['kind'] == 'reserve' and e['episode_id'] == self.episode['episode_id']
                        and e['attempt_id'] == attempt for e in self.events), 'duplicate_admission')
        self.check_headroom(Decimal('0.1'), 1)
        receipt = dict(schema='tackle-controlled-synthetic-bound/1', proof_scope='synthetic_nonbillable',
            provider_applicable=False, body_sha256=digest(raw), fingerprint=self.config['pins']['fingerprint'],
            currency='USD', maximum_usd='0.1', request_units=1, source_sha256=self.config['pins']['policy_sha256'])
        permit = dict(permit_id='permit_' + uuid.uuid4().hex, ledger_id=self.checkpoint['ledger_id'],
            reservation_sequence=len(self.events) + 1, episode_id=self.episode['episode_id'], session_id=session,
            attempt_id=attempt, body_sha256=digest(raw), bound_receipt_sha256=digest(encoded(receipt)),
            fingerprint=self.config['pins']['fingerprint'], reserved_usd='0.1',
            authority_id=self.authority['authority_id'], episode_origin_event_id=self.origin['origin_event_id'])
        self.append('reserve', permit)
        return permit, receipt

    def consume(self, permit, raw):
        fields(permit, ('permit_id', 'ledger_id', 'reservation_sequence', 'episode_id', 'session_id',
                       'attempt_id', 'body_sha256', 'bound_receipt_sha256', 'fingerprint', 'reserved_usd',
                       'authority_id', 'episode_origin_event_id'))
        original = next((e for e in self.events if e['kind'] == 'reserve' and e['permit_id'] == permit['permit_id']), None)
        require(original is not None and permit['reservation_sequence'] == original['sequence']
                and all(permit[k] == original[k] for k in permit if k != 'reservation_sequence'), 'permit_mismatch')
        require(permit['authority_id'] == self.authority['authority_id'] and permit['body_sha256'] == digest(raw), 'permit_mismatch')
        require(not any(e['kind'] == 'consume' and e['permit_id'] == permit['permit_id'] for e in self.events), 'permit_reuse')
        self.check_headroom(Decimal(0), 0)
        self.append('consume', permit)

    def close(self):
        if self.fd is not None:
            fcntl.flock(self.fd, fcntl.LOCK_UN); os.close(self.fd); self.fd = None


def captured(argv, data, cwd, env, extras=(), preexec=None, timeout=40, maximum=None):
    """Bounded pipes with observed EOF, exit and the actual Popen handle."""
    import selectors
    maximum = maximum or IO['max_response_raw_bytes']
    start = time.monotonic_ns()
    process = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True,
        pass_fds=tuple(extras), preexec_fn=preexec)
    process.stdin.write(data); process.stdin.close()
    selector = selectors.DefaultSelector()
    streams = {'stdout': bytearray(), 'stderr': bytearray()}
    for name, stream in (('stdout', process.stdout), ('stderr', process.stderr)):
        selector.register(stream, selectors.EVENT_READ, name)
    for name, fd in getattr(preexec, 'capture_fds', ()):
        streams[name] = bytearray(); selector.register(fd, selectors.EVENT_READ, name)
    for fd in getattr(preexec, 'parent_close', ()):
        os.close(fd)
    eof, overflow, timed_out = set(), False, False
    while selector.get_map():
        if time.monotonic_ns() - start > timeout * 1000000000:
            timed_out = True
            if process.poll() is None: process.kill()
        ready = selector.select(.05)
        for key, _ in ready:
            fd = key.fileobj if type(key.fileobj) is int else key.fileobj.fileno()
            chunk = os.read(fd, 65536)
            if not chunk:
                eof.add(key.data); selector.unregister(key.fileobj)
                if type(key.fileobj) is int: os.close(key.fileobj)
                continue
            limit = IO['max_worker_stdout_bytes'] if key.data == 'command_stdout' else IO['max_worker_stderr_bytes'] if key.data == 'command_stderr' else maximum
            if len(streams[key.data]) + len(chunk) > limit:
                overflow = True
                streams[key.data].extend(chunk[:max(0, limit - len(streams[key.data]))])
                if process.poll() is None: process.kill()
            else:
                streams[key.data].extend(chunk)
        if timed_out and process.poll() is not None and time.monotonic_ns() - start > (timeout + 1) * 1000000000:
            break
    selector.close()
    code = process.wait(timeout=2)
    result = dict(argv=list(argv), cwd=str(cwd), pid=process.pid, started_ns=start,
        ended_ns=time.monotonic_ns(), exit_code=code if code >= 0 else None,
        signal=-code if code < 0 else None, timeout=timed_out, capture_complete=not overflow and len(eof) == len(streams),
        eof=sorted(eof), overflow=overflow, streams={k: bytes(v) for k, v in streams.items()})
    process.stdout.close(); process.stderr.close()
    return result


def lexical_span(line, target):
    """Locate a JSON value by structural path, including its original spelling."""
    text = line.decode('utf-8')
    decoder = json.JSONDecoder()
    found = []

    def walk(offset, path):
        while offset < len(text) and text[offset].isspace(): offset += 1
        start = offset
        if text[offset] == '{':
            offset += 1
            while True:
                while text[offset].isspace(): offset += 1
                if text[offset] == '}': offset += 1; break
                key, offset = decoder.raw_decode(text, offset)
                while text[offset].isspace(): offset += 1
                require(text[offset] == ':', 'invalid_json'); offset += 1
                offset = walk(offset, path + (key,))
                while text[offset].isspace(): offset += 1
                if text[offset] == ',': offset += 1; continue
                require(text[offset] == '}', 'invalid_json'); offset += 1; break
        elif text[offset] == '[':
            offset += 1; index = 0
            while True:
                while text[offset].isspace(): offset += 1
                if text[offset] == ']': offset += 1; break
                offset = walk(offset, path + (index,)); index += 1
                while text[offset].isspace(): offset += 1
                if text[offset] == ',': offset += 1; continue
                require(text[offset] == ']', 'invalid_json'); offset += 1; break
        else:
            _, offset = decoder.raw_decode(text, offset)
        if path == target:
            found.append((len(text[:start].encode('utf-8')), len(text[:offset].encode('utf-8'))))
        return offset
    walk(0, ())
    require(len(found) == 1, 'source_span_missing')
    return found[0]


def parse_response(raw, ref, store, session, attempt):
    require(len(raw) <= IO['max_response_raw_bytes'] and raw.endswith(b'\n'), 'response_incomplete')
    common = ('schema', 'event_id', 'session_id', 'attempt_id', 'response_id', 'kind')
    extras = dict(response_started=('model_echo',), item_completed=('item_index', 'item'),
                  response_completed=('status', 'item_count'), response_failed=('status', 'error_code'))
    seen, items, spans, sources, offset, completed, response = set(), {}, {}, {}, 0, False, None
    started = False
    call_ids, item_ids = {}, {}
    for line in raw.splitlines(keepends=True):
        event = strict_json(line)
        require(type(event) is dict and event.get('kind') in extras, 'unknown_event')
        fields(event, common + extras[event['kind']])
        require(not completed and event['schema'] == VERSIONS['stub_events']
                and event['session_id'] == session and event['attempt_id'] == attempt, 'event_identity')
        identifier(event['event_id']); identifier(event['response_id'])
        require(event['event_id'] not in seen, 'duplicate_event')
        seen.add(event['event_id'])
        response = response or event['response_id']
        require(response == event['response_id'], 'response_identity')
        source = store.source(ref, event['event_id'], 'stub', offset, offset + len(line))
        kind = event['kind']
        if kind == 'response_started':
            require(not started and not items and event['model_echo'] == MODEL, 'response_order')
            started = True
        elif kind == 'item_completed':
            require(started, 'response_order')
            typed(event['item_index'], 'uint')
            index, item = event['item_index'], event['item']
            validate_item(item)
            if index in items:
                require(items[index] == item, 'conflicting_item')
            else:
                require(index == len(items) and len(items) < IO['max_response_items'], 'item_order')
                require(item['id'] not in item_ids, 'duplicate_item')
                item_ids[item['id']] = index
                if item['type'] == 'function_call':
                    require(item['call_id'] not in call_ids, 'duplicate_call')
                    call_ids[item['call_id']] = index
                    start, end = lexical_span(line, ('item', 'arguments'))
                    spans[index] = store.source(ref, event['event_id'], 'stub', offset + start, offset + end)
                items[index], sources[index] = item, source
        elif kind == 'response_completed':
            require(started and event['status'] == 'completed' and type(event['item_count']) is int
                    and event['item_count'] == len(items), 'response_incomplete')
            completed = True
        else:
            raise Refusal('response_failed', event['error_code'])
        offset += len(line)
    require(completed, 'response_incomplete')
    return response, [items[i] for i in range(len(items))], spans, sources


def length_id(*parts):
    result = '_'.join(str(len(p)) + '_' + p for p in parts)
    identifier(result)
    return result


def worker_bindings(paths):
    bindings, handles = [], []
    for role, slot, access in (('work', 10, 'read_write'), ('tmp', 11, 'read_write'),
                              ('install', 12, 'read_only'), ('runtime', 13, 'read_only')):
        if role not in paths: continue
        fd = os.open(paths[role], os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        # Keep every owned descriptor outside the fixed child slot range.
        owned_fd = fcntl.fcntl(fd, fcntl.F_DUPFD_CLOEXEC, 64)
        os.close(fd)
        fd = owned_fd
        info = os.fstat(fd)
        handles.append((fd, slot))
        bindings.append(record('root_binding', role=role, handle_id=role + '_root', descriptor_slot=slot,
            access=access, device=info.st_dev, inode=info.st_ino, owner_uid=info.st_uid, initial_tree_sha256=tree_digest(paths[role])))
    return bindings, handles


def execute_tool(invocation, paths, store):
    validate_invocation(invocation)
    prefix = 'workers/' + invocation['worker_handle']
    bindings, descriptors = worker_bindings(paths)
    spawn_source = store.fact(prefix, 'supervisor', dict(kind='worker_authority', invocation_id=invocation['call_id'], root_bindings=bindings))
    authority = record('worker_authority', episode_id=invocation['episode_id'], session_id=invocation['session_id'],
        worker_handle=invocation['worker_handle'], boundary_handle='fixture_boundary', controller_owner_handle='episode_owner',
        fingerprint=invocation['fingerprint'], spawn_event_id=spawn_source['event_id'], spawn_source=spawn_source,
        root_bindings=bindings, command_profile='fixed-command-helper/1')
    envelope = record('worker_envelope', invocation=invocation, authority=authority)
    envelope_ref = store.json(prefix + '/invocation.json', envelope)
    stdout_read, stdout_write = os.pipe()
    stderr_read, stderr_write = os.pipe()
    moved = []
    for descriptor in (stdout_read, stdout_write, stderr_read, stderr_write):
        moved.append(fcntl.fcntl(descriptor, fcntl.F_DUPFD_CLOEXEC, 64))
        os.close(descriptor)
    stdout_read, stdout_write, stderr_read, stderr_write = moved
    assigned = descriptors + [(stdout_write, 14), (stderr_write, 15)]
    saved, copies = {}, []
    for _, slot in assigned:
        try: saved[slot] = fcntl.fcntl(slot, fcntl.F_DUPFD_CLOEXEC, 30)
        except OSError: saved[slot] = None
    for fd, slot in assigned:
        copies.append((fcntl.fcntl(fd, fcntl.F_DUPFD_CLOEXEC, 30), slot))
    for fd, slot in copies: os.dup2(fd, slot, inheritable=True)
    for fd, _ in copies: os.close(fd)
    def inherited():
        pass
    inherited.capture_fds = [('command_stdout', stdout_read), ('command_stderr', stderr_read)]
    inherited.parent_close = [14, 15]
    # Original writers may equal fixed slots; retain only the fixed copies.
    for writer in (stdout_write, stderr_write):
        if writer not in (slot for _, slot in assigned): os.close(writer)
    try:
        observation = captured([PYTHON, '-B', str(HERE / 'controlled_worker.py')], encoded(envelope), paths['work'],
            fresh_environment(paths['work'], paths['tmp']), extras=[slot for _, slot in assigned],
            preexec=inherited, timeout=IO['max_tool_seconds'] + 2, maximum=IO['max_worker_result_bytes'])
    finally:
        for slot, prior in saved.items():
            if prior is None:
                try: os.close(slot)
                except OSError: pass
            else: os.dup2(prior, slot); os.close(prior)
        for fd, _ in descriptors:
            if fd not in saved: os.close(fd)
    raw_ref = store.put(prefix + '/result.raw.jsonl', observation['streams']['stdout'])
    native_ref = store.put(prefix + '/native.stderr.jsonl', observation['streams']['stderr'])
    stream_refs = {channel: store.put(prefix + '/' + channel + '.bin', observation['streams']['command_' + channel])
                   for channel in ('stdout', 'stderr')}
    require(observation['exit_code'] == 0 and observation['capture_complete'] and not observation['timeout'], 'worker_incomplete')
    result = strict_json(observation['streams']['stdout'])
    validate_result(result, invocation)
    require(result['complete'], 'worker_incomplete')
    result_source = store.source(raw_ref, invocation['worker_handle'] + '_result', 'worker')
    if result['kind'] == 'Bash':
        for channel in ('stdout', 'stderr'):
            source = result['facts'][channel + '_source']
            require(source['sha256'] == stream_refs[channel]['sha256'] and source['byte_end'] == stream_refs[channel]['byte_length']
                    and result['facts'][channel + '_utf8'].encode() == observation['streams']['command_' + channel], 'stream_mismatch')
    result['sources'] = [result_source]
    result_ref = store.json(prefix + '/result.json', result)
    owned = strict_json(observation['streams']['stderr'])
    fields(owned, ('schema', 'worker_handle', 'handles', 'remaining_handle_ids'))
    require(owned['schema'] == 'tackle-controlled-owned-handles/1' and owned['worker_handle'] == invocation['worker_handle']
            and owned['remaining_handle_ids'] == [], 'owned_handles_live')
    receipt_ref = finalize(invocation['episode_id'], invocation['session_id'], invocation['worker_handle'],
        invocation['fingerprint'], observation, owned['handles'], paths['work'], store, prefix, stream_refs, native_ref)
    return result, result_ref, receipt_ref, envelope_ref


def validate_result(result, invocation=None):
    fields(result, ('schema', 'episode_id', 'session_id', 'attempt_id', 'response_id', 'item_index', 'item_id',
           'call_id', 'function_name', 'worker_handle', 'kind', 'facts', 'returned_output_utf8_b64',
           'returned_output_sha256', 'complete', 'sources'))
    require(result['schema'] == VERSIONS['result'] and result['kind'] in ('Read', 'Write', 'Bash', 'refused'), 'result_version')
    if invocation:
        require(all(result[k] == invocation[k] for k in ('episode_id', 'session_id', 'attempt_id', 'response_id',
            'item_index', 'item_id', 'call_id', 'function_name', 'worker_handle')), 'result_identity')
    typed(result['complete'], 'bool')
    for source in result['sources']: validate_record('raw_source', source)
    try: returned = base64.b64decode(result['returned_output_utf8_b64'], validate=True)
    except ValueError as exc: raise Refusal('invalid_base64') from exc
    require(digest(returned) == result['returned_output_sha256'], 'result_hash')
    facts, kind = result['facts'], result['kind']
    allowed = dict(Read=('file_path', 'byte_offset', 'requested_max_bytes', 'returned_bytes', 'content_utf8', 'content_sha256', 'eof'),
        Write=('file_path', 'bytes_written', 'content_sha256'),
        Bash=('command', 'argv', 'shell_path', 'cwd', 'stdout_source', 'stderr_source', 'stdout_utf8', 'stderr_utf8', 'exit_code', 'signal', 'timeout', 'capture_complete'),
        refused=('error_code', 'errno', 'mechanism', 'effect_started'))
    fields(facts, allowed[kind])
    if kind == 'Read':
        for key in ('byte_offset', 'requested_max_bytes', 'returned_bytes'): typed(facts[key], 'uint')
        typed(facts['eof'], 'bool')
        require(facts['content_utf8'].encode() == returned and len(returned) == facts['returned_bytes']
                and digest(returned) == facts['content_sha256'], 'read_mismatch')
        if invocation: require(all(facts[k] == invocation['parsed_input'][k] for k in ('file_path', 'byte_offset'))
                               and facts['requested_max_bytes'] == invocation['parsed_input']['max_bytes'], 'read_mismatch')
    elif kind == 'Write':
        typed(facts['bytes_written'], 'uint'); typed(facts['content_sha256'], 'sha256')
        require(returned == encoded(facts), 'write_mismatch')
        if invocation:
            content = invocation['parsed_input']['content'].encode()
            require(facts['file_path'] == invocation['parsed_input']['file_path'] and facts['bytes_written'] == len(content)
                    and facts['content_sha256'] == digest(content), 'write_mismatch')
    elif kind == 'Bash':
        typed(facts['timeout'], 'bool'); typed(facts['capture_complete'], 'bool')
        typed(facts['exit_code'], 'nullable<int>'); typed(facts['signal'], 'nullable<positive_int>')
        for channel in ('stdout', 'stderr'): validate_record('raw_source', facts[channel + '_source'])
        require(facts['shell_path'] == SHELL and facts['argv'] == [SHELL, '-c', facts['command']]
                and facts['command'] in {command(mode) for mode in POLICY['modes']}, 'command_mismatch')
        require(returned == encoded([dict(type='text', text=facts['stdout_utf8']), dict(type='text', text=facts['stderr_utf8'])]), 'stream_mismatch')
        if invocation: require(all(facts[k] == invocation['parsed_input'][k] for k in ('command', 'cwd')), 'command_mismatch')
    else:
        typed(facts['effect_started'], 'bool'); typed(facts['errno'], 'nullable<int>')
        require(returned == encoded(facts) and (facts['mechanism'] == 'observed_os_error' or facts['errno'] is None), 'refusal_mismatch')


def finalize(episode, session, worker, fingerprint, observation, children, work, store, prefix, stream_refs, native_ref):
    require(observation['capture_complete'] and not observation['overflow'] and not observation['timeout']
            and (observation['exit_code'] is not None or observation['signal'] is not None), 'capture_incomplete')
    events, handles = [], []
    def emit(kind, facts):
        source = store.fact(prefix + '/supervisor', 'supervisor', dict(kind=kind, facts=facts))
        event = record('supervisor_event', event_id=source['event_id'], episode_id=episode, session_id=session,
            invocation_id=worker, worker_handle=worker, boundary_handle='fixture_boundary', fingerprint=fingerprint,
            source=source, monotonic_ns=time.monotonic_ns(), kind=kind, facts=facts)
        events.append(event)
        return event
    spawn = store.fact(prefix + '/supervisor', 'supervisor', {k: observation[k] for k in ('pid', 'argv', 'cwd', 'started_ns')})
    exited = store.fact(prefix + '/supervisor', 'supervisor', {k: observation[k] for k in ('pid', 'exit_code', 'signal', 'ended_ns')})
    main_handle = record('process_handle', handle_id=worker, pid=observation['pid'], parent_handle_id='episode_owner',
        spawn_source=spawn, exit_source=exited, exit_code=observation['exit_code'], signal=observation['signal'])
    handles.append(main_handle)
    for index, child in enumerate(children):
        fields(child, ('pid', 'started_ns', 'role', 'exit_code', 'exited_ns'))
        require(child['exited_ns'] >= child['started_ns'] and child['exit_code'] is not None, 'owned_handles_live')
        source = store.source(native_ref, worker + '_owned_' + str(index), 'worker')
        code = child['exit_code']
        handles.append(record('process_handle', handle_id=worker + '_child_' + str(index), pid=child['pid'],
            parent_handle_id=worker, spawn_source=source, exit_source=source,
            exit_code=code if code >= 0 else None, signal=-code if code < 0 else None))
    spawned = emit('spawn_ack', record('supervisor_spawn_facts', main_process=main_handle, owned_processes=handles,
        stdout_stream_id=worker + '_stdout', stderr_stream_id=worker + '_stderr', worker_authority_sha256=digest(encoded(handles))))
    emit('main_exit', record('supervisor_exit_facts', process_handle_id=worker, exit_code=observation['exit_code'],
        signal=observation['signal'], timeout=observation['timeout'], interrupted=False))
    empty = emit('tracked_fixture_handles_empty', record('supervisor_empty_facts', owned_processes=handles,
        remaining_handle_ids=[], last_spawn_event_id=spawned['event_id'], observed_monotonic_ns=time.monotonic_ns()))
    captures, eof_events = [], {}
    for channel in ('stdout', 'stderr'):
        source = store.fact(prefix + '/supervisor', 'supervisor', dict(channel=channel, observed_eof=observation['capture_complete']))
        capture = record('stream_capture', stream_id=worker + '_' + channel, worker_handle=worker, channel=channel,
            artifact_ref=stream_refs[channel], returned_bytes=stream_refs[channel]['byte_length'],
            capture_complete=observation['capture_complete'], truncated=observation['overflow'], eof_source=source)
        captures.append(capture)
        eof_events[channel] = emit(channel + '_eof', record('supervisor_eof_facts', capture=capture, observed_monotonic_ns=time.monotonic_ns()))
    entries = []
    for parent, dirs, names in os.walk(work, followlinks=False):
        for name in dirs: require(not (Path(parent) / name).is_symlink(), 'unsafe_snapshot')
        for name in sorted(names):
            path = Path(parent) / name
            rel = path.relative_to(work).as_posix()
            ref = store.put(prefix + '/snapshot/' + rel, artifact_read(path))
            entries.append(record('snapshot_entry', relative_path=rel, artifact_ref=ref, mode=stat.S_IMODE(path.stat().st_mode)))
    source = store.fact(prefix + '/supervisor', 'supervisor', dict(tree_sha256=tree_digest(work), entries=entries))
    snapshot = record('snapshot', snapshot_id=worker + '_snapshot', worker_handle=worker, boundary_handle='fixture_boundary',
        root_role='work', observed_monotonic_ns=time.monotonic_ns(), tree_sha256=tree_digest(work), entries=entries,
        quiescence_event_id=empty['event_id'], stdout_eof_event_id=eof_events['stdout']['event_id'],
        stderr_eof_event_id=eof_events['stderr']['event_id'], source=source)
    emit('snapshot_observed', record('supervisor_snapshot_facts', snapshot=snapshot))
    receipt = record('supervisor_receipt', episode_id=episode, session_id=session, worker_handle=worker,
        boundary_handle='fixture_boundary', fingerprint=fingerprint, proof_scope='offline_fixture_only',
        kernel_boundary_accepted=False, worker_handles=handles, sources=[e['source'] for e in events], snapshot=snapshot,
        stream_captures=captures, complete=True, missing_facts=[])
    ref = store.json(prefix + '/supervisor/receipt.json', receipt)
    receipt_ref = record('supervisor_receipt_ref', artifact_ref=ref, receipt_schema=receipt['schema'],
        episode_id=episode, session_id=session, worker_handle=worker, boundary_handle='fixture_boundary', fingerprint=fingerprint)
    emit('offline_finalized', record('supervisor_final_facts', receipt_ref=receipt_ref))
    store.json(prefix + '/supervisor/events.json', events)
    return receipt_ref


COUNT_NAMES = ('reservation_count', 'consumption_count', 'stub_ack_count', 'response_item_count',
    'tool_invocation_count', 'tool_result_count', 'raw_request_bytes', 'raw_response_bytes',
    'raw_worker_result_bytes', 'stdout_bytes', 'stderr_bytes', 'canonical_row_count', 'reserved_request_units')


def counts(scope, scope_id, ledger, **values):
    answer = {key: values.get(key, 0) for key in COUNT_NAMES}
    answer.update(episode_admitted_request_units=sum(c[2] for c in ledger.usage() if c[1] == ledger.episode['episode_id']),
        episode_elapsed_ns=ledger.elapsed(), provider_inference_attempts='n/a', provider_tokens_in='n/a',
        provider_tokens_out='n/a', provider_cost_usd='n/a', scope=scope, scope_id=scope_id)
    return record('counts', **answer)


def project_items(session, attempt, response, items, sources, invocations, results):
    rows, facts = [], []
    for index, item in enumerate(items):
        if item['type'] == 'function_call':
            invocation, result = invocations[index], results[index]
            validate_invocation(invocation); validate_result(result, invocation)
            cid = length_id(session, attempt, item['call_id'])
            use = dict(type='tool_use', id=cid, name=item['name'], input=invocation['parsed_input'],
                source=invocation['arguments_raw_span'], original_name=item['name'],
                arguments_utf8_b64=invocation['arguments_utf8_b64'], arguments_sha256=invocation['arguments_sha256'])
            if result['kind'] == 'Bash':
                content = [dict(type='text', text=result['facts']['stdout_utf8']), dict(type='text', text=result['facts']['stderr_utf8'])]
            else:
                content = base64.b64decode(result['returned_output_utf8_b64']).decode('utf-8')
            error = result['kind'] == 'refused' or (result['kind'] == 'Bash' and
                    (result['facts']['exit_code'] != 0 or result['facts']['timeout'] or result['facts']['signal'] is not None))
            returned = dict(type='tool_result', tool_use_id=cid, content=content, is_error=error,
                source=result['sources'][0], original_name=item['name'], native_result=result,
                returned_output_source=result['sources'][0])
            rows.extend([dict(type='assistant', message=dict(content=[use])), dict(type='user', message=dict(content=[returned]))])
            facts.append(dict(canonical_id=cid, fact='tool_pair', session_id=session, attempt_id=attempt,
                response_id=response, item_id=item['id'], item_index=index, call_id=item['call_id'], original_name=item['name'],
                sources=[sources[index], invocation['arguments_raw_span']] + result['sources'],
                exact_argument_utf8_b64=invocation['arguments_utf8_b64'], exact_input=invocation['parsed_input'], exact_result=result))
        else:
            rows.append(dict(type='assistant', message=dict(content=[dict(type='text', text=p['text']) for p in item['content']])))
            facts.append(dict(canonical_id=length_id(session, attempt, item['id']), fact='assistant_text',
                session_id=session, attempt_id=attempt, response_id=response, item_id=item['id'], item_index=index,
                call_id=None, original_name=None, sources=[sources[index]], exact_argument_utf8_b64=None,
                exact_input=None, exact_result=item))
    return rows, facts


def write_files(root, files):
    for name, text in files.items():
        relative(name)
        target = root / name
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with target.open('x', encoding='utf-8') as stream: stream.write(text)


def new_output(path, roots):
    path = Path(path).absolute()
    require(path.parent == roots['evidence_root'] and path.name not in ('', '.', '..'), 'output_root')
    path.mkdir(mode=0o700, exist_ok=False)
    return path


def run(config, episode, output):
    roots, checkpoint = validate_config(config)
    validate_episode(episode)
    # No artifact, process, or journal effect precedes these refusal gates.
    out = new_output(output, roots)
    base = out / episode['episode_id']; base.mkdir(mode=0o700)
    store = Store(base)
    ledger = None
    active = None
    try:
        ledger = Ledger(config, checkpoint, episode)
        run_root = roots['run_root'] / episode['episode_id']
        run_root.mkdir(mode=0o700, exist_ok=False)
        paths = dict(work=run_root / 'work', tmp=run_root / 'tmp', runtime=FIXTURE)
        for role in ('work', 'tmp'): paths[role].mkdir(mode=0o700)
        write_files(paths['work'], episode['fixture_files'])
        if episode['arm'] != 'control':
            paths['install'] = run_root / 'install'; paths['install'].mkdir(mode=0o700)
            write_files(paths['install'], episode['install_files'])
        config_ref = store.json('config.json', config)
        episode_ref = store.json('episode.json', episode)
        store.put('checkpoint.json', artifact_read(config['checkpoint']['path']))
        sessions, facts, all_raw, supervisor_refs = [], [], [], []
        for ordinal, session in enumerate(episode['sessions'], 1):
            sid = session['session_id']; prefix = 'sessions/%02d' % ordinal
            controller_handle = 'controller_' + sid
            controller_start = time.monotonic_ns()
            active = subprocess.Popen([PYTHON, '-B', str(Path(__file__)), '--session-controller'],
                cwd=paths['work'], env=fresh_environment(paths['work'], paths['tmp']),
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
            active.stdin.write(encoded(dict(session_id=sid, prompt=session['prompt'])) + b'\n'); active.stdin.flush()
            owned_history = [dict(role='user', content=session['prompt'])]
            controller_bytes, canonical, local_raw, attempt_order = bytearray(), [], [], []
            local = {key: 0 for key in COUNT_NAMES}
            last_receipt, finished, seen_calls, seen_items = None, False, set(), set()
            for number, script in enumerate(session['responses'], 1):
                attempt = 'a_' + sid + '_' + str(number)
                identifier(attempt)
                line = active.stdout.readline(IO['max_serialized_request_bytes'] * 2 + 1)
                require(bool(line) and len(line) <= IO['max_serialized_request_bytes'] * 2, 'controller_incomplete')
                controller_bytes.extend(line)
                prepared = strict_json(line); fields(prepared, ('kind', 'body'))
                require(prepared['kind'] == 'request' and prepared['body'] == body(owned_history), 'history_mismatch')
                request = encoded(prepared['body'])
                request_ref = store.put(prefix + '/' + attempt + '/request.json', request)
                permit, bound = ledger.reserve(sid, attempt, request)
                store.json(prefix + '/' + attempt + '/bound.json', bound)
                store.json(prefix + '/' + attempt + '/permit.json', permit)
                actual_script = dict(script, session_id=sid)
                script_ref = store.json(prefix + '/' + attempt + '/script.json', actual_script)
                ledger.consume(permit, request)
                observed = captured([PYTHON, '-B', str(FIXTURE / 'stub_responses.py'), '--script', str(base / script_ref['artifact']),
                    '--attempt-id', attempt, '--body-sha256', digest(request)], request, paths['work'],
                    fresh_environment(paths['work'], paths['tmp']))
                native_ref = store.put(prefix + '/' + attempt + '/stub.stderr.jsonl', observed['streams']['stderr'])
                raw_ref = store.put(prefix + '/' + attempt + '/response.raw.jsonl', observed['streams']['stdout'])
                store.json(prefix + '/' + attempt + '/stub.process.json', {k: v for k, v in observed.items() if k != 'streams'})
                try:
                    ack = strict_json(observed['streams']['stderr'])
                    fields(ack, ('schema', 'attempt_id', 'body_sha256', 'pid'))
                    require(ack == dict(schema='tackle-controlled-stub-ack/1', attempt_id=attempt,
                            body_sha256=digest(request), pid=observed['pid']), 'stub_ack_mismatch')
                    require(observed['exit_code'] == 0 and observed['capture_complete'] and not observed['timeout'], 'stub_incomplete')
                except Refusal:
                    ledger.append('uncertain', permit, digest(encoded(observed['argv'])))
                    raise
                ledger.append('dispatch_ack', permit, native_ref['sha256'])
                response, items, spans, sources = parse_response(observed['streams']['stdout'], raw_ref, store, sid, attempt)
                local_raw.append(record('raw_component', session_id=sid, attempt_id=attempt, response_id=response,
                    order_index=len(all_raw), artifact_ref=raw_ref))
                all_raw.append(local_raw[-1]); attempt_order.append(attempt)
                local['reservation_count'] += 1; local['consumption_count'] += 1; local['stub_ack_count'] += 1
                local['reserved_request_units'] += 1; local['raw_request_bytes'] += request_ref['byte_length']
                local['raw_response_bytes'] += raw_ref['byte_length']; local['response_item_count'] += len(items)
                invocations, results, outputs = {}, {}, []
                for index, item in enumerate(items):
                    require(item['id'] not in seen_items, 'duplicate_item'); seen_items.add(item['id'])
                    if item['type'] != 'function_call': continue
                    require(item['call_id'] not in seen_calls, 'duplicate_call'); seen_calls.add(item['call_id'])
                    argument = item['arguments'].encode('utf-8')
                    parsed = strict_json(argument)
                    worker_handle = 'w_' + sid + '_' + str(number) + '_' + str(index)
                    invocation = dict(schema=VERSIONS['invocation'], episode_id=episode['episode_id'], session_id=sid,
                        attempt_id=attempt, response_id=response, item_index=index, item_id=item['id'], call_id=item['call_id'],
                        function_name=item['name'], arguments_utf8_b64=base64.b64encode(argument).decode(), arguments_sha256=digest(argument),
                        arguments_raw_span=spans[index], parsed_input=parsed, worker_handle=worker_handle, fingerprint=config['pins']['fingerprint'])
                    validate_invocation(invocation)
                    result, result_ref, receipt, _ = execute_tool(invocation, paths, store)
                    invocations[index], results[index] = invocation, result
                    supervisor_refs.append(receipt); last_receipt = receipt
                    outputs.append(dict(type='function_call_output', call_id=item['call_id'],
                        output=base64.b64decode(result['returned_output_utf8_b64']).decode('utf-8')))
                    local['tool_invocation_count'] += 1; local['tool_result_count'] += 1
                    local['raw_worker_result_bytes'] += (base / ('workers/' + worker_handle + '/result.raw.jsonl')).stat().st_size
                    if result['kind'] == 'Bash':
                        local['stdout_bytes'] += len(result['facts']['stdout_utf8'].encode())
                        local['stderr_bytes'] += len(result['facts']['stderr_utf8'].encode())
                rows, projected_facts = project_items(sid, attempt, response, items, sources, invocations, results)
                canonical.extend(rows); facts.extend(projected_facts)
                owned_history.extend(items); owned_history.extend(outputs)
                finished = not outputs
                if finished:
                    require(number == len(session['responses']) and any(i['type'] == 'message' for i in items), 'terminal_missing')
                    terminal = ''.join(p['text'] for i in items if i['type'] == 'message' for p in i['content'])
                    canonical.append(dict(type='result', subtype='success', result=terminal))
                active.stdin.write(encoded(dict(items=items, outputs=outputs, finished=finished)) + b'\n'); active.stdin.flush()
                if finished: break
            require(finished, 'terminal_missing')
            active.stdin.close()
            extra = active.stdout.read(IO['max_serialized_request_bytes'] + 1)
            controller_bytes.extend(extra)
            controller_stderr = active.stderr.read(IO['max_worker_stderr_bytes'] + 1)
            code = active.wait(timeout=2)
            require(code == 0 and not extra and not controller_stderr, 'controller_incomplete')
            controller_observation = dict(pid=active.pid, argv=active.args, cwd=str(paths['work']), started_ns=controller_start,
                ended_ns=time.monotonic_ns(), exit_code=code, signal=None, timeout=False, capture_complete=True, overflow=False)
            active.stdout.close(); active.stderr.close(); active = None
            controller_ref = store.put(prefix + '/controller.stdout.jsonl', bytes(controller_bytes))
            native_ref = store.put(prefix + '/controller.stderr.bin', controller_stderr)
            store.json(prefix + '/controller.process.json', controller_observation)
            last_receipt = finalize(episode['episode_id'], sid, controller_handle, config['pins']['fingerprint'],
                controller_observation, [], paths['work'], store, prefix + '/controller',
                dict(stdout=controller_ref, stderr=native_ref), native_ref)
            supervisor_refs.append(last_receipt)
            canonical_ref = store.put(prefix + '/stdout.jsonl', b''.join(encoded(row) + b'\n' for row in canonical))
            local['canonical_row_count'] = len(canonical)
            sessions.append(record('mapping_session', index=ordinal, episode_id=episode['episode_id'], session_id=sid,
                controller_handle=controller_handle, episode_origin_event_id=ledger.origin['origin_event_id'], attempt_order=attempt_order,
                raw_components=local_raw, supervisor_receipt_ref=last_receipt, counts=counts('session', sid, ledger, **local), complete=True))
        journal_ref = store.put('journal.jsonl', artifact_read(ledger.path))
        checkpoint_ref = record('artifact_reference', artifact='checkpoint.json', byte_length=(base / 'checkpoint.json').stat().st_size,
            sha256=digest(artifact_read(base / 'checkpoint.json')))
        ledger_sources, position = [], 0
        for event in ledger.events:
            line = encoded(event) + b'\n'
            ledger_sources.append(store.source(journal_ref, event['event_id'], 'ledger', position, position + len(line)))
            position += len(line)
        admissions = [e['permit_id'] for e in ledger.events if e['kind'] == 'reserve' and e['episode_id'] == episode['episode_id']]
        ledger_receipt = record('ledger_receipt', initiative_id=checkpoint['initiative_id'], ledger_id=checkpoint['ledger_id'],
            authority_id=ledger.authority['authority_id'], episode_id=episode['episode_id'], episode_origin_event_id=ledger.origin['origin_event_id'],
            checkpoint_ref=checkpoint_ref, journal_ref=journal_ref, first_sequence=1, last_sequence=len(ledger.events),
            prefix_sha256=checkpoint['journal_prefix']['cutoff_sha256'], last_event_sha256=digest(encoded(ledger.events[-1]) + b'\n'),
            admission_ids=admissions, admitted_request_units=sum(c[2] for c in ledger.usage() if c[1] == episode['episode_id']),
            elapsed_ns=ledger.elapsed(), fingerprint=config['pins']['fingerprint'], sources=ledger_sources)
        ledger_ref = store.json('ledger-receipt.json', ledger_receipt)
        ledger_reference = record('ledger_receipt_ref', artifact_ref=ledger_ref, receipt_schema=ledger_receipt['schema'],
            initiative_id=checkpoint['initiative_id'], ledger_id=checkpoint['ledger_id'], authority_id=ledger.authority['authority_id'],
            episode_id=episode['episode_id'], episode_origin_event_id=ledger.origin['origin_event_id'], fingerprint=config['pins']['fingerprint'])
        combined = b''.join(artifact_read(base / ('sessions/%02d/stdout.jsonl' % s['index'])) for s in sessions)
        canonical_ref = store.put('transcript.jsonl', combined)
        raw_hash = digest(b''.join(artifact_read(base / c['artifact_ref']['artifact']) for c in all_raw))
        total = {key: sum(s['counts'][key] for s in sessions) for key in COUNT_NAMES}
        total_counts = counts('bundle', episode['episode_id'], ledger, **total)
        # Final authoritative unit/time values are copied, never summed over sessions.
        total_counts['episode_elapsed_ns'] = ledger_receipt['elapsed_ns']
        mapping = dict(schema=VERSIONS['mapping'], fingerprint=config['pins']['fingerprint'], sessions=sessions,
            facts=facts, counts=total_counts, raw_transcript_sha256=raw_hash, canonical_sha256=canonical_ref['sha256'])
        mapping_ref = store.json('mapping.json', mapping)
        artifacts = []
        for parent, _, names in os.walk(base):
            for name in names:
                path = Path(parent) / name
                data = artifact_read(path)
                artifacts.append(record('artifact_reference', artifact=path.relative_to(base).as_posix(), byte_length=len(data), sha256=digest(data)))
        bundle = dict(schema=VERSIONS['bundle'], proof_scope='offline_fixture_only', fingerprint=config['pins']['fingerprint'],
            episode_id=episode['episode_id'], session_order=[s['session_id'] for s in sessions], artifacts=sorted(artifacts, key=lambda a: a['artifact']),
            raw_transcript_components=all_raw, raw_transcript_sha256=raw_hash, canonical_sha256=canonical_ref['sha256'],
            mapping_sha256=mapping_ref['sha256'], supervisor_receipts=supervisor_refs, ledger_receipts=[ledger_reference],
            counts=total_counts, complete=True, private_consumer_accepted=False)
        store.json('bundle.json', bundle)
        verify_bundle(config, base / 'bundle.json')
        packet = make_packet('controlled-run', 'offline_completed', '', config)
        (out / 'packet.json').write_bytes(encoded(packet) + b'\n')
        return packet
    except (Refusal, OSError, subprocess.SubprocessError, UnicodeError) as exc:
        if active is not None:
            if active.poll() is None: active.kill()
            active.wait(timeout=2)
            for stream in (active.stdin, active.stdout, active.stderr):
                try: stream.close()
                except OSError: pass
        if ledger is not None:
            if not (base / 'journal.jsonl').exists(): store.put('journal.jsonl', artifact_read(ledger.path))
        reason = exc.code if isinstance(exc, Refusal) else type(exc).__name__
        packet = make_packet('controlled-run', 'instrument_incomplete', reason, config)
        (out / 'packet.json').write_bytes(encoded(packet) + b'\n')
        return packet
    finally:
        if ledger is not None: ledger.close()


def make_packet(command_name, outcome, reason, config=None):
    config = config if type(config) is dict else {}
    mode = config.get('mode') if config.get('mode') in ('offline', 'live') else 'offline'
    fixed = config.get('pins') if type(config.get('pins')) is dict else {}
    return dict(schema=VERSIONS['packet'], command=command_name, mode=mode,
        outcome=outcome, reason=reason, missing_capabilities=list(LIVE_MISSING),
        requested_binding=dict(model=MODEL, effort='xhigh'),
        actual_provider_telemetry=dict(model='n/a', effort='n/a', tokens_in='n/a', tokens_out='n/a', cost_usd='n/a'),
        synthetic_binding_echo=MODEL if outcome == 'offline_completed' else None,
        fingerprint=fixed.get('fingerprint'), checked=outcome == 'offline_completed',
        limitations=['fixed non-billable local fixtures only'], live_ready=False, task_complete=False, private_consumer_accepted=False)


def verified_reference(base, reference):
    validate_record('artifact_reference', reference)
    path = Path(base) / reference['artifact']
    for parent in (path, *path.parents):
        if parent == Path(base).parent: break
        require(not parent.is_symlink(), 'unsafe_artifact')
    data = artifact_read(path)
    require(len(data) == reference['byte_length'] and digest(data) == reference['sha256'], 'artifact_mismatch')
    return data


def verify_source(base, source, refs):
    validate_record('raw_source', source)
    require(source['artifact'] in refs, 'source_missing')
    ref = refs[source['artifact']]
    require(ref['sha256'] == source['sha256'], 'source_mismatch')
    raw = verified_reference(base, ref)
    require(0 <= source['byte_start'] <= source['byte_end'] <= len(raw), 'source_span')
    producer = source['producer']
    if producer in ('supervisor',):
        fact = strict_json(raw)
        require(fact['event_id'] == source['event_id'] and fact['producer'] == producer, 'source_mismatch')
    elif producer in ('stub', 'ledger'):
        start = raw.rfind(b'\n', 0, source['byte_start']) + 1
        end = raw.find(b'\n', source['byte_start'])
        event = strict_json(raw[start:len(raw) if end < 0 else end])
        require(event['event_id'] == source['event_id'], 'source_mismatch')
    elif producer == 'worker' and source['artifact'].endswith('result.raw.jsonl'):
        result = strict_json(raw)
        require(source['event_id'] == result['worker_handle'] + '_result', 'source_mismatch')
    return raw[source['byte_start']:source['byte_end']]


def verify_supervisor(base, reference, refs):
    validate_record('supervisor_receipt_ref', reference)
    receipt = strict_json(verified_reference(base, reference['artifact_ref']))
    validate_record('supervisor_receipt', receipt)
    require(receipt['complete'] is True and receipt['missing_facts'] == []
            and receipt['kernel_boundary_accepted'] is False, 'supervisor_incomplete')
    require(all(reference[k] == receipt[k] for k in ('episode_id', 'session_id', 'worker_handle', 'boundary_handle', 'fingerprint')), 'receipt_identity')
    event_path = str(PurePosixPath(reference['artifact_ref']['artifact']).with_name('events.json'))
    require(event_path in refs, 'supervisor_events_missing')
    events = strict_json(verified_reference(base, refs[event_path]))
    require([e['kind'] for e in events] == ['spawn_ack', 'main_exit', 'tracked_fixture_handles_empty',
            'stdout_eof', 'stderr_eof', 'snapshot_observed', 'offline_finalized'], 'supervisor_order')
    last, seen = -1, set()
    for event in events:
        validate_record('supervisor_event', event)
        require(event['event_id'] not in seen and event['monotonic_ns'] >= last, 'late_fact')
        seen.add(event['event_id']); last = event['monotonic_ns']
        require(all(event[k] == receipt[k] for k in ('episode_id', 'session_id', 'worker_handle', 'boundary_handle', 'fingerprint')), 'authority_mismatch')
        source_data = verify_source(base, event['source'], refs)
        observed = strict_json(source_data)['observed']
        require(observed == dict(kind=event['kind'], facts=event['facts']), 'supervisor_fact_mismatch')
    require(receipt['sources'] == [e['source'] for e in events[:-1]]
            and events[-1]['facts']['receipt_ref'] == reference, 'receipt_source_mismatch')
    spawn, exited, empty = events[0]['facts'], events[1]['facts'], events[2]['facts']
    require(spawn['owned_processes'] == receipt['worker_handles'] == empty['owned_processes']
            and empty['remaining_handle_ids'] == [] and empty['last_spawn_event_id'] == events[0]['event_id'], 'owned_handles_live')
    handles = receipt['worker_handles']
    require(handles and len({h['handle_id'] for h in handles}) == len(handles), 'authority_mismatch')
    for handle in handles:
        require(handle['exit_source'] is not None and (handle['exit_code'] is not None or handle['signal'] is not None), 'main_exit_missing')
        verify_source(base, handle['spawn_source'], refs); verify_source(base, handle['exit_source'], refs)
    require(spawn['main_process'] == handles[0] and exited['process_handle_id'] == receipt['worker_handle']
            and exited['exit_code'] == handles[0]['exit_code'] and exited['signal'] == handles[0]['signal']
            and not exited['timeout'] and not exited['interrupted'], 'main_exit_missing')
    for index, channel in ((3, 'stdout'), (4, 'stderr')):
        capture = events[index]['facts']['capture']
        require(capture == receipt['stream_captures'][index - 3] and capture['channel'] == channel
                and capture['worker_handle'] == receipt['worker_handle']
                and capture['capture_complete'] and not capture['truncated'], 'capture_incomplete')
        data = verified_reference(base, capture['artifact_ref'])
        require(len(data) == capture['returned_bytes'], 'stream_mismatch')
        source = strict_json(verify_source(base, capture['eof_source'], refs))
        require(source['observed'] == dict(channel=channel, observed_eof=True), 'eof_missing')
    snapshot = receipt['snapshot']
    require(snapshot is not None and snapshot == events[5]['facts']['snapshot']
            and snapshot['worker_handle'] == receipt['worker_handle']
            and snapshot['boundary_handle'] == receipt['boundary_handle']
            and snapshot['quiescence_event_id'] == events[2]['event_id']
            and snapshot['stdout_eof_event_id'] == events[3]['event_id']
            and snapshot['stderr_eof_event_id'] == events[4]['event_id']
            and snapshot['observed_monotonic_ns'] > max(events[i]['monotonic_ns'] for i in (2, 3, 4)), 'snapshot_order')
    tuples = []
    for entry in snapshot['entries']:
        data = verified_reference(base, entry['artifact_ref'])
        tuples.append([entry['relative_path'], len(data), digest(data)])
    require(len({t[0] for t in tuples}) == len(tuples) and digest(encoded(sorted(tuples))) == snapshot['tree_sha256'], 'snapshot_mismatch')
    source = strict_json(verify_source(base, snapshot['source'], refs))
    require(source['observed'] == dict(tree_sha256=snapshot['tree_sha256'], entries=snapshot['entries']), 'snapshot_mismatch')
    return receipt


def verify_bundle(config, bundle_path):
    validate_config(config)
    bundle_path = Path(bundle_path)
    base = bundle_path.parent
    bundle = strict_json(artifact_read(bundle_path))
    fields(bundle, ('schema', 'proof_scope', 'fingerprint', 'episode_id', 'session_order', 'artifacts',
        'raw_transcript_components', 'raw_transcript_sha256', 'canonical_sha256', 'mapping_sha256',
        'supervisor_receipts', 'ledger_receipts', 'counts', 'complete', 'private_consumer_accepted'))
    require(bundle['schema'] == VERSIONS['bundle'] and bundle['proof_scope'] == 'offline_fixture_only'
            and bundle['complete'] is True and bundle['private_consumer_accepted'] is False
            and bundle['fingerprint'] == config['pins']['fingerprint'], 'bundle_version')
    refs = {}
    for ref in bundle['artifacts']:
        require(ref['artifact'] not in refs, 'duplicate_artifact')
        verified_reference(base, ref); refs[ref['artifact']] = ref
    actual = set()
    for parent, dirs, names in os.walk(base, followlinks=False):
        require(all(not (Path(parent) / name).is_symlink() for name in dirs), 'unsafe_artifact')
        actual.update((Path(parent) / name).relative_to(base).as_posix() for name in names)
    require(actual == set(refs) | {'bundle.json'}, 'artifact_census')
    require(refs['mapping.json']['sha256'] == bundle['mapping_sha256']
            and refs['transcript.jsonl']['sha256'] == bundle['canonical_sha256'], 'bundle_hash')
    mapping = strict_json(verified_reference(base, refs['mapping.json']))
    fields(mapping, ('schema', 'fingerprint', 'sessions', 'facts', 'counts', 'raw_transcript_sha256', 'canonical_sha256'))
    require(mapping['schema'] == VERSIONS['mapping'] and mapping['fingerprint'] == bundle['fingerprint']
            and mapping['counts'] == bundle['counts'] and mapping['canonical_sha256'] == bundle['canonical_sha256'], 'mapping_identity')
    validate_record('counts', bundle['counts'])
    require(bundle['counts']['scope'] == 'bundle' and bundle['counts']['scope_id'] == bundle['episode_id'], 'count_scope')
    components, raw, attempts = bundle['raw_transcript_components'], bytearray(), set()
    for index, component in enumerate(components):
        validate_record('raw_component', component)
        require(component['order_index'] == index and component['attempt_id'] not in attempts, 'component_order')
        attempts.add(component['attempt_id']); raw.extend(verified_reference(base, component['artifact_ref']))
    require(digest(raw) == bundle['raw_transcript_sha256'] == mapping['raw_transcript_sha256'], 'raw_hash')
    require([s['session_id'] for s in mapping['sessions']] == bundle['session_order']
            and len(bundle['session_order']) == len(set(bundle['session_order'])), 'session_order')
    supervisor = {}
    for ref in bundle['supervisor_receipts']:
        require(ref['worker_handle'] not in supervisor, 'duplicate_receipt')
        supervisor[ref['worker_handle']] = verify_supervisor(base, ref, refs)
    episode = strict_json(verified_reference(base, refs['episode.json'])); validate_episode(episode)
    require(episode['episode_id'] == bundle['episode_id'], 'episode_identity')
    checkpoint = strict_json(verified_reference(base, refs['checkpoint.json']))
    require(digest(verified_reference(base, refs['checkpoint.json'])) == config['checkpoint']['sha256'], 'checkpoint_pin')
    # Replay the immutable checkpoint/journal without acquiring authority or a clock.
    replay = object.__new__(Ledger)
    replay.config, replay.checkpoint, replay.episode, replay.authority = config, checkpoint, episode, checkpoint['authority_binding']
    journal_raw = verified_reference(base, refs['journal.jsonl'])
    require(journal_raw.endswith(b'\n'), 'journal_torn')
    replay.events = [strict_json(line) for line in journal_raw.splitlines()]
    replay.verify()
    require(len(bundle['ledger_receipts']) == 1, 'ledger_receipt_census')
    ledger_ref = bundle['ledger_receipts'][0]; validate_record('ledger_receipt_ref', ledger_ref)
    ledger_receipt = strict_json(verified_reference(base, ledger_ref['artifact_ref'])); validate_record('ledger_receipt', ledger_receipt)
    for key in ('initiative_id', 'ledger_id', 'authority_id', 'episode_id', 'episode_origin_event_id', 'fingerprint'):
        require(ledger_receipt[key] == ledger_ref[key], 'ledger_receipt_identity')
    own_events = [e for e in replay.events if e['episode_id'] == episode['episode_id']]
    require(own_events and own_events[0]['kind'] == 'episode_open'
            and ledger_receipt['episode_origin_event_id'] == own_events[0]['event_id']
            and ledger_receipt['admission_ids'] == [e['permit_id'] for e in own_events if e['kind'] == 'reserve']
            and ledger_receipt['admitted_request_units'] == sum(c[2] for c in replay.usage() if c[1] == episode['episode_id'])
            and ledger_receipt['elapsed_ns'] >= own_events[-1]['monotonic_elapsed_ns']
            and ledger_receipt['last_event_sha256'] == digest(encoded(replay.events[-1]) + b'\n')
            and ledger_receipt['last_sequence'] == len(replay.events)
            and ledger_receipt['journal_ref'] == refs['journal.jsonl'] and ledger_receipt['checkpoint_ref'] == refs['checkpoint.json'], 'ledger_receipt_census')
    for source in ledger_receipt['sources']: verify_source(base, source, refs)
    require(len(ledger_receipt['sources']) == len(replay.events), 'ledger_source_census')
    require(bundle['counts']['episode_admitted_request_units'] == ledger_receipt['admitted_request_units']
            and bundle['counts']['episode_elapsed_ns'] == ledger_receipt['elapsed_ns'], 'count_authority')
    expected_facts, combined, global_counts = [], bytearray(), {key: 0 for key in COUNT_NAMES}
    for index, session in enumerate(mapping['sessions'], 1):
        validate_record('mapping_session', session)
        sid = session['session_id']; source_session = episode['sessions'][index - 1]
        require(session['index'] == index and session['episode_id'] == episode['episode_id']
                and sid == source_session['session_id'] and session['complete']
                and session['episode_origin_event_id'] == own_events[0]['event_id']
                and session['counts']['scope'] == 'session' and session['counts']['scope_id'] == sid, 'session_identity')
        local_components = [c for c in components if c['session_id'] == sid]
        require(session['raw_components'] == local_components and session['attempt_order'] == [c['attempt_id'] for c in local_components], 'session_components')
        rows, history, local = [], [dict(role='user', content=source_session['prompt'])], {key: 0 for key in COUNT_NAMES}
        seen_calls, seen_items = set(), set()
        for number, component in enumerate(local_components, 1):
            attempt = component['attempt_id']; prefix = 'sessions/%02d/%s/' % (index, attempt)
            request = verified_reference(base, refs[prefix + 'request.json'])
            require(strict_json(request) == body(history), 'history_mismatch')
            permit = strict_json(verified_reference(base, refs[prefix + 'permit.json']))
            bound = strict_json(verified_reference(base, refs[prefix + 'bound.json']))
            require(permit['body_sha256'] == bound['body_sha256'] == digest(request)
                    and permit['bound_receipt_sha256'] == digest(encoded(bound))
                    and bound['provider_applicable'] is False and bound['proof_scope'] == 'synthetic_nonbillable'
                    and permit['episode_origin_event_id'] == own_events[0]['event_id'], 'permit_mismatch')
            reserved = [e for e in own_events if e['kind'] == 'reserve' and e['attempt_id'] == attempt]
            consumed = [e for e in own_events if e['kind'] == 'consume' and e['attempt_id'] == attempt]
            acknowledged = [e for e in own_events if e['kind'] == 'dispatch_ack' and e['attempt_id'] == attempt]
            require(len(reserved) == len(consumed) == len(acknowledged) == 1
                    and reserved[0]['body_sha256'] == digest(request) and reserved[0]['permit_id'] == permit['permit_id']
                    and reserved[0]['sequence'] < consumed[0]['sequence'] < acknowledged[0]['sequence'], 'admission_census')
            native = strict_json(verified_reference(base, refs[prefix + 'stub.stderr.jsonl']))
            process = strict_json(verified_reference(base, refs[prefix + 'stub.process.json']))
            require(native == dict(schema='tackle-controlled-stub-ack/1', attempt_id=attempt, body_sha256=digest(request), pid=process['pid'])
                    and process['exit_code'] == 0 and process['signal'] is None and not process['timeout'] and process['capture_complete']
                    and acknowledged[0]['evidence_sha256'] == refs[prefix + 'stub.stderr.jsonl']['sha256'], 'stub_census')
            raw_response = verified_reference(base, component['artifact_ref'])
            response, items, spans, sources = parse_response(raw_response, component['artifact_ref'], Store(base), sid, attempt)
            require(response == component['response_id'], 'response_identity')
            invocations, results, outputs = {}, {}, []
            for item_index, item in enumerate(items):
                require(item['id'] not in seen_items, 'duplicate_item'); seen_items.add(item['id'])
                if item['type'] != 'function_call': continue
                require(item['call_id'] not in seen_calls, 'duplicate_call'); seen_calls.add(item['call_id'])
                worker = 'w_' + sid + '_' + str(number) + '_' + str(item_index)
                envelope = strict_json(verified_reference(base, refs['workers/' + worker + '/invocation.json']))
                validate_record('worker_envelope', envelope)
                invocation = envelope['invocation']
                require(invocation['arguments_raw_span'] == spans[item_index]
                        and base64.b64decode(invocation['arguments_utf8_b64']) == item['arguments'].encode()
                        and invocation['item_id'] == item['id'] and invocation['call_id'] == item['call_id']
                        and invocation['function_name'] == item['name'], 'argument_mismatch')
                lexical = strict_json(verify_source(base, spans[item_index], refs))
                require(lexical == item['arguments'], 'source_span')
                result = strict_json(verified_reference(base, refs['workers/' + worker + '/result.json']))
                actual_result = strict_json(verified_reference(base, refs['workers/' + worker + '/result.raw.jsonl']))
                validate_result(result, invocation)
                require(dict(result, sources=[]) == actual_result and result['complete'] and worker in supervisor, 'result_source_mismatch')
                for source in result['sources']: verify_source(base, source, refs)
                if result['kind'] == 'Bash':
                    for channel in ('stdout', 'stderr'):
                        data = verify_source(base, result['facts'][channel + '_source'], refs)
                        require(data == result['facts'][channel + '_utf8'].encode(), 'stream_mismatch')
                    local['stdout_bytes'] += len(result['facts']['stdout_utf8'].encode())
                    local['stderr_bytes'] += len(result['facts']['stderr_utf8'].encode())
                invocations[item_index], results[item_index] = invocation, result
                outputs.append(dict(type='function_call_output', call_id=item['call_id'], output=base64.b64decode(result['returned_output_utf8_b64']).decode()))
                local['tool_invocation_count'] += 1; local['tool_result_count'] += 1
                local['raw_worker_result_bytes'] += refs['workers/' + worker + '/result.raw.jsonl']['byte_length']
            projected_rows, projected_facts = project_items(sid, attempt, response, items, sources, invocations, results)
            rows.extend(projected_rows); expected_facts.extend(projected_facts)
            history.extend(items); history.extend(outputs)
            if not outputs:
                require(number == len(local_components), 'terminal_order')
                rows.append(dict(type='result', subtype='success', result=''.join(p['text'] for i in items if i['type'] == 'message' for p in i['content'])))
            local['reservation_count'] += 1; local['consumption_count'] += 1; local['stub_ack_count'] += 1; local['reserved_request_units'] += 1
            local['response_item_count'] += len(items); local['raw_request_bytes'] += len(request); local['raw_response_bytes'] += len(raw_response)
        local['canonical_row_count'] = len(rows)
        expected_bytes = b''.join(encoded(row) + b'\n' for row in rows)
        require(expected_bytes == verified_reference(base, refs['sessions/%02d/stdout.jsonl' % index]), 'canonical_mismatch')
        require(all(session['counts'][key] == local[key] for key in COUNT_NAMES), 'count_mismatch')
        require(session['supervisor_receipt_ref']['worker_handle'] in supervisor, 'session_receipt_missing')
        for key in COUNT_NAMES: global_counts[key] += local[key]
        combined.extend(expected_bytes)
    require(mapping['facts'] == expected_facts and bytes(combined) == verified_reference(base, refs['transcript.jsonl'])
            and all(bundle['counts'][key] == global_counts[key] for key in COUNT_NAMES), 'projection_mismatch')
    require(bundle['counts']['stub_ack_count'] == bundle['counts']['consumption_count'] == bundle['counts']['reservation_count']
            == len([e for e in own_events if e['kind'] == 'reserve']), 'inference_census')
    return bundle


def main_parsed(args):
    config = None
    try:
        config = strict_json(artifact_read(args.config, IO['max_serialized_request_bytes']))
        roots, checkpoint = validate_config(config)
        if args.command == 'controlled-run':
            episode = strict_json(artifact_read(args.episode, IO['max_response_raw_bytes']))
            result = run(config, episode, args.out)
        else:
            if args.command == 'controlled-verify': verify_bundle(config, args.bundle)
            journal = roots['state_root'] / 'journal.jsonl'
            if journal.exists() or journal.is_symlink():
                raw = artifact_read(journal)
                require(not raw or raw.endswith(b'\n'), 'journal_torn')
                replay = object.__new__(Ledger)
                replay.config, replay.checkpoint = config, checkpoint
                replay.authority = checkpoint['authority_binding']
                replay.events = [strict_json(line) for line in raw.splitlines()]
                replay.verify()
            out = new_output(args.out, roots)
            result = make_packet(args.command, 'offline_completed', '', config)
            (out / 'packet.json').write_bytes(encoded(result) + b'\n')
    except (Refusal, OSError, UnicodeError, KeyError, TypeError, ValueError) as exc:
        reason = exc.code if isinstance(exc, Refusal) else type(exc).__name__
        result = make_packet(args.command, 'unsupported' if reason in ('live_unsupported', 'network_unsupported', 'timer_continuity_unverifiable') else 'malformed', reason, config)
    print(json.dumps(result, sort_keys=True))
    return 0 if result['outcome'] == 'offline_completed' else 2 if result['outcome'] == 'malformed' else 1


# The isolated component deliberately has no entry into the old route/bundle.
def isolated_policy():
    value = strict_json(artifact_read(FIXTURE / 'isolated_adapter.json'))
    require(value['schema'] == 'isolated-tool-policy/1', 'isolated_policy_version')
    # The pinned socket may name the owner's home as ~, so the public policy carries no user path.
    endpoint = value.get('docker_cli', {}).get('endpoint', '')
    if endpoint.startswith('const unix://~/'):
        value['docker_cli']['endpoint'] = 'const unix://' + os.path.expanduser(endpoint[len('const unix://'):])
    return value


def isolated_record(record_type, /, **values):
    versions = dict(Artifact='tackle-isolated-artifact/1', FileRequest='tackle-isolated-file-request/1',
        FileClaim='tackle-isolated-file-claim/1', NativeCommand='tackle-isolated-native-command/1',
        ContainerFacts='tackle-isolated-container-facts/1', ComponentResult='tackle-isolated-tool-result/1',
        Snapshot='tackle-isolated-component-snapshot/1', ComponentReceipt='tackle-isolated-component-receipt/1',
        ComponentBundle='tackle-isolated-component-bundle/1',
        ControllerInput='tackle-isolated-controller-input/1', HostRunObservation='tackle-isolated-host-run-observation/1')
    if record_type in versions: values = dict(schema=versions[record_type], **values)
    fields(values, isolated_policy()['record_fields'][record_type])
    return values


def isolated_path(value):
    require(type(value) is str and value.startswith('/') and '\\' not in value and '\0' not in value,
            'isolated_path')
    relative(value[1:])
    return value


def isolated_tree(root):
    entries = []
    for parent, dirs, names in os.walk(root, followlinks=False):
        for name in dirs:
            require(not (Path(parent) / name).is_symlink(), 'isolated_unsafe_tree')
        for name in sorted(names):
            path = Path(parent) / name
            data = artifact_read(path)
            entries.append([path.relative_to(root).as_posix(), len(data), digest(data)])
    return digest(encoded(sorted(entries)))


def isolated_fingerprint(config):
    return digest(encoded(dict(adapter=config['adapter'], image=config['image_id'],
        pins={k: v for k, v in config['pins'].items() if k != 'fingerprint'},
        caps=config['caps'], policy_sha256=config['policy_sha256'],
        network=config['network'], seccomp=config['seccomp'])))


def validate_isolated_config(config):
    policy = isolated_policy()
    fields(config, policy['record_fields']['ComponentConfig'])
    require(config['schema'] == 'tackle-isolated-component-config/1'
            and config['mode'] == 'component-offline' and config['adapter'] == policy['adapter'], 'isolated_version')
    fields(config['docker_cli'], policy['record_fields']['DockerCLI'])
    expected_cli = {k: v.removeprefix('const ') for k, v in policy['docker_cli'].items()}
    require(config['docker_cli'] == expected_cli, 'isolated_cli_pin')
    require(config['image_id'] == policy['image_id'] and config['network'] == 'none'
            and config['seccomp'] == 'docker-default', 'isolated_configuration')
    require(type(config['provider_requests']) is int and config['provider_requests'] == 0, 'isolated_provider_absent')
    require(config['caps'] == policy['caps'] and all(type(v) is int for v in config['caps'].values()), 'isolated_caps')
    typed(config['policy_sha256'], 'sha256')
    require(config['policy_sha256'] == digest(artifact_read(FIXTURE / 'isolated_adapter.json')), 'isolated_policy_pin')
    fields(config['roots'], policy['record_fields']['ComponentRoots'])
    roots = {name: directory(value) for name, value in config['roots'].items()}
    parent = roots['component_root']
    temporary = Path(tempfile.gettempdir()).resolve()
    require(parent != temporary and temporary in parent.parents, 'isolated_temporary_root')
    require(len(set(roots.values())) == len(roots) and all(path.parent == parent for name, path in roots.items()
            if name != 'component_root'), 'isolated_root_relationship')
    require(not list(roots['cli_home'].iterdir()) and not list(roots['cli_config'].iterdir()), 'isolated_inherited_config')
    fields(config['pins'], policy['record_fields']['ComponentPins'])
    sources = {'controlled_route.py': HERE / 'controlled_route.py', 'controlled_worker.py': HERE / 'controlled_worker.py',
               'streams.json': FIXTURE / 'streams.json', 'isolated_adapter.json': FIXTURE / 'isolated_adapter.json'}
    fields(config['pins']['source_files'], sources)
    for name, path in sources.items():
        typed(config['pins']['source_files'][name], 'sha256')
        copied = roots['runtime'] / 'harness' / (('fixtures/controlled-route/' + name) if name.endswith('.json') else name)
        require(digest(artifact_read(path)) == config['pins']['source_files'][name]
                == digest(artifact_read(copied)), 'isolated_source_pin')
    fields(config['pins']['engine_files'], policy['engine_files'])
    for name, text in policy['engine_files'].items():
        data = artifact_read(roots['runtime'] / 'engine-files' / name)
        require(data == text.encode() and digest(data) == config['pins']['engine_files'][name], 'isolated_engine_file_pin')
    allowed_files = {'harness/controlled_route.py', 'harness/controlled_worker.py',
        'harness/fixtures/controlled-route/streams.json', 'harness/fixtures/controlled-route/isolated_adapter.json',
        *('engine-files/' + name for name in policy['engine_files'])}
    observed_files = set()
    for parent_path, dirs, names in os.walk(roots['runtime'], followlinks=False):
        require(stat.S_IMODE(Path(parent_path).stat().st_mode) == 0o555, 'isolated_runtime_permissions')
        for name in names:
            path = Path(parent_path) / name
            require(stat.S_IMODE(path.lstat().st_mode) == 0o444, 'isolated_runtime_permissions')
            observed_files.add(path.relative_to(roots['runtime']).as_posix())
    require(observed_files == allowed_files, 'isolated_runtime_manifest')
    for name in ('runtime_tree_sha256', 'image_config_sha256', 'fingerprint'): typed(config['pins'][name], 'sha256')
    require(isolated_tree(roots['runtime']) == config['pins']['runtime_tree_sha256'], 'isolated_runtime_pin')
    for role in ('work', 'tmp'): isolated_tree(roots[role])
    require(config['pins']['fingerprint'] == isolated_fingerprint(config), 'isolated_fingerprint')
    return roots


def validate_isolated_invocation(invocation):
    validate_invocation(invocation)
    raw = strict_json(base64.b64decode(invocation['arguments_utf8_b64'], validate=True))
    validate_tool(invocation['function_name'], raw)
    require(encoded(raw) == encoded(invocation['parsed_input']), 'isolated_argument_continuity')
    require(invocation['function_name'] in ('Read', 'Write', 'Bash'), 'isolated_tool')
    for key in ('episode_id', 'session_id', 'attempt_id', 'response_id', 'item_id', 'call_id', 'worker_handle'):
        require(len(invocation[key]) <= 128, 'isolated_identifier')
    value = invocation['parsed_input']
    if invocation['function_name'] == 'Bash':
        require(len(value['command'].encode('utf-8')) <= 65536, 'isolated_command_size')
        isolated_path(value['cwd'])
    else:
        isolated_path(value['file_path'])
    return invocation


def isolated_plan(config, invocation, request_id, output=None):
    roots = validate_isolated_config(config)
    validate_isolated_invocation(invocation)
    require(invocation['fingerprint'] == config['pins']['fingerprint'], 'isolated_invocation_pin')
    require(type(request_id) is str and re.fullmatch('[0-9a-f]{32}', request_id), 'isolated_request_id')
    value, name = invocation['parsed_input'], invocation['function_name']
    cwd = value['cwd'] if name == 'Bash' else '/work'
    chosen = next((role for role in ('work', 'tmp') if cwd == '/' + role or cwd.startswith('/' + role + '/')), None)
    require(chosen is not None, 'isolated_cwd')
    host_cwd = roots[chosen] / cwd[len(chosen) + 2:]
    require(not host_cwd.is_symlink() and host_cwd.is_dir(), 'isolated_cwd')
    for ancestor in host_cwd.parents:
        if ancestor == roots[chosen].parent: break
        require(not ancestor.is_symlink(), 'isolated_cwd')
    out = Path(output) if output is not None else roots['evidence_parent'] / request_id
    require(out.is_absolute() and out.parent == roots['evidence_parent'], 'isolated_output_root')
    mounts = [dict(role=role, source=str(roots[role]), destination='/' + role, writable=role in ('work', 'tmp'))
              for role in ('runtime', 'work', 'tmp')]
    mounts += [dict(role=role, source=str(roots['runtime'] / 'engine-files' / filename), destination='/etc/' + filename,
                    writable=False) for role, filename in (('image_hosts', 'hosts'), ('image_hostname', 'hostname'),
                                                           ('image_resolver', 'resolv.conf'))]
    argv = [config['docker_cli']['path'], 'create', '--pull=never', '--interactive', '--network=none', '--read-only',
        '--name=tackle-isolated-' + request_id, '--cidfile=' + str(out / 'owned-cid.txt'),
        '--label=dev.tackle.isolated-tool=' + request_id, '--cap-drop=ALL', '--security-opt=no-new-privileges',
        '--user=65534:65534', '--pids-limit=64', '--memory=256m', '--memory-swap=256m', '--cpus=1',
        '--ipc=none', '--log-driver=none', '--stop-timeout=1', '--hostname=tackle-isolated-worker', '--workdir=' + cwd]
    argv += ['--env=' + key + '=' + value for key, value in isolated_policy()['participant_env'].items()]
    for mount in mounts:
        argv += ['--mount', 'type=bind,src=' + mount['source'] + ',dst=' + mount['destination']
                 + (',readonly' if not mount['writable'] else '')]
    process = [SHELL, '-c', value['command']] if name == 'Bash' else [
        '/usr/local/bin/python3', '-I', '-B', '/runtime/harness/controlled_worker.py', '--isolated-file-worker/1']
    argv += ['--entrypoint=' + process[0], config['image_id'], *process[1:]]
    request = b'' if name == 'Bash' else encoded(isolated_record('FileRequest', request_id=request_id,
        function_name=name, arguments=value))
    require(len(request) <= config['caps']['max_request_bytes'], 'isolated_request_size')
    return dict(request_id=request_id, name='tackle-isolated-' + request_id,
        mounts=mounts, create_argv=argv, process_argv=process, cwd=cwd, request=request, output=out)


def isolated_put(store, path, data):
    ref = store.put(path, data)
    return isolated_record('Artifact', artifact=ref['artifact'], sha256=ref['sha256'], byte_length=ref['byte_length'])


def isolated_capture(argv, data, deadline, limits, record_store):
    """Actual host subprocess capture; callers cannot turn missing EOF into success."""
    import selectors
    start = time.monotonic_ns()
    process = subprocess.Popen(argv, cwd=HERE.parents[2], env=record_store['environment'],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True, close_fds=True)
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ, 'stdout')
    selector.register(process.stderr, selectors.EVENT_READ, 'stderr')
    selector.register(process.stdin, selectors.EVENT_WRITE, 'input')
    offset, eof, streams = 0, set(), dict(stdout=bytearray(), stderr=bytearray())
    received = dict(stdout=0, stderr=0)
    timeout = overflow = killed = False
    drain_deadline = None
    for stream in (process.stdout, process.stderr, process.stdin): os.set_blocking(stream.fileno(), False)
    while selector.get_map():
        now = time.monotonic()
        if now >= deadline or overflow:
            timeout = timeout or now >= deadline
            if not killed:
                try: os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError: pass
                killed, drain_deadline = True, now + 1
            if now >= drain_deadline: break
        for key, _ in selector.select(.02):
            if key.data == 'input':
                if offset == len(data):
                    selector.unregister(key.fileobj); key.fileobj.close(); continue
                try: offset += os.write(key.fileobj.fileno(), data[offset:offset + 65536])
                except BrokenPipeError:
                    selector.unregister(key.fileobj); key.fileobj.close()
                continue
            chunk = os.read(key.fileobj.fileno(), 65536)
            if not chunk:
                eof.add(key.data); selector.unregister(key.fileobj); key.fileobj.close(); continue
            received[key.data] += len(chunk)
            available = max(0, limits[key.data] - len(streams[key.data]))
            streams[key.data].extend(chunk[:available])
            if len(chunk) > available: overflow = True
    selector.close()
    if not timeout and not overflow and process.poll() is None:
        remaining = deadline - time.monotonic()
        if remaining > 0:
            try: process.wait(timeout=remaining)
            except subprocess.TimeoutExpired: timeout = True
        else:
            timeout = True
    if process.poll() is None:
        try: os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError: pass
    code = process.wait(timeout=2)
    for stream in (process.stdin, process.stdout, process.stderr):
        if not stream.closed: stream.close()
    end = time.monotonic_ns()
    timeout = timeout or end > int(deadline * 1000000000)
    return dict(argv=argv, started_ns=start, ended_ns=end,phase_deadline_ns=int(deadline*1000000000),
        input_bytes_total=len(data),input_bytes_written=offset,stdout_received_bytes=received['stdout'],stderr_received_bytes=received['stderr'],
        exit_code=code if code >= 0 else None, signal=-code if code < 0 else None, timeout=timeout,
        overflow=overflow, eof_channels=sorted(eof), capture_complete=not timeout and not overflow
        and eof == {'stdout', 'stderr'} and offset == len(data),
        streams={name: bytes(value) for name, value in streams.items()})


def isolated_image(raw, config):
    require(digest(raw) == config['pins']['image_config_sha256'], 'isolated_image_config_pin')
    image, = strict_json(raw)
    require(image['Id'] == config['image_id'] and image['Os'] == 'linux'
            and image['Architecture'] in ('arm64', 'amd64'), 'isolated_image')
    image_config = image.get('Config')
    require(type(image_config) is dict, 'isolated_image_config')
    volumes = image_config.get('Volumes')
    require(volumes is None or (type(volumes) is dict and not volumes), 'isolated_image_volume')
    env = image_config['Env']
    require(type(env) is list and all(type(x) is str and '=' in x for x in env), 'isolated_image_env')
    names = [x.split('=', 1)[0] for x in env]
    require(len(names) == len(set(names)) and set(names) <= set(isolated_policy()['image_env_names']), 'isolated_image_env')
    return dict(x.split('=', 1) for x in env)


def isolated_owned_identity(info, plan, cid, config=None, command_id='inspect'):
    require(type(info) is dict and info['Id'] == cid and re.fullmatch('[0-9a-f]{64}', cid), 'isolated_ownership')
    cfg, host, state = info['Config'], info['HostConfig'], info['State']
    require(type(info['Mounts']) is list and all(type(item) is dict
        and type(item['Source']) is str and type(item['Destination']) is str
        and type(item['RW']) is bool for item in info['Mounts']), 'isolated_mounts')
    for key in ('PidsLimit', 'Memory', 'MemorySwap', 'NanoCpus'): typed(host[key], 'uint')
    require(info['Name'] == '/' + plan['name'] and cfg['Labels'] == {'dev.tackle.isolated-tool': plan['request_id']}
        and info['Image'] == (config or {})['image_id'] and cfg['User'] == '65534:65534', 'isolated_ownership')
    observed = [dict(role=next((m['role'] for m in plan['mounts'] if m['destination'] == item['Destination']), 'unknown'),
        source=item['Source'], destination=item['Destination'], writable=item['RW']) for item in info['Mounts']]
    require(all(item['Type'] == 'bind' for item in info['Mounts'])
        and sorted(observed, key=lambda x: x['destination']) == sorted(plan['mounts'], key=lambda x: x['destination']), 'isolated_mounts')
    require(host['NetworkMode'] == 'none' and host['ReadonlyRootfs'] is True and host['Privileged'] is False
        and host['CapDrop'] == ['ALL'] and host['CapAdd'] in (None, []) and host['SecurityOpt'] == ['no-new-privileges']
        and host['IpcMode'] == 'none' and host['PidsLimit'] == 64 and host['Memory'] == 268435456
        and host['MemorySwap'] == 268435456 and host['NanoCpus'] == 1000000000
        and host['LogConfig']['Type'] == 'none' and host['Devices'] in (None, [])
        and host['DeviceRequests'] in (None, []) and host['GroupAdd'] in (None, [])
        and host['PortBindings'] in (None, {}) and host['ExtraHosts'] in (None, []), 'isolated_kernel_config')
    require(cfg['Tty'] is False and cfg['WorkingDir'] == plan['cwd']
        and cfg['Entrypoint'] == [plan['process_argv'][0]] and cfg['Cmd'] == plan['process_argv'][1:]
        and cfg['Hostname'] == 'tackle-isolated-worker', 'isolated_process_config')
    expected_env = dict(plan['image_env'], **isolated_policy()['participant_env'])
    require(type(cfg['Env']) is list and all(type(x) is str and '=' in x for x in cfg['Env'])
        and len(cfg['Env']) == len(expected_env)
        and dict(x.split('=', 1) for x in cfg['Env']) == expected_env, 'isolated_environment')
    for key in ('Running', 'OOMKilled'): typed(state[key], 'bool')
    typed(state['Pid'], 'uint'); typed(state['ExitCode'], 'int')
    return isolated_record('ContainerFacts', request_id=plan['request_id'], cid=cid, name=plan['name'],
        label_key='dev.tackle.isolated-tool', label_value=plan['request_id'], image_id=config['image_id'],
        user='65534:65534', mounts=observed, network='none', readonly_rootfs=True, caps_drop=['ALL'],
        no_new_privileges=True, default_seccomp=True, privileged=False, ipc='none', tty=False,
        pids_limit=64, memory_bytes=268435456, memory_swap_bytes=268435456, nano_cpus=1000000000,
        running=state['Running'], pid=state['Pid'], exit_code=state['ExitCode'], oom_killed=state['OOMKilled'],
        source_command_id=command_id)


def validate_isolated_result(result, invocation, host_records):
    fields(result, isolated_policy()['record_fields']['ComponentResult'])
    require(result['schema'] == 'tackle-isolated-tool-result/1', 'isolated_result_version')
    keys = isolated_policy()['record_fields']['InvocationIdentity']
    fields(result['identity'], keys)
    require(result['identity'] == {k: invocation[k] for k in keys}
        and encoded(result['identity']) == encoded({k: invocation[k] for k in keys})
        and result['invocation_sha256'] == digest(encoded(invocation)), 'isolated_result_identity')
    require(type(result['complete']) is bool and result['complete'] is True, 'isolated_result_incomplete')
    typed(result['returned_sha256'], 'sha256')
    try: returned = base64.b64decode(result['returned_utf8_b64'], validate=True)
    except (ValueError, TypeError) as exc: raise Refusal('isolated_base64') from exc
    require(digest(returned) == result['returned_sha256'], 'isolated_result_hash')
    kind, facts, value = result['kind'], result['facts'], invocation['parsed_input']
    require(type(kind) is str, 'isolated_result_kind')
    require(kind in (('Bash',) if invocation['function_name'] == 'Bash'
            else (invocation['function_name'], 'refused')), 'isolated_result_kind')
    fields(facts, isolated_policy()['record_fields'][{'Read':'ReadFacts','Write':'WriteFacts','Bash':'BashFacts','refused':'RefusalFacts'}[kind]])
    if kind == 'Read':
        for key in ('byte_offset', 'requested_max_bytes', 'returned_bytes'): typed(facts[key], 'uint')
        typed(facts['eof'], 'bool')
        require(type(facts['file_path']) is str and type(facts['content_utf8']) is str, 'isolated_read')
        typed(facts['content_sha256'],'sha256')
        require(invocation['function_name'] == kind and facts['file_path'] == value['file_path']
            and facts['byte_offset'] == value['byte_offset'] and facts['requested_max_bytes'] == value['max_bytes']
            and facts['returned_bytes'] <= value['max_bytes'] and facts['content_utf8'].encode() == returned
            and len(returned) == facts['returned_bytes'] and digest(returned) == facts['content_sha256'], 'isolated_read')
    elif kind == 'Write':
        typed(facts['bytes_written'], 'uint'); typed(facts['content_sha256'], 'sha256')
        require(invocation['function_name'] == kind and facts['file_path'] == value['file_path']
            and facts['bytes_written'] == len(value['content'].encode())
            and facts['content_sha256'] == digest(value['content'].encode()) and returned == encoded(facts), 'isolated_write')
    elif kind == 'Bash':
        require(all(type(facts[k]) is str for k in ('command','cwd','shell_path','stdout_utf8','stderr_utf8')), 'isolated_bash')
        require(invocation['function_name'] == kind and facts['command'] == value['command'] and facts['cwd'] == value['cwd']
            and facts['argv'] == [SHELL, '-c', value['command']] and facts['shell_path'] == SHELL, 'isolated_bash')
        typed(facts['timeout'], 'bool'); typed(facts['capture_complete'], 'bool')
        typed(facts['exit_code'], 'nullable<int>'); typed(facts['signal'], 'nullable<positive_int>')
        require(not facts['timeout'] and facts['capture_complete'] and facts['signal'] is None, 'isolated_bash_incomplete')
        require(facts['exit_code'] == host_records['stopped']['exit_code'], 'isolated_exit')
        for channel in ('stdout', 'stderr'):
            isolated_validate_artifact(facts[channel + '_ref'])
            require(facts[channel + '_ref'] == host_records['start'][channel + '_ref']
                and facts[channel + '_utf8'].encode() == host_records[channel], 'isolated_stream')
        require(returned == encoded([dict(type='text', text=facts['stdout_utf8']), dict(type='text', text=facts['stderr_utf8'])]), 'isolated_returned')
    else:
        typed(facts['errno'], 'nullable<int>'); typed(facts['effect_started'], 'bool')
        require(facts['mechanism'] in ('path_policy','observed_os_error','observed_decode')
            and (facts['mechanism'] == 'observed_os_error' or facts['errno'] is None)
            and type(facts['error_code']) is str and returned == encoded(facts), 'isolated_refusal')
    require(result['host_command_ids'] == host_records['command_ids'], 'isolated_result_sources')
    if invocation['function_name'] == 'Bash': require(result['claim_ref'] is None, 'isolated_claim_authority')
    else:
        isolated_validate_artifact(result['claim_ref'])
        require(result['claim_ref'] == host_records['start']['stdout_ref'], 'isolated_claim_source')
        claim = strict_json(host_records['stdout'])
        isolated_validate_file_claim(claim, invocation, result['request_id'])
        require(claim['schema'] == 'tackle-isolated-file-claim/1' and type(claim['complete']) is bool
            and claim['complete'] is True and claim['request_id'] == result['request_id']
            and claim['kind'] == kind and encoded(claim['facts']) == encoded(facts)
            and claim['returned_utf8_b64'] == result['returned_utf8_b64']
            and claim['returned_sha256'] == result['returned_sha256'], 'isolated_file_claim')
    return result


def isolated_validate_artifact(ref):
    fields(ref, isolated_policy()['record_fields']['Artifact'])
    require(ref['schema'] == 'tackle-isolated-artifact/1', 'isolated_artifact_version')
    relative(ref['artifact']); typed(ref['sha256'], 'sha256'); typed(ref['byte_length'], 'uint')


def isolated_missing(command, cid):
    return command['exit_code'] == 1 and command['signal'] is None and command['capture_complete'] \
        and command['streams']['stdout'] in (b'', b'[]\n') and command['streams']['stderr'] in (
            ('Error: No such object: ' + cid + '\n').encode(),
            ('Error response from daemon: No such container: ' + cid + '\n').encode())


def isolated_host_controller(config, invocation, output, request_id, run_started_ns, run_deadline_ns, _simulation=None):
    """One component; simulation is a source-test seam, never a public capability."""
    roots = validate_isolated_config(config)
    validate_isolated_invocation(invocation)
    out = Path(output).absolute()
    require(not out.exists() and not out.is_symlink() and out.parent == roots['evidence_parent'], 'isolated_output_exists')
    plan = isolated_plan(config, invocation, request_id, out)
    if _simulation is not None:
        fields(_simulation, ('state_path',))
        simulated_state = Path(_simulation['state_path'])
        require(simulated_state.is_absolute() and roots['component_root'] in simulated_state.parents
                and not simulated_state.is_symlink(), 'isolated_simulation_state')
    else:
        require(digest(artifact_read(config['docker_cli']['path'])) == config['docker_cli']['sha256'], 'isolated_cli_pin')
    out.mkdir(mode=0o700)
    store = Store(out)
    commands, artifacts = [], []
    retained = 0
    def put(path, data):
        nonlocal retained
        require(retained + len(data) <= config['caps']['max_retained_bytes'], 'isolated_retention_cap')
        ref = isolated_put(store, path, data); artifacts.append(ref); retained += len(data); return ref
    invocation_ref = put('invocation.json', encoded(invocation))
    put('create-intent.json', encoded(dict(request_id=request_id, name=plan['name'], label_key='dev.tackle.isolated-tool',
        label_value=request_id, cidfile=str(out/'owned-cid.txt'), effect_observed=False)))
    environment = dict(PATH='/usr/bin:/bin', HOME=str(roots['cli_home']), DOCKER_CONFIG=str(roots['cli_config']),
        DOCKER_HOST=config['docker_cli']['endpoint'], LANG='C.UTF-8')
    main_deadline = (run_started_ns + config['caps']['run_main_seconds'] * 1000000000) / 1000000000
    final_deadline = run_deadline_ns / 1000000000
    docker = config['docker_cli']['path']
    def native(phase, args, data=b''):
        planned = [docker, *args]
        argv = planned if _simulation is None else [PYTHON, '-B', str(FIXTURE/'isolated_engine_fixture.py'),
            '--state', str(_simulation['state_path']), '--', *planned]
        cleanup = phase.startswith('cleanup')
        deadline = min(final_deadline if cleanup else main_deadline,
                       time.monotonic() + (config['caps']['tool_seconds'] if phase == 'start_attached' else 8))
        require(deadline > time.monotonic(), 'isolated_deadline')
        maximum = config['caps']['max_engine_command_stream_bytes']
        limits = dict(stdout=maximum, stderr=maximum)
        if phase == 'start_attached':
            limits = dict(stdout=config['caps']['max_stdout_bytes'] if invocation['function_name']=='Bash'
                else config['caps']['max_file_result_bytes'], stderr=config['caps']['max_stderr_bytes'])
        observed = isolated_capture(argv, data, deadline, limits, dict(environment=environment))
        ordinal = len(commands); prefix = 'native/%02d-' % ordinal + phase
        record = isolated_record('NativeCommand', command_id='command_' + str(ordinal), sequence=ordinal, phase=phase,
            argv=argv, cwd=str(HERE.parents[2]), input_ref=put(prefix+'/input.bin', data) if data else None,
            stdout_ref=put(prefix+'/stdout.bin', observed['streams']['stdout']),
            stderr_ref=put(prefix+'/stderr.bin', observed['streams']['stderr']),
            **{key: observed[key] for key in ('started_ns','ended_ns','exit_code','signal','timeout','overflow','eof_channels','capture_complete',
                'phase_deadline_ns','input_bytes_total','input_bytes_written','stdout_received_bytes','stderr_received_bytes')})
        commands.append(record)
        return observed, record
    def complete(observation):
        require(observation['capture_complete'] and not observation['timeout'] and not observation['overflow'], 'isolated_capture_incomplete')
    def inspect(phase, target):
        observation, reference = native(phase, ['inspect','--type=container',target]); complete(observation)
        require(observation['exit_code'] == 0, 'isolated_inspect')
        info, = strict_json(observation['streams']['stdout'])
        return info, reference
    created = stopped = result = result_ref = snapshot = None
    cid = None; attempted = owned = cleanup_confirmed = False; failures = []
    try:
        image_obs, _ = native('image_inspect',['image','inspect',config['image_id']]); complete(image_obs)
        require(image_obs['exit_code']==0, 'isolated_image_unavailable')
        plan['image_env'] = isolated_image(image_obs['streams']['stdout'], config)
        validate_isolated_config(config)
        attempted = True
        create_obs, _ = native('create',plan['create_argv'][1:])
        cid_path=out/'owned-cid.txt'
        if cid_path.exists():
            cid_data=artifact_read(cid_path,65)
            cid=cid_data.decode().strip()
            require(re.fullmatch('[0-9a-f]{64}',cid) is not None, 'isolated_cid')
            require(retained+len(cid_data)<=config['caps']['max_retained_bytes'],'isolated_retention_cap')
            artifacts.append(isolated_record('Artifact',artifact='owned-cid.txt',sha256=digest(cid_data),byte_length=len(cid_data)))
            retained+=len(cid_data)
        require(cid is not None, 'isolated_create_unknown')
        info, ref = inspect('inspect_created',cid)
        created = isolated_owned_identity(info,plan,cid,config,ref['command_id']); owned=True
        complete(create_obs)
        require(create_obs['exit_code']==0 and create_obs['streams']['stdout']==(cid+'\n').encode(), 'isolated_create_unknown')
        validate_isolated_config(config)
        require(main_deadline-time.monotonic()>=config['caps']['tool_seconds'], 'isolated_start_deadline')
        start_obs,start_ref=native('start_attached',['start','--attach','--interactive',cid],plan['request'])
        complete(start_obs)
        wait_obs,_=native('wait',['wait',cid]); complete(wait_obs)
        require(wait_obs['exit_code']==0, 'isolated_wait')
        info,ref=inspect('inspect_stopped',cid)
        stopped=isolated_owned_identity(info,plan,cid,config,ref['command_id'])
        require(not stopped['running'] and stopped['pid']==0 and not stopped['oom_killed']
            and start_obs['exit_code']==stopped['exit_code']
            and wait_obs['streams']['stdout']==(str(stopped['exit_code'])+'\n').encode(), 'isolated_exit')
        if invocation['function_name']=='Bash':
            facts=dict(command=invocation['parsed_input']['command'],argv=plan['process_argv'],shell_path=SHELL,cwd=plan['cwd'],
                stdout_ref=start_ref['stdout_ref'],stderr_ref=start_ref['stderr_ref'],
                stdout_utf8=start_obs['streams']['stdout'].decode('utf-8'),stderr_utf8=start_obs['streams']['stderr'].decode('utf-8'),
                exit_code=stopped['exit_code'],signal=None,timeout=False,capture_complete=True)
            kind='Bash'; claim_ref=None
            returned=encoded([dict(type='text',text=facts['stdout_utf8']),dict(type='text',text=facts['stderr_utf8'])])
        else:
            claim=strict_json(start_obs['streams']['stdout'])
            fields(claim,isolated_policy()['record_fields']['FileClaim'])
            require(claim['schema']=='tackle-isolated-file-claim/1' and claim['request_id']==request_id
                and type(claim['complete']) is bool and claim['complete'], 'isolated_file_claim')
            kind,facts=claim['kind'],claim['facts']; returned=base64.b64decode(claim['returned_utf8_b64'],validate=True)
            claim_ref=start_ref['stdout_ref']
        result=isolated_record('ComponentResult',request_id=request_id,invocation_sha256=digest(encoded(invocation)),
            identity={key:invocation[key] for key in isolated_policy()['record_fields']['InvocationIdentity']},
            kind=kind,facts=facts,returned_utf8_b64=base64.b64encode(returned).decode(),returned_sha256=digest(returned),
            complete=True,claim_ref=claim_ref,host_command_ids=[c['command_id'] for c in commands])
        validate_isolated_result(result,invocation,dict(stopped=stopped,start=start_ref,
            **start_obs['streams'],command_ids=result['host_command_ids']))
    except (Refusal,OSError,UnicodeError,ValueError,KeyError,TypeError) as exc:
        failures.append(exc.code if isinstance(exc,Refusal) else type(exc).__name__)
    finally:
        if attempted:
            try:
                info,ref=inspect('cleanup_reconcile',plan['name'])
                recovered=info['Id']
                require(cid is None or cid==recovered, 'isolated_ownership')
                observed=isolated_owned_identity(info,plan,recovered,config,ref['command_id'])
                cid,owned=recovered,True
                if observed['running']:
                    killed,_=native('cleanup_kill',['kill',cid]); complete(killed)
                    require(killed['exit_code']==0, 'isolated_cleanup_kill')
                removed,_=native('cleanup_remove',['rm','--force',cid]); complete(removed)
                require(removed['exit_code']==0 and removed['streams']['stdout']==(cid+'\n').encode(), 'isolated_cleanup_remove')
                absent,_=native('cleanup_absence',['inspect','--type=container',cid]); complete(absent)
                require(isolated_missing(absent,cid), 'isolated_cleanup_absence')
                cleanup_confirmed=True
            except (Refusal,OSError,UnicodeError,ValueError,KeyError,TypeError) as exc:
                failures.append(exc.code if isinstance(exc,Refusal) else type(exc).__name__)
        if not failures and result is not None and cleanup_confirmed:
            try:
                if _simulation is not None and strict_json(artifact_read(_simulation['state_path']))['fault'] == 'finalize_stall':
                    subprocess.run([PYTHON, '-B', str(FIXTURE/'isolated_engine_fixture.py'), '--finalization-control=stall'], check=True)
                require(time.monotonic_ns() < run_deadline_ns, 'isolated_run_deadline')
                tree=isolated_tree(roots['work']); entries=[]
                for parent,dirs,names in os.walk(roots['work'],followlinks=False):
                    for name in sorted(names):
                        path=Path(parent)/name; rel=path.relative_to(roots['work']).as_posix()
                        entries.append(isolated_record('SnapshotEntry',relative_path=rel,mode=stat.S_IMODE(path.stat().st_mode),
                            artifact_ref=put('snapshot/'+rel,artifact_read(path))))
                snapshot=isolated_record('Snapshot',root_role='work',observed_ns=time.monotonic_ns(),entries=entries,tree_sha256=tree)
                result_ref=put('result.json',encoded(result))
                require(time.monotonic_ns() < run_deadline_ns, 'isolated_run_deadline')
            except (Refusal,OSError,UnicodeError,ValueError,KeyError,TypeError) as exc:
                failures.append(exc.code if isinstance(exc,Refusal) else type(exc).__name__)
                result_ref = snapshot = None
    receipt=isolated_record('ComponentReceipt',proof_scope='source_simulation' if _simulation is not None else 'native_public_component',
        request_id=request_id,fingerprint=config['pins']['fingerprint'],invocation_ref=invocation_ref,result_ref=result_ref,
        native_commands=commands,container_created=created,container_stopped=stopped,cleanup_confirmed=cleanup_confirmed,
        owned_cid=cid if owned else None,snapshot=snapshot,component_boundary_observed=_simulation is None and not failures and result_ref is not None,
        cgroup_empty_observed=False,descendant_census='n/a',complete=not failures and result_ref is not None,
        failure_codes=failures,full_route_accepted=False,C07_accepted=False,C20_accepted=False,liveReady=False,
        T12Ready=False,sourceReady=False,T17Complete=False,run_started_ns=run_started_ns,
        main_deadline_ns=run_started_ns+config['caps']['run_main_seconds']*1000000000,run_deadline_ns=run_deadline_ns)
    receipt_ref=put('receipt.json',encoded(receipt))
    bundle=isolated_record('ComponentBundle',adapter=config['adapter'],fingerprint=config['pins']['fingerprint'],
        config_sha256=digest(encoded(config)),receipt_ref=receipt_ref,artifacts=list(artifacts),
        outcome='component_completed' if receipt['complete'] else 'instrument_incomplete')
    put('bundle.json',encoded(bundle))
    require(time.monotonic_ns() < run_deadline_ns, 'isolated_run_deadline')
    return bundle


def isolated_validate_file_claim(claim, invocation, request_id):
    fields(claim, isolated_policy()['record_fields']['FileClaim'])
    require(claim['schema'] == 'tackle-isolated-file-claim/1' and claim['request_id'] == request_id
        and type(claim['complete']) is bool and claim['complete'], 'isolated_file_claim')
    kind, facts = claim['kind'], claim['facts']
    require(type(kind) is str and invocation['function_name'] in ('Read', 'Write')
        and kind in (invocation['function_name'], 'refused'), 'isolated_result_kind')
    fields(facts, isolated_policy()['record_fields'][{'Read':'ReadFacts','Write':'WriteFacts','refused':'RefusalFacts'}[kind]])
    if kind == 'Read':
        for key in ('byte_offset','requested_max_bytes','returned_bytes'): typed(facts[key], 'uint')
        typed(facts['eof'], 'bool'); typed(facts['content_sha256'], 'sha256')
        require(type(facts['file_path']) is str and type(facts['content_utf8']) is str, 'isolated_file_claim_type')
    elif kind == 'Write':
        typed(facts['bytes_written'], 'uint'); typed(facts['content_sha256'], 'sha256')
        require(type(facts['file_path']) is str, 'isolated_file_claim_type')
    else:
        typed(facts['errno'], 'nullable<int>'); typed(facts['effect_started'], 'bool')
        require(type(facts['error_code']) is str and facts['mechanism'] in
            ('path_policy','observed_os_error','observed_decode')
            and (facts['mechanism']=='observed_os_error' or facts['errno'] is None), 'isolated_refusal')
    require(type(claim['returned_utf8_b64']) is str, 'isolated_base64')
    raw = base64.b64decode(claim['returned_utf8_b64'], validate=True)
    require(base64.b64encode(raw).decode() == claim['returned_utf8_b64'], 'isolated_base64')
    typed(claim['returned_sha256'], 'sha256')
    require(digest(raw) == claim['returned_sha256'], 'isolated_result_hash')
    return claim


def isolated_controller_argv():
    return [PYTHON, '-I', '-B', str(HERE/'controlled_route.py'), '--isolated-host-controller/1']


def isolated_watchdog_capture(argv, payload, deadline, environment):
    # Canonical wire cap is fixed here so launching the watchdog performs no policy IO.
    maximum = 4194304
    return isolated_capture(argv, payload, deadline, dict(stdout=maximum, stderr=maximum), dict(environment=environment))


def isolated_controller_wire(payload):
    """Bounded in-memory wire preparation; no path, policy, or artifact IO."""
    maximum=4194304;remaining=maximum
    def bounded(value,depth=0):
        nonlocal remaining
        require(depth<=64,'isolated_controller_input_cap')
        remaining-=1
        require(remaining>=0,'isolated_controller_input_cap')
        if type(value) is dict:
            require(len(value)<=remaining,'isolated_controller_input_cap')
            for key,item in value.items():
                require(type(key) is str,'isolated_controller_input_type');bounded(key,depth+1);bounded(item,depth+1)
        elif type(value) is list:
            require(len(value)<=remaining,'isolated_controller_input_cap')
            for item in value:bounded(item,depth+1)
        elif type(value) is str:
            remaining-=len(value);require(remaining>=0,'isolated_controller_input_cap')
        else:
            require(value is None or type(value) in (int,float,bool),'isolated_controller_input_type')
            if type(value) is int:require(value.bit_length()<=maximum,'isolated_controller_input_cap')
    bounded(payload)
    raw=bytearray()
    for piece in json.JSONEncoder(ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).iterencode(payload):
        data=piece.encode('utf-8');require(len(raw)+len(data)<=maximum,'isolated_controller_input_cap');raw.extend(data)
    return bytes(raw)


def isolated_controller_environment():
    """Only bounded trusted temporary values cross the fixed child launch; no IO."""
    environment = dict(PATH='/usr/bin:/bin', LANG='C.UTF-8')
    for key in ('TMPDIR', 'TEMP', 'TMP'):
        value = os.environ.get(key)
        if value is None:
            continue
        require(type(value) is str and len(value) <= 4096, 'isolated_temporary_environment')
        if not value:
            continue
        try:
            raw = value.encode('utf-8')
        except UnicodeError:
            raise Refusal('isolated_temporary_environment')
        require(len(raw) <= 4096 and not any(ord(char) < 32 or ord(char) == 127 for char in value)
            and not any(part in ('.', '..') for part in value.split('/')), 'isolated_temporary_environment')
        require(Path(value).is_absolute(), 'isolated_temporary_environment')
        environment[key] = value
    return environment


def isolated_watchdog(payload, config):
    environment = isolated_controller_environment()
    observed = isolated_watchdog_capture(isolated_controller_argv(), isolated_controller_wire(payload),
        payload['run_deadline_ns']/1000000000, environment)
    require(not (observed['capture_complete'] and observed['exit_code']==2), 'isolated_controller_malformed')
    reference = None; outcome = 'instrument_incomplete'
    if observed['capture_complete'] and observed['exit_code'] in (0,6):
        summary = strict_json(observed['streams']['stdout'])
        fields(summary, ('request_id','fingerprint','bundle_ref','outcome','retained_bytes'))
        require(summary['request_id']==payload['request_id'] and summary['fingerprint']==config['pins']['fingerprint'], 'isolated_controller_identity')
        isolated_validate_artifact(summary['bundle_ref'])
        require(summary['bundle_ref']['artifact']==Path(payload['output']).name+'/bundle.json', 'isolated_controller_bundle')
        require(summary['outcome'] in ('component_completed','instrument_incomplete')
            and (observed['exit_code']==0)==(summary['outcome']=='component_completed'), 'isolated_controller_status')
        reference, outcome = summary['bundle_ref'], summary['outcome']
    observation = isolated_record('HostRunObservation', adapter=config['adapter'], request_id=payload['request_id'],
        fingerprint=config['pins']['fingerprint'],proof_scope='source_simulation' if payload['simulation'] else 'native_public_component',
        controller_argv=isolated_controller_argv(),started_ns=payload['run_started_ns'],deadline_ns=payload['run_deadline_ns'],
        ended_ns=observed['ended_ns'],exit_code=observed['exit_code'],signal=observed['signal'],timeout=observed['timeout'],
        overflow=observed['overflow'],eof_channels=observed['eof_channels'],capture_complete=observed['capture_complete'],
        input_bytes_total=observed['input_bytes_total'],input_bytes_written=observed['input_bytes_written'],
        stdout_utf8_b64=base64.b64encode(observed['streams']['stdout']).decode(),
        stderr_utf8_b64=base64.b64encode(observed['streams']['stderr']).decode(),bundle_ref=reference,outcome=outcome,
        component_boundary_observed=payload['simulation'] is None and outcome=='component_completed',
        full_route_accepted=False,sourceReady=False,liveReady=False,T12Ready=False,T17Complete=False,C07_accepted=False,C20_accepted=False)
    if reference is not None:
        typed(summary['retained_bytes'], 'uint')
        if summary['retained_bytes'] + len(encoded(observation)) > config['caps']['max_retained_bytes']:
            observation.update(bundle_ref=None,outcome='instrument_incomplete',component_boundary_observed=False)
    return observation


def isolated_run(config, invocation, output, _simulation=None):
    # Bulk validation and all participant-controlled filesystem work belong to the watched child.
    start = time.monotonic_ns()
    fields(config, ('schema','mode','adapter','docker_cli','image_id','roots','pins','caps',
        'policy_sha256','network','seccomp','provider_requests'))
    out = Path(output)
    require(out.is_absolute() and out.parent == Path(config['roots']['evidence_parent']), 'isolated_output_root')
    payload = dict(schema='tackle-isolated-controller-input/1',config=config, invocation=invocation, request_id=uuid.uuid4().hex,
        run_started_ns=start,run_deadline_ns=start+90000000000,
        simulation=_simulation,output=str(out))
    return isolated_watchdog(payload,config)


def isolated_controller_main():
    maximum = isolated_policy()['caps']['max_engine_command_stream_bytes']
    raw = sys.stdin.buffer.read(maximum+1)
    require(len(raw)<=maximum, 'isolated_controller_input_cap')
    payload = strict_json(raw); fields(payload,isolated_policy()['record_fields']['ControllerInput'])
    require(payload['schema']=='tackle-isolated-controller-input/1' and type(payload['request_id']) is str
        and re.fullmatch('[0-9a-f]{32}',payload['request_id']), 'isolated_controller_identity')
    require(type(payload['output']) is str and Path(payload['output']).is_absolute()
        and Path(payload['output']).parent==Path(payload['config']['roots']['evidence_parent'])
        and not Path(payload['output']).exists() and not Path(payload['output']).is_symlink(), 'isolated_output_root')
    for key in ('run_started_ns','run_deadline_ns'):typed(payload[key],'uint')
    require(payload['run_deadline_ns']==payload['run_started_ns']+isolated_policy()['caps']['run_total_seconds']*1000000000
        and time.monotonic_ns()<payload['run_deadline_ns'], 'isolated_run_deadline')
    bundle = isolated_host_controller(payload['config'],payload['invocation'],payload['output'],payload['request_id'],
        payload['run_started_ns'],payload['run_deadline_ns'],payload['simulation'])
    data = artifact_read(Path(payload['output'])/'bundle.json',maximum)
    reference = isolated_record('Artifact',artifact=Path(payload['output']).name+'/bundle.json',sha256=digest(data),byte_length=len(data))
    print(json.dumps(dict(request_id=payload['request_id'],fingerprint=payload['config']['pins']['fingerprint'],
        bundle_ref=reference,outcome=bundle['outcome'],
        retained_bytes=sum(ref['byte_length'] for ref in bundle['artifacts'])+len(data)),sort_keys=True))
    return 0 if bundle['outcome']=='component_completed' else 6


def isolated_validate_observation(observation, config, base, bundle_raw):
    fields(observation,isolated_policy()['record_fields']['HostRunObservation'])
    require(observation['schema']=='tackle-isolated-host-run-observation/1' and observation['adapter']==config['adapter']
        and observation['fingerprint']==config['pins']['fingerprint']
        and observation['controller_argv']==isolated_controller_argv(), 'isolated_controller_identity')
    require(type(observation['request_id']) is str and re.fullmatch('[0-9a-f]{32}',observation['request_id'])
        and observation['proof_scope'] in ('source_simulation','native_public_component'), 'isolated_controller_identity')
    for key in ('started_ns','deadline_ns','ended_ns','input_bytes_total','input_bytes_written'):typed(observation[key],'uint')
    for key in ('timeout','overflow','capture_complete','component_boundary_observed'):typed(observation[key],'bool')
    for key in ('sourceReady','liveReady','T12Ready','T17Complete','C07_accepted','C20_accepted','full_route_accepted'):
        require(type(observation[key]) is bool and observation[key] is False, 'isolated_readiness_claim')
    require(observation['proof_scope']!='source_simulation' or observation['component_boundary_observed'] is False, 'isolated_simulation_claim')
    typed(observation['exit_code'],'nullable<int>');typed(observation['signal'],'nullable<positive_int>')
    maximum=config['caps']['max_engine_command_stream_bytes']
    streams={}
    for channel in ('stdout','stderr'):
        text=observation[channel+'_utf8_b64'];require(type(text) is str,'isolated_base64')
        data=base64.b64decode(text,validate=True)
        require(base64.b64encode(data).decode()==text and len(data)<=maximum,'isolated_stream_cap')
        streams[channel]=data
    require(observation['deadline_ns']==observation['started_ns']+config['caps']['run_total_seconds']*1000000000
        and observation['ended_ns']>=observation['started_ns'] and observation['input_bytes_total']<=maximum
        and observation['input_bytes_written']<=observation['input_bytes_total'], 'isolated_run_deadline')
    require(type(observation['eof_channels']) is list and all(type(x) is str for x in observation['eof_channels'])
        and observation['eof_channels']==sorted(set(observation['eof_channels']))
        and set(observation['eof_channels'])<={'stdout','stderr'}, 'isolated_native_type')
    require(observation['capture_complete'] and observation['eof_channels']==['stderr','stdout']
        and not observation['timeout'] and not observation['overflow']
        and observation['input_bytes_written']==observation['input_bytes_total']
        and observation['signal'] is None and observation['ended_ns']<=observation['deadline_ns'], 'isolated_controller_incomplete')
    ref=observation['bundle_ref'];isolated_validate_artifact(ref)
    require(ref['artifact']==base.name+'/bundle.json' and ref['byte_length']==len(bundle_raw)
        and ref['sha256']==digest(bundle_raw), 'isolated_controller_bundle')
    summary=strict_json(streams['stdout']);fields(summary,('request_id','fingerprint','bundle_ref','outcome','retained_bytes'))
    typed(summary['retained_bytes'],'uint')
    require(encoded({k:v for k,v in summary.items() if k!='retained_bytes'})==
        encoded({k:observation[k] for k in summary if k!='retained_bytes'}), 'isolated_controller_bundle')
    require(observation['outcome'] in ('component_completed','instrument_incomplete')
        and observation['exit_code']==(0 if observation['outcome']=='component_completed' else 6), 'isolated_controller_status')
    return observation


def isolated_retention_total(refs, bundle_raw, observation_raw, maximum):
    total=len(bundle_raw)+len(observation_raw)
    for ref in refs:
        isolated_validate_artifact(ref);total+=ref['byte_length']
        require(total<=maximum,'isolated_retention_cap')
    require(total<=maximum,'isolated_retention_cap')
    return total


def isolated_validate_capture(row, config, invocation, run_observation, read):
    for key in ('started_ns','ended_ns','phase_deadline_ns','input_bytes_total','input_bytes_written',
                'stdout_received_bytes','stderr_received_bytes'):typed(row[key],'uint')
    for key in ('timeout','overflow','capture_complete'):typed(row[key],'bool')
    typed(row['exit_code'],'nullable<int>');typed(row['signal'],'nullable<positive_int>')
    require((row['exit_code'] is None)!=(row['signal'] is None), 'isolated_native_disposition')
    require(type(row['argv']) is list and row['argv'] and all(type(x) is str and '\0' not in x for x in row['argv'])
        and row['cwd']==str(HERE.parents[2]) and type(row['eof_channels']) is list
        and all(type(x) is str for x in row['eof_channels'])
        and row['eof_channels']==sorted(set(row['eof_channels'])) and set(row['eof_channels'])<={'stdout','stderr'}, 'isolated_native_type')
    maximum=config['caps']['max_engine_command_stream_bytes']
    limits={'stdout':maximum,'stderr':maximum}
    if row['phase']=='start_attached':
        limits={'stdout':config['caps']['max_stdout_bytes'] if invocation['function_name']=='Bash'
                else config['caps']['max_file_result_bytes'],'stderr':config['caps']['max_stderr_bytes']}
    raw={channel:read(row[channel+'_ref'],limit) for channel,limit in limits.items()}
    input_bytes=read(row['input_ref'],config['caps']['max_request_bytes']) if row['input_ref'] is not None else b''
    require(row['input_bytes_total']==len(input_bytes) and row['input_bytes_written']<=len(input_bytes), 'isolated_native_input')
    for channel in ('stdout','stderr'):
        require(row[channel+'_received_bytes']>=len(raw[channel]),'isolated_native_type')
    overflow=any(row[channel+'_received_bytes']>limits[channel] for channel in limits)
    require(row['overflow']==overflow,'isolated_capture_incomplete')
    complete=(not row['timeout'] and not row['overflow'] and row['eof_channels']==['stderr','stdout']
        and row['input_bytes_written']==row['input_bytes_total'])
    require(row['capture_complete']==complete,'isolated_capture_incomplete')
    if complete:
        require(all(row[channel+'_received_bytes']==len(raw[channel]) for channel in raw),'isolated_native_type')
        require(row['ended_ns']<=row['phase_deadline_ns'],'isolated_phase_deadline')
    else:
        require(row['timeout'] or row['overflow'] or row['eof_channels']!=['stderr','stdout']
            or row['input_bytes_written']!=row['input_bytes_total'],'isolated_capture_incomplete')
    run_start=run_observation['started_ns'];run_end=run_observation['ended_ns']
    main_end=run_start+config['caps']['run_main_seconds']*1000000000
    target=run_observation['deadline_ns'] if row['phase'].startswith('cleanup') else main_end
    duration=(config['caps']['tool_seconds'] if row['phase']=='start_attached' else 8)*1000000000
    require(run_start<=row['started_ns']<=row['ended_ns']<=run_end
        and row['started_ns']<row['phase_deadline_ns']<=min(target,row['started_ns']+duration), 'isolated_chronology')
    require(not row['timeout'] or row['ended_ns']>=row['phase_deadline_ns'], 'isolated_phase_deadline')
    if row['phase']!='start_attached':require(input_bytes==b'','isolated_native_input')
    return raw,input_bytes


def isolated_validate_lifecycle(receipt, plan, invocation, config, rows, raws):
    main=['image_inspect','create','inspect_created','start_attached','wait','inspect_stopped']
    phases=list(rows);prefix=[p for p in phases if not p.startswith('cleanup')]
    suffix=[p for p in phases if p.startswith('cleanup')]
    require(prefix==main[:len(prefix)] and phases==prefix+suffix and suffix in ([],['cleanup_reconcile'],
        ['cleanup_reconcile','cleanup_kill'],['cleanup_reconcile','cleanup_remove'],
        ['cleanup_reconcile','cleanup_kill','cleanup_remove'],['cleanup_reconcile','cleanup_remove','cleanup_absence'],
        ['cleanup_reconcile','cleanup_kill','cleanup_remove','cleanup_absence']), 'isolated_lifecycle_order')
    def success(phase):
        row=rows.get(phase)
        return row is not None and row['capture_complete'] and row['exit_code']==0 and row['signal'] is None
    if success('image_inspect'):plan['image_env']=isolated_image(raws['image_inspect']['stdout'],config)
    cid=None
    if 'create' in raws:
        text=raws['create']['stdout']
        if re.fullmatch(b'[0-9a-f]{64}\n',text):cid=text.decode().strip()
    if cid is None:
        for phase in ('inspect_created','inspect_stopped','cleanup_reconcile'):
            if success(phase):
                try:
                    info,=strict_json(raws[phase]['stdout']);candidate=info['Id']
                    if type(candidate) is str and re.fullmatch('[0-9a-f]{64}',candidate):cid=candidate;break
                except (Refusal,KeyError,ValueError,TypeError):pass
    expected={'image_inspect':['image','inspect',config['image_id']],'create':plan['create_argv'][1:],
        'inspect_created':['inspect','--type=container',cid],'start_attached':['start','--attach','--interactive',cid],
        'wait':['wait',cid],'inspect_stopped':['inspect','--type=container',cid],
        'cleanup_reconcile':['inspect','--type=container',plan['name']],'cleanup_kill':['kill',cid],
        'cleanup_remove':['rm','--force',cid],'cleanup_absence':['inspect','--type=container',cid]}
    facts={}
    for phase,row in rows.items():
        argv=[config['docker_cli']['path'],*expected[phase]]
        if receipt['proof_scope']=='source_simulation':
            require(row['argv'][:4]==[PYTHON,'-B',str(FIXTURE/'isolated_engine_fixture.py'),'--state']
                and len(row['argv'])>=6 and row['argv'][5]=='--','isolated_native_argv')
            state=Path(row['argv'][4]);root=Path(config['roots']['component_root'])
            require(state.is_absolute() and root in state.parents and not state.is_symlink(),'isolated_simulation_state')
            argv=[*row['argv'][:6],*argv]
        require(row['argv']==argv,'isolated_native_argv')
        if phase in ('inspect_created','inspect_stopped','cleanup_reconcile') and success(phase) and 'image_env' in plan:
            try:
                info,=strict_json(raws[phase]['stdout'])
                facts[phase]=isolated_owned_identity(info,plan,cid,config,row['command_id'])
            except (Refusal,KeyError,ValueError,TypeError):pass
    require(not suffix or 'create' in rows, 'isolated_lifecycle_order')
    require('create' not in rows or success('image_inspect'), 'isolated_lifecycle_order')
    require('start_attached' not in rows or (success('create') and 'inspect_created' in facts), 'isolated_lifecycle_order')
    require('wait' not in rows or rows['start_attached']['capture_complete'], 'isolated_lifecycle_order')
    require('inspect_stopped' not in rows or success('wait'), 'isolated_lifecycle_order')
    for key,phase in [('container_created','inspect_created'),('container_stopped','inspect_stopped')]:
        require(encoded(receipt[key])==encoded(facts.get(phase)),'isolated_lifecycle_unproven')
    owned=cid if facts else None
    require(receipt['owned_cid']==owned,'isolated_lifecycle_unproven')
    cleaned=('cleanup_reconcile' in facts and success('cleanup_remove') and 'cleanup_absence' in rows
        and rows['cleanup_absence']['capture_complete']
        and raws['cleanup_remove']['stdout']==(cid+'\n').encode()
        and isolated_missing(dict(rows['cleanup_absence'],streams=raws['cleanup_absence']),cid)
        and (not facts['cleanup_reconcile']['running'] or success('cleanup_kill')))
    require(receipt['cleanup_confirmed'] is bool(cleaned),'isolated_cleanup_unproven')
    if 'cleanup_kill' in rows:require('cleanup_reconcile' in facts and facts['cleanup_reconcile']['running'],'isolated_cleanup_unproven')
    if receipt['complete']:
        require(phases==main+['cleanup_reconcile','cleanup_remove','cleanup_absence'] and all(success(p) for p in phases[:-1] if p!='start_attached')
            and cleaned and cid is not None,'isolated_lifecycle_missing')
        stopped=facts['inspect_stopped']
        require(not stopped['running'] and stopped['pid']==0 and not stopped['oom_killed']
            and rows['start_attached']['exit_code']==stopped['exit_code']
            and raws['wait']['stdout']==(str(stopped['exit_code'])+'\n').encode(),'isolated_exit')
    return facts


def isolated_validate_chronology(receipt, observation):
    require(receipt['run_started_ns']==observation['started_ns']
        and receipt['main_deadline_ns']==observation['started_ns']+70000000000
        and receipt['run_deadline_ns']==observation['deadline_ns'],'isolated_run_deadline')
    previous=observation['started_ns']
    for row in receipt['native_commands']:
        require(previous<=row['started_ns'],'isolated_chronology');previous=row['ended_ns']
    if receipt['snapshot'] is not None:
        typed(receipt['snapshot']['observed_ns'],'uint')
        require(previous<=receipt['snapshot']['observed_ns']<=observation['ended_ns'],'isolated_snapshot_order')


def verify_isolated_bundle(config, bundle_path, run_observation_path):
    roots=validate_isolated_config(config)
    base=Path(bundle_path).absolute().parent
    require(base.parent==roots['evidence_parent'] and Path(bundle_path).name=='bundle.json','isolated_output_root')
    observation_path=Path(run_observation_path).absolute()
    require(observation_path.parent==roots['evidence_parent'] and observation_path.exists()
        and not observation_path.is_symlink(),'isolated_observation_path')
    maximum=config['caps']['max_retained_bytes']
    bundle_raw=artifact_read(bundle_path,maximum)
    observation_raw=artifact_read(observation_path,config['caps']['max_engine_command_stream_bytes']*3)
    bundle=strict_json(bundle_raw);fields(bundle,isolated_policy()['record_fields']['ComponentBundle'])
    require(bundle['schema']=='tackle-isolated-component-bundle/1' and bundle['adapter']==config['adapter']
        and bundle['fingerprint']==config['pins']['fingerprint'] and bundle['config_sha256']==digest(encoded(config)), 'isolated_bundle')
    require(type(bundle['artifacts']) is list and bundle['outcome'] in ('component_completed','instrument_incomplete'),'isolated_bundle_type')
    refs={}
    for ref in bundle['artifacts']:
        isolated_validate_artifact(ref)
        require(ref['artifact'] not in refs,'isolated_duplicate_artifact');refs[ref['artifact']]=ref
    isolated_retention_total(list(refs.values()),bundle_raw,observation_raw,maximum)
    def read(ref,cap=maximum):
        isolated_validate_artifact(ref)
        require(refs.get(ref['artifact'])==ref,'isolated_artifact_missing')
        require(ref['byte_length']<=cap,'isolated_stream_cap')
        path=base/ref['artifact']
        for component in (path,*path.parents):
            if component==base.parent:break
            require(not component.is_symlink(),'isolated_artifact_path')
        require(path.stat().st_size<=cap,'isolated_stream_cap')
        data=artifact_read(path,cap)
        require(len(data)==ref['byte_length'] and digest(data)==ref['sha256'],'isolated_artifact_pin')
        return data
    observation=isolated_validate_observation(strict_json(observation_raw),config,base,bundle_raw)
    summary=strict_json(base64.b64decode(observation['stdout_utf8_b64'],validate=True))
    require(summary['retained_bytes']==sum(ref['byte_length'] for ref in refs.values())+len(bundle_raw),'isolated_retention_cap')
    receipt=strict_json(read(bundle['receipt_ref']));fields(receipt,isolated_policy()['record_fields']['ComponentReceipt'])
    require(receipt['schema']=='tackle-isolated-component-receipt/1' and receipt['proof_scope']==observation['proof_scope']
        and receipt['request_id']==observation['request_id'] and receipt['fingerprint']==config['pins']['fingerprint']
        and observation['outcome']==bundle['outcome'],'isolated_receipt')
    for key in ('complete','cleanup_confirmed','component_boundary_observed'):typed(receipt[key],'bool')
    for key in ('run_started_ns','main_deadline_ns','run_deadline_ns'):typed(receipt[key],'uint')
    for key in ('cgroup_empty_observed','full_route_accepted','C07_accepted','C20_accepted','liveReady','T12Ready','sourceReady','T17Complete'):
        require(type(receipt[key]) is bool and receipt[key] is False,'isolated_readiness_claim')
    require(receipt['descendant_census']=='n/a' and receipt['component_boundary_observed']==observation['component_boundary_observed']
        and (receipt['proof_scope']!='source_simulation' or receipt['component_boundary_observed'] is False),'isolated_simulation_claim')
    require(type(receipt['native_commands']) is list and type(receipt['failure_codes']) is list
        and all(type(code) is str and re.fullmatch('[A-Za-z0-9_.:-]{1,128}',code) for code in receipt['failure_codes']),'isolated_receipt_type')
    if receipt['owned_cid'] is not None:typed(receipt['owned_cid'],'sha256')
    invocation=strict_json(read(receipt['invocation_ref']));validate_isolated_invocation(invocation)
    plan=isolated_plan(config,invocation,receipt['request_id'],base)
    rows,raws={},{}
    allowed=('image_inspect','create','inspect_created','start_attached','wait','inspect_stopped',
        'cleanup_reconcile','cleanup_kill','cleanup_remove','cleanup_absence')
    for index,row in enumerate(receipt['native_commands']):
        fields(row,isolated_policy()['record_fields']['NativeCommand'])
        require(row['schema']=='tackle-isolated-native-command/1' and type(row['sequence']) is int
            and row['sequence']==index and row['command_id']=='command_'+str(index)
            and type(row['phase']) is str and row['phase'] in allowed and row['phase'] not in rows,'isolated_native_identity')
        raw,input_bytes=isolated_validate_capture(row,config,invocation,observation,read)
        require(input_bytes==(plan['request'] if row['phase']=='start_attached' else b''),'isolated_native_input')
        rows[row['phase']]=row;raws[row['phase']]=raw
    facts=isolated_validate_lifecycle(receipt,plan,invocation,config,rows,raws)
    isolated_validate_chronology(receipt,observation)
    for ref in refs.values():read(ref)
    if not receipt['complete']:
        require(bundle['outcome']=='instrument_incomplete' and receipt['failure_codes']
            and receipt['result_ref'] is None and receipt['snapshot'] is None
            and receipt['component_boundary_observed'] is False,'isolated_incomplete')
        return receipt
    require(bundle['outcome']=='component_completed' and not receipt['failure_codes']
        and receipt['cleanup_confirmed'] and receipt['result_ref'] is not None and receipt['snapshot'] is not None,'isolated_lifecycle_missing')
    result=strict_json(read(receipt['result_ref']))
    require(result['request_id']==receipt['request_id'],'isolated_result_identity')
    validate_isolated_result(result,invocation,dict(stopped=facts['inspect_stopped'],start=rows['start_attached'],
        **raws['start_attached'],command_ids=[r['command_id'] for r in receipt['native_commands'] if not r['phase'].startswith('cleanup')]))
    snapshot=receipt['snapshot'];fields(snapshot,isolated_policy()['record_fields']['Snapshot'])
    require(snapshot['schema']=='tackle-isolated-component-snapshot/1' and snapshot['root_role']=='work'
        and type(snapshot['entries']) is list,'isolated_snapshot')
    typed(snapshot['tree_sha256'],'sha256')
    tree=[];paths=set()
    for entry in snapshot['entries']:
        fields(entry,isolated_policy()['record_fields']['SnapshotEntry'])
        relative(entry['relative_path']);typed(entry['mode'],'uint')
        require(entry['relative_path'] not in paths and entry['mode']<=0o7777,'isolated_snapshot')
        paths.add(entry['relative_path'])
        require(entry['artifact_ref']['artifact']=='snapshot/'+entry['relative_path'],'isolated_snapshot')
        data=read(entry['artifact_ref']);tree.append([entry['relative_path'],len(data),digest(data)])
    require(digest(encoded(sorted(tree)))==snapshot['tree_sha256'],'isolated_snapshot')
    return receipt

def isolated_main(argv):
    import argparse
    parser=argparse.ArgumentParser(description='Isolated public component; not the Responses route.')
    parser.add_argument('command',choices=('isolated-preflight','isolated-run','isolated-verify'))
    parser.add_argument('--config',required=True);parser.add_argument('--out',required=True)
    parser.add_argument('--invocation');parser.add_argument('--bundle')
    parser.add_argument('--run-observation')
    args=parser.parse_args(argv)
    try:
        config=strict_json(artifact_read(args.config))
        if args.command=='isolated-run':
            require(args.invocation is not None and args.bundle is None and args.run_observation is None, 'isolated_cli_arguments')
            value=isolated_run(config,strict_json(artifact_read(args.invocation)),args.out)
            print(json.dumps(value,sort_keys=True));return 0 if value['outcome']=='component_completed' else 6
        roots=validate_isolated_config(config)
        require(args.command!='isolated-preflight' or args.run_observation is None, 'isolated_cli_arguments')
        require(args.invocation is None and (args.bundle is not None)==(args.command=='isolated-verify'), 'isolated_cli_arguments')
        out=Path(args.out).absolute()
        require(not out.exists() and not out.is_symlink() and out.parent==roots['evidence_parent'], 'isolated_output_exists')
        if args.command=='isolated-verify':
            require(args.run_observation is not None, 'isolated_observation_required')
            receipt=verify_isolated_bundle(config,args.bundle,args.run_observation)
            value=dict(outcome='component_completed' if receipt['complete'] else 'instrument_incomplete',receipt=receipt)
        else:
            require(digest(artifact_read(config['docker_cli']['path']))==config['docker_cli']['sha256'], 'isolated_cli_pin')
            observed=isolated_capture([config['docker_cli']['path'],'image','inspect',config['image_id']],b'',time.monotonic()+8,
                dict(stdout=config['caps']['max_engine_command_stream_bytes'],stderr=config['caps']['max_engine_command_stream_bytes']),
                dict(environment=dict(PATH='/usr/bin:/bin',HOME=str(roots['cli_home']),DOCKER_CONFIG=str(roots['cli_config']),
                    DOCKER_HOST=config['docker_cli']['endpoint'],LANG='C.UTF-8')))
            require(observed['capture_complete'] and observed['exit_code']==0, 'isolated_image_unavailable')
            isolated_image(observed['streams']['stdout'],config)
            value=dict(outcome='preflight_valid',image_id=config['image_id'],sourceReady=False,liveReady=False,T12Ready=False,T17Complete=False)
        out.mkdir(mode=0o700)
        (out/'result.json').write_bytes(encoded(value))
        if args.command=='isolated-preflight':
            for channel,data in observed['streams'].items():(out/(channel+'.bin')).write_bytes(data)
            (out/'native.json').write_bytes(encoded({k:v for k,v in observed.items() if k!='streams'}))
        print(json.dumps(value,sort_keys=True));return 0 if value['outcome']!='instrument_incomplete' else 6
    except (Refusal,OSError,UnicodeError,ValueError,KeyError,TypeError) as exc:
        print(json.dumps(dict(outcome='malformed',reason=exc.code if isinstance(exc,Refusal) else type(exc).__name__,
            sourceReady=False,liveReady=False,T12Ready=False,T17Complete=False),sort_keys=True));return 2


if __name__ == '__main__':
    if sys.argv[1:] == ['--isolated-host-controller/1']:
        try:
            raise SystemExit(isolated_controller_main())
        except (Refusal,OSError,UnicodeError,ValueError,KeyError,TypeError) as exc:
            print(str(exc),file=sys.stderr)
            raise SystemExit(2)
    if sys.argv[1:2] in (['isolated-preflight'], ['isolated-run'], ['isolated-verify']):
        raise SystemExit(isolated_main(sys.argv[1:]))
    if sys.argv[1:] == ['--session-controller']:
        try:
            raise SystemExit(session_controller())
        except (Refusal, OSError, UnicodeError) as exc:
            print(str(exc), file=sys.stderr)
            raise SystemExit(6)
    raise SystemExit('Use gpt_route.py controlled-* commands')
