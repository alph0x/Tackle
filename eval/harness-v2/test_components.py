"""Unit tests for the T-05 components: credscan, usage, broker.

Write scope note: this file, together with broker.py, credscan.py and usage.py, is the
component worker's entire write scope for T-05. It never imports adapters.py, harness.py,
fake_agent.py or test_harness.py -- those belong to the coordinator's parallel task.

Run only this file:
    python3 -m unittest discover -s eval/harness-v2 -p 'test_components.py' -v

Every secret used below is generated at run time (secrets.token_urlsafe /
secrets.token_hex); none is a literal that a repository guard would flag, and no
credential value is ever asserted with assertIn/assertEqual/assertNotIn (which would
echo it into a failure message) -- assertFalse/assertTrue with a plain message is used
instead wherever a secret is involved.
"""

import http.client
import json
import secrets
import socket
import ssl
import threading
import time
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

# Import guard: if a module under test does not exist yet (red phase) or fails to
# import, each test that needs it still runs (and fails on its own -- an AttributeError
# on None) instead of one blanket collection error hiding the rest.
try:
    import credscan
except ImportError:
    credscan = None

try:
    import usage
except ImportError:
    usage = None

try:
    import broker as broker_module
except ImportError:
    broker_module = None


def _secret(n=24):
    return secrets.token_urlsafe(n)


# ---------------------------------------------------------------------------
# credscan.py
# ---------------------------------------------------------------------------

class CredscanEncodingsTests(unittest.TestCase):
    def test_all_forms_present_and_correct(self):
        # A value with a character that base64/hex encoders leave untouched but that
        # urllib.parse.quote(safe='') and JSON string escaping both transform, so every
        # clause of the spec is actually exercised (not vacuously equal to the input).
        value = _secret(16) + '"' + _secret(8)
        raw = value.encode('utf-8')

        import base64 as _b64
        std = _b64.b64encode(raw).decode('ascii')
        url = _b64.urlsafe_b64encode(raw).decode('ascii')
        expected = {
            value,
            std, std.rstrip('='),
            url, url.rstrip('='),
            raw.hex(), raw.hex().upper(),
            urllib.parse.quote(value, safe=''),
            json.dumps(value)[1:-1],
        }
        result = credscan.encodings(value)
        self.assertIsInstance(result, list)
        self.assertEqual(set(result), expected)
        # Padding and quoting must actually differ from the raw value for this input,
        # otherwise the assertion above would pass even if encodings() were broken.
        self.assertIn('=', std)
        self.assertNotEqual(urllib.parse.quote(value, safe=''), value)
        self.assertNotEqual(json.dumps(value)[1:-1], value)

    def test_deduplicated(self):
        # Chosen so std and urlsafe base64 coincide (neither alphabet-distinguishing
        # character '+/-_' appears in the encoded output), forcing a real collision.
        value = 'plain ascii value, no slashes here 12345'
        result = credscan.encodings(value)
        self.assertEqual(len(result), len(set(result)))
        import base64 as _b64
        raw = value.encode('utf-8')
        std = _b64.b64encode(raw).decode('ascii')
        url = _b64.urlsafe_b64encode(raw).decode('ascii')
        self.assertEqual(std, url)  # confirms the collision actually happens
        self.assertLess(len(result), 9)


class CredscanSecretValuesTests(unittest.TestCase):
    def test_pretty_json_leaves_only_long_strings(self):
        secret_a = _secret(16)
        secret_b = _secret(20)
        payload = json.dumps({
            'nested': {'token': secret_a, 'note': 'short'},
            'list': [secret_b, 'x', 42, None, True],
        }, indent=2).encode('utf-8')
        result = credscan.secret_values(payload)
        self.assertEqual(set(result), {secret_a, secret_b})
        # braces/indentation/punctuation must never show up as a "secret" on their own
        for value in result:
            self.assertNotIn('{', value)
            self.assertNotIn('\n', value)

    def test_json_with_no_long_leaves_falls_back_to_whole_stripped_content(self):
        payload = b'  {"a": 1, "b": true}  \n'
        result = credscan.secret_values(payload)
        self.assertEqual(result, ['{"a": 1, "b": true}'])

    def test_non_json_uses_stripped_utf8_content(self):
        secret = _secret(20)
        payload = ('\n  ' + secret + '  \n').encode('utf-8')
        result = credscan.secret_values(payload)
        self.assertEqual(result, [secret])

    def test_values_shorter_than_8_are_dropped(self):
        payload = b'   short   '
        result = credscan.secret_values(payload)
        self.assertEqual(result, [])

    def test_json_leaf_exactly_16_chars_is_kept_15_is_not(self):
        exactly_16 = 'a' * 16
        only_15 = 'b' * 15
        payload = json.dumps({'k1': exactly_16, 'k2': only_15}).encode('utf-8')
        result = credscan.secret_values(payload)
        self.assertEqual(result, [exactly_16])

    def test_deduplicated_and_sorted_by_length_descending(self):
        longer = _secret(24)   # secrets.token_urlsafe(24) -> 32 chars
        shorter = _secret(16)  # secrets.token_urlsafe(16) -> 22 chars, still >= 16
        payload = json.dumps([longer, shorter, longer]).encode('utf-8')
        result = credscan.secret_values(payload)
        self.assertEqual(result, [longer, shorter])


class CredscanFindTests(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmpdir = Path(self._tmp.name)

    def _write_credential(self, secret_value):
        cred_path = self.tmpdir / 'real' / 'cred.json'
        cred_path.parent.mkdir(parents=True, exist_ok=True)
        cred_path.write_text(json.dumps({'token': secret_value}))
        return cred_path

    def test_finds_every_encoded_copy_and_the_credential_path(self):
        secret_value = _secret(24)
        cred_path = self._write_credential(secret_value)
        forms = credscan.encodings(secret_value)
        texts = {}
        for i, form in enumerate(forms):
            texts['loc:%02d' % i] = 'noise-before ' + form + ' -noise-after'
        texts['prompt:path'] = 'the file was at ' + str(cred_path)
        texts['file:clean.md'] = 'nothing sensitive here at all'

        result = credscan.find(cred_path, texts)
        expected_hits = sorted(set(texts.keys()) - {'file:clean.md'})
        self.assertEqual(result, expected_hits)
        self.assertNotIn('file:clean.md', result)

    def test_bytes_text_searched_as_bytes_and_as_utf8(self):
        secret_value = _secret(24)
        cred_path = self._write_credential(secret_value)
        as_bytes = ('payload: ' + secret_value).encode('utf-8')
        clean_bytes = b'\xff\xfe totally unrelated binary noise'
        result = credscan.find(cred_path, {'file:bin': as_bytes, 'file:other-bin': clean_bytes})
        self.assertEqual(result, ['file:bin'])

    def test_bytes_location_with_invalid_utf8_found_via_replacement_decode(self):
        # 0xFF is not a valid UTF-8 byte in any position, so secret_values() takes the
        # "decode with replacement" branch and the resulting secret value contains
        # U+FFFD. U+FFFD's own UTF-8 encoding (EF BF BD) does not equal the raw 0xFF
        # byte, so a *direct* byte search for that needle cannot find it in a location
        # whose bytes still hold the original 0xFF -- only decoding the location the
        # same way (UTF-8 with replacement) and comparing as text can. This exercises
        # that fallback path specifically.
        secret_tail = _secret(20)
        raw_credential = b'\xff' + secret_tail.encode('utf-8')
        cred_path = self.tmpdir / 'binary-ish' / 'cred'
        cred_path.parent.mkdir(parents=True, exist_ok=True)
        cred_path.write_bytes(raw_credential)

        location_bytes = b'noise ' + raw_credential + b' more-noise'
        result = credscan.find(cred_path, {'file:raw': location_bytes})
        self.assertEqual(result, ['file:raw'])

    def test_resolved_symlink_path_is_also_checked(self):
        secret_value = _secret(24)
        cred_path = self._write_credential(secret_value)
        link_dir = self.tmpdir / 'link'
        link_dir.symlink_to(cred_path.parent, target_is_directory=True)
        symlink_cred_path = link_dir / 'cred.json'
        self.assertTrue(symlink_cred_path.is_file())

        real_form = str(cred_path.resolve())
        symlink_form = str(symlink_cred_path)
        texts = {
            'sees-real-path': 'note: ' + real_form,
            'sees-symlink-path': 'note: ' + symlink_form,
            'sees-neither': 'nothing to see here',
        }
        result = credscan.find(symlink_cred_path, texts)
        self.assertEqual(result, ['sees-real-path', 'sees-symlink-path'])

    def test_locations_sorted(self):
        secret_value = _secret(24)
        cred_path = self._write_credential(secret_value)
        texts = {
            'zeta': secret_value,
            'alpha': secret_value,
            'mu': 'clean',
        }
        result = credscan.find(cred_path, texts)
        self.assertEqual(result, ['alpha', 'zeta'])

    def test_never_returns_a_secret_value(self):
        secret_value = _secret(24)
        cred_path = self._write_credential(secret_value)
        result = credscan.find(cred_path, {'loc': secret_value})
        for name in result:
            self.assertFalse(secret_value in name, 'find() must return only location names')

    def test_missing_credential_file_raises(self):
        missing = self.tmpdir / 'does' / 'not' / 'exist.json'
        with self.assertRaises(OSError):
            credscan.find(missing, {'loc': 'anything'})


# ---------------------------------------------------------------------------
# usage.py -- claude_code_transcript
# ---------------------------------------------------------------------------

def _usage_row(request_id, output_tokens, input_tokens=10, cache_creation=0, cache_read=0,
               model='claude-x'):
    return json.dumps({
        'message': {
            'model': model,
            'usage': {
                'input_tokens': input_tokens,
                'cache_creation_input_tokens': cache_creation,
                'cache_read_input_tokens': cache_read,
                'output_tokens': output_tokens,
            },
        },
        'requestId': request_id,
    })


class UsageClaudeCodeTranscriptTests(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmpdir = Path(self._tmp.name)

    def _write(self, name, lines):
        path = self.tmpdir / name
        path.write_text('\n'.join(lines) + '\n')
        return path

    def test_no_usage_rows_gives_na_and_zero_requests(self):
        path = self._write('t1.jsonl', [
            json.dumps({'message': {'role': 'user', 'content': 'hi'}}),
            json.dumps({'type': 'summary'}),
        ])
        result = usage.claude_code_transcript(path)
        self.assertEqual(result['tokens_in'], 'n/a')
        self.assertEqual(result['tokens_out'], 'n/a')
        self.assertEqual(result['cache_read'], 'n/a')
        self.assertEqual(result['cache_write'], 'n/a')
        self.assertEqual(result['requests'], 0)
        self.assertEqual(result['models'], [])
        self.assertEqual(result['unkeyed'], 0)
        self.assertEqual(result['bad_lines'], 0)
        self.assertEqual(result['reason'], 'no usage rows')

    def test_out_of_order_duplicate_requestid_keeps_largest_output(self):
        # Row order deliberately not monotonic: 30 then 90 then 10 for the same id.
        path = self._write('t2.jsonl', [
            _usage_row('req-1', output_tokens=30, input_tokens=5),
            _usage_row('req-1', output_tokens=90, input_tokens=7, cache_creation=2, cache_read=3),
            _usage_row('req-1', output_tokens=10, input_tokens=1),
            _usage_row('req-2', output_tokens=40, input_tokens=11, cache_read=4),
        ])
        result = usage.claude_code_transcript(path)
        self.assertEqual(result['reason'], None)
        self.assertEqual(result['requests'], 2)
        # Only the max-output row of req-1 (90 out, 7 in, 2 cw, 3 cr) should count,
        # plus req-2's single row (40 out, 11 in, 0 cw, 4 cr).
        self.assertEqual(result['tokens_out'], 90 + 40)
        self.assertEqual(result['tokens_in'], (7 + 2 + 3) + (11 + 0 + 4))
        self.assertEqual(result['cache_write'], 2 + 0)
        self.assertEqual(result['cache_read'], 3 + 4)

    def test_unkeyed_row_counted_and_forces_na_without_raising(self):
        keyed = _usage_row('req-1', output_tokens=10)
        unkeyed_row = json.dumps({'message': {'model': 'claude-x', 'usage': {
            'input_tokens': 1, 'output_tokens': 1,
            'cache_creation_input_tokens': 0, 'cache_read_input_tokens': 0}}})
        path = self._write('t3.jsonl', [keyed, unkeyed_row])
        result = usage.claude_code_transcript(path)
        self.assertEqual(result['unkeyed'], 1)
        self.assertEqual(result['bad_lines'], 0)
        self.assertEqual(result['tokens_in'], 'n/a')
        self.assertEqual(result['tokens_out'], 'n/a')
        self.assertIsNotNone(result['reason'])
        self.assertEqual(result['requests'], 1)  # the keyed row still forms one group

    def test_bad_line_counted_and_forces_na_without_raising(self):
        keyed = _usage_row('req-1', output_tokens=10)
        path = self._write('t4.jsonl', [keyed, 'not-json-at-all{{{'])
        result = usage.claude_code_transcript(path)
        self.assertEqual(result['bad_lines'], 1)
        self.assertEqual(result['unkeyed'], 0)
        self.assertEqual(result['tokens_in'], 'n/a')
        self.assertEqual(result['tokens_out'], 'n/a')
        self.assertIsNotNone(result['reason'])

    def test_blank_lines_skipped_not_counted_as_bad(self):
        path = self._write('t5.jsonl', [
            '',
            '   ',
            _usage_row('req-1', output_tokens=5),
            '',
        ])
        result = usage.claude_code_transcript(path)
        self.assertEqual(result['bad_lines'], 0)
        self.assertEqual(result['reason'], None)
        self.assertEqual(result['requests'], 1)

    def test_models_sorted_and_deduplicated(self):
        path = self._write('t6.jsonl', [
            _usage_row('req-1', output_tokens=1, model='zeta-model'),
            _usage_row('req-2', output_tokens=1, model='alpha-model'),
            _usage_row('req-3', output_tokens=1, model='alpha-model'),
        ])
        result = usage.claude_code_transcript(path)
        self.assertEqual(result['models'], ['alpha-model', 'zeta-model'])


class UsageSubagentsSessionsTests(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.home = Path(self._tmp.name)

    def _project_dir(self):
        d = self.home / '.claude' / 'projects' / 'proj-1'
        d.mkdir(parents=True, exist_ok=True)
        return d

    def test_two_subagent_transcripts_counted_apart(self):
        proj = self._project_dir()
        sub_dir = proj / 'session-a' / 'subagents'
        sub_dir.mkdir(parents=True)
        (sub_dir / 'agent-one.jsonl').write_text(_usage_row('r1', output_tokens=10) + '\n')
        (sub_dir / 'agent-one.meta.json').write_text(json.dumps({'description': 'role-one',
                                                                   'model': 'model-a'}))
        (sub_dir / 'agent-two.jsonl').write_text(_usage_row('r2', output_tokens=99) + '\n')
        (sub_dir / 'agent-two.meta.json').write_text(json.dumps({'agentType': 'type-two'}))

        result = usage.claude_code_subagents(self.home)
        self.assertEqual([r['agent_id'] for r in result], ['one', 'two'])
        one, two = result
        self.assertEqual(one['role'], 'role-one')
        self.assertEqual(one['model_requested'], 'model-a')
        self.assertEqual(one['usage']['tokens_out'], 10)
        self.assertEqual(two['role'], 'type-two')
        self.assertEqual(two['model_requested'], 'n/a')
        self.assertEqual(two['usage']['tokens_out'], 99)
        # Counted apart: agent one's numbers must not leak into agent two's.
        self.assertNotEqual(one['usage']['tokens_out'], two['usage']['tokens_out'])

    def test_missing_meta_json_gives_na_and_never_raises(self):
        proj = self._project_dir()
        sub_dir = proj / 'session-b' / 'subagents'
        sub_dir.mkdir(parents=True)
        (sub_dir / 'agent-lonely.jsonl').write_text(_usage_row('r1', output_tokens=1) + '\n')
        result = usage.claude_code_subagents(self.home)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['role'], 'n/a')
        self.assertEqual(result[0]['model_requested'], 'n/a')

    def test_sessions_lists_top_level_files_sorted_and_excludes_subagents(self):
        proj = self._project_dir()
        (proj / 'session-zzz.jsonl').write_text(_usage_row('r1', output_tokens=3) + '\n')
        (proj / 'session-aaa.jsonl').write_text(_usage_row('r2', output_tokens=7) + '\n')
        sub_dir = proj / 'session-aaa' / 'subagents'
        sub_dir.mkdir(parents=True)
        (sub_dir / 'agent-x.jsonl').write_text(_usage_row('r3', output_tokens=999) + '\n')

        result = usage.claude_code_sessions(self.home)
        self.assertEqual([r['session_id'] for r in result], ['session-aaa', 'session-zzz'])
        totals = {r['session_id']: r['usage']['tokens_out'] for r in result}
        self.assertEqual(totals['session-aaa'], 7)
        self.assertEqual(totals['session-zzz'], 3)


class UsageClaudeCodeResultTests(unittest.TestCase):
    def test_stream_json_last_result_wins(self):
        lines = [
            json.dumps({'type': 'assistant', 'message': {'content': 'partial'}}),
            json.dumps({'type': 'result', 'session_id': 'sess-1',
                        'usage': {'input_tokens': 1, 'output_tokens': 2}}),
            'not-json-line',
            json.dumps({'type': 'result', 'session_id': 'sess-2',
                        'usage': {'input_tokens': 100, 'cache_creation_input_tokens': 5,
                                  'cache_read_input_tokens': 7, 'output_tokens': 200}}),
        ]
        stdout = ('\n'.join(lines) + '\n').encode('utf-8')
        result = usage.claude_code_result(stdout)
        self.assertEqual(result['session_id'], 'sess-2')
        self.assertEqual(result['tokens_in'], 100 + 5 + 7)
        self.assertEqual(result['tokens_out'], 200)

    def test_whole_json_document_result(self):
        doc = {
            'type': 'result',
            'session_id': 'sess-solo',
            'usage': {'input_tokens': 3, 'output_tokens': 4},
        }
        stdout = json.dumps(doc, indent=2).encode('utf-8')
        result = usage.claude_code_result(stdout)
        self.assertEqual(result['session_id'], 'sess-solo')
        self.assertEqual(result['tokens_in'], 3)
        self.assertEqual(result['tokens_out'], 4)

    def test_absent_usage_gives_na(self):
        stdout = json.dumps({'type': 'other', 'session_id': 'sess-x'}).encode('utf-8')
        result = usage.claude_code_result(stdout)
        self.assertEqual(result['tokens_in'], 'n/a')
        self.assertEqual(result['tokens_out'], 'n/a')
        self.assertEqual(result['session_id'], 'n/a')


class UsageCodexTurnsTests(unittest.TestCase):
    def test_two_turn_stream_summed(self):
        lines = [
            json.dumps({'type': 'thread.started', 'thread_id': 'thread-abc'}),
            json.dumps({'type': 'turn.completed',
                        'usage': {'input_tokens': 10, 'cached_input_tokens': 2, 'output_tokens': 5}}),
            'garbage-not-json',
            json.dumps({'type': 'turn.completed',
                        'usage': {'input_tokens': 20, 'cached_input_tokens': 3, 'output_tokens': 8}}),
        ]
        stdout = ('\n'.join(lines) + '\n').encode('utf-8')
        result = usage.codex_turns(stdout)
        self.assertEqual(result['turns'], 2)
        self.assertEqual(result['tokens_in'], 30)
        self.assertEqual(result['cache_read'], 5)
        self.assertEqual(result['tokens_out'], 13)
        self.assertEqual(result['thread_id'], 'thread-abc')

    def test_absent_usage_gives_na(self):
        stdout = json.dumps({'type': 'thread.started', 'thread_id': 'only-thread'}).encode('utf-8')
        result = usage.codex_turns(stdout)
        self.assertEqual(result['tokens_in'], 'n/a')
        self.assertEqual(result['tokens_out'], 'n/a')
        self.assertEqual(result['cache_read'], 'n/a')
        self.assertEqual(result['turns'], 'n/a')
        self.assertEqual(result['thread_id'], 'only-thread')

    def test_completely_empty_stream_gives_na_thread_id_too(self):
        result = usage.codex_turns(b'')
        self.assertEqual(result['thread_id'], 'n/a')
        self.assertEqual(result['turns'], 'n/a')


# ---------------------------------------------------------------------------
# broker.py
# ---------------------------------------------------------------------------

class _EchoUpstreamHandler(BaseHTTPRequestHandler):
    """Fake loopback upstream: records every request it receives and answers with a
    small configurable response. Never contacted over a real network -- the test that
    starts it binds 127.0.0.1:0 itself."""

    protocol_version = 'HTTP/1.1'

    def log_message(self, fmt, *args):
        pass

    def _handle(self):
        length = self.headers.get('Content-Length')
        body = self.rfile.read(int(length)) if length else b''
        record = {
            'method': self.command,
            'path': self.path,
            'headers': {k.lower(): v for k, v in self.headers.items()},
            'body': body,
        }
        self.server.requests_seen.append(record)
        status = getattr(self.server, 'response_status', 200)
        resp_body = getattr(self.server, 'response_body', b'ok')
        resp_headers = getattr(self.server, 'response_headers', {})
        self.send_response(status)
        for key, value in resp_headers.items():
            self.send_header(key, value)
        self.send_header('Content-Length', str(len(resp_body)))
        self.end_headers()
        self.wfile.write(resp_body)

    do_GET = _handle
    do_POST = _handle
    do_PUT = _handle
    do_DELETE = _handle
    do_PATCH = _handle


class _StreamingUpstreamHandler(BaseHTTPRequestHandler):
    """Fake loopback upstream that sends one chunk, waits on an event the test
    controls, then sends a second chunk -- used to prove the broker forwards each
    chunk as it arrives instead of buffering the whole response."""

    protocol_version = 'HTTP/1.1'

    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        chunk1 = self.server.chunk1
        chunk2 = self.server.chunk2
        self.send_response(200)
        self.send_header('Transfer-Encoding', 'chunked')
        self.end_headers()
        self.wfile.write(('%x\r\n' % len(chunk1)).encode('ascii') + chunk1 + b'\r\n')
        self.wfile.flush()
        self.server.chunk1_sent.set()
        released = self.server.release_chunk2.wait(timeout=3)
        self.server.chunk2_sent.set()
        if released:
            self.wfile.write(('%x\r\n' % len(chunk2)).encode('ascii') + chunk2 + b'\r\n')
        self.wfile.write(b'0\r\n\r\n')
        self.wfile.flush()


def _start_upstream(handler_cls=_EchoUpstreamHandler, **attrs):
    server = ThreadingHTTPServer(('127.0.0.1', 0), handler_cls)
    server.requests_seen = []
    for key, value in attrs.items():
        setattr(server, key, value)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def _stop_server(server, thread):
    server.shutdown()
    server.server_close()
    thread.join(timeout=3)


def _raw_request(method, target, host_header, extra_headers, body=b''):
    headers = dict(extra_headers)
    headers['Host'] = host_header
    headers['Content-Length'] = str(len(body))
    headers['Connection'] = 'close'
    header_text = ''.join('{}: {}\r\n'.format(k, v) for k, v in headers.items())
    request_line = '{} {} HTTP/1.1\r\n'.format(method, target)
    return (request_line + header_text + '\r\n').encode('latin-1') + body


def _raw_exchange(host, port, request_bytes, timeout=2):
    sock = socket.create_connection((host, port), timeout=timeout)
    try:
        sock.sendall(request_bytes)
        chunks = []
        while True:
            piece = sock.recv(4096)
            if not piece:
                break
            chunks.append(piece)
        return b''.join(chunks)
    finally:
        sock.close()


def _status_of(raw_response):
    first_line = raw_response.split(b'\r\n', 1)[0]
    parts = first_line.split(b' ', 2)
    return int(parts[1]) if len(parts) >= 2 else None


class BrokerValidationTests(unittest.TestCase):
    def _make(self, upstream):
        return broker_module.Broker(credential=_secret(), upstream=upstream, token=_secret())

    def test_valid_origins_accepted(self):
        self._make('http://example-host')
        self._make('https://example-host:8443')
        self._make('http://127.0.0.1:9')

    def test_rejects_bad_scheme(self):
        with self.assertRaises(ValueError):
            self._make('ftp://example-host')

    def test_rejects_missing_host(self):
        with self.assertRaises(ValueError):
            self._make('http://')

    def test_rejects_path(self):
        with self.assertRaises(ValueError):
            self._make('http://example-host/some/path')

    def test_rejects_query(self):
        with self.assertRaises(ValueError):
            self._make('http://example-host?x=1')

    def test_rejects_fragment(self):
        with self.assertRaises(ValueError):
            self._make('http://example-host#frag')

    def test_rejects_userinfo(self):
        with self.assertRaises(ValueError):
            self._make('http://user:pass@example-host')

    def test_rejects_bare_string(self):
        with self.assertRaises(ValueError):
            self._make('not-a-url-at-all')

    def test_docstring_states_the_three_guarantees(self):
        doc = broker_module.Broker.__doc__ or ''
        self.assertIn('host-side only', doc)
        self.assertIn('never reaches the participant', doc)
        self.assertIn('one fixed upstream origin', doc)


class _BrokerTestBase(unittest.TestCase):
    def setUp(self):
        self.upstream, self.upstream_thread = _start_upstream()
        self.addCleanup(_stop_server, self.upstream, self.upstream_thread)
        self.upstream_base = 'http://127.0.0.1:%d' % self.upstream.server_address[1]
        self.token = _secret(24)
        self.credential = _secret(24)
        self.broker = broker_module.Broker(
            credential=self.credential, upstream=self.upstream_base, token=self.token)
        self.broker_base = self.broker.start()
        self.addCleanup(self.broker.stop)
        parsed = urllib.parse.urlsplit(self.broker_base)
        self.broker_host = parsed.hostname
        self.broker_port = parsed.port


class BrokerRejectionTests(_BrokerTestBase):
    def test_wrong_token_rejected_and_not_forwarded(self):
        conn = http.client.HTTPConnection(self.broker_host, self.broker_port, timeout=2)
        conn.request('GET', '/ok', headers={'Authorization': 'Bearer ' + _secret(24)})
        resp = conn.getresponse()
        resp.read()
        conn.close()
        self.assertEqual(resp.status, 403)
        self.assertEqual(self.upstream.requests_seen, [])

    def test_missing_token_header_rejected(self):
        conn = http.client.HTTPConnection(self.broker_host, self.broker_port, timeout=2)
        conn.request('GET', '/ok')
        resp = conn.getresponse()
        resp.read()
        conn.close()
        self.assertEqual(resp.status, 403)
        self.assertEqual(self.upstream.requests_seen, [])

    def test_wrong_host_header_rejected_with_valid_token(self):
        raw = _raw_request('GET', '/ok', host_header='definitely-not-the-broker:1',
                            extra_headers={'Authorization': 'Bearer ' + self.token})
        response = _raw_exchange(self.broker_host, self.broker_port, raw)
        self.assertEqual(_status_of(response), 403)
        self.assertEqual(self.upstream.requests_seen, [])

    def test_absolute_uri_target_rejected_with_valid_token_and_host(self):
        own_host = '{}:{}'.format(self.broker_host, self.broker_port)
        raw = _raw_request('GET', 'http://somewhere-else/x', host_header=own_host,
                            extra_headers={'Authorization': 'Bearer ' + self.token})
        response = _raw_exchange(self.broker_host, self.broker_port, raw)
        self.assertEqual(_status_of(response), 403)
        self.assertEqual(self.upstream.requests_seen, [])

    def test_double_slash_target_rejected_with_valid_token_and_host(self):
        # Regression guard: some stdlib patch levels normalize a leading "//" in the
        # request line down to a single "/" by the time self.path is available, so the
        # broker must inspect the raw request line for this check, not self.path.
        own_host = '{}:{}'.format(self.broker_host, self.broker_port)
        raw = _raw_request('GET', '//evil-target', host_header=own_host,
                            extra_headers={'Authorization': 'Bearer ' + self.token})
        response = _raw_exchange(self.broker_host, self.broker_port, raw)
        self.assertEqual(_status_of(response), 403)
        self.assertEqual(self.upstream.requests_seen, [])

    def test_connect_method_rejected_and_logged(self):
        own_host = '{}:{}'.format(self.broker_host, self.broker_port)
        raw = _raw_request('CONNECT', 'somewhere-else.example:443', host_header=own_host,
                            extra_headers={'Authorization': 'Bearer ' + self.token})
        response = _raw_exchange(self.broker_host, self.broker_port, raw)
        self.assertEqual(_status_of(response), 403)
        self.assertEqual(self.upstream.requests_seen, [])
        self.assertEqual(len(self.broker.log), 1)
        self.assertEqual(self.broker.log[0]['method'], 'CONNECT')
        self.assertEqual(self.broker.log[0]['status'], 403)

    def test_malformed_non_ascii_token_header_gives_403_not_crash(self):
        own_host = '{}:{}'.format(self.broker_host, self.broker_port)
        raw_bytes = (
            b'GET /ok HTTP/1.1\r\n'
            b'Host: ' + own_host.encode('ascii') + b'\r\n'
            b'Authorization: Bearer \xff\xfe\x00garbage\r\n'
            b'Content-Length: 0\r\n'
            b'Connection: close\r\n'
            b'\r\n'
        )
        response = _raw_exchange(self.broker_host, self.broker_port, raw_bytes)
        self.assertEqual(_status_of(response), 403)
        self.assertEqual(self.upstream.requests_seen, [])

    def test_a_valid_request_still_works_after_all_the_rejections(self):
        # Sanity check: proves the empty requests_seen assertions above are because
        # each request was genuinely rejected, not because the test wiring is broken.
        conn = http.client.HTTPConnection(self.broker_host, self.broker_port, timeout=2)
        conn.request('GET', '/ok', headers={'Authorization': 'Bearer ' + self.token})
        resp = conn.getresponse()
        resp.read()
        conn.close()
        self.assertEqual(resp.status, 200)
        self.assertEqual(len(self.upstream.requests_seen), 1)


class BrokerForwardingTests(_BrokerTestBase):
    def test_upstream_sees_credential_and_upstream_host_never_the_token(self):
        conn = http.client.HTTPConnection(self.broker_host, self.broker_port, timeout=2)
        conn.request('GET', '/anything', headers={'Authorization': 'Bearer ' + self.token})
        resp = conn.getresponse()
        resp.read()
        conn.close()
        self.assertEqual(resp.status, 200)
        self.assertEqual(len(self.upstream.requests_seen), 1)
        seen = self.upstream.requests_seen[0]
        self.assertEqual(seen['headers'].get('authorization'), 'Bearer ' + self.credential)
        expected_host = '127.0.0.1:%d' % self.upstream.server_address[1]
        self.assertEqual(seen['headers'].get('host'), expected_host)
        serialized = str(seen)  # seen['body'] is bytes, so json.dumps would raise here
        self.assertFalse(self.token in serialized, 'the episode token must never reach the upstream')

    def test_custom_token_header_never_forwarded(self):
        upstream, upstream_thread = _start_upstream()
        self.addCleanup(_stop_server, upstream, upstream_thread)
        upstream_base = 'http://127.0.0.1:%d' % upstream.server_address[1]
        token = _secret(24)
        credential = _secret(24)
        b = broker_module.Broker(credential=credential, upstream=upstream_base, token=token,
                                  token_header='x-episode-token')
        base = b.start()
        self.addCleanup(b.stop)
        parsed = urllib.parse.urlsplit(base)
        conn = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=2)
        conn.request('GET', '/anything', headers={'X-Episode-Token': 'Bearer ' + token})
        resp = conn.getresponse()
        resp.read()
        conn.close()
        self.assertEqual(resp.status, 200)
        self.assertEqual(len(upstream.requests_seen), 1)
        seen = upstream.requests_seen[0]
        self.assertNotIn('x-episode-token', seen['headers'])
        serialized = str(seen)  # seen['body'] is bytes, so json.dumps would raise here
        self.assertFalse(token in serialized, 'a custom token header must never reach the upstream')
        self.assertEqual(seen['headers'].get('authorization'), 'Bearer ' + credential)

    def test_method_path_query_and_body_preserved(self):
        conn = http.client.HTTPConnection(self.broker_host, self.broker_port, timeout=2)
        body = json.dumps({'hello': 'world'}).encode('utf-8')
        conn.request('POST', '/foo/bar?x=1&y=2', body=body,
                     headers={'Authorization': 'Bearer ' + self.token,
                              'Content-Type': 'application/json'})
        resp = conn.getresponse()
        resp.read()
        conn.close()
        seen = self.upstream.requests_seen[0]
        self.assertEqual(seen['method'], 'POST')
        self.assertEqual(seen['path'], '/foo/bar?x=1&y=2')
        self.assertEqual(seen['body'], body)

    def test_hop_by_hop_and_credential_shaped_inbound_headers_stripped(self):
        conn = http.client.HTTPConnection(self.broker_host, self.broker_port, timeout=2)
        conn.request('GET', '/anything', headers={
            'Authorization': 'Bearer ' + self.token,
            'Cookie': 'session=abc123',
            'X-Api-Key': 'someleakedkey',
            'Proxy-Authorization': 'Basic zzzz',
            'Connection': 'keep-alive',
            'Keep-Alive': 'timeout=5',
            'Upgrade': 'websocket',
        })
        resp = conn.getresponse()
        resp.read()
        conn.close()
        seen = self.upstream.requests_seen[0]
        headers = seen['headers']
        self.assertNotIn('cookie', headers)
        self.assertNotIn('x-api-key', headers)
        self.assertNotIn('proxy-authorization', headers)
        # Hop-by-hop headers, distinct from the always-stripped credential-shaped set
        # above: http.client adds no Connection header of its own (verified separately),
        # so any of these reaching the upstream can only mean the broker forwarded them.
        self.assertNotIn('connection', headers)
        self.assertNotIn('keep-alive', headers)
        self.assertNotIn('upgrade', headers)
        self.assertEqual(headers.get('authorization'), 'Bearer ' + self.credential)

    def test_response_status_and_headers_passed_back_minus_hop_by_hop(self):
        self.upstream.response_status = 201
        self.upstream.response_headers = {
            'X-Custom': 'value123',
            'Connection': 'keep-alive',
            'Keep-Alive': 'timeout=5',
        }
        conn = http.client.HTTPConnection(self.broker_host, self.broker_port, timeout=2)
        conn.request('GET', '/anything', headers={'Authorization': 'Bearer ' + self.token})
        resp = conn.getresponse()
        resp.read()
        conn.close()
        self.assertEqual(resp.status, 201)
        self.assertEqual(resp.getheader('X-Custom'), 'value123')
        # Keep-Alive has no other source (the broker never sends one), so its presence
        # can only mean upstream's hop-by-hop header leaked through unstripped.
        self.assertIsNone(resp.getheader('Keep-Alive'))
        # Every broker response also sends its own Connection: close (see
        # BrokerTeardownTests); checking for exact equality here, not just
        # "!= 'keep-alive'", matters because a broken strip would leave BOTH upstream's
        # and the broker's Connection headers on the wire, which http.client's
        # getheader() joins into 'keep-alive, close' -- a value that still satisfies a
        # weaker "!=" check even though stripping is broken.
        self.assertEqual(resp.getheader('Connection'), 'close')


class BrokerStreamingTests(unittest.TestCase):
    def setUp(self):
        self.upstream = ThreadingHTTPServer(('127.0.0.1', 0), _StreamingUpstreamHandler)
        self.upstream.chunk1 = b'first-chunk-payload'
        self.upstream.chunk2 = b'second-chunk-payload-is-longer'
        self.upstream.chunk1_sent = threading.Event()
        self.upstream.chunk2_sent = threading.Event()
        self.upstream.release_chunk2 = threading.Event()
        self.upstream_thread = threading.Thread(target=self.upstream.serve_forever, daemon=True)
        self.upstream_thread.start()
        self.addCleanup(_stop_server, self.upstream, self.upstream_thread)

        self.upstream_base = 'http://127.0.0.1:%d' % self.upstream.server_address[1]
        self.token = _secret(24)
        self.credential = _secret(24)
        self.broker = broker_module.Broker(
            credential=self.credential, upstream=self.upstream_base, token=self.token)
        self.broker_base = self.broker.start()
        self.addCleanup(self.broker.stop)
        parsed = urllib.parse.urlsplit(self.broker_base)
        self.broker_host = parsed.hostname
        self.broker_port = parsed.port

    def test_first_chunk_readable_before_second_is_sent(self):
        conn = http.client.HTTPConnection(self.broker_host, self.broker_port, timeout=3)
        conn.request('GET', '/stream', headers={'Authorization': 'Bearer ' + self.token})
        resp = conn.getresponse()
        self.assertEqual(resp.status, 200)

        reader = resp.read1 if hasattr(resp, 'read1') else resp.read
        first = reader(65536)
        self.assertEqual(first, self.upstream.chunk1)
        self.assertTrue(self.upstream.chunk1_sent.wait(timeout=3))
        # The crux of the guarantee: the upstream must not have been allowed to send
        # (or even reach the point of sending) chunk2 while we were still reading chunk1.
        self.assertFalse(self.upstream.chunk2_sent.is_set(),
                          'broker must not block waiting for chunk2 before releasing chunk1')

        self.upstream.release_chunk2.set()
        rest = resp.read()
        self.assertEqual(rest, self.upstream.chunk2)
        self.assertTrue(self.upstream.chunk2_sent.wait(timeout=3))
        conn.close()

    def test_content_length_upstream_passthrough(self):
        self.upstream.release_chunk2.set()  # let the streaming handler finish on its own
        plain_upstream, plain_thread = _start_upstream()
        self.addCleanup(_stop_server, plain_upstream, plain_thread)
        plain_upstream.response_body = b'a fixed length body'
        plain_base = 'http://127.0.0.1:%d' % plain_upstream.server_address[1]
        b = broker_module.Broker(credential=self.credential, upstream=plain_base, token=self.token)
        base = b.start()
        self.addCleanup(b.stop)
        parsed = urllib.parse.urlsplit(base)
        conn = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=3)
        conn.request('GET', '/x', headers={'Authorization': 'Bearer ' + self.token})
        resp = conn.getresponse()
        self.assertEqual(resp.getheader('Content-Length'), str(len(b'a fixed length body')))
        body = resp.read()
        conn.close()
        self.assertEqual(body, b'a fixed length body')


class BrokerLogTests(_BrokerTestBase):
    """_record() runs in the handler thread, strictly after the response body has been
    flushed to the client -- so a client-side resp.read() returning is not proof the
    log entry has been appended yet (that append happens a little later, in the same
    background thread). Every test here calls self.broker.stop() before inspecting
    self.broker.log: stop() joins every handler thread (daemon_threads = False on the
    server), which is what actually guarantees the log has reached its final state.
    stop() is idempotent, so the addCleanup(self.broker.stop) from setUp firing again
    afterward is a safe no-op.
    """

    def test_log_entries_have_exactly_the_specified_fields(self):
        conn = http.client.HTTPConnection(self.broker_host, self.broker_port, timeout=2)
        conn.request('GET', '/some/path?withquery=1',
                      headers={'Authorization': 'Bearer ' + self.token})
        resp = conn.getresponse()
        resp.read()
        conn.close()
        self.broker.stop()
        self.assertEqual(len(self.broker.log), 1)
        entry = self.broker.log[0]
        self.assertEqual(set(entry.keys()), {'method', 'path', 'status', 'bytes', 'seconds'})
        self.assertEqual(entry['method'], 'GET')
        self.assertEqual(entry['path'], '/some/path')
        self.assertEqual(entry['status'], 200)
        self.assertIsInstance(entry['bytes'], int)
        self.assertIsInstance(entry['seconds'], float)

    def test_log_never_contains_secrets_or_query(self):
        conn = http.client.HTTPConnection(self.broker_host, self.broker_port, timeout=2)
        conn.request('GET', '/p?token=' + self.token,
                      headers={'Authorization': 'Bearer ' + self.token})
        resp = conn.getresponse()
        resp.read()
        conn.close()
        self.broker.stop()
        # Must not pass vacuously because the log happened to still be empty.
        self.assertEqual(len(self.broker.log), 1)
        serialized = json.dumps(self.broker.log)
        self.assertFalse(self.token in serialized, 'log must never contain the token')
        self.assertFalse(self.credential in serialized, 'log must never contain the credential')
        self.assertFalse('?' in serialized, 'log path must never contain the query string')

    def test_log_accumulates_across_requests(self):
        for _ in range(3):
            conn = http.client.HTTPConnection(self.broker_host, self.broker_port, timeout=2)
            conn.request('GET', '/x', headers={'Authorization': 'Bearer ' + self.token})
            conn.getresponse().read()
            conn.close()
        self.broker.stop()
        self.assertEqual(len(self.broker.log), 3)


class BrokerTeardownTests(_BrokerTestBase):
    def test_stop_joins_an_in_flight_handler_before_returning(self):
        # Regression guard for daemon_threads: hold the upstream response behind an
        # event so the broker's handler thread is provably still in flight when stop()
        # is called, prove stop() actually blocks on it (not just that it eventually
        # finishes), then release it and require stop() to have joined it -- rather
        # than abandoning it as an unjoined daemon thread.
        upstream_received = threading.Event()
        release_upstream = threading.Event()
        self.addCleanup(release_upstream.set)  # never leave the held handler blocked

        class _HeldHandler(BaseHTTPRequestHandler):
            protocol_version = 'HTTP/1.1'

            def log_message(self, *args):
                pass

            def do_GET(self):
                upstream_received.set()
                release_upstream.wait(timeout=5)
                body = b'held-ok'
                self.send_response(200)
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        held_upstream = ThreadingHTTPServer(('127.0.0.1', 0), _HeldHandler)
        held_thread = threading.Thread(target=held_upstream.serve_forever, daemon=True)
        held_thread.start()
        self.addCleanup(_stop_server, held_upstream, held_thread)
        held_base = 'http://127.0.0.1:%d' % held_upstream.server_address[1]

        b = broker_module.Broker(credential=self.credential, upstream=held_base, token=self.token)
        base = b.start()
        self.addCleanup(b.stop)  # stop() is idempotent; safe even after the explicit call below
        parsed = urllib.parse.urlsplit(base)

        def _make_request():
            conn = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=5)
            conn.request('GET', '/held', headers={'Authorization': 'Bearer ' + self.token})
            conn.getresponse().read()
            conn.close()

        requester = threading.Thread(target=_make_request)
        requester.start()
        self.assertTrue(upstream_received.wait(timeout=3),
                         'the held upstream never received the forwarded request')

        stop_done = threading.Event()

        def _do_stop():
            b.stop()
            stop_done.set()

        stopper = threading.Thread(target=_do_stop)
        stopper.start()
        # Give stop() a generous window to finish on its own -- comfortably longer than
        # ThreadingHTTPServer.shutdown()'s own ~0.5s poll_interval, so that delay (which
        # happens regardless of any handler thread) can never be mistaken for stop()
        # having joined the handler. release_upstream is deliberately NOT set yet, so
        # the handler is still guaranteed blocked (up to its own 5s timeout) throughout
        # this whole window: if stop() finishes anyway, that alone proves it did not
        # join the still-in-flight handler thread.
        stop_done.wait(timeout=3)
        self.assertFalse(stop_done.is_set(),
                          'stop() returned while the handler was still provably blocked '
                          '(release_upstream not yet set) -- it must join the handler '
                          'thread, not abandon it as an unjoined daemon thread')

        release_upstream.set()
        stopper.join(timeout=5)
        self.assertTrue(stop_done.is_set(), 'stop() did not finish after being released')
        self.assertEqual(len(b.log), 1,
                          'stop() returned before the in-flight handler finished logging '
                          '-- server_close() must join handler threads, not abandon them')
        requester.join(timeout=3)

    def test_stop_does_not_hang_when_client_leaves_connection_open(self):
        conn = http.client.HTTPConnection(self.broker_host, self.broker_port, timeout=5)
        conn.request('GET', '/anything', headers={'Authorization': 'Bearer ' + self.token})
        resp = conn.getresponse()
        resp.read()
        # Deliberately do NOT close conn -- simulates a participant HTTP client that
        # pools/reuses connections and never explicitly closes this one. Regression
        # guard: stop() must not block waiting on it (it previously blocked for up to
        # the broker's configured timeout).
        stop_finished = threading.Event()

        def _do_stop():
            self.broker.stop()
            stop_finished.set()

        stopper = threading.Thread(target=_do_stop)
        stopper.start()
        stopper.join(timeout=3)
        self.assertTrue(stop_finished.is_set(),
                         'stop() must not hang waiting on a connection the client left open')
        conn.close()


class BrokerHTTPSTests(unittest.TestCase):
    def test_https_uses_verified_default_context(self):
        captured = {}

        class _FakeResponse:
            status = 200

            def __init__(self):
                self._sent = False

            def getheaders(self):
                return [('Content-Length', '2')]

            def getheader(self, name, default=None):
                return '2' if name.lower() == 'content-length' else default

            def read1(self, n=-1):
                if not self._sent:
                    self._sent = True
                    return b'ok'
                return b''

            def read(self, n=-1):
                return self.read1(n)

            def close(self):
                pass

        class _FakeHTTPSConnection:
            def __init__(self, host, port, timeout=None, context=None):
                captured['host'] = host
                captured['port'] = port
                captured['context'] = context

            def request(self, method, url, body=None, headers=None):
                captured['method'] = method
                captured['url'] = url

            def getresponse(self):
                return _FakeResponse()

            def close(self):
                pass

        token = _secret(24)
        credential = _secret(24)
        b = broker_module.Broker(credential=credential, upstream='https://upstream.example:443',
                                  token=token)
        base = b.start()
        self.addCleanup(b.stop)
        parsed = urllib.parse.urlsplit(base)

        with mock.patch('broker.http.client.HTTPSConnection', _FakeHTTPSConnection):
            conn = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=3)
            conn.request('GET', '/x', headers={'Authorization': 'Bearer ' + token})
            resp = conn.getresponse()
            resp.read()
            conn.close()

        self.assertEqual(captured.get('host'), 'upstream.example')
        self.assertEqual(captured.get('port'), 443)
        context = captured.get('context')
        self.assertIsNotNone(context)
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(context.check_hostname)


class BrokerChunkedRequestTests(_BrokerTestBase):
    """Added by the coordinator at T-05 integration: a chunked request body is refused, never forwarded empty."""

    def test_chunked_request_body_is_refused_and_not_forwarded(self):
        own_host = '{}:{}'.format(self.broker_host, self.broker_port)
        head = ('POST /v1/messages HTTP/1.1\r\nHost: %s\r\nAuthorization: Bearer %s\r\n'
                'Transfer-Encoding: chunked\r\nConnection: close\r\n\r\n' % (own_host, self.token))
        raw = head.encode('latin-1') + b'5\r\nhello\r\n0\r\n\r\n'
        response = _raw_exchange(self.broker_host, self.broker_port, raw)
        self.assertEqual(_status_of(response), 411)
        self.assertEqual(self.upstream.requests_seen, [])


if __name__ == '__main__':
    unittest.main()
