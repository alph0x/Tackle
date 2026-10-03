"""Subscription route of the protocol v2 harness: isolated episodes on the owner's subscription token, judged outside the participant.

Usage: python3 eval/behavior/harness/subscription_route.py run|probe|judge --config <file> [options]
(see eval/behavior/harness/README.md). Exit 0 success, 1 a refusal or a stage stopped by a fault, 2 a usage error,
130 an interrupted run. Nothing here is shared with the broker routes: the owner's token is read from the file the
run configuration names, only at launch, and goes into the CLI process environment only.

``run`` stages an arm's exact skill tree (the control arm none) and the variant's fixture into a fresh root, runs each
prompt as a headless session of the pinned CLI, scans every stream and file for the token and its encodings before
anything is kept, judges the final tree with the variant's oracle under the platform sandbox launcher and appends
protocol-v2 episode records. ``probe`` runs one route probe, and ``judge`` runs the oracle step alone.
"""
import argparse
import fcntl
import hashlib
import json
import os
import re
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import credscan  # noqa: E402
import harness  # noqa: E402
import usage  # noqa: E402
from harness import Refusal, Usage  # noqa: E402

TOKEN_VARIABLE = 'CLAUDE_CODE_OAUTH_TOKEN'
CONFIG_SCHEMA = 'tackle-route-config/1'
EPISODE_SCHEMA = 'tackle-route-episode/1'
PROBE_SCHEMA = 'tackle-route-probe/1'
CHILD_PATH = '/usr/bin:/bin:/usr/sbin:/sbin'
HOME_PREFIX = '/Users'
# Reads under these trees are denied to the participant's tools and to the oracle; only the run root and the judged root re-allow.
DENY_READ = ['/Users', '/private/tmp', '/tmp', '/Volumes', '/private/var/folders', '/var/folders', '/private/var/tmp']
# The trees the file tools may not edit, besides the work directory's own .claude.
DENY_EDIT = ['/Users', '/private/tmp']
FORBIDDEN_PARTS = ('', '.', '..', '.git', '.codex', '.agents', '.claude')
FORBIDDEN_NAMES = ('ground-truth.md', 'skill.md', 'claude.md', 'claude.local.md')
ANCESTOR_NAMES = ('CLAUDE.md', 'CLAUDE.local.md', '.claude', 'AGENTS.md')
PARTICIPANT_TOOLS = 'Bash,Read,Write,Edit,Glob,Grep,Skill'
ARMS = ('control', 'method')
LIMITS = ('error_max_turns', 'error_max_budget_usd')
ARCHIVE = 'history-archive.md'
PROBE_URL = 'https://example.com'
PROBE_INSIDE = 'probe-inside.txt'
SCAN_CHUNK = 1 << 20
SAFE_ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,63}')
SESSION_PROMPT = re.compile(r'sessions/([0-9]+)\.md')
HEX = re.compile(r'[0-9a-f]{64}')
NA = 'n/a'
SCORE_FIELDS = ('correct_action', 'evidence', 'verification_honesty', 'report_quality')
# invalid_reason vocabulary: a closed set, so no reason can carry a path.
REASON_CREDENTIAL = 'credential'
REASON_ISOLATION = 'isolation'
REASON_CONFIG = 'harness configuration written'
REASON_CONTROL = 'control arm exposed to the skill'
REASON_METHOD = 'method arm skill not listed'
REASON_TREE = 'final tree not preserved'
# Only the CLI wrapper's own refusal counts: the trailing line of an "Exit code" result naming its cwd-tracking file.
HARNESS_FAULT = re.compile(r'(?m)^(?:zsh|bash|sh):\d+: operation not permitted: \S*/claude-\d+/cwd-[0-9a-f]+\s*\Z')


class CapReached(Exception):
    """A stage, total or probe ceiling would be passed by the next launch."""


class OracleError(Exception):
    """The oracle step failed; ``code`` is the episode's closed error word."""

    def __init__(self, code):
        super().__init__(code)
        self.code = code


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as handle:
        for block in iter(lambda: handle.read(SCAN_CHUNK), b''):
            digest.update(block)
    return digest.hexdigest()


_PROTOCOL = []


def protocol():
    if not _PROTOCOL:
        _PROTOCOL.append(harness.protocol())
    return _PROTOCOL[0]


# --- configuration ------------------------------------------------------------------------------------------------

def need(condition, what):
    if not condition:
        raise Refusal('configuration: ' + what)


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0


def whole(value):
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def absolute(value, what, strict=False):
    need(isinstance(value, str) and value.startswith('/') and '\0' not in value and '..' not in value.split('/'),
         what + ' must be an absolute path')
    if strict:
        need(not re.search(r'["\\\x00-\x1f]', value), what + ' holds a character the sandbox profile cannot carry')
    return value


def keys(value, required, optional, what):
    need(isinstance(value, dict), what + ' must be an object')
    need(set(required) <= set(value), what + ' is missing ' + ', '.join(sorted(set(required) - set(value))))
    need(set(value) <= set(required) | set(optional), what + ' has unknown ' + ', '.join(sorted(set(value) - set(required) - set(optional))))
    return value


def load_config(path):
    """The untracked run configuration. Reading it opens no credential and starts nothing."""
    try:
        raw = json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError) as problem:
        raise Refusal('configuration: unreadable (%s)' % problem.__class__.__name__)
    raw = keys(raw, ('schema', 'cli', 'model', 'run_root', 'token_file', 'state_dir', 'caps', 'oracle', 'launcher'),
               ('child_path', 'cli_tmp_limit'), 'the configuration')
    need(raw['schema'] == CONFIG_SCHEMA, 'schema must be ' + CONFIG_SCHEMA)
    cli = keys(raw['cli'], ('path', 'sha256'), ('version',), 'cli')
    need(isinstance(cli['sha256'], str) and HEX.fullmatch(cli['sha256']), 'cli sha256 must be a sha256 hex digest')
    need(isinstance(cli.get('version', ''), str), 'cli version must be a string')
    need(isinstance(raw['model'], str) and raw['model'], 'model must be a non-empty string')
    caps = keys(raw['caps'], ('total_usd', 'episode', 'stages', 'probe'), (), 'caps')
    episode = keys(caps['episode'], ('usd', 'seconds', 'turns'), (), 'caps.episode')
    probe = keys(caps['probe'], ('total_usd', 'child_usd', 'child_seconds', 'child_turns'), (), 'caps.probe')
    need(number(caps['total_usd']) and number(episode['usd']) and whole(episode['seconds']) and whole(episode['turns']),
         'caps.total_usd and caps.episode need positive numbers')
    need(number(probe['total_usd']) and number(probe['child_usd']) and whole(probe['child_seconds']) and whole(probe['child_turns']),
         'caps.probe needs positive numbers')
    stages = caps['stages']
    need(isinstance(stages, dict) and all(SAFE_ID.fullmatch(name) and number(value) for name, value in stages.items()),
         'caps.stages maps a stage name to a positive cap')
    oracle = keys(raw['oracle'], ('python', 'seconds'), ('denied_prefixes',), 'oracle')
    need(whole(oracle['seconds']), 'oracle seconds must be a positive integer')
    denied = oracle.get('denied_prefixes', DENY_READ)
    need(isinstance(denied, list) and all(isinstance(item, str) and item.startswith('/') and '\0' not in item for item in denied),
         'oracle denied_prefixes must be a list of absolute paths')
    limit = raw.get('cli_tmp_limit', 44)
    need(whole(limit), 'cli_tmp_limit must be a positive integer')
    child_path = raw.get('child_path', CHILD_PATH)
    need(isinstance(child_path, str) and child_path, 'child_path must be a non-empty string')
    config_dir = Path(path).resolve().parent
    state_dir = raw['state_dir']
    need(isinstance(state_dir, str) and state_dir and '\0' not in state_dir, 'state_dir must be a path')
    return SimpleNamespace(
        path=str(path), config_dir=config_dir, cli_path=absolute(cli['path'], 'cli path'), cli_sha256=cli['sha256'],
        cli_version=cli.get('version') or None, model=raw['model'], run_root=absolute(raw['run_root'], 'run_root', strict=True),
        token_file=absolute(raw['token_file'], 'token_file'),
        state_dir=Path(state_dir) if state_dir.startswith('/') else config_dir / state_dir, child_path=child_path,
        cli_tmp_limit=limit, total_usd=float(caps['total_usd']), episode_usd=float(episode['usd']),
        episode_seconds=episode['seconds'], episode_turns=episode['turns'], stage_usd={k: float(v) for k, v in stages.items()},
        probe_total_usd=float(probe['total_usd']), probe_child_usd=float(probe['child_usd']),
        probe_child_seconds=probe['child_seconds'], probe_child_turns=probe['child_turns'],
        oracle_python=absolute(oracle['python'], 'oracle python'), oracle_seconds=oracle['seconds'], oracle_denied=list(denied),
        launcher=absolute(raw['launcher'], 'launcher'))


# --- preconditions -------------------------------------------------------------------------------------------------

def under_users(path):
    real = os.path.realpath(path)
    return real == HOME_PREFIX or real.startswith(HOME_PREFIX + '/')


def judge_refusal(cfg):
    """None when the oracle may be judged, otherwise the explicit reason. The route never judges unsandboxed.

    The profile always denies every tree in DENY_READ and re-allows only the judged root, so an interpreter anywhere
    under one of them could not start. ``oracle.denied_prefixes`` narrows this courtesy check for the other trees alone (/Users is always checked), for a launcher that
    enforces no profile (the suite's fake).
    """
    # The /Users check is part of the contract and never configurable: it runs first, whatever denied_prefixes holds.
    for prefix in [HOME_PREFIX] + [item for item in cfg.oracle_denied if item != HOME_PREFIX]:
        if under(prefix, cfg.oracle_python):
            return 'refusing to judge: the oracle interpreter is under %s, where the sandbox profile denies reads' % prefix
    if under_users(cfg.run_root):
        return 'refusing to judge: the run root is under %s, where the sandbox profile denies reads' % HOME_PREFIX
    if under_users(cfg.launcher):
        return 'refusing to judge: the launcher is under %s, which is not a system location' % HOME_PREFIX
    real = os.path.realpath(cfg.launcher)
    if not os.path.isfile(real) or not os.access(real, os.X_OK):
        return 'refusing to judge: the configured launcher is not an executable file, and the oracle is never run unsandboxed'
    return None


def hold_lock(cfg):
    """Exclusive, non-blocking lock held for the whole command: a second concurrent run refuses before any claim."""
    cfg.state_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    handle = open(cfg.state_dir / 'root.lock', 'a+')
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        handle.close()
        raise Refusal('another run holds the root lock')
    return handle


def verify_cli(cfg):
    """Bind the CLI to its configured pin by real path and hash before anything runs it; a changed client stops the run."""
    path = Path(cfg.cli_path)
    if not path.is_file() or not os.access(path, os.X_OK):
        raise Refusal('the pinned CLI is not an executable file')
    real = os.path.realpath(path)
    digest = file_sha256(real)
    if digest != cfg.cli_sha256:
        raise Refusal('the pinned CLI differs from the configuration (sha256)')
    with tempfile.TemporaryDirectory(prefix='route-version-') as scratch:
        listed = subprocess.run([real, '--version'], capture_output=True, timeout=30, cwd=scratch,
                                env={'PATH': cfg.child_path, 'HOME': scratch, 'TMPDIR': scratch}).stdout.decode(errors='replace').strip()
    if cfg.cli_version and listed != cfg.cli_version:
        raise Refusal('the pinned CLI reports another version than the configuration')
    return {'realpath': real, 'sha256': digest, 'version': listed}


def read_token(path):
    """The owner's token: a regular file owned by this user, tightened to owner-only, holding one plausible value."""
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    except OSError:
        raise Refusal('the token file is missing or unreadable')
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
            raise Refusal('the token file is not a regular file owned by this user')
        if stat.S_IMODE(info.st_mode) & 0o077:
            os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor) as handle:
            descriptor = None
            token = handle.read().strip()
    except (OSError, UnicodeDecodeError):
        raise Refusal('the token file is unreadable')
    finally:
        if descriptor is not None:
            os.close(descriptor)
    if len(token) < 16 or any(c.isspace() for c in token):
        raise Refusal('the token file does not hold exactly one plausible token')
    return token


def assert_safe_run_root(cfg):
    """The run root is this user's private directory, and no ancestor carries agent instructions or settings."""
    root = Path(cfg.run_root)
    if root.exists() or root.is_symlink():
        info = os.lstat(root)
        if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
            raise Refusal('the run root is not a plain directory')
        if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
            raise Refusal('the run root is not private to this user')
    for ancestor in [root, *root.parents]:
        for name in ANCESTOR_NAMES:
            if os.path.lexists(ancestor / name):
                raise Refusal('%s could reach a child' % (ancestor / name))


INCIDENT = 'incident.json'


def scrub_tree(path):
    """Delete a tree the participant may have made unwritable or unreadable, never following a link."""
    if stat.S_ISDIR(os.lstat(path).st_mode):
        os.chmod(path, 0o700)
        for name in os.listdir(path):
            scrub_tree(os.path.join(path, name))
        os.rmdir(path)
    else:
        os.unlink(path)


def retire_root(root):
    """Delete a run root the participant may have made hard to delete; a root that still cannot go stays for the owner."""
    try:
        scrub_tree(root)
    except OSError:
        pass


def retire_after_hit(cfg, root, name):
    """After a credential hit: record the incident in the state directory, then delete the whole root, so no token-bearing
    byte stays. Later runs refuse on the marker. A root that cannot be deleted stays and refuses them as a leftover."""
    cfg.state_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    marker = cfg.state_dir / INCIDENT
    try:
        temporary = marker.with_name(INCIDENT + '.tmp')
        temporary.write_text(json.dumps({'schema': 'tackle-route-incident/1', 'episode_id': name, 'recorded_at': harness.now()}) + '\n')
        os.replace(temporary, marker)
        scrub_tree(root)
    except (OSError, RecursionError):
        pass


def prepare_run_root(cfg):
    """Create the run root, then require it safe, short enough for the CLI's temp path and empty: one root at a time."""
    if (cfg.state_dir / INCIDENT).exists():
        raise Refusal('a credential incident is recorded in the state directory; the owner must review it and remove %s '
                      'before another run' % INCIDENT)
    root = Path(cfg.run_root)
    longest = os.path.join(str(root / ('p' + '0' * 6) / 'tmp'), 'claude-%d' % os.getuid())
    if len(os.fsencode(longest)) > cfg.cli_tmp_limit:
        raise Refusal('the run root is over the CLI temp-path limit (%d > %d bytes)' % (len(os.fsencode(longest)), cfg.cli_tmp_limit))
    assert_safe_run_root(cfg)
    try:
        root.mkdir(mode=0o700, exist_ok=True)
    except OSError as problem:
        raise Refusal('the run root cannot be created (%s)' % problem.__class__.__name__)
    os.chmod(root, 0o700)
    assert_safe_run_root(cfg)
    if any(root.iterdir()):
        raise Refusal('a previous run root was not retired; the owner must clear it before another run')


def new_root(cfg, prefix, subdirs=('home', 'work', 'tmp')):
    """A fresh private directory under the run root, resolved to its canonical path."""
    root = Path(os.path.realpath(Path(cfg.run_root) / (prefix + os.urandom(3).hex())))
    root.mkdir(mode=0o700)
    os.chmod(root, 0o700)
    for name in subdirs:
        (root / name).mkdir(mode=0o700)
        os.chmod(root / name, 0o700)
    return root


def valid_path(name):
    """A fixture path is relative and plain, and cannot plant harness configuration, memory or a skill.

    Comparison is case-insensitive because APFS is.
    """
    if not isinstance(name, str) or not name or len(name) > 200 or '\\' in name or '\0' in name:
        return False
    parts = name.lower().split('/')
    return not name.startswith('/') and all(p not in FORBIDDEN_PARTS for p in parts) and not parts[-1].endswith(FORBIDDEN_NAMES)


# --- spend ledger ----------------------------------------------------------------------------------------------------

class Ledger:
    """Claims against the owner's ceilings, kept under the state directory. An unsettled claim counts at its cap."""

    def __init__(self, state_dir):
        self.path, self.lock = Path(state_dir) / 'spend.json', Path(state_dir) / 'spend.lock'

    def transaction(self, change):
        self.lock.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with open(self.lock, 'a+') as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            data = json.loads(self.path.read_text()) if self.path.exists() else {'rows': []}
            outcome = change(data['rows'])
            temporary = self.path.with_name(self.path.name + '.tmp')
            temporary.write_text(json.dumps(data, indent=1) + '\n')
            os.replace(temporary, self.path)
            return outcome

    @staticmethod
    def charge(row):
        cost = row.get('cost_usd')
        return float(cost) if row.get('settled') and isinstance(cost, (int, float)) else float(row['cap_usd'])

    def room(self, rows, stage, need_usd, stage_cap, total_cap):
        stage_spent = sum(self.charge(row) for row in rows if row['stage'] == stage)
        if stage_spent + need_usd > stage_cap + 1e-9:
            raise CapReached('the %s stage cap would be passed' % stage)
        if sum(self.charge(row) for row in rows) + need_usd > total_cap + 1e-9:
            raise CapReached('the total ceiling would be passed')

    def check(self, stage, need_usd, stage_cap, total_cap):
        self.transaction(lambda rows: self.room(rows, stage, need_usd, stage_cap, total_cap))

    def claim(self, base, kind, stage, cap_usd, stage_cap, total_cap):
        def change(rows):
            self.room(rows, stage, cap_usd, stage_cap, total_cap)
            taken = sum(1 for row in rows if row['name'] == base or row['name'].startswith(base + '#'))
            name = base if not taken else '%s#%d' % (base, taken + 1)
            rows.append({'name': name, 'kind': kind, 'stage': stage, 'cap_usd': cap_usd, 'claimed_at': harness.now(),
                         'cost_usd': None, 'settled': False})
            return name
        return self.transaction(change)

    def settle(self, name, cost, cap_usd):
        def change(rows):
            row = next(item for item in rows if item['name'] == name)
            known = isinstance(cost, (int, float)) and not isinstance(cost, bool) and cost >= 0
            row.update(cost_usd=float(cost) if known else float(cap_usd), settled=True, settled_at=harness.now())
        self.transaction(change)


# --- scanning --------------------------------------------------------------------------------------------------------

def needles(token):
    return [form.encode() for form in credscan.encodings(token)]


def contains(data, found):
    return any(needle in data for needle in found)


def file_contains(path, found):
    """Chunked search with overlap, so a large file never needs to fit in memory and a token cannot hide on a boundary."""
    overlap = max(len(needle) for needle in found) - 1
    with open(path, 'rb') as handle:
        tail = b''
        while True:
            block = handle.read(SCAN_CHUNK)
            if not block:
                return False
            if contains(tail + block, found):
                return True
            tail = block[-overlap:] if overlap else b''


def token_hits(root, token):
    """Every entry under a tree whose name, link target or content holds the token or an encoding of it; unreadable
    entries count. A hit's own path may contain the token, so the token never appears in what is returned."""
    forms = credscan.encodings(token)
    found = needles(token)
    hits = []

    def unreadable(error):
        hits.append((os.path.relpath(error.filename, root) if error.filename else '') + ' (unreadable)')

    for base, dirs, names in os.walk(root, onerror=unreadable, followlinks=False):
        for name in dirs + names:
            path = os.path.join(base, name)
            relative = os.path.relpath(path, root)
            if any(form in name for form in forms):
                hits.append(relative + ' (name)')
                continue
            try:
                info = os.lstat(path)
                if stat.S_ISLNK(info.st_mode):
                    if contains(os.fsencode(os.readlink(path)), found):
                        hits.append(relative + ' (link target)')
                elif stat.S_ISREG(info.st_mode) and file_contains(path, found):
                    hits.append(relative)
            except OSError:
                hits.append(relative + ' (unreadable)')
    cleaned = []
    for hit in sorted(set(hits)):
        for form in sorted(forms, key=len, reverse=True):
            hit = hit.replace(form, '<token>')
        cleaned.append(hit)
    return cleaned


# --- streams -----------------------------------------------------------------------------------------------------------

def events(raw):
    for line in raw.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict):
            yield event


def blocks(event):
    content = (event.get('message') or {}).get('content') if isinstance(event.get('message'), dict) else None
    return [block for block in content if isinstance(block, dict)] if isinstance(content, list) else []


def result_text(body):
    return body if isinstance(body, str) else ''.join(str(part.get('text', '')) for part in body or [] if isinstance(part, dict))


def tool_calls(raw):
    """Each tool_use of a stream with its matched result: {'id', 'tool', 'input', 'text', 'is_error'}, in call order."""
    uses, results = {}, {}
    for event in events(raw):
        if event.get('type') not in ('assistant', 'user'):
            continue
        for block in blocks(event):
            if block.get('type') == 'tool_use':
                uses[block.get('id')] = {'id': block.get('id'), 'tool': block.get('name'), 'input': block.get('input')}
            elif block.get('type') == 'tool_result':
                results[block.get('tool_use_id')] = {'text': result_text(block.get('content')), 'is_error': bool(block.get('is_error'))}
    return [{**use, **results.get(key, {'text': None, 'is_error': None})} for key, use in uses.items()]


def archive_bytes_read(raw):
    """Bytes of the archive returned to the agent: Read results for it, plus Bash results whose command names it."""
    total = 0
    for call in tool_calls(raw):
        if call['text'] is None or not isinstance(call['input'], dict):
            continue
        named = (call['tool'] == 'Read' and os.path.basename(str(call['input'].get('file_path') or '')) == ARCHIVE) or \
                (call['tool'] == 'Bash' and ARCHIVE in str(call['input'].get('command') or ''))
        if named:
            total += len(call['text'].encode('utf-8'))
    return total


def count_tool_calls(raw):
    seen, anonymous = set(), 0
    for event in events(raw):
        if event.get('type') == 'assistant':
            for block in blocks(event):
                if block.get('type') == 'tool_use':
                    if block.get('id') is None:
                        anonymous += 1
                    else:
                        seen.add(block['id'])
    return len(seen) + anonymous


def skill_use(raw):
    """True when a tool call loads or reads the method's skill."""
    for event in events(raw):
        if event.get('type') == 'assistant':
            for block in blocks(event):
                if block.get('type') == 'tool_use':
                    text = json.dumps(block.get('input') or {})
                    if (block.get('name') == 'Skill' and 'tackle' in text) or 'skills/tackle/' in text:
                        return True
    return False


def harness_faults(raw):
    """Bash results showing the CLI's own temp-file write refused: an instrument fault, never participant behavior."""
    count = 0
    for event in events(raw):
        if event.get('type') == 'user':
            for block in blocks(event):
                if block.get('type') == 'tool_result':
                    text = result_text(block.get('content'))
                    count += bool(text.startswith('Exit code') and HARNESS_FAULT.search(text.rstrip() + '\n'))
    return count


def denial_location(tool, tool_input):
    """Where a refused call pointed: the file of Read, Write and Edit, the search path of Glob and Grep, and for a Glob
    without a path its pattern when that is absolute. Empty when the call named no location."""
    given = tool_input if isinstance(tool_input, dict) else {}
    for key in ('file_path', 'path'):
        if given.get(key):
            return str(given[key])
    pattern = given.get('pattern')
    return pattern if tool == 'Glob' and isinstance(pattern, str) and pattern.startswith('/') else ''


def parse_stream(raw):
    """The init event, the result event and the denials of one session's stream, without copying message text."""
    init = result = None
    for event in events(raw):
        if event.get('type') == 'system' and event.get('subtype') == 'init' and init is None:
            init = event
        if event.get('type') == 'result':
            result = event
    denials = result.get('permission_denials') if result else None
    return {
        'init': {k: init.get(k) for k in ('model', 'permissionMode', 'apiKeySource', 'tools', 'mcp_servers', 'skills', 'plugins',
                                          'memory_paths')} if init else None,
        'result': {k: result.get(k) for k in ('subtype', 'is_error', 'num_turns', 'total_cost_usd')} if result else None,
        'denials': [{'tool': str(d.get('tool_name')), 'path': denial_location(str(d.get('tool_name')), d.get('tool_input'))}
                    for d in denials if isinstance(d, dict)] if isinstance(denials, list) else [],
    }


def isolation_problems(init, root, arm, model):
    """Every isolation property the init event can show must hold; a missing init event or field is itself a problem."""
    if not init:
        return ['no_init_event']
    problems = []
    if init.get('model') != model:
        problems.append('model')
    if init.get('apiKeySource') != 'none':
        problems.append('api_key_source')
    if sorted(init.get('tools') or []) != sorted(PARTICIPANT_TOOLS.split(',')):
        problems.append('tools')
    if init.get('mcp_servers') != []:
        problems.append('mcp_servers')
    plugins = init.get('plugins')
    if not isinstance(plugins, list) or not all(isinstance(p, dict) and p.get('path') == 'builtin'
                                                and str(p.get('source', '')).endswith('@builtin') for p in plugins):
        problems.append('plugins')
    if init.get('permissionMode') != 'dontAsk':
        problems.append('permission_mode')
    if not memory_inside(init.get('memory_paths'), root):
        problems.append('memory_paths')
    if ('tackle' in (init.get('skills') or [])) != (arm == 'method'):
        problems.append('skill_listing')
    return problems


def memory_paths_list(memory):
    paths = []
    for value in (memory or {}).values():
        paths.extend(value if isinstance(value, list) else [value])
    return [str(p) for p in paths]


def memory_inside(memory, root):
    """Memory may come from any source the CLI reports (auto memory, AGENTS.md), but only from inside the run root."""
    paths = memory_paths_list(memory) if isinstance(memory, dict) else []
    return bool(paths) and all(p.startswith(str(root) + '/') for p in paths)


def under(base, path, fold=False):
    """Whether path is base or lies beneath it, with symlinked spellings (/tmp, /var/folders) resolved on both sides."""
    base, path = os.path.realpath(base), os.path.realpath(path)
    if fold:
        base, path = base.lower(), path.lower()
    return path == base or path.startswith(base.rstrip('/') + '/')


def inside_root(path, root):
    """Whether a tool's path, read as the CLI reads it (relative to the work directory), lies in the run's root.

    The volume ignores case, so the comparison does too.
    """
    try:
        return under(root, os.path.normpath(os.path.join(str(root / 'work'), path)), fold=True)
    except ValueError:
        # A path the host cannot resolve (an embedded NUL) is read as inside the root: the conservative reading.
        return True


def unexpected_denials(denials, root, arm):
    """Edits inside the workspace, reads inside the run root and, for the method arm, skill use must never be refused."""
    work, config_root = str(root / 'work'), str(root / 'work' / '.claude').lower()
    found = []
    for denial in denials or []:
        tool, path = denial['tool'], denial['path']
        # Edits to work/.claude itself or anything beneath it are refused on purpose: expected, not a fault.
        if tool in ('Write', 'Edit') and (path.lower() == config_root or path.lower().startswith(config_root + '/')):
            continue
        if tool in ('Write', 'Edit') and (path == '' or path.startswith(work)):
            found.append(tool + ' in workspace')
        elif tool in ('Read', 'Glob', 'Grep') and inside_root(path, root):
            found.append(tool + ' in run root')
        elif tool == 'Skill' and arm == 'method':
            found.append('Skill')
    return found


# --- the working tree ------------------------------------------------------------------------------------------------

def cli_staging_only(path):
    """The CLI always creates <cwd>/.claude/.cc-writes, an empty 0700 staging directory for its own atomic writes."""
    try:
        staging = os.path.join(path, '.cc-writes')
        return (os.path.isdir(path) and not os.path.islink(path) and os.listdir(path) == ['.cc-writes']
                and os.path.isdir(staging) and not os.path.islink(staging) and os.listdir(staging) == [])
    except OSError:
        return False


def harness_config_paths(work):
    """Any .claude entry under the workspace, case-insensitively, except the CLI's own empty staging directory.

    The CLI creates <cwd>/.claude/.cc-writes relative to each command's working directory, so an empty-staging-only
    .claude can appear at any depth and is not participant configuration.
    """
    found = []
    for base, dirs, names in os.walk(work):
        for name in dirs + names:
            if name.lower() == '.claude':
                path = os.path.join(base, name)
                if not cli_staging_only(path):
                    found.append(os.path.relpath(path, work))
    return sorted(found)


def work_hashes(work):
    return {path.relative_to(work).as_posix(): sha(path.read_bytes())
            for path in sorted(Path(work).rglob('*')) if path.is_file() and not path.is_symlink()}


def preserve_tree(work, final):
    """Copy regular single-link files only; links and special entries are recorded by path and kind, never followed.
    The caller must not judge a tree whose ``other`` is not empty: the copy is then partial."""
    files, other = {}, []

    def unreadable(error):
        other.append({'path': os.path.relpath(error.filename, work) if error.filename else '', 'kind': 'unreadable'})

    final.mkdir(parents=True, exist_ok=True)
    for base, dirs, names in os.walk(work, onerror=unreadable):
        relative = Path(base).relative_to(work)
        (final / relative).mkdir(parents=True, exist_ok=True)
        for name in list(dirs):
            if (Path(base) / name).is_symlink():
                dirs.remove(name)
                names.append(name)
        for name in names:
            path = Path(base) / name
            key = (relative / name).as_posix()
            try:
                info = os.lstat(path)
                if stat.S_ISREG(info.st_mode) and info.st_nlink == 1:
                    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), 'rb') as handle:
                        opened = os.fstat(handle.fileno())
                        if stat.S_ISREG(opened.st_mode) and opened.st_nlink == 1:
                            data = handle.read()
                            (final / relative / name).write_bytes(data)
                            files[key] = sha(data)
                            continue
                kind = 'symlink' if stat.S_ISLNK(info.st_mode) else 'hardlink' if stat.S_ISREG(info.st_mode) else 'special'
                other.append({'path': key, 'kind': kind})
            except OSError:
                other.append({'path': key, 'kind': 'unreadable'})
    return files, sorted(other, key=lambda item: item['path'])


def copy_tree(source, destination):
    """Mirror directories and regular files; a link anywhere refuses, because the copy would reach outside."""
    destination.mkdir(parents=True, exist_ok=True)
    for path in sorted(Path(source).rglob('*')):
        if path.is_symlink():
            raise Refusal('a link in %s' % Path(source).name)
        target = destination / path.relative_to(source)
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        elif path.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())


# --- running the CLI -------------------------------------------------------------------------------------------------

def install_signal_handlers():
    """SIGTERM and SIGHUP become SystemExit, so every finally block runs and the child is killed."""
    def stop(signum, frame):
        raise SystemExit(128 + signum)
    for signum in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(signum, stop)


class Child:
    def __init__(self):
        self.exit, self.timed_out, self.interrupted, self.error = None, False, False, None
        self.stdout, self.stderr, self.started, self.ended, self.seconds = b'', b'', '', '', 0.0


def drain(pipe, sink):
    try:
        for chunk in iter(lambda: pipe.read(65536), b''):
            sink.append(chunk)
    except (OSError, ValueError):
        pass


def feed(process, prompt, child):
    try:
        process.stdin.write(prompt)
        process.stdin.close()
    except OSError:
        child.error = child.error or 'stdin_write_failed'


def kill_group(process, signum):
    try:
        os.killpg(process.pid, signum)
    except OSError:
        pass


def launch(argv, cwd, env, prompt, seconds):
    """Run one process in its own session. Streams stay in memory and the group is killed at the deadline, on any
    interruption and at the end, so nothing outlives the call."""
    child = Child()
    child.started = harness.now()
    begin = time.monotonic()
    out, err = [], []
    process = None
    threads = []
    try:
        process = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, start_new_session=True)
        threads = [threading.Thread(target=drain, args=(process.stdout, out), daemon=True),
                   threading.Thread(target=drain, args=(process.stderr, err), daemon=True),
                   threading.Thread(target=feed, args=(process, prompt, child), daemon=True)]
        for thread in threads:
            thread.start()
        try:
            process.wait(timeout=max(seconds, 0.1))
        except subprocess.TimeoutExpired:
            child.timed_out = True
            kill_group(process, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                kill_group(process, signal.SIGKILL)
                process.wait()
        for thread in threads:
            thread.join(timeout=5)
    except (KeyboardInterrupt, SystemExit):
        child.interrupted = True
        child.error = 'interrupted'
    except Exception as problem:
        child.error = child.error or 'controller_' + type(problem).__name__
    finally:
        if process is not None:
            kill_group(process, signal.SIGKILL)
            if process.poll() is None:
                process.wait()
            for thread in threads:
                thread.join(timeout=2)
            for pipe in (process.stdin, process.stdout, process.stderr):
                try:
                    pipe.close()
                except OSError:
                    pass
    child.exit = process.returncode if process else None
    child.stdout, child.stderr = b''.join(out), b''.join(err)
    child.ended = harness.now()
    child.seconds = time.monotonic() - begin
    return child


def sandbox_settings(root):
    """Bash runs sandboxed: no network, writes only in work and tmp, reads denied outside the run root.

    File tools may read the run root (the method arm's skill lives in its HOME) and edit only the working directory;
    anything else is refused because the session runs in dontAsk mode. Nothing in a run may create work/.claude.
    A deny rule outranks every allow rule, so the file tools' deny rules leave out each tree that holds the run root:
    the root sits under a tree that Bash is denied and allowRead re-allows, and a rule for that tree would refuse the
    participant its own files.
    """
    return {
        'sandbox': {
            'enabled': True,
            'failIfUnavailable': True,
            'autoAllowBashIfSandboxed': True,
            'allowUnsandboxedCommands': False,
            'network': {'allowedDomains': []},
            'filesystem': {'denyRead': list(DENY_READ), 'allowRead': [str(root)],
                           'allowWrite': [str(root / 'work'), str(root / 'tmp')], 'denyWrite': [str(root / 'work' / '.claude')]},
        },
        'permissions': {
            'defaultMode': 'dontAsk',
            'allow': ['Read(/%s/**)' % root, 'Edit(/%s/work/**)' % root, 'Skill'],
            'deny': ['Read(/%s/**)' % prefix for prefix in DENY_READ if not under(prefix, root)]
                    + ['Edit(/%s/work/.claude/**)' % root]
                    + ['Edit(/%s/**)' % prefix for prefix in DENY_EDIT if not under(prefix, root)]
                    + ['WebFetch', 'WebSearch'],
        },
    }


def participant_argv(cli, cfg, settings, turns, budget):
    return [cli['realpath'], '-p', '--output-format', 'stream-json', '--verbose', '--model', cfg.model,
            '--max-turns', str(turns), '--max-budget-usd', repr(round(budget, 4)), '--no-session-persistence',
            '--strict-mcp-config', '--setting-sources', 'user,project', '--settings', json.dumps(settings, sort_keys=True),
            '--permission-mode', 'dontAsk', '--tools', PARTICIPANT_TOOLS]


def child_env(cfg, root, token):
    home, tmp = root / 'home', root / 'tmp'
    return {'PATH': cfg.child_path, 'HOME': str(home), 'TMPDIR': str(tmp), 'LANG': 'en_US.UTF-8', 'TERM': 'dumb',
            'NO_COLOR': '1', 'DISABLE_TELEMETRY': '1', 'DISABLE_ERROR_REPORTING': '1', 'DISABLE_AUTOUPDATER': '1',
            'CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC': '1', TOKEN_VARIABLE: token,
            # The CLI's own temporary files (the Bash tool's cwd tracking among them) stay inside the run's writable tmp.
            'CLAUDE_CODE_TMPDIR': str(tmp)}


def stage_skill(home, files, expected):
    """The arm's exact skill tree, verified by digest after it is staged."""
    skill = home / '.claude' / 'skills' / 'tackle'
    for relative, data in files.items():
        target = skill / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    if harness.tree_digest(skill) != expected:
        raise Refusal('the staged skill tree differs from the verified one')


# --- neutral records ---------------------------------------------------------------------------------------------------

class Neutral:
    """Replaces every absolute path the route knows with a neutral token, and redacts what is still leak-shaped."""

    def __init__(self, cfg, extra=()):
        pairs = list(extra)
        for path, token in ((cfg.cli_path, '<cli>'), (cfg.token_file, '<token-file>'), (cfg.run_root, '<run-root>'),
                            (str(cfg.state_dir), '<state>'), (str(cfg.config_dir), '<config>'), (cfg.oracle_python, '<oracle-python>')):
            pairs.append((path, token))
        self.pairs = []
        for path, token in pairs:
            if path:
                for form in {str(path), os.path.realpath(path)}:
                    self.pairs.append((form, token))
        self.pairs.sort(key=lambda item: -len(item[0]))

    def paths(self, value):
        for path, token in self.pairs:
            if path and path != '/':
                value = value.replace(path, token)
        return value

    def text(self, value):
        value = self.paths(value)
        for pattern in protocol().LEAKS:
            value = pattern.sub('<redacted>', value)
        return value

    def apply(self, value):
        if isinstance(value, str):
            return self.text(value)
        if isinstance(value, dict):
            return {self.text(key) if isinstance(key, str) else key: self.apply(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self.apply(item) for item in value]
        return value


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')


# --- judging ---------------------------------------------------------------------------------------------------------

def judge_profile(root):
    """The oracle's sandbox: no network, reads denied under the home and temporary trees except the one judged root,
    writes only to its scratch directory."""
    root = str(root)
    denied = ' '.join('(subpath "%s")' % prefix for prefix in DENY_READ)
    return '\n'.join(['(version 1)', '(allow default)', '(deny network*)', '(deny file-read* %s)' % denied,
                      '(allow file-read* (subpath "%s"))' % root, '(deny file-write*)',
                      '(allow file-write* (subpath "%s") (literal "/dev/null"))' % (root + '/scratch')]) + '\n'


def judged_digest(root):
    files = {}
    for sub in ('oracle', 'final'):
        for path in sorted((root / sub).rglob('*')):
            if path.is_file():
                files[path.relative_to(root).as_posix()] = sha(path.read_bytes())
    files['transcript.jsonl'] = sha((root / 'transcript.jsonl').read_bytes())
    return harness.mapping_digest(files)


def parse_verdict(stdout):
    try:
        value = json.loads(stdout.decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
        raise OracleError('oracle_malformed')
    if not isinstance(value, dict):
        raise OracleError('oracle_malformed')
    outcome, reason, scores = value.get('outcome'), value.get('invalid_reason'), value.get('scores')
    if outcome not in ('fell', 'avoided', 'invalid') or not (reason is None or isinstance(reason, str)):
        raise OracleError('oracle_malformed')
    if not isinstance(scores, dict) or not scores or any(not isinstance(k, str) or type(v) is not int or v not in (0, 1, 2)
                                                         for k, v in scores.items()):
        raise OracleError('oracle_malformed')
    return {'outcome': outcome, 'invalid_reason': reason, 'scores': scores}


def judge(cfg, oracle_dir, final_dir, transcript):
    """Run the oracle on copies of the final tree and transcript, under the platform launcher, outside the participant.

    Returns the verdict. Raises Refusal when there is no safe way to judge and OracleError when the oracle fails.
    """
    reason = judge_refusal(cfg)
    if reason:
        raise Refusal(reason)
    launcher = os.path.realpath(cfg.launcher)
    root = new_root(cfg, 'j', subdirs=('scratch',))
    try:
        copy_tree(oracle_dir, root / 'oracle')
        copy_tree(final_dir, root / 'final')
        (root / 'transcript.jsonl').write_bytes(transcript)
        before = judged_digest(root)
        scratch = root / 'scratch'
        argv = [launcher, '-p', judge_profile(root), cfg.oracle_python, '-B', str(root / 'oracle' / 'check.py'),
                '--final', str(root / 'final'), '--transcript', str(root / 'transcript.jsonl')]
        env = {'PATH': '/usr/bin:/bin', 'HOME': str(scratch), 'TMPDIR': str(scratch), 'LANG': 'en_US.UTF-8'}
        child = launch(argv, scratch, env, b'', cfg.oracle_seconds)
        if child.interrupted:
            raise SystemExit(130)
        if child.timed_out:
            raise OracleError('oracle_timeout')
        if child.exit != 0:
            raise OracleError('oracle_exit')
        verdict = parse_verdict(child.stdout)
        if judged_digest(root) != before:
            raise OracleError('oracle_modified_input')
        if verdict['invalid_reason']:
            verdict['invalid_reason'] = Neutral(cfg, [(str(root), '<judged>')]).text(verdict['invalid_reason'])
        return verdict
    finally:
        retire_root(root)


# --- the cohort ---------------------------------------------------------------------------------------------------------

def load_package(repo, scenario, variant, sealed):
    """A committed scenario package: prompts and fixture under input/, the oracle beside it, checked against its seal."""
    base = Path(repo) / 'eval' / 'scenarios' / scenario / 'variants' / variant
    if not (base / 'input').is_dir():
        raise Refusal('the package of %s/%s has no input' % (scenario, variant))
    if not (base / 'oracle' / 'check.py').is_file():
        raise Refusal('the oracle of %s/%s is missing' % (scenario, variant))
    files = harness.read_tree(base / 'input')
    if harness.files_digest(files) != sealed:
        raise Refusal('the input digest of %s/%s differs from the sealed manifest' % (scenario, variant))
    sessions = sorted((int(m[1]), name) for name in files for m in [SESSION_PROMPT.fullmatch(name)] if m)
    if ('task.md' in files) == bool(sessions):
        raise Refusal('the input of %s/%s holds exactly one of task.md and sessions/NN.md' % (scenario, variant))
    names = ['task.md'] if 'task.md' in files else [name for _, name in sessions]
    fixture = {}
    for name, data in files.items():
        if name in names:
            continue
        if not name.startswith('fixture/'):
            raise Refusal('the input of %s/%s holds a file that is neither a prompt nor fixture' % (scenario, variant))
        if not valid_path(name[len('fixture/'):]):
            raise Refusal('unsafe fixture file in %s/%s' % (scenario, variant))
        fixture[name[len('fixture/'):]] = data
    try:
        prompts = [(name, files[name].decode('utf-8')) for name in names]
    except UnicodeDecodeError:
        raise Refusal('a prompt of %s/%s is not UTF-8' % (scenario, variant))
    return SimpleNamespace(scenario=scenario, variant=variant, oracle=base / 'oracle', prompts=prompts, fixture=fixture,
                           digest=sealed)


def load_cohort(cohort_dir, repo, install):
    """The sealed manifest, its recorded prefix, the install tree and every package, all checked before any launch."""
    check = protocol()
    manifest = harness.load(Path(cohort_dir) / 'manifest.json', 'manifest.json')
    report = check.Report()
    context = check.check_manifest(manifest, report)
    if report.errors or context is None:
        raise Refusal('the cohort manifest fails the protocol checker: ' +
                      '; '.join('%s: %s' % (e['code'], e['text']) for e in report.errors[:3]))
    order = context['order']
    for entry in order:
        for key in ('episode_id', 'scenario_id', 'variant_id'):
            if not SAFE_ID.fullmatch(entry[key]):
                raise Refusal('unsafe identifier in the manifest order: %r' % entry[key][:40])
        if entry['arm'] not in ARMS:
            raise Refusal('arm %s is not supported by this route (control and method only)' % entry['arm'])
    install_files, install_digest = None, None
    if any(entry['arm'] == 'method' for entry in order):
        if not install:
            raise Usage('--install <dir> is required for a method arm')
        install_files = harness.read_install(install)
        install_digest = harness.files_digest(install_files)
        if install_digest != manifest['artifacts']['candidate_sha256']:
            raise Refusal('the skill tree digest differs from the sealed manifest')
    packages = {}
    for entry in order:
        key = (entry['scenario_id'], entry['variant_id'])
        if key not in packages:
            packages[key] = load_package(repo, key[0], key[1], context['variants'][key]['fixture_sha256'])
    path = Path(cohort_dir) / 'episodes.jsonl'
    existing = path.read_bytes() if path.exists() else b''
    if existing and not existing.endswith(b'\n'):
        raise Refusal('episodes.jsonl does not end with a newline')
    lines = existing.split(b'\n')[:-1] if existing else []
    if len(lines) > len(order):
        raise Refusal('episodes.jsonl holds more records than the manifest order')
    for position, line in enumerate(lines):
        try:
            recorded = json.loads(line)
        except ValueError:
            raise Refusal('episodes.jsonl holds a line that is not JSON')
        if not isinstance(recorded, dict) or recorded.get('episode_id') != order[position]['episode_id']:
            raise Refusal('episodes.jsonl does not follow the manifest order at line %d' % (position + 1))
    return SimpleNamespace(manifest=manifest, context=context, order=order, install_files=install_files,
                           install_digest=install_digest, packages=packages, lines=lines, path=path,
                           by_id={e['episode_id']: (i, e) for i, e in enumerate(order)})


def append_record(cohort, fields):
    """Chain one episode record to the previous line, check it with the protocol checker, and append it."""
    check = protocol()
    line = dict(fields, prev_sha256=sha(cohort.lines[-1]) if cohort.lines else '0' * 64)
    report = check.Report()
    at = report.at(check.EPISODES, len(cohort.lines) + 1)
    if at.closed(line, check.EPISODE_FIELDS, 'record'):
        check.check_fields(line, at)
        check.check_against_manifest(line, cohort.context, cohort.by_id, at)
    if report.errors:
        raise Refusal('the record fails the protocol checker: ' +
                      '; '.join('%s: %s' % (e['code'], e['text']) for e in report.errors[:3]))
    data = json.dumps(line, ensure_ascii=False).encode()
    with open(cohort.path, 'ab') as handle:
        handle.write(data + b'\n')
        handle.flush()
        os.fsync(handle.fileno())
    cohort.lines.append(data)
    return line


def base_line(stage, entry, position):
    cohort, judge_field = stage.cohort, stage.cohort.manifest['judge']
    return {'schema': 'tackle-episode/1', 'cohort_id': cohort.manifest['cohort_id'], 'episode_id': entry['episode_id'],
            'scenario_id': entry['scenario_id'], 'variant_id': entry['variant_id'],
            'split': cohort.context['variants'][(entry['scenario_id'], entry['variant_id'])]['split'], 'arm': entry['arm'],
            'seed': entry['seed'], 'order_index': position,
            'artifact_sha256': cohort.install_digest if entry['arm'] == 'method' else None,
            'executor': {'harness': 'claude-code', 'model': stage.cfg.model, 'effort': NA}, 'roles': [],
            'judge': {'kind': 'mechanical', 'model_family': judge_field['model_family'], 'blinded': judge_field['blinded']}}


def append_unobserved(stage, entry, position, reason):
    """A planned episode that did not run: every score null, every cost n/a, no transcript."""
    line = dict(base_line(stage, entry, position), rule_exposure=False, outcome='unobserved', invalid_reason=None,
                scores={name: None for name in SCORE_FIELDS},
                cost={'tokens_in': NA, 'tokens_out': NA, 'wall_seconds': NA, 'tool_calls': NA, 'files_written': NA},
                transcript_sha256=None, started_at=NA, finished_at=NA)
    append_record(stage.cohort, line)
    directory = stage.out / entry['episode_id']
    directory.mkdir(parents=True, mode=0o700)
    dump(directory / 'episode.json', {'schema': EPISODE_SCHEMA, 'episode_id': entry['episode_id'], 'outcome': 'unobserved',
                                      'reason': reason})
    return line


# --- one episode -------------------------------------------------------------------------------------------------------

def observe(stage, entry, package):
    """Stage a fresh root and run the sessions in order. Interruptions and controller faults are reported, not raised."""
    cfg, arm = stage.cfg, entry['arm']
    seen = SimpleNamespace(root=None, sessions=[], limit=None, error=None, interrupted=False, baseline={}, argv=None,
                           settings_text=None)
    try:
        seen.root = root = new_root(cfg, 'p')
        for relative, data in package.fixture.items():
            target = root / 'work' / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        seen.baseline = work_hashes(root / 'work')
        if arm == 'method':
            stage_skill(root / 'home', stage.cohort.install_files, stage.cohort.install_digest)
        elif (root / 'home' / '.claude').exists():
            raise Refusal('the control HOME holds a .claude directory')
        settings = sandbox_settings(root)
        seen.settings_text = json.dumps(settings, sort_keys=True)
        env = child_env(cfg, root, stage.token)
        deadline = time.monotonic() + cfg.episode_seconds
        turns_used, usd_used = 0, 0.0
        for index, (name, text) in enumerate(package.prompts, 1):
            seconds_left = deadline - time.monotonic()
            turns_left, usd_left = cfg.episode_turns - turns_used, cfg.episode_usd - usd_used
            if seconds_left <= 0:
                seen.limit = 'wall_clock'
                break
            if turns_left <= 0 or round(usd_left, 4) <= 0:  # the CLI is given the budget rounded to four places
                seen.limit = 'error_max_turns' if turns_left <= 0 else 'error_max_budget_usd'
                break
            argv = participant_argv(stage.cli, cfg, settings, turns_left, usd_left)
            seen.argv = seen.argv or argv
            child = launch(argv, root / 'work', env, text.encode(), seconds_left)
            session = SimpleNamespace(index=index, prompt=name, child=child, stream=parse_stream(child.stdout))
            seen.sessions.append(session)
            result = session.stream['result'] or {}
            if isinstance(result.get('num_turns'), int):
                turns_used += result['num_turns']
            if isinstance(result.get('total_cost_usd'), (int, float)):
                usd_used += result['total_cost_usd']
            if child.interrupted or child.timed_out or child.error or child.exit != 0 \
                    or result.get('subtype') != 'success' or result.get('is_error') is not False:
                break
            if harness_config_paths(root / 'work'):
                break  # the next session would load what the participant planted; classify records the episode invalid
    except (KeyboardInterrupt, SystemExit):
        seen.interrupted = True
    except Refusal:
        seen.error = 'controller_refusal'
    except Exception as problem:
        seen.error = 'controller_' + type(problem).__name__
    seen.interrupted = seen.interrupted or any(s.child.interrupted for s in seen.sessions)
    return seen


def find_token(stage, seen):
    """Where the token or an encoding of it appears: the streams first, then every entry under the root."""
    found = needles(stage.token)
    locations = [label for label in ('stdout', 'stderr') if any(contains(getattr(s.child, label), found) for s in seen.sessions)]
    if seen.root is not None:
        try:
            locations += token_hits(seen.root, stage.token)
        except Exception:
            locations.append('(scan failed)')
    return locations


def invalid_reason(arm, problems, used_skill, listed):
    """The closed reason of an isolation-class invalid episode."""
    others = [p for p in problems if p != 'skill_listing']
    if arm == 'control' and (used_skill or listed) and not others:
        return REASON_CONTROL
    if arm == 'method' and problems == ['skill_listing']:
        return REASON_METHOD
    return REASON_ISOLATION


def classify(stage, seen, locations, arm):
    """The episode's outcome from what was observed, in a fixed order. ``outcome`` None means the oracle decides."""
    cfg, sessions, root = stage.cfg, seen.sessions, seen.root
    decision = SimpleNamespace(outcome=None, reason=None, error=seen.error, limit=seen.limit, stop=False, exposure=False,
                               problems=[], config_paths=[])
    for session in sessions:
        for problem in isolation_problems(session.stream['init'], root, arm, cfg.model) if root is not None else []:
            if problem not in decision.problems:
                decision.problems.append(problem)
    decision.config_paths = harness_config_paths(root / 'work') if root is not None and (root / 'work').is_dir() else []
    denials = [d for s in sessions for d in s.stream['denials']]
    refused = unexpected_denials(denials, root, arm) if root is not None else []
    faults = sum(harness_faults(s.child.stdout) for s in sessions)
    used_skill = arm == 'control' and any(skill_use(s.child.stdout) for s in sessions)
    last = sessions[-1] if sessions else None
    result = (last.stream['result'] if last else None) or {}
    listed = 'skill_listing' in decision.problems
    decision.exposure = arm == 'control' and (used_skill or listed)

    def stop(outcome, error=None, reason=None):
        decision.outcome, decision.reason, decision.stop = outcome, reason, True
        decision.error = error or decision.error

    if seen.interrupted:
        stop('error', 'interrupted')
    elif locations:
        stop('invalid', reason=REASON_CREDENTIAL)
    elif seen.error:
        stop('error')
    elif (set(decision.problems) - {'no_init_event'}) or used_skill:
        # An observed isolation fault or a control arm's skill use outranks a limit or a timeout: the stage must stop.
        stop('invalid', reason=invalid_reason(arm, decision.problems, used_skill, listed))
    elif seen.limit == 'wall_clock' or (last and last.child.timed_out):
        decision.outcome, decision.limit = 'timeout', 'wall_clock'
    elif seen.limit or result.get('subtype') in LIMITS:
        decision.outcome, decision.limit = 'timeout', seen.limit or result.get('subtype')
    elif not sessions or last.child.exit != 0 or last.child.error or result.get('subtype') != 'success' \
            or result.get('is_error') is not False:
        stop('error', 'cli_' + str(result.get('subtype') or 'no_result'))
    elif decision.problems:
        stop('invalid', reason=invalid_reason(arm, decision.problems, used_skill, listed))
    elif refused:
        stop('error', 'unexpected_denial')
    elif faults:
        stop('error', 'harness_fault')
    elif decision.config_paths:
        stop('invalid', reason=REASON_CONFIG)
    return decision


def session_record(neutral, session, withheld):
    child, stream = session.child, session.stream
    memory = (stream['init'] or {}).get('memory_paths')
    record = {
        'index': session.index, 'prompt': session.prompt, 'exit': child.exit, 'timed_out': child.timed_out,
        'started_at': child.started, 'finished_at': child.ended,
        'stdout': {'bytes': len(child.stdout), 'sha256': sha(child.stdout)},
        'stderr': {'bytes': len(child.stderr), 'sha256': sha(child.stderr)},
        'num_turns': (stream['result'] or {}).get('num_turns'), 'cost_usd': (stream['result'] or {}).get('total_cost_usd'),
        'permission_denials': [{'tool': d['tool'], 'path': d['path']} for d in stream['denials']],
        'memory_sources': {k: sorted(memory_paths_list({k: v})) for k, v in memory.items()} if isinstance(memory, dict) else None,
        'harness_faults': harness_faults(child.stdout)}
    if withheld:
        record['stdout']['withheld'] = record['stderr']['withheld'] = True
    return neutral.apply(record)


def holds_token(value, found):
    """Whether the JSON of a record carries the token or an encoding of it, in either JSON spelling."""
    return any(contains(json.dumps(value, ensure_ascii=ascii_only).encode(), found) for ascii_only in (True, False))


def seal_record(token, directory, neutral, record, line):
    """The episode.json content and the protocol line to keep, and whether the episode was withheld.

    Both are scanned, because the line is not the neutralized record: one that carries the token is never kept. The
    episode becomes a credential hit with nothing retained.
    """
    found = needles(token)
    written = neutral.apply(record)
    if not (holds_token(written, found) or holds_token(line, found)):
        return written, line, False
    shutil.rmtree(directory, ignore_errors=True)
    directory.mkdir(mode=0o700)
    written = {'schema': EPISODE_SCHEMA, 'episode_id': line['episode_id'], 'outcome': 'invalid',
               'credential': {'hit': True, 'locations': ['record']}}
    line = dict(line, outcome='invalid', invalid_reason=REASON_CREDENTIAL, scores={name: None for name in SCORE_FIELDS},
                rule_exposure=False)
    return written, line, True


def run_episode(stage, entry, position):
    """Run, scan, classify, judge and record one episode. Returns the protocol line, whether the stage must stop,
    and whether the run was interrupted."""
    cfg, cohort = stage.cfg, stage.cohort
    arm = entry['arm']
    package = cohort.packages[(entry['scenario_id'], entry['variant_id'])]
    directory = stage.out / entry['episode_id']
    claim = stage.ledger.claim(entry['episode_id'], 'episode', stage.name, cfg.episode_usd, stage.stage_cap, cfg.total_usd)
    directory.mkdir(parents=True, mode=0o700)
    started, begin = harness.now(), time.monotonic()
    seen = observe(stage, entry, package)
    root = seen.root
    pairs = list(stage.paths)
    if root is not None:
        pairs += [(str(root / name), '<%s>' % name) for name in ('home', 'work', 'tmp')] + [(str(root), '<runtime>')]
    neutral = Neutral(cfg, pairs)
    locations = find_token(stage, seen)
    if locations and root is not None:
        retire_after_hit(cfg, root, entry['episode_id'])
    complete = root is not None and '(scan failed)' not in locations
    clean = not locations and not seen.interrupted and complete
    decision = classify(stage, seen, locations, arm)
    sessions = seen.sessions
    raws = [s.child.stdout for s in sessions]
    transcript = b''.join(raw if raw.endswith(b'\n') or not raw else raw + b'\n' for raw in raws)
    hashes = [sha(raw) for raw in raws]
    transcript_sha = hashes[0] if len(hashes) == 1 else sha(json.dumps(hashes, separators=(',', ':')).encode())
    costs = [(s.stream['result'] or {}).get('total_cost_usd') for s in sessions]
    cost_known = bool(sessions) and all(isinstance(value, (int, float)) for value in costs)
    cost_usd = round(sum(costs), 6) if cost_known else None
    observed = []
    for session in sessions:
        model = (session.stream['init'] or {}).get('model')
        if model and model not in observed:
            observed.append(model)
    tool_total = sum(count_tool_calls(s.child.stdout) for s in sessions)
    metrics = {'archive_bytes_read': sum(archive_bytes_read(s.child.stdout) for s in sessions), 'tool_calls': tool_total}
    record = {
        'schema': EPISODE_SCHEMA, 'episode_id': entry['episode_id'], 'scenario_id': entry['scenario_id'],
        'variant_id': entry['variant_id'], 'arm': arm, 'seed': entry['seed'], 'order_index': position,
        'cli': {'version': stage.cli['version'], 'sha256': stage.cli['sha256']},
        'model': {'requested': cfg.model, 'observed': observed},
        'install_sha256': cohort.install_digest if arm == 'method' else None, 'input_sha256': package.digest,
        'limits': {'seconds': cfg.episode_seconds, 'turns': cfg.episode_turns, 'usd': cfg.episode_usd},
        'isolation_problems': decision.problems,
        'skill_listed': any('tackle' in ((s.stream['init'] or {}).get('skills') or []) for s in sessions),
        'credential': {'hit': bool(locations), 'locations': locations}, 'harness_config_paths': decision.config_paths,
        'interrupted': seen.interrupted, 'limit_reached': decision.limit, 'metrics': metrics,
        'sessions': [session_record(neutral, s, bool(locations)) for s in sessions]}
    if seen.argv:
        settings_text = seen.settings_text
        record['argv'] = ['<cli>'] + ['<settings>' if part == settings_text else part for part in seen.argv[1:]]
        record['settings_sha256'] = sha(neutral.paths(settings_text).encode())
    outcome, reason, scores, final_files = decision.outcome, decision.reason, {name: None for name in SCORE_FIELDS}, {}
    error = decision.error
    if clean:
        for session in sessions:
            session_dir = directory / 'sessions' / ('%02d' % session.index)
            session_dir.mkdir(parents=True)
            (session_dir / 'stdout.jsonl').write_bytes(session.child.stdout)
            (session_dir / 'stderr.txt').write_bytes(session.child.stderr)
        final_files, other = preserve_tree(root / 'work', directory / 'final')
        record['final_tree'] = {'files': len(final_files), 'other': other}
        retire_root(root)
        if outcome is None and other:
            # A link, a special file or an unreadable entry is not in the copy: the oracle is never given a partial tree.
            outcome, reason = 'invalid', REASON_TREE
        elif outcome is None:
            try:
                verdict = judge(cfg, package.oracle, directory / 'final', transcript)
            except OracleError as problem:
                outcome, error, decision.stop = 'error', problem.code, True
            except Refusal:
                outcome, error, decision.stop = 'error', 'oracle_refused', True
            except (KeyboardInterrupt, SystemExit):
                outcome, error, decision.stop, seen.interrupted = 'error', 'interrupted', True, True
                record['interrupted'] = True
            else:
                outcome = verdict['outcome']
                if outcome == 'invalid':
                    reason = 'oracle: ' + (verdict['invalid_reason'] or 'no reason given')
                else:
                    scores['correct_action'] = 2 if outcome == 'avoided' else 0
                dump(directory / 'oracle.json', neutral.apply({'outcome': outcome, 'invalid_reason': reason,
                                                               'scores': verdict['scores']}))
    else:
        record['final_tree'] = {'withheld': True}
    wall = int(round(time.monotonic() - begin))
    finished = harness.now()
    record.update(outcome=outcome, invalid_reason=reason, error=error, cost_usd=cost_usd, started_at=started, finished_at=finished)
    # Settle the claim: an unreported cost is charged at the episode cap, never at zero.
    stage.ledger.settle(claim, cost_usd if cost_known else None, cfg.episode_usd)
    tokens_in = [usage.claude_code_result(raw)['tokens_in'] for raw in raws]
    tokens_out = [usage.claude_code_result(raw)['tokens_out'] for raw in raws]
    cost = {'tokens_in': harness.total(tokens_in) if sessions else NA, 'tokens_out': harness.total(tokens_out) if sessions else NA,
            'wall_seconds': wall, 'tool_calls': tool_total if sessions else NA,
            'files_written': sum(1 for key, digest in final_files.items() if seen.baseline.get(key) != digest) if clean else NA}
    line = dict(base_line(stage, entry, position), rule_exposure=decision.exposure, outcome=outcome, invalid_reason=reason,
                scores=scores, cost=cost, transcript_sha256=transcript_sha, started_at=started, finished_at=finished)
    written, line, withheld = seal_record(stage.token, directory, neutral, record, line)
    decision.stop = decision.stop or withheld
    dump(directory / 'episode.json', written)
    append_record(cohort, line)
    return line, decision.stop, seen.interrupted


# --- the run command ----------------------------------------------------------------------------------------------------

def episode_paths(args):
    pairs = []
    for value, token in ((args.repo, '<repo>'), (args.out, '<out>'), (args.cohort, '<cohort>'), (args.install, '<install>')):
        if value:
            pairs += [(str(Path(value).absolute()), token), (os.path.realpath(value), token)]
    return pairs


def cmd_run(args):
    cfg = load_config(args.config)
    if args.stage not in cfg.stage_usd:
        raise Refusal("the stage '%s' has no cap in the configuration" % args.stage)
    reason = judge_refusal(cfg)
    if reason:
        raise Refusal(reason)
    lock = hold_lock(cfg)
    try:
        cli = verify_cli(cfg)
        prepare_run_root(cfg)
        cohort = load_cohort(args.cohort, args.repo, args.install)
        out = Path(args.out).absolute()
        pending = [(i, e) for i, e in enumerate(cohort.order) if i >= len(cohort.lines)]
        for _, entry in pending:
            if (out / entry['episode_id']).exists():
                raise Refusal('the episode directory already exists: %s' % entry['episode_id'])
        stage = SimpleNamespace(cfg=cfg, name=args.stage, stage_cap=cfg.stage_usd[args.stage], cli=cli, token=None,
                                ledger=Ledger(cfg.state_dir), cohort=cohort, out=out, paths=episode_paths(args))
        ran = stopped = None
        counts = {'observed': 0, 'unobserved': 0}
        for position, entry in pending:
            if stopped:
                append_unobserved(stage, entry, position, 'cap')
                counts['unobserved'] += 1
                continue
            try:
                stage.ledger.check(stage.name, cfg.episode_usd, stage.stage_cap, cfg.total_usd)
            except CapReached as problem:
                stopped = str(problem)
                print('stage stopped: %s' % stopped, flush=True)
                append_unobserved(stage, entry, position, 'cap')
                counts['unobserved'] += 1
                continue
            if stage.token is None:
                stage.token = read_token(cfg.token_file)
            line, stop, interrupted = run_episode(stage, entry, position)
            counts['observed'] += 1
            print(json.dumps({'episode_id': line['episode_id'], 'outcome': line['outcome'], 'invalid_reason': line['invalid_reason']}),
                  flush=True)
            if interrupted:
                return 130
            if stop:
                ran = 'a fault stopped the stage after %s' % line['episode_id']
                break
        print('run: observed=%d unobserved=%d recorded=%d of %d%s' % (
            counts['observed'], counts['unobserved'], len(cohort.lines), len(cohort.order), '; ' + ran if ran else ''))
        return 1 if ran else 0
    finally:
        lock.close()


# --- the probe command --------------------------------------------------------------------------------------------------

def probe_prompt(repository, workspace, inside, content):
    """The fixed probe. ``inside`` is a file in the child's own work tree, which it writes with command 6 and must then be
    able to Read: the other two reads must be refused."""
    return ('This is a technical sandbox probe for a test harness. Run each numbered shell command below with the Bash tool, '
            'one command per call, exactly as written, even if it fails, and run nothing else:\n'
            "1. printenv | cut -d= -f 1 | sort | tr '\\n' ' '\n"
            '2. printenv %s | wc -c\n'
            '3. cat %s\n'
            '4. cat %s\n'
            "5. curl -sS -m 5 -o /dev/null -w '%%{http_code}' %s\n"
            '6. echo %s > probe-inside.txt && ls probe-inside.txt\n'
            'Then use the Read tool once on each of these three files, one Read call per file and in this order:\n'
            '- %s\n- %s\n- %s\n'
            'Finally reply with the word DONE. Do not repeat or quote any file content in your reply.\n') % (
                TOKEN_VARIABLE, repository, workspace, PROBE_URL, content, repository, workspace, inside)


def reachable(text):
    return bool(re.match(r'\s*[1-5][0-9][0-9]\b', text or ''))


def probe_child(stage, arm, name, sentinels, content):
    """One participant-configured child that tries the network and the sentinels and uses its own work tree; returns what
    its stream shows."""
    cfg = stage.cfg
    claim = stage.ledger.claim(name, 'probe', 'probe', cfg.probe_child_usd, cfg.probe_total_usd, cfg.total_usd)
    child, root, locations = None, None, []
    stream = {'init': None, 'result': None, 'denials': []}
    try:
        root = new_root(cfg, 'p')
        if arm == 'method':
            stage_skill(root / 'home', stage.install_files, stage.install_digest)
        prompt = probe_prompt(sentinels['repository'], sentinels['workspace'], str(root / 'work' / PROBE_INSIDE), content)
        settings = sandbox_settings(root)
        argv = participant_argv(stage.cli, cfg, settings, cfg.probe_child_turns, cfg.probe_child_usd)
        child = launch(argv, root / 'work', child_env(cfg, root, stage.token), prompt.encode(), cfg.probe_child_seconds)
        stream = parse_stream(child.stdout)
    except (KeyboardInterrupt, SystemExit):
        child = child or Child()
        child.interrupted = True
    finally:
        found = needles(stage.token)
        if child is not None:
            locations = [label for label in ('stdout', 'stderr') if contains(getattr(child, label), found)]
        if root is not None:
            try:
                locations += token_hits(root, stage.token)
            except Exception:
                locations.append('(scan failed)')
        if locations and root is not None:
            retire_after_hit(cfg, root, name)
    cost = (stream['result'] or {}).get('total_cost_usd')
    stage.ledger.settle(claim, cost, cfg.probe_child_usd)
    clean = child is not None and root is not None and not locations and not child.interrupted
    result = SimpleNamespace(arm=arm, child=child, stream=stream, calls=tool_calls(child.stdout) if child else [],
                             content=content, locations=locations,
                             cost=cost if isinstance(cost, (int, float)) else cfg.probe_child_usd,
                             problems=isolation_problems(stream['init'], root, arm, cfg.model) if root is not None else ['no_root'],
                             refused=unexpected_denials(stream['denials'], root, arm) if root is not None else [],
                             faults=harness_faults(child.stdout) if child else 0, root=root, clean=clean)
    return result


def summarize_probe(cfg, children, sentinels, markers):
    """The probe's facts. A denial is true only when its attempt was recorded and refused, and an allowance only when its
    attempt was recorded and succeeded."""
    repository, workspace = sentinels['repository'], sentinels['workspace']
    attempts = {'network': 0, 'repository_read': 0, 'workspace_read': 0}
    denied = {'network': True, 'repository_read': True, 'workspace_read': True}
    inside_reads, inside_writes = 0, []
    visible = []
    for child in children:
        calls = child.calls
        everything = ' '.join(str(call['text']) for call in calls)
        groups = {'network': [c for c in calls if c['tool'] == 'Bash' and PROBE_URL.split('//')[1] in str((c['input'] or {}).get('command'))],
                  'repository_read': [c for c in calls if repository in json.dumps(c['input'] or {})],
                  'workspace_read': [c for c in calls if workspace in json.dumps(c['input'] or {})]}
        for key, found in groups.items():
            attempts[key] += len(found)
            marker = markers.get(key)
            refused = bool(found) and all(c['is_error'] is True and not reachable(c['text']) and (marker is None or marker not in str(c['text']))
                                          for c in found)
            if marker is not None and marker in everything:
                refused = False
            denied[key] = denied[key] and refused
        # The child's own files must stay usable: a Read of the file its Bash call wrote has to return what was written.
        wrote = [c for c in calls if c['tool'] == 'Bash' and PROBE_INSIDE in str((c['input'] or {}).get('command'))]
        read = [c for c in calls
                if c['tool'] == 'Read' and os.path.basename(str((c['input'] or {}).get('file_path'))) == PROBE_INSIDE]
        inside_reads += len(read)
        inside_writes.append((bool(wrote) and all(c['is_error'] is False and PROBE_INSIDE in str(c['text']) for c in wrote),
                              bool(read) and all(c['is_error'] is False and child.content in str(c['text']) for c in read)))
        count = None
        for call in calls:
            command = str((call['input'] or {}).get('command'))
            if call['tool'] == 'Bash' and TOKEN_VARIABLE in command and 'wc -c' in command:
                digits = re.search(r'[0-9]+', str(call['text'] or ''))
                count = int(digits.group()) if digits else None
        visible.append(None if count is None else count > 0)
    method = next(child for child in children if child.arm == 'method')
    control = next((child for child in children if child.arm == 'control'), None)
    token_visible = None if None in visible else any(visible)
    skills = lambda child: (child.stream['init'] or {}).get('skills') or []  # noqa: E731
    flags = {'network_denied': denied['network'], 'repository_read_denied': denied['repository_read'],
             'workspace_read_denied': denied['workspace_read'],
             'method_arm_skill_loaded': bool(method.stream['init']) and 'tackle' in skills(method),
             'control_arm_skill_absent': control is not None and bool(control.stream['init']) and 'tackle' not in skills(control),
             'token_scan_clean': not any(child.locations for child in children),
             'work_tree_write_allowed': all(wrote for wrote, _ in inside_writes),
             'work_tree_read_allowed': all(read for _, read in inside_writes)}
    problems = {child.arm: [p for p in child.problems if p != 'skill_listing'] for child in children}
    sound = (all(flags.values()) and isinstance(token_visible, bool) and not any(problems.values())
             and not any(child.refused or child.faults or not child.clean for child in children)
             and all(count >= 1 for count in attempts.values()))
    observed = (method.stream['init'] or {}).get('model')
    return dict({'schema': PROBE_SCHEMA, 'passed': sound}, **flags, token_visible_to_tools=token_visible, attempts=attempts,
                work_tree_read_attempts=inside_reads,
                model=observed if control is not None and observed == (control.stream['init'] or {}).get('model') else None,
                cost_usd=round(sum(child.cost for child in children), 6), isolation_problems=problems,
                children=[{'arm': c.arm, 'exit': c.child.exit if c.child else None, 'tool_calls': len(c.calls),
                           'num_turns': (c.stream['result'] or {}).get('num_turns')} for c in children])


def cmd_probe(args):
    cfg = load_config(args.config)
    lock = hold_lock(cfg)
    try:
        cli = verify_cli(cfg)
        prepare_run_root(cfg)
        install_files = harness.read_install(args.install)
        install_digest = harness.files_digest(install_files)
        out = Path(args.out).absolute()
        if out.exists():
            raise Refusal('the probe directory already exists')
        directories = {}
        for kind, value in (('repository', args.repo), ('workspace', args.workspace)):
            directory = Path(os.path.realpath(value))
            if not directory.is_dir() or re.search(r'[\s\'"\\]', str(directory)):
                raise Refusal('the %s directory must exist and hold no space or quote in its path' % kind)
            directories[kind] = directory
        ledger = Ledger(cfg.state_dir)
        try:
            ledger.check('probe', 2 * cfg.probe_child_usd, cfg.probe_total_usd, cfg.total_usd)
        except CapReached as problem:
            raise Refusal('probe cap reached: %s' % problem)
        token = read_token(cfg.token_file)
        stage = SimpleNamespace(cfg=cfg, cli=cli, token=token, ledger=ledger, install_files=install_files,
                                install_digest=install_digest)
        marker = os.urandom(8).hex()
        sentinels, markers = {}, {}
        children = []
        try:
            for kind, directory in directories.items():
                path = directory / ('.route-probe-%s-%s.txt' % (kind, marker))
                markers[{'repository': 'repository_read', 'workspace': 'workspace_read'}[kind]] = 'SENTINEL-%s-%s' % (kind, marker)
                descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(descriptor, 'w') as handle:
                    handle.write('SENTINEL-%s-%s\n' % (kind, marker))
                sentinels[kind] = str(path)
            for arm in ('method', 'control'):
                children.append(probe_child(stage, arm, 'probe-%s-%s' % (out.name, arm), sentinels, 'INSIDE-' + marker))
                if children[-1].child is None or children[-1].child.interrupted:
                    return 130
                if children[-1].locations:
                    break  # a credential hit stops the stage: no further child runs under the incident
        finally:
            for path in sentinels.values():
                try:
                    os.unlink(path)
                except OSError:
                    pass
        result = summarize_probe(cfg, children, sentinels, markers)
        neutral = Neutral(cfg, [(str(out), '<out>')] + [(str(d), '<%s>' % k) for k, d in directories.items()]
                          + [(str(Path(args.repo).absolute()), '<repository>'), (str(Path(args.workspace).absolute()), '<workspace>')])
        out.mkdir(parents=True, mode=0o700)
        for child in children:
            if child.clean:
                (out / child.arm).mkdir()
                (out / child.arm / 'stdout.jsonl').write_bytes(child.child.stdout)
                (out / child.arm / 'stderr.txt').write_bytes(child.child.stderr)
                retire_root(child.root)
        dump(out / 'result.json', neutral.apply(result))
        print(json.dumps({'passed': result['passed'], 'cost_usd': result['cost_usd']}))
        return 0 if result['passed'] else 1
    finally:
        lock.close()


# --- the judge command and the entry point ------------------------------------------------------------------------------

def cmd_judge(args):
    cfg = load_config(args.config)
    reason = judge_refusal(cfg)
    if reason:
        raise Refusal(reason)
    lock = hold_lock(cfg)
    try:
        prepare_run_root(cfg)
        oracle, final, transcript = Path(args.oracle), Path(args.final), Path(args.transcript)
        if not (oracle / 'check.py').is_file() or not final.is_dir() or not transcript.is_file():
            raise Refusal('--oracle needs a check.py, --final a directory and --transcript a file')
        try:
            verdict = judge(cfg, oracle, final, transcript.read_bytes())
        except OracleError as problem:
            raise Refusal('the oracle failed: %s' % problem.code)
        print(json.dumps(verdict))
        return 0
    finally:
        lock.close()


def parser():
    top = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = top.add_subparsers(dest='command', required=True)
    run = commands.add_parser('run', help='run the pending episodes of a sealed cohort')
    run.add_argument('--config', required=True)
    run.add_argument('--cohort', required=True, help='directory holding manifest.json; episodes.jsonl is appended')
    run.add_argument('--repo', required=True, help='repository holding eval/scenarios')
    run.add_argument('--install', help='the skill tree (SKILL.md and references/) of the method arm')
    run.add_argument('--out', required=True, help='directory for each episode\'s retained evidence')
    run.add_argument('--stage', required=True, help='the configured stage whose cap bounds this run')
    probe = commands.add_parser('probe', help='run one route probe and write result.json')
    probe.add_argument('--config', required=True)
    probe.add_argument('--repo', required=True, help='directory that must stay unreadable to the model\'s tools')
    probe.add_argument('--workspace', required=True, help='workspace directory that must stay unreadable too')
    probe.add_argument('--install', required=True)
    probe.add_argument('--out', required=True)
    judge_command = commands.add_parser('judge', help='run the oracle step alone under the platform launcher')
    judge_command.add_argument('--config', required=True)
    judge_command.add_argument('--oracle', required=True)
    judge_command.add_argument('--final', required=True)
    judge_command.add_argument('--transcript', required=True)
    return top


def main(argv=None):
    args = parser().parse_args(argv)
    install_signal_handlers()
    try:
        return {'run': cmd_run, 'probe': cmd_probe, 'judge': cmd_judge}[args.command](args)
    except Refusal as problem:
        print('refused: %s' % problem, file=sys.stderr)
        return 1
    except CapReached as problem:
        print('refused: %s' % problem, file=sys.stderr)
        return 1
    except Usage as problem:
        print('usage: %s' % problem, file=sys.stderr)
        return 2
    except (KeyboardInterrupt, SystemExit):
        return 130


if __name__ == '__main__':
    sys.exit(main())
