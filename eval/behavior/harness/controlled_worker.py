#!/usr/bin/env python3
"""Fixed fixture worker. Directory descriptors, never caller paths, grant access."""
import base64
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time

if sys.argv[1:] == ['--isolated-file-worker/1']:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import controlled_route as route


def roots(authority):
    route.validate_record('worker_authority', authority)
    observed = {}
    for binding in authority['root_bindings']:
        role = binding['role']
        slot, access = {'work': (10, 'read_write'), 'tmp': (11, 'read_write'),
                        'install': (12, 'read_only'), 'runtime': (13, 'read_only')}[role]
        route.require(role not in observed and binding['descriptor_slot'] == slot
                      and binding['access'] == access, 'authority_mismatch')
        info = os.fstat(slot)
        route.require(stat.S_ISDIR(info.st_mode) and info.st_dev == binding['device']
                      and info.st_ino == binding['inode'] and info.st_uid == binding['owner_uid'], 'authority_mismatch')
        observed[role] = slot
    route.require('work' in observed and 'tmp' in observed and 'runtime' in observed, 'authority_mismatch')
    return observed


def open_file(path, allowed, write=False, on_effect=None):
    path = Path(path)
    route.require(path.is_absolute(), 'path_unsupported')
    # Kernel descriptors are compared to declared roots; the absolute spelling
    # is only a routing label, and each component is opened without following links.
    selected = None
    for role, descriptor in allowed.items():
        root_path = Path(os.readlink('/proc/self/fd/' + str(descriptor))) if sys.platform.startswith('linux') else None
        if root_path is None:
            import fcntl
            import struct
            raw = fcntl.fcntl(descriptor, 50, bytes(1024))  # macOS F_GETPATH
            root_path = Path(raw.split(b'\0', 1)[0].decode())
        try:
            remaining = path.relative_to(root_path)
        except ValueError:
            continue
        route.require(not write or role in ('work', 'tmp'), 'read_only_root')
        route.relative(remaining.as_posix())
        selected = descriptor, remaining.parts
        break
    route.require(selected is not None, 'path_unsupported')
    descriptor, components = selected
    current = os.dup(descriptor)
    try:
        for component in components[:-1]:
            if write:
                try: os.mkdir(component, mode=0o700, dir_fd=current)
                except FileExistsError: pass
                else:
                    if on_effect is not None: on_effect()
            next_fd = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=current)
            os.close(current); current = next_fd
        flags = os.O_WRONLY if write else os.O_RDONLY
        try:
            fd = os.open(components[-1], flags | os.O_NOFOLLOW, dir_fd=current)
        except FileNotFoundError:
            if not write: raise
            fd = os.open(components[-1], flags | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600, dir_fd=current)
            if on_effect is not None: on_effect()
        try:
            info = os.fstat(fd)
            route.require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, 'unsafe_file')
        except BaseException:
            os.close(fd)
            raise
        return fd
    finally:
        os.close(current)


def main():
    raw = sys.stdin.buffer.read(route.IO['max_serialized_request_bytes'] + 1)
    envelope = route.strict_json(raw)
    route.validate_record('worker_envelope', envelope)
    invocation, authority = envelope['invocation'], envelope['authority']
    route.require(all(invocation[key] == authority[key] for key in ('episode_id', 'session_id', 'worker_handle', 'fingerprint')),
                  'authority_mismatch')
    allowed = roots(authority)
    value, name = invocation['parsed_input'], invocation['function_name']
    facts, returned, kind, complete = {}, b'', name, True
    owned = []
    effect_started = False
    def mark_effect():
        nonlocal effect_started
        effect_started = True
    try:
        if name == 'Read':
            fd = open_file(value['file_path'], allowed)
            try:
                info = os.fstat(fd)
                mark_effect()
                data = os.pread(fd, value['max_bytes'], value['byte_offset'])
            finally: os.close(fd)
            text = data.decode('utf-8', errors='strict')
            facts = dict(file_path=value['file_path'], byte_offset=value['byte_offset'],
                requested_max_bytes=value['max_bytes'], returned_bytes=len(data), content_utf8=text,
                content_sha256=route.digest(data), eof=value['byte_offset'] + len(data) >= info.st_size)
            returned = data
        elif name == 'Write':
            fd = open_file(value['file_path'], allowed, write=True, on_effect=mark_effect)
            data = value['content'].encode('utf-8')
            try:
                # Once a mutating operation starts, an error cannot prove that
                # the file was untouched. Retain that fact through every handler.
                mark_effect()
                os.ftruncate(fd, 0)
                offset = 0
                while offset < len(data): offset += os.write(fd, data[offset:])
                os.fsync(fd)
                route.require(os.fstat(fd).st_size == len(data), 'write_ack')
            finally: os.close(fd)
            facts = dict(file_path=value['file_path'], bytes_written=len(data), content_sha256=route.digest(data))
            returned = route.encoded(facts)
        else:
            choices = {route.command(mode): mode for mode in route.POLICY['modes']}
            route.require(value['command'] in choices, 'command_unsupported')
            # A fixed cwd descriptor is mandatory; no arbitrary shell cwd is accepted.
            route.require(value['cwd'] == os.environ['HOME'], 'cwd_unsupported')
            argv = [route.SHELL, '-c', value['command']]
            start = time.monotonic_ns()
            mark_effect()
            main = subprocess.Popen(argv, cwd=value['cwd'], env=route.fresh_environment(value['cwd'], os.environ['TMPDIR']),
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
            owned.append(dict(pid=main.pid, started_ns=start, role='command'))
            helper = None
            if choices[value['command']] == 'owned_helper':
                # Both handles are explicitly created and waited by this trusted worker.
                helper = subprocess.Popen([route.PYTHON, '-B', str(route.FIXTURE / 'command_fixture.py'), 'delay'],
                    cwd=value['cwd'], env=route.fresh_environment(value['cwd'], os.environ['TMPDIR']),
                    stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
                owned.append(dict(pid=helper.pid, started_ns=time.monotonic_ns(), role='owned_helper'))
            timeout = False
            try: stdout, stderr = main.communicate(timeout=route.IO['max_tool_seconds'])
            except subprocess.TimeoutExpired:
                timeout = True; main.kill(); stdout, stderr = main.communicate()
            owned[0].update(exit_code=main.returncode, exited_ns=time.monotonic_ns())
            if helper is not None:
                try: hs, he = helper.communicate(timeout=route.IO['max_tool_seconds'])
                except subprocess.TimeoutExpired:
                    timeout = True; helper.kill(); hs, he = helper.communicate()
                stdout += hs; stderr += he
                owned[1].update(exit_code=helper.returncode, exited_ns=time.monotonic_ns())
            os.write(14, stdout); os.write(15, stderr)
            complete = not timeout and len(stdout) <= route.IO['max_worker_stdout_bytes'] and len(stderr) <= route.IO['max_worker_stderr_bytes']
            stdout_text, stderr_text = stdout.decode('utf-8', errors='strict'), stderr.decode('utf-8', errors='strict')
            prefix = 'workers/' + invocation['worker_handle']
            def source(channel, data):
                return route.record('raw_source', artifact=prefix + '/' + channel + '.bin', sha256=route.digest(data),
                    byte_start=0, byte_end=len(data), event_id=invocation['worker_handle'] + '_' + channel, producer='worker')
            facts = dict(command=value['command'], argv=argv, shell_path=route.SHELL, cwd=value['cwd'],
                stdout_source=source('stdout', stdout), stderr_source=source('stderr', stderr),
                stdout_utf8=stdout_text, stderr_utf8=stderr_text,
                exit_code=main.returncode if main.returncode >= 0 else None,
                signal=-main.returncode if main.returncode < 0 else None, timeout=timeout, capture_complete=complete)
            returned = route.encoded([dict(type='text', text=stdout_text), dict(type='text', text=stderr_text)])
    except route.Refusal as exc:
        kind = 'refused'
        facts = dict(error_code=exc.code, errno=None, mechanism='fixture_policy', effect_started=effect_started)
        returned = route.encoded(facts)
    except OSError as exc:
        kind = 'refused'
        facts = dict(error_code='os_error', errno=exc.errno, mechanism='observed_os_error', effect_started=effect_started)
        returned = route.encoded(facts)
    except UnicodeError:
        kind, complete = 'refused', False
        facts = dict(error_code='invalid_utf8', errno=None, mechanism='observed_decode', effect_started=effect_started)
        returned = route.encoded(facts)
    result = {key: invocation[key] for key in ('episode_id', 'session_id', 'attempt_id', 'response_id', 'item_index',
               'item_id', 'call_id', 'function_name', 'worker_handle')}
    result.update(schema=route.VERSIONS['result'], kind=kind, facts=facts,
                  returned_output_utf8_b64=base64.b64encode(returned).decode(),
                  returned_output_sha256=route.digest(returned), complete=complete, sources=[])
    # Observations are separate from participant returned text and are not tool calls.
    sys.stderr.buffer.write(route.encoded(dict(schema='tackle-controlled-owned-handles/1',
        worker_handle=invocation['worker_handle'], handles=owned, remaining_handle_ids=[])) + b'\n')
    sys.stderr.buffer.flush()
    sys.stdout.buffer.write(route.encoded(result) + b'\n')
    sys.stdout.buffer.flush()
    return 0 if complete else 6


def isolated_file_request(raw):
    envelope = route.strict_json(raw)
    route.fields(envelope, route.isolated_policy()['record_fields']['FileRequest'])
    route.require(envelope['schema'] == 'tackle-isolated-file-request/1'
        and type(envelope['request_id']) is str and len(envelope['request_id']) <= 128
        and envelope['function_name'] in ('Read','Write'), 'isolated_file_request')
    route.require(route.re.fullmatch('[A-Za-z0-9_.:-]{1,128}', envelope['request_id']) is not None, 'isolated_file_request')
    route.validate_tool(envelope['function_name'], envelope['arguments'])
    route.isolated_path(envelope['arguments']['file_path'])
    return envelope


def isolated_file_roots():
    return {role:os.open('/' + role, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            for role in ('work','tmp','runtime')}


def isolated_file_main():
    """Immutable file helper; its data claims confer no host lifecycle authority."""
    os.environ.clear(); os.environ.update(route.isolated_policy()['participant_env'])
    raw=sys.stdin.buffer.read(route.isolated_policy()['caps']['max_request_bytes']+1)
    route.require(len(raw)<=route.isolated_policy()['caps']['max_request_bytes'], 'isolated_request_size')
    envelope=isolated_file_request(raw)
    allowed=isolated_file_roots()
    value,name=envelope['arguments'],envelope['function_name']
    kind,complete,facts,returned=name,True,{},b''
    effect_started=False
    def effect():
        nonlocal effect_started
        effect_started=True
    try:
        if name=='Read':
            fd=open_file(value['file_path'],allowed)
            try:
                info=os.fstat(fd);effect()
                data=os.pread(fd,value['max_bytes'],value['byte_offset'])
            finally:os.close(fd)
            text=data.decode('utf-8')
            facts=dict(file_path=value['file_path'],byte_offset=value['byte_offset'],requested_max_bytes=value['max_bytes'],
                returned_bytes=len(data),content_utf8=text,content_sha256=route.digest(data),
                eof=value['byte_offset']+len(data)>=info.st_size)
            returned=data
        else:
            fd=open_file(value['file_path'],allowed,write=True,on_effect=effect)
            data=value['content'].encode('utf-8')
            try:
                effect();os.ftruncate(fd,0)
                offset=0
                while offset<len(data):
                    count=os.write(fd,data[offset:])
                    route.require(count>0,'isolated_write_progress');offset+=count
                os.fsync(fd)
                route.require(os.fstat(fd).st_size==len(data),'isolated_write_ack')
            finally:os.close(fd)
            facts=dict(file_path=value['file_path'],bytes_written=len(data),content_sha256=route.digest(data))
            returned=route.encoded(facts)
    except route.Refusal as exc:
        kind='refused'
        facts=dict(error_code=exc.code,errno=None,mechanism='path_policy',effect_started=effect_started)
        returned=route.encoded(facts)
    except OSError as exc:
        kind='refused'
        facts=dict(error_code='os_error',errno=exc.errno,mechanism='observed_os_error',effect_started=effect_started)
        returned=route.encoded(facts)
    except UnicodeError:
        if name == 'Read':
            sys.stderr.buffer.write(data); sys.stderr.buffer.flush()
        kind,complete='refused',False
        facts=dict(error_code='invalid_utf8',errno=None,mechanism='observed_decode',effect_started=effect_started)
        returned=route.encoded(facts)
    finally:
        for descriptor in allowed.values():os.close(descriptor)
    claim=route.isolated_record('FileClaim',request_id=envelope['request_id'],kind=kind,facts=facts,
        returned_utf8_b64=base64.b64encode(returned).decode(),returned_sha256=route.digest(returned),complete=complete)
    sys.stdout.buffer.write(route.encoded(claim)+b'\n');sys.stdout.buffer.flush()
    return 0 if complete else 6


if __name__ == '__main__':
    if sys.argv[1:] == ['--isolated-file-worker/1']:
        try:
            raise SystemExit(isolated_file_main())
        except (route.Refusal, OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
            print(str(exc), file=sys.stderr)
            raise SystemExit(6)
    try: raise SystemExit(main())
    except (route.Refusal, OSError) as exc:
        sys.stderr.write(str(exc) + '\n')
        raise SystemExit(8)
