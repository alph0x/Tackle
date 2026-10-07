"""Existing-only opaque session inspection; no refresh, networking or exports.

The CLI consumes the system user's previously authorized store internally and
emits finite metadata. Retained authentication is not current plan entitlement.
No bearer, account/client identifier, claim, private bytes or their hash escapes.
"""
import base64
import contextlib
import fcntl
import json
import math
import os
from pathlib import Path
import pwd
import re
import signal
import stat
import sys
import time

MAX_FILE = 131072
ISSUER = 'https://auth.openai.com'
DIRECT = 'chatgpt.tokens.use.direct'
REASONS = {'storage', 'busy', 'unavailable', 'binding', 'grant', 'expired',
           'interrupted_auth', 'credentials', 'deadline', 'invocation', 'internal'}


class Refusal(Exception):
    pass


def need(condition, reason):
    if not condition:
        raise Refusal(reason)


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, 'storage')
            result[key] = value
        return result
    def invalid(_):
        raise Refusal('storage')
    need(len(raw) <= MAX_FILE, 'storage')
    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)
    need(isinstance(value, dict), 'storage')
    return value


def check_fd(fd, directory=False, private=True):
    info = os.fstat(fd)
    need(info.st_uid == os.getuid(), 'storage')
    need(stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode), 'storage')
    mode = stat.S_IMODE(info.st_mode)
    need(mode == (0o700 if directory else 0o600) if private else not mode & 0o022, 'storage')
    if not directory:
        need(info.st_nlink == 1 and info.st_size <= MAX_FILE, 'storage')


class ExistingStore:
    """Descriptor-pinned existing directories/lock. Never mkdir, create or write."""
    def __init__(self, home):
        self.home = home
        self.fd = self.lockfd = None

    def __enter__(self):
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
        current = os.open(self.home, flags)
        try:
            check_fd(current, directory=True, private=False)
            for index, name in enumerate(('.tackle', 'runtime', 'chatgpt-oauth')):
                child = os.open(name, flags, dir_fd=current)
                try:
                    check_fd(child, directory=True, private=index != 0)
                except BaseException:
                    os.close(child)
                    raise
                os.close(current)
                current = child
            self.fd, current = current, None
            self.lockfd = os.open('invocation.lock', os.O_RDONLY | os.O_NOFOLLOW |
                                  os.O_CLOEXEC | os.O_NONBLOCK, dir_fd=self.fd)
            check_fd(self.lockfd)
            try:
                fcntl.flock(self.lockfd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise Refusal('busy') from None
            for name in os.listdir(self.fd):
                fd = os.open(name, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW |
                             os.O_CLOEXEC, dir_fd=self.fd)
                try:
                    check_fd(fd)
                finally:
                    os.close(fd)
            need(not any(name in os.listdir(self.fd) for name in (
                'refresh-inflight.json', 'refresh_inflight.json')), 'interrupted_auth')
            return self
        except BaseException:
            if current is not None:
                os.close(current)
            self.__exit__(None, None, None)
            raise

    def __exit__(self, *_):
        for name in ('lockfd', 'fd'):
            value = getattr(self, name)
            if value is not None:
                os.close(value)
                setattr(self, name, None)

    def read(self, name):
        fd = os.open(name, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW |
                     os.O_CLOEXEC, dir_fd=self.fd)
        try:
            check_fd(fd)
            with os.fdopen(fd, 'rb', closefd=False) as stream:
                return strict_json(stream.read(MAX_FILE + 1))
        finally:
            os.close(fd)


def retained_reference(value):
    reference = value.get('authentication_reference')
    if reference is None:
        token = value.get('id_token')
        need(isinstance(token, str) and len(token) <= 65536, 'binding')
        pieces = token.split('.')
        need(len(pieces) == 3 and re.fullmatch(r'[A-Za-z0-9_-]+', pieces[1]), 'binding')
        raw = base64.b64decode(pieces[1] + '=' * (-len(pieces[1]) % 4),
                              altchars=b'-_', validate=True)
        reference = strict_json(raw)
    need(isinstance(reference, dict), 'binding')
    # These are retained signed-at-consent bindings, not a new JWT verification.
    need(reference.get('iss') == ISSUER and reference.get('sub') == value.get('subject'), 'binding')
    need(reference.get('aud') in (value['client_id'], [value['client_id']]), 'binding')


def validate_session(store, now):
    value = store.read('credentials.json')
    registration = store.read('registration.json')
    pending = store.read('pending.json')
    client = value.get('client_id')
    need(isinstance(client, str) and re.fullmatch(r'oaiapp_[A-Za-z0-9_-]{1,240}', client), 'binding')
    need(registration.get('client_id') == client and pending.get('client_id') in (None, client), 'binding')
    need(pending.get('stage') == 'complete', 'interrupted_auth')
    need(value.get('issuer') == ISSUER and isinstance(value.get('subject'), str)
         and 0 < len(value['subject']) <= 4096, 'binding')
    retained_reference(value)
    scopes = value.get('scopes')
    need(isinstance(scopes, list) and all(isinstance(x, str) for x in scopes)
         and DIRECT in scopes and 'resource.invoke' in scopes, 'grant')
    need(value.get('token_type') == 'Bearer', 'credentials')
    bearer = value.get('access_token')
    need(isinstance(bearer, str) and 0 < len(bearer) <= 16384
         and re.fullmatch(r'[A-Za-z0-9._~+/-]+=*', bearer), 'credentials')
    saved, expires = value.get('saved_at'), value.get('expires_at')
    need(all(type(x) in (int, float) and math.isfinite(x) for x in (saved, expires, now)), 'credentials')
    need(saved <= now + 5 and 0 < expires - saved <= 86400, 'credentials')
    need(expires > now + 120, 'expired')
    # Never return the source or any of its identifiers.


def receipt(stage, reason):
    return dict(schema='tackle-opaque-session-status/1', stage=stage, reason=reason,
                auth='valid_for_probe' if stage == 'session_ready' else 'unavailable',
                binding='retained_binding_checked' if stage == 'session_ready' else 'unknown',
                included_only_admission='unestablished', network_requests=0,
                inference_requests=0, store_writes=0)


def inspect_existing(home, now=None):
    try:
        with ExistingStore(home) as store:
            validate_session(store, time.time() if now is None else now)
        return receipt('session_ready', 'none')
    except Refusal as exc:
        reason = exc.args[0] if exc.args and exc.args[0] in REASONS else 'internal'
    except (FileNotFoundError, NotADirectoryError):
        reason = 'unavailable'
    except (OSError, ValueError, KeyError, TypeError):
        reason = 'storage'
    return receipt('refused', reason)


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if args != ['inspect']:
        result = receipt('refused', 'invocation')
    else:
        def expired(*_):
            raise Refusal('deadline')
        signal.signal(signal.SIGALRM, expired)
        signal.alarm(15)
        try:
            home = Path(pwd.getpwuid(os.getuid()).pw_dir)
            result = inspect_existing(home)
        except BaseException:
            result = receipt('refused', 'internal')
        finally:
            signal.alarm(0)
    sys.stdout.write(json.dumps(result, sort_keys=True, separators=(',', ':')) + '\n')
    return 0 if result['stage'] == 'session_ready' else 1


if __name__ == '__main__':
    raise SystemExit(main())
