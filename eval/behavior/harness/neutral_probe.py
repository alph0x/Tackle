"""Neutral one-attempt components; production policy admission is unavailable.

No CLI activates inference. Qualification admission can exercise injected local
senders only; dispatch accepts a concrete data-only synthetic sender. A live driver
needs an independently reviewed authoritative policy observer and supervisor.
"""
import contextlib
import fcntl
import hashlib
import http.client
import json
import math
import os
from pathlib import Path
import re
import ssl
import stat
import time

REQUEST = (b'{"input":[{"content":[{"text":"Reply with the single word READY.",'
           b'"type":"input_text"}],"role":"user"}],"model":"gpt-5.6-luna",'
           b'"reasoning":{"effort":"xhigh"},"store":false,"stream":true}\n')
REQUEST_SHA = hashlib.sha256(REQUEST).hexdigest()
MAX_STREAM = 1048576
MAX_EVENT = 262144
LIMIT = 120


class Refusal(Exception):
    """Finite local diagnostic only, never remote bodies/exception strings."""


def need(value, reason):
    if not value:
        raise Refusal(reason)


def encoded(value):
    return json.dumps(value, allow_nan=False, sort_keys=True, separators=(',', ':')).encode() + b'\n'


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, 'malformed')
            result[key] = value
        return result
    def invalid(_):
        raise Refusal('malformed')
    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)
    except (ValueError, UnicodeError):
        raise Refusal('malformed') from None


def safe_fd(fd, directory=False):
    value = os.fstat(fd)
    need(value.st_uid == os.getuid() and (stat.S_ISDIR(value.st_mode) if directory
         else stat.S_ISREG(value.st_mode)), 'storage')
    need(stat.S_IMODE(value.st_mode) == (0o700 if directory else 0o600), 'storage')
    if not directory:
        need(value.st_nlink == 1 and value.st_size <= 16384, 'storage')


class AttemptGate:
    """One stable state directory per operation. Initiation fence never removed."""
    def __init__(self, root, clock=time.monotonic):
        self.root, self.clock = Path(root), clock
        self.fd = self.lock = None
        self.state = None

    def __enter__(self):
        try:
            need(self.root.absolute() == self.root.resolve(), 'storage')
            self.fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
            safe_fd(self.fd, directory=True)
            self.lock = os.open('attempt.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW |
                                os.O_NONBLOCK | os.O_CLOEXEC, 0o600, dir_fd=self.fd)
            safe_fd(self.lock)
            try:
                fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise Refusal('busy') from None
            current = self.clock()
            need(type(current) in (int, float) and math.isfinite(current), 'deadline')
            try:
                self.state = self.read('attempt.json')
            except FileNotFoundError:
                need(set(os.listdir(self.fd)) == {'attempt.lock'}, 'state')
                self.state = dict(schema='tackle-neutral-attempt/1', request_sha256=REQUEST_SHA,
                                  started=current, last=current, deadline=current + LIMIT,
                                  initiated=0, outcome='prepared')
                self.write()
            self.validate(current)
            return self
        except Refusal:
            self.__exit__(None, None, None)
            raise
        except (OSError, ValueError, TypeError, KeyError):
            self.__exit__(None, None, None)
            raise Refusal('storage') from None

    def __exit__(self, *_):
        for name in ('lock', 'fd'):
            value = getattr(self, name)
            if value is not None:
                os.close(value)
                setattr(self, name, None)

    def read(self, name):
        fd = os.open(name, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=self.fd)
        try:
            safe_fd(fd)
            return strict_json(os.read(fd, 16385))
        finally:
            os.close(fd)

    def validate(self, current):
        value = self.state
        need(isinstance(value, dict) and set(value) == {'schema', 'request_sha256',
             'started', 'last', 'deadline', 'initiated', 'outcome'}, 'state')
        need(value['schema'] == 'tackle-neutral-attempt/1' and value['request_sha256'] == REQUEST_SHA, 'state')
        need(all(type(value[k]) in (int, float) and math.isfinite(value[k])
                 for k in ('started', 'last', 'deadline')), 'state')
        need(value['deadline'] == value['started'] + LIMIT and
             value['started'] <= value['last'] <= current < value['deadline'], 'deadline')
        need(type(value['initiated']) is int and value['initiated'] in (0, 1) and
             value['outcome'] in ('prepared', 'initiated', 'uncertain', 'completed'), 'state')

    def write(self):
        # An interrupted rewrite leaves an exclusive temp fence and refuses reuse.
        fd = os.open('attempt.next', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW |
                     os.O_CLOEXEC, 0o600, dir_fd=self.fd)
        try:
            raw = encoded(self.state)
            with os.fdopen(fd, 'wb', closefd=False) as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(fd)
        finally:
            os.close(fd)
        os.rename('attempt.next', 'attempt.json', src_dir_fd=self.fd, dst_dir_fd=self.fd)
        os.fsync(self.fd)

    def remaining(self):
        current = self.clock()
        self.validate(current)
        self.state['last'] = current
        self.write()
        return self.state['deadline'] - current

    def initiate(self):
        self.remaining()
        need(self.state['initiated'] == 0, 'consumed')
        # O_EXCL is the final persistent gate, before any possible request.
        try:
            fd = os.open('initiated', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW |
                         os.O_CLOEXEC, 0o600, dir_fd=self.fd)
        except FileExistsError:
            raise Refusal('consumed') from None
        try:
            os.write(fd, b'one initiated unit; no retry or refund\n')
            os.fsync(fd)
        finally:
            os.close(fd)
        os.fsync(self.fd)
        self.state.update(initiated=1, outcome='initiated')
        self.write()

    def finalize(self, outcome):
        need(outcome in ('uncertain', 'completed') and self.state['initiated'] == 1, 'state')
        self.state['outcome'] = outcome
        self.write()


class TerminalConsumer:
    """Incremental SSE: unexpected sensitive bytes are never retained or hashed."""
    def __init__(self):
        self.buffer = b''
        self.total = 0
        self.result = None
        self.failed = False
        self.search_from = 0

    def feed(self, raw):
        need(not self.failed, 'stream_poisoned')
        try:
            self._feed(raw)
        except BaseException:
            self.failed = True
            self.result = None
            self.buffer = b''
            raise

    def _feed(self, raw):
        need(isinstance(raw, bytes), 'stream')
        self.total += len(raw)
        need(self.total <= MAX_STREAM, 'stream_limit')
        self.buffer += raw
        # Normalize CRLF only once a complete frame is present, including splits.
        while True:
            match = re.compile(b'\r?\n\r?\n').search(self.buffer, self.search_from)
            if match is None:
                self.search_from = max(0, len(self.buffer) - 3)
                break
            frame, self.buffer = self.buffer[:match.start()], self.buffer[match.end():]
            self.search_from = 0
            need(len(frame) <= MAX_EVENT, 'event_limit')
            self.frame(frame.replace(b'\r\n', b'\n'))
        need(len(self.buffer) <= MAX_EVENT, 'event_limit')

    def frame(self, frame):
        data = []
        for line in frame.split(b'\n'):
            if line.startswith(b'data:'):
                data.append(line[5:].lstrip(b' '))
            else:
                need(not line or line.startswith((b'event:', b':')), 'stream')
        if not data:
            return
        raw = b'\n'.join(data)
        if raw == b'[DONE]':
            need(self.result is not None, 'nonterminal')
            return
        event = strict_json(raw)
        need(isinstance(event, dict) and isinstance(event.get('type'), str), 'stream')
        kind = event['type']
        need(kind not in ('response.failed', 'response.incomplete', 'error'), 'remote_failure')
        if kind == 'response.completed':
            need(self.result is None, 'duplicate_terminal')
            response = event.get('response')
            need(isinstance(response, dict) and response.get('status') == 'completed'
                 and response.get('model') == 'gpt-5.6-luna', 'terminal_binding')
            output = response.get('output')
            need(isinstance(output, list) and len(output) > 0, 'output')
            texts = []
            for item in output:
                need(isinstance(item, dict) and item.get('type') in ('message', 'reasoning'), 'unexpected_tool')
                if item['type'] == 'reasoning':
                    continue
                need(item.get('role') == 'assistant' and isinstance(item.get('content'), list), 'output')
                for content in item['content']:
                    need(isinstance(content, dict) and content.get('type') == 'output_text'
                         and isinstance(content.get('text'), str), 'output')
                    texts.append(content['text'])
            text = ''.join(texts)
            need(text.strip() == 'READY' and len(text) <= 32, 'unexpected_output')
            usage = response.get('usage')
            if usage is not None:
                need(isinstance(usage, dict), 'usage')
                usage = {key: usage[key] for key in ('input_tokens', 'output_tokens', 'total_tokens')
                         if key in usage}
                need(all(type(v) is int and 0 <= v <= 10000000 for v in usage.values()), 'usage')
            effort = response.get('reasoning', {}).get('effort', 'n/a')
            need(effort in ('n/a', 'xhigh'), 'terminal_binding')
            self.result = dict(status='completed', text='READY', model='gpt-5.6-luna',
                               effort=effort, usage=usage if usage else 'n/a', cost_usd='n/a')
        else:
            need(self.result is None, 'after_terminal')
            need(kind.startswith(('response.created', 'response.in_progress', 'response.output_',
                                  'response.content_', 'response.reasoning_', 'response.completed')), 'stream')
            item = event.get('item')
            if item is not None:
                need(isinstance(item, dict) and item.get('type') in ('message', 'reasoning'), 'unexpected_tool')
            # Delta/partial event bodies are intentionally discarded, never hashed.

    def finish(self):
        need(not self.failed and not self.buffer.strip() and self.result is not None, 'nonterminal')
        return self.result


class Admission:
    """Qualification only. There is no live-admission factory or policy observer."""
    def __init__(self):
        self.mode = 'qualification'

    @classmethod
    def for_qualification(cls):
        return cls()


class QualificationSender:
    """Concrete synthetic data-only effect; no injected executable callback."""
    def __init__(self, fail=False):
        need(type(fail) is bool, 'fixture')
        self.fail = fail
        self.calls = []

    def send(self, body, seconds):
        self.calls.append((body, seconds))
        if self.fail:
            raise Refusal('synthetic_failure')
        return dict(status='completed')


def dispatch(gate, admission, sender):
    need(type(admission) is Admission and admission.mode == 'qualification', 'admission_unavailable')
    need(type(sender) is QualificationSender, 'live_admission_unavailable')
    seconds = gate.remaining()
    gate.initiate()
    try:
        result = sender.send(REQUEST, seconds)
        gate.remaining()
        need(isinstance(result, dict) and result.get('status') == 'completed', 'nonterminal')
        gate.finalize('completed')
        return result
    except BaseException:
        with contextlib.suppress(Exception):
            gate.finalize('uncertain')
        raise Refusal('uncertain') from None


def single_https_request(bearer, body, seconds):
    """Transport component only; not accepted as an activatable live driver.

The caller's independent supervisor must enforce its absolute deadline. Socket
timeouts alone do not prove that supervisor. No proxies, redirects or retries.
"""
    need(body == REQUEST and isinstance(bearer, str) and
         re.fullmatch(r'[A-Za-z0-9._~+/-]+=*', bearer), 'wire')
    need(type(seconds) in (int, float) and math.isfinite(seconds) and 0 < seconds <= LIMIT, 'deadline')
    deadline = time.monotonic() + seconds
    connection = http.client.HTTPSConnection('api.openai.com', timeout=seconds,
                                             context=ssl.create_default_context())
    try:
        connection.request('POST', '/v1/responses', body=body, headers={
            'Authorization': 'Bearer ' + bearer, 'Content-Type': 'application/json',
            'Accept': 'text/event-stream'})
        response = connection.getresponse()
        need(response.status == 200 and response.getheader('Content-Type', '').split(';')[0]
             == 'text/event-stream', 'http_refused')
        consumer = TerminalConsumer()
        while True:
            remaining = deadline - time.monotonic()
            need(remaining > 0, 'deadline')
            if connection.sock is not None:
                connection.sock.settimeout(remaining)
            raw = response.read(8192)
            need(time.monotonic() < deadline, 'deadline')
            if not raw:
                break
            consumer.feed(raw)
        return consumer.finish()
    except Refusal:
        raise
    except Exception:
        raise Refusal('transport_uncertain') from None
    finally:
        connection.close()
