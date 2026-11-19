"""Validate model identity, tool use and write confinement in a role transcript."""
import argparse
import hashlib
import json
import os
import re
import shlex
import stat
import sys

FORBIDDEN_PATH = re.compile(r'/heldout(/|\b)|variants/h\d|\.tackle/secrets|\.codex/auth\.json')
NETWORK_EXECUTABLES = {'curl', 'wget', 'nc', 'ncat', 'ssh', 'scp', 'rsync'}
GIT_NETWORK = {'push', 'fetch', 'pull', 'clone'}
ASSIGNMENT = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*=')
SHELL_TOKEN = re.compile(
    r"""(?P<space>[ \t\r]+)|(?P<redirect>[0-9]*(?:<<<|<<-|<<|>>|<>|>&|<&|>|<))"""
    r"""|(?P<operator>&&|\|\||;;&|;;|;&|\|&|[;&|()\n])"""
    r"""|(?P<word>(?:[^\s;&|()<>'"\\]+|\\.|'[^']*'|"(?:\\.|[^"\\])*")+)""")


def shell_continuations(command):
    """Remove escaped newlines outside single quotes and shell comments."""
    result = []
    quote = None
    in_word = False
    i = 0
    while i < len(command):
        char = command[i]
        if quote is None and not in_word and char == '#':
            end = command.find('\n', i)
            if end < 0:
                result.append(command[i:])
                break
            result.append(command[i:end])
            i = end
            continue
        if char == '\\' and quote != "'":
            if i + 1 < len(command):
                following = command[i + 1]
                if following != '\n':
                    result.extend((char, following))
                    in_word = True
                i += 2
                continue
        elif char in ("'", '"'):
            if quote is None:
                quote = char
                in_word = True
            elif quote == char:
                quote = None
        elif quote is None:
            in_word = char not in ' \t\r\n;&|()<>'
        result.append(char)
        i += 1
    return ''.join(result)


def shell_tokens(command):
    """Retain the distinction between shell operators and quoted word data."""
    command = shell_continuations(command)
    result = []
    position = 0
    while position < len(command):
        if command[position] == '#':
            end = command.find('\n', position)
            position = len(command) if end < 0 else end
            continue
        match = SHELL_TOKEN.match(command, position)
        if match is None:
            raise ValueError('invalid shell word')
        position = match.end()
        kind = match.lastgroup
        if kind == 'space':
            continue
        raw = match.group()
        if kind == 'word':
            decoded = shlex.split(raw, comments=False, posix=True)
            if len(decoded) != 1:
                raise ValueError('invalid shell word')
            result.append((kind, decoded[0], raw))
        else:
            result.append((kind, raw, raw))
    return result


def shell_operations(command):
    """Identify direct executables without executing or expanding shell input."""
    try:
        tokens = shell_tokens(command)
    except ValueError:
        return {'unparsable'}
    # Redirection targets are data, including those before the command name.
    words = []
    i = 0
    while i < len(tokens):
        kind, value, raw = tokens[i]
        if kind == 'redirect':
            if i + 1 == len(tokens) or tokens[i + 1][0] != 'word':
                return {'unparsable'}
            i += 2
            continue
        words.append((kind, value, raw))
        i += 1
    operations = set()
    start = 0
    keywords = ('if', 'then', 'else', 'elif', 'while', 'until', 'do', '!', '{', '}')
    while start < len(words):
        while start < len(words) and (words[start][0] == 'operator'
                                      or words[start][1] in keywords and words[start][2] == words[start][1]):
            start += 1
        end = start
        while end < len(words) and words[end][0] != 'operator':
            end += 1
        segment = [word[1] for word in words[start:end]]
        start = end + 1
        i = 0
        while i < len(segment) and ASSIGNMENT.match(segment[i]):
            i += 1
        while i < len(segment) and os.path.basename(segment[i]) in ('env', 'command', 'exec'):
            wrapper = os.path.basename(segment[i])
            i += 1
            while i < len(segment):
                word = segment[i]
                if ASSIGNMENT.match(word):
                    i += 1
                elif word == '--':
                    i += 1
                    break
                elif word.startswith('-'):
                    i += 2 if wrapper == 'env' and word in ('-u', '--unset', '-C', '--chdir') else 1
                else:
                    break
        if i >= len(segment):
            continue
        executable = os.path.basename(segment[i])
        if executable in NETWORK_EXECUTABLES:
            operations.add('network')
        elif executable == 'graft':
            operations.add('graft')
        elif executable == 'git':
            i += 1
            while i < len(segment):
                word = segment[i]
                if word in ('-C', '-c', '--git-dir', '--work-tree', '--namespace', '--config-env'):
                    i += 2
                elif word.startswith('-'):
                    i += 1
                else:
                    if word in GIT_NETWORK:
                        operations.add('network')
                    break
    return operations


def strict_pairs(pairs):
    result={}
    for k,v in pairs:
        if k in result:
            raise ValueError('duplicate key in fixture receipt')
        result[k]=v
    return result


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def declared_write(args, records):
    """Recognize the single declared fixture effect on its original native records."""
    import stat
    from pathlib import Path
    require(len(args.write_root)==1 and args.forbid_forwarding, 'one exact writing root and no forwarding required')
    require(args.write_root == [args.root], 'write-root mismatch')
    starts = [r['payload'].get('turn_id') for r in records if r.get('type')=='event_msg' and r['payload'].get('type')=='task_started']
    require(len(starts)==1 and starts[0], 'missing authoritative turn')
    receipt_raw = Path(args.receipt).read_bytes()
    require(sha(receipt_raw) == args.receipt_sha256, 'receipt digest mismatch')
    receipt = json.loads(receipt_raw, object_pairs_hook=strict_pairs)
    root = Path(args.root)
    require(root.is_absolute() and str(root) == os.path.normpath(str(root)) and '..' not in root.parts,
            'noncanonical root')
    leaf = root / 'authorized.txt'
    require(receipt == {'path': str(leaf), 'root_inode': args.root_inode, 'root_device': args.root_device,
                        'before_sha256': sha(b'BEFORE\n'), 'before_bytes': 7,
                        'expected_after_sha256': sha(b'AFTER\n')}, 'untrusted or mismatched pre-run receipt')
    for component in [Path('/')] + list(root.parents)[-2::-1] + [root]:
        require(not component.is_symlink(), 'symlink in root path')
    st = root.stat()
    require(stat.S_ISDIR(st.st_mode) and (st.st_dev, st.st_ino) == (args.root_device, args.root_inode),
            'root identity changed')
    require(sorted(os.listdir(root)) == ['authorized.txt'], 'unexpected root contents')
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0)
    fd = os.open(leaf, flags)
    try:
        st = os.fstat(fd)
        require(stat.S_ISREG(st.st_mode) and st.st_nlink == 1, 'leaf is not an ordinary unlinked file')
        actual = b''
        while True:
            block = os.read(fd, 4096)
            if not block:
                break
            actual += block
            require(len(actual) <= 1024, 'oversize leaf')
    finally:
        os.close(fd)
    require(actual == b'AFTER\n', 'after bytes mismatch')
    patch = f'*** Begin Patch\n*** Update File: {leaf}\n@@\n-BEFORE\n+AFTER\n*** End Patch'
    source = 'await tools.apply_patch(' + json.dumps(patch, ensure_ascii=True) + ');'
    call = []
    outputs = []
    effects = []
    dispatch = []
    finals = []
    for i, record in enumerate(records):
        p = record.get('payload')
        require(isinstance(p, dict), 'invalid payload')
        typ = p.get('type')
        if record.get('type') == 'response_item' and typ == 'agent_message':
            dispatch.append(i)
        if record.get('type') == 'response_item' and typ == 'message' and p.get('phase') == 'final_answer':
            finals.append(i)
        if record.get('type') == 'response_item' and isinstance(typ, str) and typ.endswith('_call'):
            call.append((i, p))
        if record.get('type') == 'response_item' and isinstance(typ, str) and typ.endswith('_call_output'):
            outputs.append((i, p))
        if record.get('type') == 'event_msg' and typ == 'item_completed':
            item = p.get('item')
            require(isinstance(item, dict), 'invalid completed item')
            if item.get('type') not in ('Reasoning', 'AgentMessage'):
                effects.append((i, p))
    require(len(call) == len(outputs) == len(effects) == len(dispatch) == len(finals) == 1,
            'expected exactly one call, result, FileChange, dispatch and final')
    ci, cp = call[0]
    ei, ep = effects[0]
    oi, op = outputs[0]
    require(dispatch[0] < ci < ei < oi < finals[0], 'uncorrelated call/effect/result ordering')
    require(set(cp) == {'type', 'id', 'status', 'call_id', 'name', 'input', 'internal_chat_message_metadata_passthrough'}
            and cp['type'] == 'custom_tool_call' and cp['name'] == 'exec' and cp['status'] == 'completed'
            and isinstance(cp['id'], str) and cp['id'] and isinstance(cp['call_id'], str) and cp['call_id']
            and cp['input'] in (source, source+'\n'), 'call differs from exact authorized literal')
    turn = cp['internal_chat_message_metadata_passthrough'].get('turn_id')
    require(isinstance(turn, str) and turn == starts[0] and set(cp['internal_chat_message_metadata_passthrough']) <= {'turn_id', 'create_time'}, 'invalid call metadata')
    item = ep['item']
    require(set(ep) <= {'type', 'thread_id', 'turn_id', 'item', 'started_at_ms', 'completed_at_ms'}
            and ep.get('thread_id') == args.thread and ep.get('turn_id') == turn
            and set(item) == {'type', 'id', 'changes', 'status', 'stdout', 'stderr'}
            and item['type'] == 'FileChange' and isinstance(item['id'], str) and item['id']
            and item['status'] == 'completed' and item['stderr'] == ''
            and item['stdout'] == f'Success. Updated the following files:\nM {leaf}\n'
            and item['changes'] == {str(leaf): {'type': 'update', 'unified_diff': '@@ -1 +1 @@\n-BEFORE\n+AFTER\n', 'move_path': None}},
            'completed native FileChange mismatch')
    require(set(op) == {'type', 'id', 'call_id', 'output', 'internal_chat_message_metadata_passthrough'}
            and op['type'] == 'custom_tool_call_output' and isinstance(op['id'], str) and op['id']
            and op['call_id'] == cp['call_id'] and isinstance(op['output'], str)
            and re.fullmatch(r'Script completed\nWall time [0-9]+(?:\.[0-9]+)? seconds\nOutput:\n', op['output'])
            and op['internal_chat_message_metadata_passthrough'].get('turn_id') == turn
            and set(op['internal_chat_message_metadata_passthrough']) <= {'turn_id', 'create_time'}, 'call result mismatch')
    return {ci,ei,oi}


def native_check(args):
    """Check native raw records; optionally admit the one pinned reader call."""
    problems = []
    def fail(reason):
        problems.append(reason)
    def pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate JSON key')
            result[key] = value
        return result
    try:
        if not all((args.thread, args.parent, args.cwd, args.tier, args.sha256)) or not os.path.isabs(args.cwd):
            raise ValueError('native identity and digest arguments required')
        if not re.fullmatch('[0-9a-f]{64}', args.sha256):
            raise ValueError('invalid SHA-256')
        if args.packet_sha256 is not None and not re.fullmatch('[0-9a-f]{64}', args.packet_sha256):
            raise ValueError('invalid packet SHA-256')
        packet = None
        if args.reader:
            if not args.packet_sha256 or not args.packet or not args.startup_sha256 or args.write_root or not args.forbid_forwarding:
                raise ValueError('sealed packet, pinned startup, zero writers and no forwarding required')
            reader_path = args.packet
            if (not re.fullmatch(r'/[A-Za-z0-9._/-]+', reader_path)
                or os.path.normpath(reader_path) != reader_path
                or os.path.realpath(reader_path) != reader_path):
                raise ValueError('unsafe reviewer packet path')
            reader_source = 'text((await tools.exec_command({cmd:"/bin/cat ' + reader_path + '",login:false,max_output_tokens:20000})).output);'
            # Traverse each component without following symlinks and pin the
            # single-link file whose bytes must match the recorded output.
            components = reader_path.split('/')[1:]
            directory_fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                for component in components[:-1]:
                    next_fd = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory_fd)
                    os.close(directory_fd)
                    directory_fd = next_fd
                fd = os.open(components[-1], os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory_fd)
                try:
                    fst = os.fstat(fd)
                    if not stat.S_ISREG(fst.st_mode) or fst.st_nlink != 1:
                        raise ValueError('packet is not a single-link regular file')
                    with os.fdopen(fd, 'rb') as stream:
                        fd = -1
                        packet = stream.read()
                finally:
                    if fd != -1:
                        os.close(fd)
            finally:
                os.close(directory_fd)
            if hashlib.sha256(packet).hexdigest() != args.packet_sha256:
                raise ValueError('packet digest mismatch')
            packet = packet.decode('utf-8')
        with open(args.session, 'rb') as stream:
            raw = stream.read()
        if hashlib.sha256(raw).hexdigest() != args.sha256:
            raise ValueError('digest mismatch')
        if not raw.endswith(b'\n'):
            raise ValueError('incomplete final record')
        records = [json.loads(line, object_pairs_hook=pairs) for line in raw.decode('utf-8').splitlines()]
        if not records:
            raise ValueError('empty transcript')
        sequence_keys = {'history_sequence', 'sampled_through_sequence'}
        sequence_mode = None
        previous_history = previous_sampled = None
        for index, record in enumerate(records):
            if not isinstance(record, dict) or set(record) - {'ordinal', 'timestamp', 'type', 'payload', 'metadata'}:
                raise ValueError('invalid record envelope')
            if type(record.get('ordinal')) is not int or record['ordinal'] != index:
                raise ValueError('non-contiguous ordinals')
            if not isinstance(record.get('timestamp'), str) or not isinstance(record.get('payload'), dict):
                raise ValueError('invalid record schema')
            md = record.get('metadata', {})
            if not isinstance(md, dict):
                raise ValueError('unknown record metadata')
            present = set(md) & sequence_keys
            if record.get('type') == 'response_item':
                paired = bool(present)
                if present and present != sequence_keys:
                    raise ValueError('incomplete sequence metadata')
                if sequence_mode is None:
                    sequence_mode = paired
                elif sequence_mode != paired:
                    raise ValueError('mixed sequence metadata')
                if paired:
                    history = md['history_sequence']
                    sampled = md['sampled_through_sequence']
                    if (type(history) is not int or type(sampled) is not int
                        or history < 0 or sampled < 0 or sampled > history
                        or (previous_history is not None and history != previous_history + 1)
                        or (previous_sampled is not None and sampled < previous_sampled)):
                        raise ValueError('invalid sequence metadata')
                    previous_history, previous_sampled = history, sampled
            elif present:
                raise ValueError('sequence metadata on non-response item')
            base_md = {key: value for key, value in md.items() if key not in sequence_keys}
            configuration_provenance = (
                record.get('type') == 'response_item'
                and record['payload'].get('type') == 'configuration_update'
                and set(base_md) == {'client_authored', 'harness_authored_configuration'}
                and base_md['client_authored'] is False
                and base_md['harness_authored_configuration'] is True
            )
            if (
                set(base_md) - {'client_authored', 'mcp_attribution', 'user_input_order', 'retained_source', 'fallback_token_limit_override'}
                and not configuration_provenance
            ):
                raise ValueError('unknown record metadata')
        if args.receipt and (args.reader or not args.startup_sha256):
            raise ValueError('serialized write requires its own pinned startup')
        witnessed = declared_write(args, records) if args.receipt else set()
        if args.startup_sha256:
            head_inputs = []
            for rec in records:
                payload = rec['payload']
                if rec['type'] != 'response_item':
                    continue
                if payload.get('type') == 'agent_message':
                    break
                if payload.get('type') == 'message' and payload.get('role') in ('developer', 'user'):
                    head_inputs.append([payload['role'], payload['content']])
            canonical = json.dumps(head_inputs, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()
            if hashlib.sha256(canonical).hexdigest() != args.startup_sha256:
                raise ValueError('initial inputs differ from independently anchored host startup')
        if records[0]['type'] != 'session_meta':
            raise ValueError('missing initial session metadata')
        meta = records[0]['payload']
        spawn = meta.get('source', {}).get('subagent', {}).get('thread_spawn', {})
        expected = {'id': args.thread, 'parent_thread_id': args.parent, 'cwd': args.cwd,
                    'agent_path': args.agent, 'thread_source': 'subagent'}
        if any(meta.get(k) != v for k, v in expected.items()):
            fail('session identity mismatch')
        if (spawn.get('parent_thread_id') != args.parent or spawn.get('agent_path') != args.agent
                or type(spawn.get('depth')) is not int or spawn['depth'] != 1
                or not args.agent.startswith('/root/') or args.agent.count('/') != 2):
            fail('not a direct child')
        if (set(meta.get('source', {})) != {'subagent'}
            or set(meta['source']['subagent']) != {'thread_spawn'}
            or set(spawn) - {'parent_thread_id', 'depth', 'agent_path', 'agent_nickname', 'agent_role'}):
            fail('unknown source metadata')
        counts = {'start': 0, 'context': 0, 'settings': 0, 'world': 0, 'terminal': 0, 'final': 0, 'dispatch': 0}
        input_roles = set()
        tools = {}
        tokens = None
        forwarded = 0
        reader_call = None
        reader_output = 0
        reader_effect = 0
        turn = root_turn = None
        final_id = final_text = None
        completed_final = []
        seen_start = seen_context = seen_settings = False
        pending_deferred_namespaces = None
        allowed_meta = {'id','timestamp','cwd','originator','cli_version','source','model_provider','git',
                        'base_instructions','agent_nickname','agent_path','parent_thread_id','thread_source',
                        'session_id','history_mode','context_window','runtime_workspace_roots','account_scoped',
                        'creator_account_id','creator_user_id','multi_agent_version'}
        if set(meta) - allowed_meta:
            fail('unknown session metadata')
        schemas = {
            ('event_msg', 'task_started'): 'type collaboration_mode_kind model_context_window root_turn_id started_at turn_attribution turn_id',
            ('event_msg', 'thread_settings_applied'): 'type thread_id thread_settings',
            ('event_msg', 'item_completed'): 'type completed_at_ms content_token_count item started_at_ms thread_id turn_id',
            ('event_msg', 'task_complete'): 'type completed_at duration_ms last_agent_message root_turn_id started_at time_to_first_token_ms turn_id',
            ('event_msg', 'token_count'): 'type info rate_limits',
            ('response_item', 'additional_tools'): 'type id role tools',
            ('response_item', 'message'): 'type content id internal_chat_message_metadata_passthrough role phase status',
            ('response_item', 'agent_message'): 'type author content id internal_chat_message_metadata_passthrough recipient',
            ('response_item', 'reasoning'): 'type encrypted_content id internal_chat_message_metadata_passthrough summary',
            ('response_item', 'custom_tool_call'): 'type id status call_id name input internal_chat_message_metadata_passthrough',
            ('response_item', 'custom_tool_call_output'): 'type id call_id output internal_chat_message_metadata_passthrough',
            ('world_state', None): 'full state',
            ('turn_context', None): 'active_permission_profile approval_policy approvals_reviewer collaboration_mode comp_hash cwd cyber_access_program disabled_plugin_ids effort file_system_sandbox_policy model multi_agent_version permission_profile realtime_active root_turn_id sandbox_policy summary turn_id',
            ('inter_agent_communication_metadata', None): 'trigger_turn',
            ('token_usage_record', None): 'response_id root_turn_id session_id thread_id thread_token_usage turn_id turn_token_usage usage',
        }
        for index, record in enumerate(records[1:], 1):
            kind, p = record['type'], record['payload']
            typ = p.get('type')
            if kind == 'event_msg' and typ == 'item_completed' and 'content_token_count' in p:
                item = p.get('item')
                count = p['content_token_count']
                if (not isinstance(item, dict) or item.get('type') != 'AgentMessage'
                        or type(count) is not int or count < 0):
                    fail('invalid content token count')
            if pending_deferred_namespaces is not None:
                expected_state = {
                    'full': False,
                    'state': {'tools': {name: '' for name in pending_deferred_namespaces}},
                }
                if (kind == 'world_state' and p == expected_state
                        and p.get('full') is False and 'metadata' not in record):
                    pending_deferred_namespaces = None
                    continue
                fail('invalid deferred namespace state')
                pending_deferred_namespaces = None
            if kind == 'response_item' and isinstance(typ, str) and typ.endswith('_call'):
                name = p.get('name') if isinstance(p.get('name'), str) else typ
                tools[name] = tools.get(name, 0) + 1
            if kind == 'event_msg' and typ == 'item_completed' and isinstance(p.get('item'), dict):
                item_type = p['item'].get('type')
                if isinstance(item_type, str) and item_type not in ('Reasoning', 'AgentMessage'):
                    name = 'completed:' + item_type
                    tools[name] = tools.get(name, 0) + 1
            if index in witnessed:
                if not seen_settings or counts['terminal']:
                    fail('witness effect outside verified turn')
                continue
            schema = schemas.get((kind, typ))
            if schema is not None and set(p) - set(schema.split()):
                fail('unknown payload field: %s/%s' % (kind, typ))
            if counts['terminal']:
                fail('record after terminal')
            if kind == 'event_msg' and typ == 'task_started':
                counts['start'] += 1
                turn, root_turn = p.get('turn_id'), p.get('root_turn_id')
                a = p.get('turn_attribution', {})
                if (index != 1 or not isinstance(turn, str) or not turn or not isinstance(root_turn, str)
                    or not root_turn or a.get('turn_id') != turn or a.get('root_turn_id') != root_turn
                    or a.get('initiating_agent_path') != '/root' or a.get('parent_turn_id') != root_turn
                    or set(a) - {'turn_id', 'turn_trigger', 'parent_turn_id', 'initiating_agent_path', 'root_turn_id'}):
                    fail('invalid task start')
                seen_start = True
            elif kind == 'turn_context':
                counts['context'] += 1
                if (not seen_start or p.get('turn_id') != turn or p.get('root_turn_id') != root_turn
                    or p.get('cwd') != args.cwd or p.get('model') != args.model or p.get('effort') != args.effort):
                    fail('turn context mismatch')
                cs = p.get('collaboration_mode', {}).get('settings', {})
                if cs.get('model') != args.model or cs.get('reasoning_effort') != args.effort:
                    fail('turn collaboration settings mismatch')
                seen_context = True
            elif kind == 'event_msg' and typ == 'thread_settings_applied':
                counts['settings'] += 1
                s = p.get('thread_settings', {})
                allowed_settings = {'active_permission_profile', 'approval_policy', 'approvals_reviewer',
                    'collaboration_mode', 'cwd', 'disabled_plugin_ids', 'model', 'model_provider_id',
                    'permission_profile', 'personality', 'reasoning_effort', 'reasoning_summary',
                    'requested_approvals_reviewer', 'runtime_workspace_roots', 'service_tier'}
                if (not seen_context or p.get('thread_id') != args.thread or s.get('cwd') != args.cwd
                    or s.get('model') != args.model or s.get('reasoning_effort') != args.effort
                    or s.get('service_tier') != args.tier or set(s) - allowed_settings
                    or ('requested_approvals_reviewer' in s
                        and s['requested_approvals_reviewer'] != 'auto_review')):
                    fail('thread settings mismatch')
                cs = s.get('collaboration_mode', {}).get('settings', {})
                if cs.get('model') != args.model or cs.get('reasoning_effort') != args.effort:
                    fail('collaboration settings mismatch')
                seen_settings = True
            elif kind == 'event_msg' and typ == 'task_complete':
                counts['terminal'] += 1
                if (p.get('turn_id') != turn or p.get('root_turn_id') != root_turn
                    or p.get('last_agent_message') != final_text or not final_id
                    or completed_final != [(final_id, final_text)] or index != len(records) - 1):
                    fail('uncorrelated task terminal')
            elif kind == 'response_item' and typ == 'message':
                role, content = p.get('role'), p.get('content')
                mm = p.get('internal_chat_message_metadata_passthrough', {})
                deferred_marker = (
                    role == 'developer'
                    and counts['dispatch']
                    and (
                        (isinstance(mm, dict) and (
                            'tools.deferred_namespaces' in mm.get('content_item_kinds', [])
                            if isinstance(mm.get('content_item_kinds', []), list) else False
                        ))
                        or (isinstance(content, list) and any(
                            isinstance(part, dict)
                            and isinstance(part.get('text'), str)
                            and part['text'].startswith('<tools>')
                            for part in content
                        ))
                    )
                )
                if deferred_marker:
                    declaration = (
                        content[0].get('text')
                        if isinstance(content, list) and len(content) == 1
                        and isinstance(content[0], dict)
                        and set(content[0]) == {'type', 'text'}
                        and content[0].get('type') == 'input_text'
                        else None
                    )
                    match = (
                        re.fullmatch(
                            r'<tools>\nAdded deferred tool namespaces:\n'
                            r'(- mcp__[A-Za-z0-9_]+(?:\n- mcp__[A-Za-z0-9_]+)*)\n</tools>',
                            declaration,
                        )
                        if isinstance(declaration, str) else None
                    )
                    names = [line[2:] for line in match.group(1).split('\n')] if match else []
                    if (
                        not match or len(names) != len(set(names))
                        or not isinstance(mm, dict)
                        or set(mm) != {'turn_id', 'create_time', 'content_item_kinds', 'content_item_metadata'}
                        or mm.get('turn_id') != turn
                        or isinstance(mm.get('create_time'), bool)
                        or not isinstance(mm.get('create_time'), (int, float))
                        or not 0 < mm.get('create_time') < float('inf')
                        or mm.get('content_item_kinds') != ['tools.deferred_namespaces']
                        or mm.get('content_item_metadata') != [
                            {'provenance': {'type': 'tool', 'namespace': 'tool_search'}}
                        ]
                        or set(p) != {'id', 'type', 'role', 'content', 'internal_chat_message_metadata_passthrough'}
                        or not isinstance(p.get('id'), str) or not p.get('id')
                        or ('metadata' in record and set(record['metadata']) != sequence_keys)
                        or not seen_settings or counts['dispatch'] != 1
                        or counts['final'] or counts['terminal'] or tools
                        or reader_call is not None or reader_output or reader_effect
                    ):
                        fail('invalid deferred namespace declaration')
                    else:
                        pending_deferred_namespaces = names
                    continue
                if role not in ('developer', 'user', 'assistant') or not isinstance(content, list) or not content:
                    fail('invalid message')
                    continue
                if p.get('internal_chat_message_metadata_passthrough', {}).get('turn_id') != turn:
                    fail('message turn mismatch')
                mm = p.get('internal_chat_message_metadata_passthrough', {})
                if set(mm) - {'turn_id', 'content_item_kinds', 'content_item_metadata', 'create_time'}:
                    fail('unknown message metadata')
                expected_type = 'output_text' if role == 'assistant' else 'input_text'
                for part in content:
                    if (not isinstance(part, dict) or part.get('type') != expected_type
                        or not isinstance(part.get('text'), str)
                        or set(part) - ({'type', 'text', 'annotations', 'logprobs'} if role == 'assistant' else {'type', 'text'})):
                        fail('unknown message content')
                if role == 'assistant':
                    if counts['dispatch'] != 1:
                        fail('assistant before dispatch')
                    if counts['final']:
                        fail('assistant message after final')
                    if not seen_settings or p.get('status') != 'completed' or p.get('phase') not in ('commentary', 'final_answer'):
                        fail('invalid assistant message')
                    if p.get('phase') == 'final_answer':
                        counts['final'] += 1
                        final_id = p.get('id')
                        final_text = ''.join(part.get('text', '') for part in content if isinstance(part, dict))
                else:
                    if not seen_start or counts['dispatch']:
                        fail('late or uncorrelated initial input')
                    input_roles.add(role)
            elif kind == 'response_item' and typ == 'custom_tool_call' and args.reader:
                mm = p.get('internal_chat_message_metadata_passthrough', {})
                if (reader_call is not None or reader_output or counts['dispatch'] != 1 or counts['final']
                    or not seen_settings or p.get('name') != 'exec' or p.get('status') != 'completed'
                    or not isinstance(p.get('id'), str) or not p['id']
                    or not isinstance(p.get('call_id'), str) or not p['call_id']
                    or p.get('input') not in (reader_source, reader_source + '\n')
                    or not isinstance(mm, dict) or mm.get('turn_id') != turn
                    or set(mm) - {'turn_id', 'create_time'}):
                    fail('unexpected reader call')
                reader_call = p.get('call_id')
            elif kind == 'response_item' and typ == 'custom_tool_call_output' and args.reader:
                mm = p.get('internal_chat_message_metadata_passthrough', {})
                output = p.get('output')
                reader_output += 1
                if (reader_call is None or p.get('call_id') != reader_call or reader_output != 1
                    or counts['final'] or not isinstance(p.get('id'), str) or not p['id']
                    or not isinstance(mm, dict) or mm.get('turn_id') != turn
                    or set(mm) - {'turn_id', 'create_time'}
                    or not isinstance(output, list) or len(output) != 2
                    or not all(isinstance(v, dict) and set(v) == {'type', 'text'}
                               and v.get('type') == 'input_text' and isinstance(v.get('text'), str) for v in output)
                    or not re.fullmatch(r'Script completed\nWall time [0-9]+(?:\.[0-9]+)? seconds\nOutput:\n', output[0]['text'])
                    or output[1]['text'] != packet):
                    fail('reader output mismatch')
            elif kind == 'event_msg' and typ == 'item_completed' and args.reader and p.get('item', {}).get('type') == 'CommandExecution':
                item = p['item']
                reader_effect += 1
                if (reader_call is None or reader_output or reader_effect != 1 or counts['final']
                    or p.get('thread_id') != args.thread or p.get('turn_id') != turn
                    or set(item) != {'type', 'id', 'process_id', 'command', 'cwd', 'parsed_cmd', 'source', 'status', 'aggregated_output', 'exit_code', 'duration'}
                    or not isinstance(item.get('id'), str) or not item['id']
                    or not isinstance(item.get('process_id'), str) or not item['process_id']
                    or item.get('command') != ['/bin/zsh', '-c', '/bin/cat ' + reader_path]
                    or item.get('cwd') != 'file://' + args.cwd
                    or item.get('parsed_cmd') != [{'type': 'unknown', 'cmd': '/bin/cat ' + reader_path}]
                    or item.get('source') != 'unified_exec_startup' or item.get('status') != 'completed'
                    or item.get('exit_code') != 0 or item.get('aggregated_output') != packet
                    or not isinstance(item.get('duration'), dict)
                    or set(item['duration']) != {'secs', 'nanos'}
                    or any(type(item['duration'][k]) is not int or item['duration'][k] < 0 for k in ('secs', 'nanos'))):
                    fail('uncorrelated reader effect')
            elif kind == 'event_msg' and typ == 'item_completed':
                item = p.get('item', {})
                if counts['dispatch'] != 1:
                    fail('inference before dispatch')
                if (not seen_settings or p.get('thread_id') != args.thread or p.get('turn_id') != turn
                    or item.get('type') not in ('Reasoning', 'AgentMessage')):
                    fail('unknown or effectful completed item')
                allowed_item = {'type', 'id', 'raw_content', 'summary_text'} if item.get('type') == 'Reasoning' else {'type', 'id', 'content', 'phase'}
                if not isinstance(item, dict) or set(item) - allowed_item:
                    fail('unknown completed item field')
                if item.get('type') == 'AgentMessage' and item.get('phase') == 'final_answer':
                    content = item.get('content')
                    if (not isinstance(content, list) or not content
                        or any(not isinstance(v, dict) or set(v) != {'type', 'text'}
                               or v.get('type') != 'Text' or not isinstance(v.get('text'), str) for v in content)):
                        fail('invalid completed final content')
                        content = []
                    completed_final.append((item.get('id'), ''.join(v['text'] for v in content)))
            elif kind == 'response_item' and typ == 'reasoning':
                if counts['dispatch'] != 1 or not seen_settings or p.get('internal_chat_message_metadata_passthrough', {}).get('turn_id') != turn:
                    fail('reasoning turn mismatch')
            elif kind == 'response_item' and typ == 'agent_message':
                counts['dispatch'] += 1
                if p.get('author') != '/root' or p.get('recipient') != args.agent:
                    forwarded += 1
                if (p.get('author') != '/root' or p.get('recipient') != args.agent
                    or not seen_settings or counts['dispatch'] != 1 or input_roles != {'developer', 'user'}
                    or p.get('internal_chat_message_metadata_passthrough', {}).get('turn_id') != turn
                    or not isinstance(p.get('content'), list) or not p['content']
                    or any(not isinstance(v, dict) or (v.get('type') == 'input_text' and (set(v) != {'type', 'text'} or not isinstance(v.get('text'), str)))
                           or (v.get('type') == 'encrypted_content' and (set(v) != {'type', 'encrypted_content'} or not isinstance(v.get('encrypted_content'), str)))
                           or v.get('type') not in ('input_text', 'encrypted_content') for v in p['content'])
                    or not any(v.get('type') == 'input_text' and v.get('text') for v in p['content'] if isinstance(v, dict))):
                    fail('unexpected inter-agent message')
                if args.packet_sha256 is not None and not args.reader:
                    content = p.get('content')
                    if (not isinstance(content, list) or len(content) != 1 or not isinstance(content[0], dict)
                        or content[0].get('type') != 'input_text' or not isinstance(content[0].get('text'), str)
                        or hashlib.sha256(content[0]['text'].encode('utf-8')).hexdigest() != args.packet_sha256):
                        fail('packet unavailable or digest mismatch')
            elif kind == 'response_item' and typ == 'additional_tools':
                if counts['dispatch'] or p.get('role') != 'developer' or not isinstance(p.get('tools'), list):
                    fail('invalid tool declaration')
            elif kind == 'world_state':
                counts['world'] += 1
                if counts['dispatch'] or p.get('full') is not True or not isinstance(p.get('state'), dict):
                    fail('invalid world state')
                else:
                    state = p['state']
                    if (state.get('model', {}).get('model') != args.model
                        or state.get('collaboration_mode', {}).get('model') != args.model):
                        fail('world model mismatch')
            elif kind == 'response_item' and typ == 'configuration_update':
                if (
                    p != {'type': 'configuration_update', 'reasoning': {'effort': args.effort}}
                    or {key: value for key, value in record.get('metadata', {}).items()
                        if key not in sequence_keys}
                       != {"client_authored": False, "harness_authored_configuration": True}
                    or not seen_settings
                    or counts['dispatch'] != 1
                    or counts['final']
                    or counts['terminal']
                ):
                    fail('invalid configuration update')
            elif kind == 'inter_agent_communication_metadata':
                if counts['dispatch'] or p != {'trigger_turn': True}:
                    fail('unexpected inter-agent metadata')
            elif kind == 'token_usage_record':
                if p.get('thread_id') != args.thread or p.get('turn_id') != turn or p.get('root_turn_id') != root_turn:
                    fail('usage turn mismatch')
                usage = p.get('turn_token_usage')
                keys = ('input_tokens', 'cached_input_tokens', 'cache_write_input_tokens', 'output_tokens', 'reasoning_output_tokens', 'total_tokens')
                if not isinstance(usage, dict) or any(type(usage.get(k)) is not int or usage[k] < 0 for k in keys):
                    fail('invalid turn token usage')
                else:
                    tokens = {k: usage[k] for k in keys}
            elif kind == 'event_msg' and typ == 'token_count':
                if not isinstance(p.get('info'), dict):
                    fail('invalid token count')
            else:
                fail('unknown or effectful record: %s/%s' % (kind, typ))
        if pending_deferred_namespaces is not None:
            fail('missing deferred namespace state')
        if any(counts[k] != 1 for k in counts):
            fail('missing or repeated lifecycle record')
        if args.reader and (reader_call is None or reader_output != 1 or reader_effect != 1):
            fail('missing or repeated reader call/output')
        print(json.dumps({'model': args.model, 'effort': args.effort, 'agent': args.agent,
                          'tools': tools, 'tokens': tokens, 'usd': None, 'forwarded': forwarded, 'problems': problems}))
        return int(bool(problems))
    except (OSError, ValueError, TypeError, AttributeError, KeyError) as error:
        print(json.dumps({'error': str(error)}))
        return 2


def legacy_owned_fixture_pid(path, expected_digest):
    """Validate an independently pinned process-ownership fixture receipt."""
    if not path or not expected_digest or not re.fullmatch(r'[0-9a-fA-F]{64}', expected_digest):
        raise ValueError('ownership receipt and SHA256 are required')
    if not os.path.isabs(path) or os.path.realpath(path) != path:
        raise ValueError('ownership receipt path must be canonical and absolute')
    before = os.lstat(path)
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        raise ValueError('ownership receipt must be a single-link regular file')
    fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
    with os.fdopen(fd, 'rb') as stream:
        opened = os.fstat(stream.fileno())
        if (not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1
                or (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino)):
            raise ValueError('ownership receipt changed while opening')
        data = stream.read()
    if hashlib.sha256(data).hexdigest() != expected_digest.lower():
        raise ValueError('ownership receipt SHA256 mismatch')

    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate ownership receipt key')
            result[key] = value
        return result

    receipt = json.loads(data, object_pairs_hook=unique_object)
    fields = {'schema', 'creator_pid', 'child_pid', 'child_ppid',
              'control_pid', 'control_ppid', 'supervisor_pid', 'provenance'}
    if not isinstance(receipt, dict) or set(receipt) != fields:
        raise ValueError('invalid ownership receipt fields')
    if receipt['schema'] != 'legacy-process-ownership-fixture/1':
        raise ValueError('invalid ownership receipt schema')
    for key in fields - {'schema', 'provenance'}:
        if type(receipt[key]) is not int or receipt[key] <= 0:
            raise ValueError('invalid ownership receipt PID')
    if (receipt['creator_pid'] == receipt['supervisor_pid']
            or receipt['child_pid'] == receipt['control_pid']
            or receipt['child_ppid'] != receipt['creator_pid']
            or receipt['control_ppid'] != receipt['supervisor_pid']):
        raise ValueError('invalid ownership receipt relationships')
    if not isinstance(receipt['provenance'], str) or not receipt['provenance'].strip():
        raise ValueError('invalid ownership receipt provenance')
    return receipt['child_pid']


def legacy_literal_print(command):
    """Recognize only a complete, literal printf or echo command."""
    try:
        tokens = shell_tokens(command)
    except ValueError:
        return False
    if not tokens or any(kind != 'word' for kind, _, _ in tokens):
        return False
    if tokens[0][1] not in ('printf', 'echo') or tokens[0][2] != tokens[0][1]:
        return False
    if tokens[0][1] == 'printf' and (len(tokens) < 2 or tokens[1][1].startswith('-')):
        return False
    def literal_word(raw):
        quote = None
        index = 0
        while index < len(raw):
            char = raw[index]
            if quote == "'":
                if char == "'":
                    quote = None
            elif char == '\\':
                index += 1
            elif char == quote:
                quote = None
            elif quote is None and char in ("'", '"'):
                quote = char
            elif char in '$`':
                return False
            elif quote is None and char in '*?[':
                return False
            index += 1
        return quote is None

    if not all(literal_word(raw) for _, _, raw in tokens[1:]):
        return False
    if tokens[0][1] == 'echo':
        return True

    # Only admit format directives whose operands are printed as strings.
    # In particular, zsh printf %n can evaluate an array assignment target.
    fmt = tokens[1][1]
    index = 0
    while index < len(fmt):
        if fmt[index] == '\\':
            if index + 1 >= len(fmt) or fmt[index + 1] != 'n':
                return False
            index += 2
        elif fmt[index] != '%':
            index += 1
        elif index + 1 < len(fmt) and fmt[index + 1] == '%':
            index += 2
        else:
            index += 1
            while index < len(fmt) and fmt[index] in '-+ #0':
                index += 1
            while index < len(fmt) and fmt[index] in '0123456789':
                index += 1
            if index < len(fmt) and fmt[index] == '.':
                index += 1
                while index < len(fmt) and fmt[index] in '0123456789':
                    index += 1
            if index >= len(fmt) or fmt[index] != 's':
                return False
            index += 1
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('session')
    parser.add_argument('--model', required=True)
    parser.add_argument('--effort', required=True)
    parser.add_argument('--agent', required=True)
    parser.add_argument('--write-root', action='append', default=[])
    parser.add_argument('--forbid-forwarding', action='store_true')
    parser.add_argument('--native', action='store_true')
    parser.add_argument('--thread')
    parser.add_argument('--parent')
    parser.add_argument('--cwd')
    parser.add_argument('--tier')
    parser.add_argument('--sha256')
    parser.add_argument('--packet-sha256')
    parser.add_argument('--reader', action='store_true')
    parser.add_argument('--packet')
    parser.add_argument('--startup-sha256')
    parser.add_argument('--receipt')
    parser.add_argument('--receipt-sha256')
    parser.add_argument('--root')
    parser.add_argument('--root-inode',type=int)
    parser.add_argument('--root-device',type=int)
    parser.add_argument('--legacy-ownership-receipt')
    parser.add_argument('--legacy-ownership-sha256')
    args = parser.parse_args()
    if args.reader and not args.native:
        parser.error('--reader requires --native')
    if args.native:
        return native_check(args)
    if not args.session or any(not root for root in args.write_root):
        print(json.dumps({'error': 'empty path argument'}))
        return 2
    args.session = args.session if os.path.isabs(args.session) else os.path.abspath(args.session)
    args.write_root = [os.path.normpath(p if os.path.isabs(p) else os.path.abspath(p)) for p in args.write_root]
    try:
        with open(args.session, encoding='utf-8') as stream:
            lines = [json.loads(line) for line in stream if line.strip()]
        if not all(isinstance(e, dict) for e in lines) or not any(e.get('type') == 'session' for e in lines):
            raise ValueError('no session entry')
    except (OSError, ValueError) as error:
        print(json.dumps({'error': str(error)}))
        return 2
    cwd = next((e.get('cwd') for e in lines if e.get('type') == 'session' and isinstance(e.get('cwd'), str)), None)
    model = effort = agent = None
    models = efforts = inits = 0
    tools, problems, forwarded = {}, [], []
    owned_fixture_pid = None
    if args.legacy_ownership_receipt or args.legacy_ownership_sha256:
        try:
            owned_fixture_pid = legacy_owned_fixture_pid(
                args.legacy_ownership_receipt, args.legacy_ownership_sha256)
        except (OSError, ValueError, UnicodeError) as error:
            problems.append('invalid legacy ownership receipt: ' + str(error))
    tokens = dict.fromkeys(('input', 'output', 'cacheRead', 'cacheWrite'), 0)
    usd = 0.0
    for entry in lines:
        kind = entry.get('type')
        if kind == 'session_init':
            inits += 1
            agent = entry.get('agent')
            if agent != args.agent:
                problems.append('agent %r, expected %r' % (agent, args.agent))
            if entry.get('resolvedModel') != args.model + ':' + args.effort:
                problems.append('resolved model %r' % entry.get('resolvedModel'))
        if kind == 'model_change':
            models += 1
            model = entry.get('model')
            if model != args.model:
                problems.append('model %r, expected %r' % (model, args.model))
            if entry.get('resolvedModelIsFallback') is True:
                problems.append('fallback model')
        if kind == 'thinking_level_change':
            efforts += 1
            effort = entry.get('thinkingLevel')
            if effort != args.effort:
                problems.append('effort %r, expected %r' % (effort, args.effort))
        message = entry.get('message') if isinstance(entry.get('message'), dict) else {}
        if message.get('role') == 'assistant' and message.get('provider', '') + '/' + message.get('model', '') != args.model:
            problems.append('assistant turn on %s/%s' % (message.get('provider'), message.get('model')))
        usage = message.get('usage') if isinstance(message.get('usage'), dict) else None
        if usage:
            for key in tokens:
                tokens[key] += int(usage.get(key) or 0)
            usd += float((usage.get('cost') or {}).get('total') or 0)
        for part in message.get('content') or []:
            if not isinstance(part, dict) or part.get('type') != 'toolCall':
                continue
            name, arguments = str(part.get('name')), part.get('arguments') or {}
            tools[name] = tools.get(name, 0) + 1
            if 'graft' in name.lower():
                problems.append('graft tool call: ' + name)
            if name in ('task', 'eval'):
                problems.append('forbidden tool: ' + name)
            if name in ('find', 'web_search'):
                forwarded.append(name)
            if name == 'web_search':
                problems.append('network tool: web_search')
            paths = []
            if name == 'edit':
                body = str(arguments.get('input', ''))
                paths = re.findall(r'^\[(.+?)#[0-9A-Fa-f]{4}\]\s*$', body, re.M)
                paths += [p.strip().strip('"\'') for p in re.findall(r'^MV (.+)$', body, re.M)]
            elif name == 'write':
                paths = [str(arguments.get('path', ''))]
            filtered = dict(arguments)
            if name in ('grep', 'glob', 'find'):
                if name == 'grep':
                    filtered.pop('pattern', None)
                if isinstance(filtered.get('path'), str):
                    filtered['path'] = ';'.join(p for p in filtered['path'].split(';') if not p.strip().startswith('!'))
            if name == 'bash' and isinstance(filtered.get('command'), str) and legacy_literal_print(filtered['command']):
                filtered.pop('command')
            inspected = paths if name in ('write', 'edit') else filtered
            if FORBIDDEN_PATH.search(json.dumps(inspected)):
                problems.append('forbidden path in %s arguments' % name)
            for key in ('path', 'url'):
                if isinstance(filtered.get(key), str) and any(p.strip().startswith(('http://', 'https://')) for p in filtered[key].split(';')):
                    problems.append('network read in ' + name)
            command = str(arguments.get('command', '')) if name == 'bash' else ''
            operations = shell_operations(command) if command else set()
            if 'network' in operations or 'unparsable' in operations:
                problems.append('network command: ' + command[:120])
            if 'graft' in operations:
                problems.append('graft command: ' + command[:120])
            if name in ('write', 'edit'):
                if name == 'edit' and not paths:
                    problems.append('edit without a parsable target path')
                for path in paths:
                    if name == 'write' and path.startswith('agent://'):
                        continue
                    if path.startswith('proc://'):
                        match = re.fullmatch(r'proc://([1-9][0-9]*)/kill', path)
                        if not match or owned_fixture_pid != int(match.group(1)):
                            problems.append('%s to an unowned or invalid process URL: %s' % (name, path))
                        continue
                    if path.startswith(('xd://', 'local://')):
                        problems.append('%s to an internal URL: %s' % (name, path))
                        continue
                    if not os.path.isabs(path):
                        if not cwd or not os.path.isabs(cwd):
                            problems.append('%s with a relative path and no session cwd: %s' % (name, path))
                            continue
                        path = os.path.join(cwd, path)
                    path = os.path.normpath(path)
                    if not any(path == root or path.startswith(root.rstrip('/') + '/') for root in args.write_root):
                        problems.append('%s outside the write roots: %s' % (name, path))
    if not models:
        problems.append('no model change recorded')
    if not efforts:
        problems.append('effort None, expected %r' % args.effort)
    if not inits:
        problems.append('no session_init entry')
    if forwarded and args.forbid_forwarding:
        problems.append('tool(s) forwarding context to another model: ' + ', '.join(sorted(set(forwarded))))
    print(json.dumps({'model': model, 'effort': effort, 'agent': agent, 'tools': tools, 'tokens': tokens, 'usd': round(usd, 6), 'forwarded': len(forwarded), 'problems': problems}))
    return int(bool(problems))


if __name__ == '__main__':
    sys.exit(main())
