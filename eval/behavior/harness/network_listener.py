"""One loopback port for the subscription route: the endpoint, a recording HTTP and SOCKS proxy, and the log.

Standard library only. ``Listener`` binds one port on 127.0.0.1 and on ::1 and serves four roles by the first
bytes of each connection:

- a plain request line (``GET /path HTTP/1.1``) is an endpoint request;
- a request line with an absolute URL is a proxied request, and ``CONNECT host:port`` is a tunnel request;
- a first byte of 0x05 opens a SOCKS5 exchange;
- anything else is a raw connection.

Every request is refused with the configured status (a SOCKS failure reply for SOCKS) and logged as one JSON line:
``session``, ``kind``, ``method``, ``host``, ``path``, ``query_sha256``, ``bytes`` and ``body_sha256``. For a proxy,
CONNECT or SOCKS line ``host`` is the requested target; for an endpoint or raw line it is the address and port the
connection arrived on, never a header value. The log never holds a body, a header value or a query string, and TLS
is never terminated: a tunnel request is refused before any handshake byte.
"""
import hashlib
import http
import ipaddress
import json
import re
import socket
import socketserver
import struct
import threading
import time
from pathlib import Path
from urllib.parse import urlsplit

IDLE_SECONDS = 1.0
REQUEST_SECONDS = 5.0
HEAD_LIMIT = 65536
BODY_LIMIT = 1 << 20
DRAIN_SECONDS = 0.5
REQUEST_LINE = re.compile(rb'([A-Za-z]+) (\S+) HTTP/1\.[01]\r?')
CONTENT_LENGTH = re.compile(rb'(?im)^content-length:[ \t]*([0-9]+)[ \t]*\r?$')
SOCKS_COMMANDS = {1: 'CONNECT', 2: 'BIND', 3: 'UDP'}
SOCKS_REFUSED = b'\x05\x02\x00\x01\x00\x00\x00\x00\x00\x00'
LOOPBACKS = (('127.0.0.1', socket.AF_INET), ('::1', socket.AF_INET6))


class PortUnavailable(Exception):
    """The declared port cannot be bound on a loopback address."""


def sha(data):
    return hashlib.sha256(data).hexdigest()


def address_text(host, port):
    return '[%s]:%d' % (host, port) if ':' in host else '%s:%d' % (host, port)


def sockets_for(port):
    """Listening sockets for the port on both loopbacks; closes whatever it opened when one cannot be bound."""
    opened = []
    try:
        for host, family in LOOPBACKS:
            sock = socket.socket(family, socket.SOCK_STREAM)
            opened.append(sock)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if family == socket.AF_INET6:
                sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
            try:
                sock.bind((host, port))
                sock.listen(64)
            except OSError as problem:
                raise PortUnavailable('port %d cannot be bound on %s (%s)' % (port, host, problem.strerror or problem.__class__.__name__))
    except PortUnavailable:
        for sock in opened:
            sock.close()
        raise
    return opened


def ensure_free(port):
    """Raises PortUnavailable when the port is busy on either loopback; holds nothing afterwards."""
    for sock in sockets_for(port):
        sock.close()


def read_until(conn, done, limit, deadline):
    """Bytes read until ``done(data)`` holds, the peer closes, one idle gap passes, or a limit is reached."""
    data = b''
    while len(data) < limit and time.monotonic() < deadline and not done(data):
        try:
            chunk = conn.recv(65536)
        except OSError:
            break
        if not chunk:
            break
        data += chunk
    return data


def read_exact(conn, count, deadline):
    data = b''
    while len(data) < count and time.monotonic() < deadline:
        try:
            chunk = conn.recv(count - len(data))
        except OSError:
            break
        if not chunk:
            break
        data += chunk
    return data


class Handler(socketserver.BaseRequestHandler):
    def handle(self):
        listener = self.server.listener
        conn = self.request
        conn.settimeout(IDLE_SECONDS)
        local = conn.getsockname()
        arrived = address_text(local[0], local[1])
        deadline = time.monotonic() + REQUEST_SECONDS
        try:
            first = read_until(conn, lambda data: data[:1] == b'\x05' or b'\n' in data, HEAD_LIMIT, deadline)
            if first[:1] == b'\x05':
                self.socks(listener, conn, first, arrived, deadline)
            else:
                self.http_or_raw(listener, conn, first, arrived, deadline)
        except OSError:
            pass
        finally:
            try:
                conn.close()
            except OSError:
                pass

    def finish_connection(self, conn, payload):
        """Send the refusal, close our side and read what the peer still sends, so the answer is not lost to a reset."""
        try:
            if payload:
                conn.sendall(payload)
            conn.shutdown(socket.SHUT_WR)
            end = time.monotonic() + DRAIN_SECONDS
            conn.settimeout(DRAIN_SECONDS)
            while time.monotonic() < end and conn.recv(65536):
                pass
        except OSError:
            pass

    def http_or_raw(self, listener, conn, first, arrived, deadline):
        line = first.split(b'\n', 1)[0] if b'\n' in first else b''
        match = REQUEST_LINE.fullmatch(line)
        if not match:
            data = first + read_until(conn, lambda data: False, HEAD_LIMIT, deadline)
            listener.record('raw', None, arrived, None, None, len(data), None)
            self.finish_connection(conn, b'')
            return
        method, target = match.group(1).decode('ascii').upper(), match.group(2).decode('latin-1')
        if method == 'CONNECT':
            head = first + read_until(conn, lambda data: b'\r\n\r\n' in data or b'\n\n' in data, HEAD_LIMIT, deadline)
            listener.record('connect', method, target.rsplit('@', 1)[-1], None, None, len(head), None)
            self.finish_connection(conn, listener.refusal())
            return
        head = first
        marker = (b'\r\n\r\n', b'\n\n')
        if not any(m in head for m in marker):
            head += read_until(conn, lambda data: any(m in head + data for m in marker), HEAD_LIMIT, deadline)
        end = min((head.index(m) + len(m) for m in marker if m in head), default=len(head))
        length = CONTENT_LENGTH.search(head[:end])
        want = 0
        if length:
            # Bound the decimal text before int(): Python may refuse thousands of digits, including leading zeroes.
            digits = length.group(1).lstrip(b'0') or b'0'
            want = BODY_LIMIT if len(digits) > len(str(BODY_LIMIT)) else min(int(digits), BODY_LIMIT)
        if len(head) - end < want:
            head += read_exact(conn, want - (len(head) - end), deadline)
        body = head[end:]
        try:
            absolute = urlsplit(target) if re.match(r'(?i)[a-z][a-z0-9+.-]*://', target) else None
            if absolute is not None and not absolute.hostname:
                raise ValueError('proxy target has no named host')
        except ValueError:
            # Invalid proxy-form syntax is still a connection to the declared endpoint.
            listener.record('raw', None, arrived, None, None, len(head), None)
            self.finish_connection(conn, b'')
            return
        if absolute is not None:
            host = absolute.netloc.rsplit('@', 1)[-1].lower()
            kind, path, query = 'proxy', absolute.path or '/', absolute.query
        elif target.startswith('/') or target == '*':
            host, kind = arrived, 'endpoint'
            path, _, query = target.partition('?')
        else:
            listener.record('raw', None, arrived, None, None, len(head), None)
            self.finish_connection(conn, b'')
            return
        listener.record(kind, method, host, path, sha(query.encode('latin-1', 'replace')) if query else None,
                        len(head), sha(body) if body else None)
        self.finish_connection(conn, listener.refusal())

    def socks(self, listener, conn, first, arrived, deadline):
        # recv may contain both the greeting and the request. Keep the unread suffix for every parse step.
        pending, seen = first, 0

        def take(count):
            nonlocal pending, seen
            if len(pending) < count:
                pending += read_exact(conn, count - len(pending), deadline)
            data, pending = pending[:count], pending[count:]
            seen += len(data)
            return data

        greeting = take(2)
        count = greeting[1] if len(greeting) == 2 else 0
        methods = take(count)
        if not count or len(methods) != count or 0 not in methods:
            extra = pending + read_until(conn, lambda data: False, HEAD_LIMIT, deadline)
            listener.record('raw', None, arrived, None, None, seen + len(extra), None)
            self.finish_connection(conn, b'')
            return
        conn.sendall(b'\x05\x00')
        head = take(4)
        target = None
        if len(head) == 4 and head[0] == 5:
            kind = head[3]
            size = {1: 4, 4: 16}.get(kind)
            if kind == 3:
                length = take(1)
                size = length[0] if length else None
            rest = take(size + 2) if size is not None else b''
            if size is not None and len(rest) == size + 2:
                port = struct.unpack('>H', rest[size:])[0]
                raw = rest[:size]
                host = (str(ipaddress.ip_address(raw)) if kind in (1, 4) else raw.decode('latin-1'))
                target = address_text(host, port) if kind != 3 else '%s:%d' % (host, port)
        method = SOCKS_COMMANDS.get(head[1]) if len(head) == 4 else None
        listener.record('socks', method, target, None, None, seen, None)
        self.finish_connection(conn, SOCKS_REFUSED)


class Server(socketserver.ThreadingTCPServer):
    daemon_threads = True

    def __init__(self, sock, listener):
        socketserver.BaseServer.__init__(self, sock.getsockname(), Handler)
        self.socket = sock
        self.listener = listener
        self.address_family = sock.family

    def server_bind(self):
        pass

    def server_activate(self):
        pass

    def server_close(self):
        self.socket.close()


class Listener:
    """The route's loopback listener. ``session`` is the index the route sets before each session."""

    def __init__(self, port, status, log_path):
        self.port, self.status, self.log_path = port, status, Path(log_path)
        self.session = 0
        self.lines = 0
        self.lock = threading.Lock()
        self.servers, self.threads = [], []

    def start(self):
        """Create the (empty) log and listen on both loopbacks. Raises PortUnavailable when a bind fails."""
        sockets = sockets_for(self.port)
        self.log_path.write_bytes(b'')
        for sock in sockets:
            server = Server(sock, self)
            thread = threading.Thread(target=server.serve_forever, kwargs={'poll_interval': 0.05}, daemon=True)
            thread.start()
            self.servers.append(server)
            self.threads.append(thread)

    def stop(self):
        for server in self.servers:
            server.shutdown()
        for thread in self.threads:
            thread.join(timeout=5)
        for server in self.servers:
            server.server_close()
        self.servers, self.threads = [], []

    def refusal(self):
        reason = http.HTTPStatus(self.status).phrase if self.status in http.HTTPStatus._value2member_map_ else 'Refused'
        body = json.dumps({'error': 'refused', 'status': self.status}).encode()
        return (b'HTTP/1.1 %d %s\r\nContent-Type: application/json\r\nContent-Length: %d\r\nConnection: close\r\n\r\n'
                % (self.status, reason.encode(), len(body))) + body

    def record(self, kind, method, host, path, query_sha256, size, body_sha256):
        line = {'session': self.session, 'kind': kind, 'method': method, 'host': host, 'path': path,
                'query_sha256': query_sha256, 'bytes': size, 'body_sha256': body_sha256}
        with self.lock:
            with open(self.log_path, 'a', encoding='utf-8') as handle:
                handle.write(json.dumps(line, sort_keys=False) + '\n')
            self.lines += 1


def free_port():
    """A port that is free on both loopbacks right now."""
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind(('127.0.0.1', 0))
            port = probe.getsockname()[1]
        try:
            ensure_free(port)
        except PortUnavailable:
            continue
        return port


class DecoyHandler(socketserver.BaseRequestHandler):
    def handle(self):
        with self.server.lock:
            self.server.accepted += 1
        try:
            self.request.settimeout(IDLE_SECONDS)
            self.request.recv(4096)
            self.request.sendall(b'HTTP/1.1 200 OK\r\nContent-Length: 5\r\nConnection: close\r\n\r\ndecoy')
        except OSError:
            pass


class Decoy(socketserver.ThreadingTCPServer):
    """A second loopback port that serves nothing the route knows: the probe asks whether the sandbox lets a command reach it."""
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self):
        super().__init__(('127.0.0.1', 0), DecoyHandler)
        self.port = self.server_address[1]
        self.accepted = 0
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self.serve_forever, kwargs={'poll_interval': 0.05}, daemon=True)

    def start(self):
        self.thread.start()

    def stop(self):
        self.shutdown()
        self.thread.join(timeout=5)
        self.server_close()
