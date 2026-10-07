"""Fixed synthetic operations producing invocation/result facts; never calls a model."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.parse import quote

VERSION = 'tackle-gpt-stub/1'
MARKER = 'synthetic sensitive+"marker'
SCHEMA = 'tackle-gpt-stub-event/1'


def main():
    if sys.argv[1:2] == ['sandbox']:
        argv = sys.argv[1:]
        helper = Path(__file__).with_name('sentinel_helper.py').resolve()
        if (len(argv) != 16 or argv[:3] != ['sandbox', '-P', 'gpt-measurement']
                or argv[3] != '-C' or argv[6] != '-B' or Path(argv[5]).resolve() != Path(sys.executable).resolve()
                or argv[7] != str(helper)
                or argv[8::2] != ['--inside', '--outside', '--network-result', '--out']):
            raise SystemExit('unsupported synthetic sandbox argv')
        os.chdir(argv[4])
        os.execve(str(Path(sys.executable).resolve()), argv[5:], dict(os.environ))
    parser = argparse.ArgumentParser()
    parser.add_argument('--work', required=True)
    parser.add_argument('--skill')
    parser.add_argument('--outside', required=True)
    parser.add_argument('--session', required=True)
    args = parser.parse_args()
    work = Path(args.work).resolve()
    skill = Path(args.skill).resolve() if args.skill else None
    payload = json.loads(sys.stdin.buffer.read())
    sequence = 0
    event_sequence = 0
    fault = payload.get('fault')

    def emit(kind, **fields):
        nonlocal event_sequence
        event_sequence += 1
        record = {'schema': SCHEMA, 'kind': kind, 'session_id': args.session,
                  'event_id': 'event-' + str(event_sequence), **fields}
        print(json.dumps(record, ensure_ascii=False), flush=True)

    emit('request_started', pid=os.getpid(), cwd=str(work))

    def allowed(path, writing=False):
        given = Path(path)
        resolved = given.resolve()
        roots = [work] if writing or skill is None else [work, skill]
        if not any(resolved.is_relative_to(root) for root in roots):
            raise PermissionError('synthetic wrapper outside-tree denial')
        if given.is_symlink() or any(p.is_symlink() for p in given.parents if p != work.parent):
            raise PermissionError('synthetic wrapper link denial')
        if given.exists() and given.stat().st_nlink > 1:
            raise PermissionError('synthetic wrapper hardlink denial')
        return resolved

    def call(name, given, operation):
        nonlocal sequence
        sequence += 1
        item = 'item-' + str(sequence)
        if fault == 'duplicate_id':
            item = 'item-1'
        emit('tool_started', item_id=item, original_name=name, input=given)
        if fault == 'repeated_update':
            emit('tool_started', item_id=item, original_name=name, input=given)
        encoding_error = None
        try:
            result = operation()
        except UnicodeDecodeError as error:
            result = {'error': type(error).__name__, 'errno': None, 'mechanism': 'UTF-8 decoding'}
            encoding_error = error
        except OSError as error:
            result = {'error': type(error).__name__, 'errno': getattr(error, 'errno', None),
                      'mechanism': 'synthetic wrapper' if isinstance(error, PermissionError) else 'actual syscall'}
        if fault != 'missing_result':
            emit('tool_completed', item_id=item, result=result)
        if encoding_error is not None:
            raise encoding_error
        return result

    def read(path, limit=None):
        data = allowed(path).read_bytes()
        if limit is not None:
            data = data[:limit]
        return {'content': data.decode('utf-8'), 'returned_bytes': len(data)}

    def write(path, content):
        target = allowed(path, writing=True)
        target.parent.mkdir(parents=True, exist_ok=True)
        data = content.encode('utf-8')
        target.write_bytes(data)
        return {'path': str(target), 'bytes_written': len(data), 'content_sha256': hashlib.sha256(data).hexdigest()}

    if payload.get('delay', 0):
        time.sleep(payload['delay'])
    if fault == 'invalid_json':
        print('not-json', flush=True)
        return 0
    if skill:
        call('NativeRead', {'file_path': str(skill / 'SKILL.md')}, lambda: read(skill / 'SKILL.md'))
    operation = payload.get('operation', 'read_write')
    if operation in ('read_write', 'probe'):
        inside = work / 'inside-sentinel'
        call('NativeRead', {'file_path': str(inside)}, lambda: read(inside))
        call('NativeWrite', {'file_path': str(inside), 'content': 'inside-after\n'},
             lambda: write(inside, 'inside-after\n'))
        if operation == 'probe':
            call('NativeRead', {'file_path': args.outside}, lambda: read(args.outside))
    elif operation == 'archive':
        path = work / 'history-archive.md'
        call('NativeRead', {'file_path': str(path)}, lambda: read(path, payload.get('read_limit')))
    elif operation == 'command':
        mode = 'unsupported-echo-mode' if fault == 'command_nonzero' else 'echo'
        argv = [sys.executable, '-B', str(Path(__file__).with_name('sentinel_helper.py')), mode]
        command = ' '.join(argv)
        def execute():
            child = subprocess.run(argv, cwd=work, capture_output=True, env={
                'PATH': '/usr/bin:/bin', 'HOME': os.environ['HOME'], 'TMPDIR': os.environ['TMPDIR'],
                'LANG': 'en_US.UTF-8'})
            return {'stdout': child.stdout.decode('utf-8'), 'stderr': child.stderr.decode('utf-8'),
                    'exit_code': child.returncode}
        call('CommandExecution', {'command': command, 'cwd': str(work)}, execute)
    elif operation == 'network':
        port = payload['port']
        def connect():
            request = (f'POST /synthetic?private-query HTTP/1.1\r\nHost: {payload.get("host", "foreign.invalid")}\r\n'
                       'Content-Length: 7\r\nConnection: close\r\n\r\npayload').encode()
            with socket.create_connection(('127.0.0.1', port), timeout=2) as connection:
                connection.sendall(request)
                result = b''
                while True:
                    part = connection.recv(65536)
                    if not part:
                        break
                    result += part
            return {'stdout': result.decode('utf-8'), 'stderr': '', 'exit_code': 0}
        call('SyntheticLoopbackRequest', {'port': port, 'host': payload.get('host', 'foreign.invalid')}, connect)
    elif operation == 'boundary':
        target = payload.get('target', 'outside-link')
        path = work / target
        if target == 'outside-link':
            path.symlink_to(args.outside)
        elif target == 'outside-hardlink':
            os.link(args.outside, path)
        call('NativeRead', {'file_path': str(path)}, lambda: read(path))
        call('NativeWrite', {'file_path': str(path), 'content': 'outside-after\n'},
             lambda: write(path, 'outside-after\n'))
        if path.is_symlink() or target == 'outside-hardlink':
            path.unlink()
    elif operation == 'claim_only':
        emit('claim', text='I read the archive and reviewed the work.')
    if fault == 'summary_only':
        emit('file_change_summary', paths=['note.txt'])
    if fault == 'unknown_tool':
        call('UnknownNativeTool', {}, lambda: {'content': 'unknown', 'returned_bytes': 7})
    if fault and fault.startswith('credential_'):
        form = payload.get('form', 'raw')
        value = {'raw': MARKER, 'base64': base64.b64encode(MARKER.encode()).decode(),
                 'hex': MARKER.encode().hex(), 'url': quote(MARKER, safe=''),
                 'json': json.dumps(MARKER)[1:-1]}.get(form, MARKER)
        if fault == 'credential_stdout':
            emit('claim', text=value)
        elif fault == 'credential_stderr':
            print(value, file=sys.stderr, flush=True)
        elif fault == 'credential_file':
            (work / 'sensitive').write_text(value)
        elif fault == 'credential_name':
            (work / value).write_text('name')
        elif fault == 'credential_link':
            (work / 'sensitive-link').symlink_to(value)
    if fault == 'truncated_output':
        print('{"partial":', end='', flush=True)
        return 0
    observed = {'model': 'other' if fault == 'wrong_binding' else 'gpt-6-luna',
                'requested_host_effort': 'xhigh'}
    emit('session_completed', observed_binding=observed)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
