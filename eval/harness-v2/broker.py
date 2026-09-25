"""A credential-forwarding HTTP proxy for one sandboxed episode.

Guarantees:
- Runs host-side only: it is started by the coordinator outside the participant's
  execution environment, and only its bind address (from start()) is handed in.
- The credential passed to __init__ never reaches the participant: it is used solely
  to build the outbound credential header sent to the upstream, and it is never
  echoed, logged, or reflected back to the client.
- Forwards only to one fixed upstream origin chosen by the adapter at construction
  time; nothing else is ever contacted.
"""

import hmac
import http.client
import ssl
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_HOP_BY_HOP = frozenset({
    'connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization',
    'te', 'trailer', 'trailers', 'transfer-encoding', 'upgrade',
})
_STRIP_ALWAYS = frozenset({'authorization', 'x-api-key', 'proxy-authorization', 'cookie'})
_READ_SIZE = 65536


def _raw_target(handler):
    """The request-target exactly as sent on the wire. Some stdlib patch levels
    normalize a leading '//' in self.path down to a single '/' during parse_request,
    which would hide an authority-form or protocol-relative attack from a check that
    only looked at self.path."""
    parts = handler.requestline.split()
    if len(parts) >= 2:
        return parts[1]
    return handler.path


def _is_origin_form(target):
    return target.startswith('/') and not target.startswith('//')


def _read_inbound_body(handler):
    length = handler.headers.get('Content-Length')
    if length is None:
        return b''
    try:
        size = int(length)
    except ValueError:
        return b''
    if size <= 0:
        return b''
    return handler.rfile.read(size)


class _Server(ThreadingHTTPServer):
    # Handler threads must be joined by stop()/server_close() so that self.log is
    # fully populated by the time stop() returns; daemon threads would not be joined.
    daemon_threads = False
    allow_reuse_address = True


class Broker:
    """A host-side-only forwarding proxy that lets a sandboxed participant reach one
    upstream origin without ever seeing the real credential.

    It runs host-side only: the caller starts it outside the participant's sandbox and
    hands the participant only the address returned by start(). The credential given to
    __init__ never reaches the participant -- it is used only to build the outbound
    credential header sent upstream. It forwards only to one fixed upstream origin,
    chosen by the adapter at construction time; every other target is refused.
    """

    def __init__(self, credential, upstream, token,
                 token_header='authorization', token_prefix='Bearer ',
                 credential_header='authorization', credential_prefix='Bearer ',
                 bind='127.0.0.1', port=0, timeout=600):
        parts = self._validate_upstream(upstream)
        self._credential = credential
        self._upstream = upstream
        self._upstream_scheme = parts.scheme
        self._upstream_host = parts.hostname
        self._upstream_port = parts.port
        self._upstream_netloc = parts.netloc
        self._token = token
        self._token_header = token_header
        self._token_prefix = token_prefix
        self._credential_header = credential_header
        self._credential_prefix = credential_prefix
        self._bind = bind
        self._port = port
        self._timeout = timeout
        self._exclude_from_copy = (
            _HOP_BY_HOP | _STRIP_ALWAYS |
            {'host', 'content-length', token_header.lower(), credential_header.lower()}
        )

        self.log = []
        self._log_lock = threading.Lock()
        self._server = None
        self._thread = None
        self._own_host_port = None

    @staticmethod
    def _validate_upstream(upstream):
        """upstream is an origin: scheme http or https, a host, an optional port, and
        no path, query or fragment. Anything else raises ValueError."""
        parts = urllib.parse.urlsplit(upstream)
        if parts.scheme not in ('http', 'https'):
            raise ValueError('upstream scheme must be http or https: {!r}'.format(upstream))
        if '@' in parts.netloc:
            raise ValueError('upstream must not include userinfo: {!r}'.format(upstream))
        if not parts.hostname:
            raise ValueError('upstream must include a host: {!r}'.format(upstream))
        try:
            _ = parts.port
        except ValueError:
            raise ValueError('upstream has an invalid port: {!r}'.format(upstream))
        if parts.path != '' or parts.query or parts.fragment:
            raise ValueError(
                'upstream must have no path, query or fragment: {!r}'.format(upstream))
        return parts

    def start(self):
        """Starts a threaded HTTP server; returns 'http://<bind>:<port>'."""
        broker = self

        class _Handler(BaseHTTPRequestHandler):
            protocol_version = 'HTTP/1.1'
            timeout = broker._timeout

            def log_message(self, fmt, *args):
                pass  # never write request lines to stderr

            def _dispatch(self):
                broker._process(self)

            do_GET = _dispatch
            do_POST = _dispatch
            do_PUT = _dispatch
            do_DELETE = _dispatch
            do_PATCH = _dispatch
            do_HEAD = _dispatch
            do_OPTIONS = _dispatch
            do_CONNECT = _dispatch
            do_TRACE = _dispatch

        self._server = _Server((self._bind, self._port), _Handler)
        self._port = self._server.server_address[1]
        self._own_host_port = '{}:{}'.format(self._bind, self._port)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return 'http://{}:{}'.format(self._bind, self._port)

    def stop(self):
        """Shuts the server down and joins its thread. Idempotent: a second call is a
        safe no-op, so a test (or caller) may call stop() explicitly and still register
        it as a cleanup."""
        server, self._server = self._server, None
        thread, self._thread = self._thread, None
        if server is not None:
            server.shutdown()
            server.server_close()
        if thread is not None:
            thread.join(timeout=self._timeout)

    # -- per-request handling -------------------------------------------------

    def _process(self, handler):
        start = time.monotonic()
        method = handler.command
        log_path = urllib.parse.urlsplit(handler.path).path or '/'
        if 'chunked' in (handler.headers.get('Transfer-Encoding') or '').lower():
            # A chunked request body is refused rather than forwarded empty (T-05 integration).
            self._reject(handler, method, log_path, start, status=411)
            return
        body = _read_inbound_body(handler)

        if not _is_origin_form(_raw_target(handler)):
            self._reject(handler, method, log_path, start)
            return
        if not self._host_matches(handler.headers.get('Host', '')):
            self._reject(handler, method, log_path, start)
            return
        if not self._token_ok(handler.headers.get(self._token_header)):
            self._reject(handler, method, log_path, start)
            return

        self._forward(handler, method, body, log_path, start)

    def _host_matches(self, host_header):
        return host_header.strip().lower() == (self._own_host_port or '').lower()

    def _token_ok(self, supplied):
        """A request is forwarded only when its token_header value equals
        token_prefix + token, compared with hmac.compare_digest. Header values arrive
        latin-1-decoded by http.server, so both sides are compared as bytes -- this
        never raises, even for a header value with arbitrary non-ASCII bytes."""
        if supplied is None:
            return False
        expected = (self._token_prefix + self._token).encode('utf-8')
        got = supplied.encode('latin-1', errors='replace')
        return hmac.compare_digest(got, expected)

    def _reject(self, handler, method, log_path, start, status=403):
        body = b'forbidden' if status == 403 else b'length required'
        try:
            handler.send_response(status)
            handler.send_header('Content-Length', str(len(body)))
            handler.send_header('Content-Type', 'text/plain; charset=utf-8')
            handler.send_header('Connection', 'close')
            handler.end_headers()
            handler.wfile.write(body)
        except OSError:
            pass
        self._record(method, log_path, status, len(body), time.monotonic() - start)

    def _forward(self, handler, method, body, log_path, start):
        outbound_headers = {}
        for key, value in handler.headers.items():
            if key.lower() in self._exclude_from_copy:
                continue
            outbound_headers[key] = value
        outbound_headers[self._credential_header] = self._credential_prefix + self._credential
        outbound_headers['Host'] = self._upstream_netloc

        target = handler.path  # already validated as origin-form; query preserved

        try:
            if self._upstream_scheme == 'https':
                context = ssl.create_default_context()
                conn = http.client.HTTPSConnection(
                    self._upstream_host, self._upstream_port,
                    timeout=self._timeout, context=context)
            else:
                conn = http.client.HTTPConnection(
                    self._upstream_host, self._upstream_port, timeout=self._timeout)
            conn.request(method, target, body=body, headers=outbound_headers)
            resp = conn.getresponse()
        except OSError:
            error_body = b'upstream unavailable'
            try:
                handler.send_response(502)
                handler.send_header('Content-Length', str(len(error_body)))
                handler.send_header('Connection', 'close')
                handler.end_headers()
                handler.wfile.write(error_body)
            except OSError:
                pass
            self._record(method, log_path, 502, len(error_body), time.monotonic() - start)
            return

        content_length = resp.getheader('Content-Length')
        total_bytes = 0
        try:
            handler.send_response(resp.status)
            for key, value in resp.getheaders():
                if key.lower() in _HOP_BY_HOP:
                    continue
                handler.send_header(key, value)
            if content_length is None:
                handler.send_header('Transfer-Encoding', 'chunked')
            # Every response closes its connection after one request-response cycle.
            # This is a proxy for a single sandboxed episode, not a long-lived pool, and
            # always closing means a handler thread never sits blocked on readline()
            # waiting for a second request that a departed or pooling client will never
            # send -- which would otherwise make stop() hang for up to `timeout`.
            handler.send_header('Connection', 'close')
            handler.end_headers()

            # Streaming: read as the data arrives, with no whole-body buffering, since
            # both hosts use server-sent events. read1() stops at whatever is already
            # available (a chunk boundary, for a chunked upstream response) instead of
            # blocking to fill the requested size, so the client can read what has
            # already arrived before the upstream sends anything more.
            reader = resp.read1 if hasattr(resp, 'read1') else (lambda n: resp.read(1))
            while True:
                piece = reader(_READ_SIZE)
                if not piece:
                    break
                if content_length is None:
                    frame = ('%x\r\n' % len(piece)).encode('ascii') + piece + b'\r\n'
                    handler.wfile.write(frame)
                else:
                    handler.wfile.write(piece)
                handler.wfile.flush()
                total_bytes += len(piece)
            if content_length is None:
                handler.wfile.write(b'0\r\n\r\n')
                handler.wfile.flush()
        except OSError:
            pass
        finally:
            resp.close()
            conn.close()

        self._record(method, log_path, resp.status, total_bytes, time.monotonic() - start)

    def _record(self, method, path, status, nbytes, seconds):
        entry = {
            'method': method,
            'path': path,
            'status': status,
            'bytes': nbytes,
            'seconds': seconds,
        }
        with self._log_lock:
            self.log.append(entry)
