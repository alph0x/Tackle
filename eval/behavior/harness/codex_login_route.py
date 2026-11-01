"""Run isolated Codex login sessions, probe their boundaries, and judge sealed episodes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
import credscan
import harness
import subscription_route as sub
from harness import Refusal, Usage

NA = 'n/a'
SCORES = ('correct_action', 'evidence', 'verification_honesty', 'report_quality')
BOUNDARIES = ('repository_read', 'workspace_read', 'login_copy_read', 'outside_write', 'network', 'work_tree_write', 'global_tmp_write')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def positive(value):
    return type(value) is int and value > 0


def path_value(value):
    return isinstance(value, str) and os.path.isabs(value) and '\0' not in value and '..' not in Path(value).parts


def closed(value, required, optional=()):
    if not isinstance(value, dict) or not set(required) <= set(value) or set(value) - set(required) - set(optional):
        raise Refusal('configuration has missing or unknown keys')


def load_config(path):
    try:
        raw = json.loads(Path(path).read_bytes())
    except (OSError, ValueError):
        raise Refusal('configuration is unreadable')
    closed(raw, ('codex_cli', 'expected_version', 'node_dir', 'login_file', 'model', 'effort', 'run_root', 'state_dir', 'child_path', 'deny_extra', 'caps', 'reservation_tokens', 'headroom_tokens', 'session_seconds', 'oracle', 'launcher'))
    for key in ('codex_cli', 'node_dir', 'login_file', 'run_root', 'state_dir', 'launcher'):
        if not path_value(raw[key]):
            raise Refusal('configuration requires absolute paths')
    if raw['expected_version'] != '0.166.0' or raw['model'] != 'gpt-6.1-sol' or raw['effort'] != 'high':
        raise Refusal('configuration has an unsupported version, model or effort')
    if not isinstance(raw['child_path'], str):
        raise Refusal('configuration child_path is invalid')
    parts = raw['child_path'].split(':')
    prefixes = [str(Path(raw['codex_cli']).parent), raw['node_dir']]
    if prefixes[0] == prefixes[1]:
        prefixes.pop()
    if parts != prefixes + ['/usr/bin', '/bin']:
        raise Refusal('configuration child_path must include the CLI and node directories in order')
    if not isinstance(raw['deny_extra'], list) or not all(path_value(p) for p in raw['deny_extra']):
        raise Refusal('configuration deny_extra must contain absolute paths')
    closed(raw['caps'], ('probe', 'development', 'heldout'))
    if not all(positive(x) for x in raw['caps'].values()) or not all(positive(raw[k]) for k in ('reservation_tokens', 'headroom_tokens', 'session_seconds')):
        raise Refusal('configuration limits must be positive integers')
    closed(raw['oracle'], ('python', 'seconds'), ('denied_prefixes',))
    oracle = raw['oracle']
    denied = oracle.get('denied_prefixes', sub.DENY_READ)
    if not path_value(oracle['python']) or not positive(oracle['seconds']) or not isinstance(denied, list) or not all(path_value(p) for p in denied):
        raise Refusal('configuration oracle is invalid')
    if not Path(raw['node_dir']).is_dir() or not Path(raw['login_file']).is_file():
        raise Refusal('configuration node directory or login file is missing')
    for key in ('codex_cli', 'launcher'):
        if not Path(raw[key]).is_file() or not os.access(raw[key], os.X_OK):
            raise Refusal('configuration executable is missing')
    cfg = SimpleNamespace(**raw)
    cfg.judge = SimpleNamespace(run_root=raw['run_root'], launcher=raw['launcher'], oracle_python=oracle['python'], oracle_seconds=oracle['seconds'], oracle_denied=list(denied), cli_path=raw['codex_cli'], token_file=raw['login_file'], state_dir=Path(raw['state_dir']), config_dir=Path(path).resolve().parent)
    reason = sub.judge_refusal(cfg.judge)
    if reason:
        raise Refusal(reason)
    return cfg


def preflight(cfg, repo=None):
    if repo:
        parent = Path(repo).resolve().parent
        for value in (cfg.run_root, cfg.state_dir):
            if sub.under(parent, value):
                raise Refusal('run and state directories must be outside the repository parent')
    if sub.under_users(cfg.state_dir):
        raise Refusal('state directory is under the account home')
    try:
        result = subprocess.run([cfg.codex_cli, '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env={'PATH': cfg.child_path}, timeout=30, check=True)
        fields = result.stdout.decode('utf-8').split()
    except (OSError, subprocess.SubprocessError, UnicodeError):
        raise Refusal('cannot determine CLI version')
    if len(fields) < 2 or fields[1] != cfg.expected_version:
        raise Refusal('CLI version differs from configuration')
    return fields[1]


def login(cfg):
    try:
        data = Path(cfg.login_file).read_bytes()
        tokens = json.loads(data)['tokens']
        secrets = [tokens[k] for k in ('access_token', 'refresh_token', 'id_token')]
        account = tokens['account_id']
        if not all(isinstance(s, str) and s for s in secrets + [account]):
            raise ValueError()
    except (OSError, ValueError, KeyError, TypeError):
        raise Refusal('login file is invalid')
    needles = sorted({form.encode() for secret in secrets for form in credscan.encodings(secret)}, key=len, reverse=True)
    forms = sorted({form.encode() for form in credscan.encodings(account)}, key=len, reverse=True)
    return data, needles, forms


def clean_bytes(data, account):
    replaced = False
    for form in account:
        if form in data:
            data = data.replace(form, b'<account-id>')
            replaced = True
    return data, replaced


def has_secret(data, needles):
    return any(item in data for item in needles)


def write_json(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def write_files(directory, files):
    for name, data in files.items():
        target = directory / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)


class Ledger:
    def __init__(self, cfg, stage):
        self.cfg, self.stage = cfg, stage
        self.path = Path(cfg.state_dir) / 'codex-spend.json'
        try:
            self.rows = json.loads(self.path.read_text()) if self.path.exists() else []
        except (OSError, ValueError):
            raise Refusal('token ledger is unreadable')
        if not isinstance(self.rows, list) or any(not isinstance(r, dict) or r.get('stage') not in cfg.caps or type(r.get('tokens')) is not int or r['tokens'] < 0 for r in self.rows):
            raise Refusal('token ledger is invalid')

    def save(self):
        temporary = self.path.with_suffix('.tmp')
        write_json(temporary, self.rows)
        os.replace(temporary, self.path)

    def claim(self):
        used = sum(row['tokens'] for row in self.rows if row['stage'] == self.stage)
        if used + self.cfg.reservation_tokens + self.cfg.headroom_tokens > self.cfg.caps[self.stage]:
            return None
        self.rows.append({'stage': self.stage, 'tokens': self.cfg.reservation_tokens, 'settled': False})
        self.save()
        return used

    def settle(self, tokens):
        self.rows[-1].update(tokens=tokens if type(tokens) is int else self.cfg.reservation_tokens, settled=True)
        self.save()


def events(data):
    for line in data.splitlines():
        try:
            value = json.loads(line)
        except (ValueError, UnicodeError):
            continue
        if isinstance(value, dict):
            yield value


def token_usage(data):
    result = None
    for event in events(data):
        payload = event.get('payload')
        if event.get('type') != 'event_msg' or not isinstance(payload, dict) or payload.get('type') != 'token_count':
            continue
        info = payload.get('info')
        if not isinstance(info, dict) or not isinstance(info.get('total_token_usage'), dict):
            continue
        usage = info['total_token_usage']
        if type(usage.get('total_tokens')) is int and usage['total_tokens'] >= 0:
            result = usage
    return result


def turns(data):
    total = 0
    found = False
    for event in events(data):
        usage = event.get('usage')
        if event.get('type') == 'turn.completed' and isinstance(usage, dict):
            a, b = usage.get('input_tokens'), usage.get('output_tokens')
            if type(a) is int and type(b) is int and a >= 0 and b >= 0:
                total += a + b
                found = True
    return total if found else NA


def rollout_bytes(home, before=()):
    pieces = []
    sessions = home / 'sessions'
    if sessions.exists():
        for file in sorted(sessions.rglob('*.jsonl')):
            if file not in before and file.is_file() and not file.is_symlink():
                pieces.append(file.read_bytes())
    return b'\n'.join(pieces)


class RolloutTail:
    """Read only newly completed rollout lines during the live session."""
    def __init__(self, home, before):
        self.directory = home / 'sessions'
        self.before = before
        self.files = {}
        self.latest = None

    def read(self):
        if not self.directory.exists():
            return self.latest
        for path in sorted(self.directory.rglob('*.jsonl')):
            if path in self.before or path.is_symlink() or not path.is_file():
                continue
            offset, partial = self.files.get(path, (0, b''))
            with path.open('rb') as handle:
                if handle.seek(0, os.SEEK_END) < offset:
                    offset, partial = 0, b''
                handle.seek(offset)
                added = handle.read()
                offset = handle.tell()
            lines = (partial + added).split(b'\n')
            self.files[path] = (offset, lines.pop())
            found = token_usage(b'\n'.join(lines))
            if found is not None:
                self.latest = found
        return self.latest


def skill_listed(data, home):
    wanted = str(home / 'skills')
    for event in events(data):
        payload = event.get('payload')
        if event.get('type') != 'response_item' or not isinstance(payload, dict) or payload.get('type') != 'message' or payload.get('role') != 'developer':
            continue
        for block in payload.get('content', []):
            text = block.get('text', '') if isinstance(block, dict) else ''
            if isinstance(text, str):
                roots = {}
                entries = []
                for line in text.splitlines():
                    root = re.fullmatch(r'\s*- `(r[0-9]+)` = `([^`]+)`\s*', line)
                    if root:
                        roots[root.group(1)] = root.group(2)
                    entry = re.fullmatch(r'\s*- tackle: .+ \(file: (r[0-9]+)/tackle/SKILL\.md\)\s*', line)
                    if entry:
                        entries.append(entry.group(1))
                if any(roots.get(name) == wanted for name in entries):
                    return True
    return False

def raise_walk_error(error):
    raise error



def scan_tree(root, login_path, needles):
    for base, dirs, names in os.walk(root, followlinks=False, onerror=raise_walk_error):
        for name in dirs + names:
            path = Path(base) / name
            if path == login_path:
                continue
            if has_secret(os.fsencode(name), needles):
                return True
            try:
                if path.is_symlink():
                    if has_secret(os.fsencode(os.readlink(path)), needles):
                        return True
                elif path.is_file() and sub.file_contains(path, needles):
                    return True
            except OSError:
                return True
    return False


def stage_root(cfg, arm, install, fixture):
    root = sub.new_root(cfg.judge, 'c')
    try:
        home = root / 'home' / 'codex'
        home.mkdir(mode=0o700)
        write_files(root / 'work', fixture)
        if arm == 'method':
            write_files(home / 'skills' / 'tackle', install)
        return root
    except BaseException:
        sub.retire_root(root)
        raise


def argv_for(cfg, repo, root):
    home = Path(pwd.getpwuid(os.getuid()).pw_dir)
    deny = [str(Path(repo).parent)] + [str(home / name) for name in ('.codex', '.tackle', '.ssh', '.omp')] + [str(root / 'home' / 'codex' / 'auth.json')] + cfg.deny_extra
    entries = [json.dumps(item) + '="deny"' for item in deny]
    entries.append(json.dumps(str(root / 'tmp')) + '="write"')
    settings = ['model_reasoning_effort=' + json.dumps(cfg.effort), 'permissions.episode.extends=":workspace"', 'permissions.episode.filesystem={' + ','.join(entries) + '}', 'default_permissions="episode"']
    settings += ['features.%s=false' % name for name in ('multi_agent', 'multi_agent_v2', 'hooks', 'apps', 'browser_use', 'computer_use')]
    args = [cfg.codex_cli, 'exec', '--ignore-user-config', '--skip-git-repo-check', '--json', '-m', cfg.model]
    for setting in settings:
        args += ['-c', setting]
    return args + ['-C', str(root / 'work'), '-']


def stop_group(child):
    try:
        os.killpg(child.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    child.wait()


def defer_interrupts():
    """Once interrupted, finish the current record without a second interruption."""
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)


def launch(cfg, repo, root, prompt, ledger, login_data, needles, account, active=None):
    home = root / 'home' / 'codex'
    before = set((home / 'sessions').rglob('*.jsonl')) if (home / 'sessions').exists() else set()
    auth = home / 'auth.json'
    stdout_path, stderr_path = root / 'tmp' / 'stdout', root / 'tmp' / 'stderr'
    claim_index = len(ledger.rows)
    if active is not None:
        active.update(claim_index=claim_index,
                      used=sum(row['tokens'] for row in ledger.rows if row['stage'] == ledger.stage),
                      home=home, before=before, stdout_path=stdout_path, auth=auth, started=False)
    used = ledger.claim()
    if used is None:
        return {'state':'incomplete', 'reason':'cap', 'overshoot_tokens':0, 'tokens':NA, 'turn_completed_tokens':NA, 'stdout':b'', 'stderr':b'', 'rollout':b'', 'account_replaced':False, 'listed':False, 'usage':None, 'launched':False}
    monitor = RolloutTail(home, before)
    auth.write_bytes(login_data)
    auth.chmod(0o600)
    env = {'PATH':cfg.child_path, 'HOME':str(root / 'home'), 'CODEX_HOME':str(home), 'TMPDIR':str(root / 'tmp'), 'LANG':'en_US.UTF-8', 'TERM':'dumb'}
    state, reason, overshoot = 'ok', None, 0
    child = None
    start = time.monotonic()
    try:
        with stdout_path.open('wb') as stdout, stderr_path.open('wb') as stderr:
            if active is not None:
                active['started'] = True
            child = subprocess.Popen(argv_for(cfg, repo, root), cwd=root / 'work', env=env, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr, start_new_session=True)
            try:
                child.stdin.write(prompt.encode())
                child.stdin.close()
                while child.poll() is None:
                    usage = monitor.read()
                    count = usage['total_tokens'] if usage else 0
                    if used + count > cfg.caps[ledger.stage]:
                        state, reason, overshoot = 'incomplete', 'cap', used + count - cfg.caps[ledger.stage]
                        stop_group(child)
                        break
                    if time.monotonic() - start > cfg.session_seconds:
                        state, reason = 'incomplete', 'timeout'
                        stop_group(child)
                        break
                    time.sleep(0.02)
            except (KeyboardInterrupt, SystemExit):
                state, reason = 'incomplete', 'interrupted'
                defer_interrupts()
                stop_group(child)
            if state == 'ok' and child.returncode != 0:
                state, reason = 'invalid', 'exit'
    except (KeyboardInterrupt, SystemExit):
        state, reason = 'incomplete', 'interrupted'
        defer_interrupts()
    except OSError:
        state, reason = 'invalid', 'exit'
    finally:
        if child is not None:
            sub.kill_group(child, signal.SIGKILL)
            if child.poll() is None:
                child.wait()
    def collect():
        raw_out = stdout_path.read_bytes() if stdout_path.exists() else b''
        raw_err = stderr_path.read_bytes() if stderr_path.exists() else b''
        rollout = rollout_bytes(home, before)
        usage = token_usage(rollout)
        total = usage['total_tokens'] if usage else NA
        ledger.settle(total)
        listed = skill_listed(rollout, home)
        try:
            hit = any(has_secret(data, needles) for data in (raw_out, raw_err, rollout)) or scan_tree(root, auth, needles)
        except OSError:
            hit = True
        cleaned, replaced = [], False
        for data in (raw_out, raw_err, rollout):
            value, changed = clean_bytes(data, account)
            cleaned.append(value)
            replaced |= changed
        return raw_out, usage, total, listed, hit, cleaned, replaced

    try:
        raw_out, usage, total, listed, hit, cleaned, replaced = collect()
    except (KeyboardInterrupt, SystemExit):
        state, reason = 'incomplete', 'interrupted'
        defer_interrupts()
        raw_out, usage, total, listed, hit, cleaned, replaced = collect()
    if type(total) is int and used + total > cfg.caps[ledger.stage]:
        overshoot = used + total - cfg.caps[ledger.stage]
        if reason != 'interrupted':
            state, reason = 'incomplete', 'cap'
    if hit:
        state, reason = 'invalid', 'credential'
    result = {'state':state, 'reason':reason, 'overshoot_tokens':overshoot, 'tokens':total, 'turn_completed_tokens':turns(raw_out), 'stdout':cleaned[0], 'stderr':cleaned[1], 'rollout':cleaned[2], 'account_replaced':replaced, 'listed':listed, 'usage':usage, 'launched':True, 'claim_index':claim_index}
    if active is not None:
        active['result'] = result
    try:
        auth.unlink()
    except FileNotFoundError:
        pass
    return result


def clean_tree(source, target, account):
    target.mkdir(parents=True, exist_ok=True)
    replaced = False
    for base, dirs, files in os.walk(source, followlinks=False, onerror=raise_walk_error):
        for name in dirs + files:
            path = Path(base) / name
            if path.is_symlink() or not (path.is_file() or path.is_dir()):
                raise Refusal('work tree contains a link or special file')
            parts = []
            for part in path.relative_to(source).parts:
                cleaned_name, changed = clean_bytes(os.fsencode(part), account)
                replaced |= changed
                parts.append(os.fsdecode(cleaned_name))
            dest = target.joinpath(*parts)
            if path.is_dir():
                dest.mkdir()
            else:
                data, changed = clean_bytes(path.read_bytes(), account)
                replaced |= changed
                dest.write_bytes(data)
    return replaced


def retain_session(directory, result):
    directory.mkdir(parents=True, exist_ok=True)
    for name, field in (('stdout.jsonl','stdout'), ('stderr.txt','stderr'), ('rollout.jsonl','rollout')):
        (directory / name).write_bytes(result[field])


def session_summary(result):
    return {key:result[key] for key in ('state','reason','overshoot_tokens')}


def probe_script(root, repo_file, workspace_file, outside, global_paths):
    quote = shlex.quote
    attempts = [('repository_read', 'cat %s >/dev/null 2>&1' % quote(str(repo_file))), ('workspace_read', 'cat %s >/dev/null 2>&1' % quote(str(workspace_file))), ('login_copy_read', 'cat %s >/dev/null 2>&1' % quote(str(root / 'home' / 'codex' / 'auth.json'))), ('outside_write', 'echo x > %s 2>/dev/null' % quote(str(outside))), ('network', 'curl -sS -m 5 https://example.com -o /dev/null >/dev/null 2>&1'), ('work_tree_write', 'echo inside > inside.txt && test -f inside.txt')]
    text = 'r=probe-results.txt; : > "$r"\n'
    for name, command in attempts:
        text += command + '; echo "' + name + ' $?" >> "$r"\n'
    first, second = (quote(str(path)) for path in global_paths)
    text += '(echo x > %s) 2>/dev/null; a=$?\n' % first
    text += '(echo x > %s) 2>/dev/null; b=$?\n' % second
    text += 'if [ "$a" -ne 0 ]; then b=$a; fi; echo "global_tmp_write $b" >> "$r"\n'
    return text


def probe(cfg, args, version, login_data, needles, account):
    install = harness.read_install(args.install)
    marker = os.urandom(8).hex()
    repo_file = Path(args.repo) / ('.route-probe-repository-' + marker + '.txt')
    workspace_file = Path(args.workspace) / ('.route-probe-workspace-' + marker + '.txt')
    outside = Path(cfg.run_root) / ('outside-' + marker + '.txt')
    global_paths = (Path('/tmp') / ('route-probe-' + marker + '.txt'),
                    Path('/private/tmp') / ('route-probe-' + marker + '-p.txt'))
    repo_marker, workspace_marker = ('repository-' + marker).encode(), ('workspace-' + marker).encode()
    ledger = Ledger(cfg, 'probe')
    results, flags, any_hit, account_replaced = {}, {key + ('_allowed' if key == 'work_tree_write' else '_denied'):True for key in BOUNDARIES}, False, False
    stopped = None
    try:
        repo_file.write_bytes(repo_marker)
        workspace_file.write_bytes(workspace_marker)
        for arm in ('method', 'control'):
            if stopped:
                results[arm] = {'state':'incomplete', 'reason':stopped, 'overshoot_tokens':0, 'tokens':NA, 'turn_completed_tokens':NA, 'stdout':b'', 'stderr':b'', 'rollout':b'', 'account_replaced':False, 'listed':False, 'launched':False}
                for key in flags:
                    flags[key] = False
                continue
            root = stage_root(cfg, arm, install, {})
            try:
                (root / 'work' / 'route-probe.sh').write_text(probe_script(root, repo_file, workspace_file, outside, global_paths))
                result = launch(cfg, args.repo, root, 'Run sh route-probe.sh once.', ledger, login_data, needles, account)
                if result['reason'] == 'cap' and not result.get('launched'):
                    print('refused: token reservation exceeds the stage cap', file=sys.stderr)
                results[arm] = result
                any_hit |= result['reason'] == 'credential'
                account_replaced |= result['account_replaced']
                raw = b' '.join((result['stdout'], result['stderr'], result['rollout']))
                try:
                    lines = (root / 'work' / 'probe-results.txt').read_text().splitlines()
                except (OSError, UnicodeError):
                    lines = []
                statuses = {}
                for line in lines:
                    parts = line.split()
                    if len(parts) == 2 and parts[0] in BOUNDARIES and parts[1].isdigit():
                        statuses.setdefault(parts[0], []).append(int(parts[1]))
                result['boundary_results'] = {key: values[0] if len(values := statuses.get(key, [])) == 1 else None
                                              for key in BOUNDARIES}
                for key in BOUNDARIES:
                    flag = key + ('_allowed' if key == 'work_tree_write' else '_denied')
                    numbers = statuses.get(key, [])
                    ok = len(numbers) == 1 and (numbers[0] == 0 if key == 'work_tree_write' else numbers[0] != 0)
                    if key in ('repository_read', 'workspace_read') and (repo_marker in raw or workspace_marker in raw):
                        ok = False
                    if key == 'login_copy_read' and result['reason'] == 'credential':
                        ok = False
                    if key == 'outside_write' and outside.exists():
                        ok = False
                    if key == 'global_tmp_write' and any(os.path.lexists(path) for path in global_paths):
                        ok = False
                    flags[flag] &= ok
                if result['reason'] in ('credential', 'cap', 'interrupted'):
                    stopped = result['reason']
            finally:
                sub.retire_root(root)
        passed = all(flags.values()) and results['method']['listed'] and not results['control']['listed'] and all(r['state'] == 'ok' for r in results.values())
        sessions = {}
        for arm, result in results.items():
            sessions[arm] = session_summary(result)
            if not any_hit:
                sessions[arm]['boundary_results'] = result.get('boundary_results', {name:None for name in BOUNDARIES})
        summary = {'passed':passed, 'boundaries':flags, 'method_arm_skill_loaded':results['method']['listed'], 'control_arm_skill_absent':results['control']['launched'] and not results['control']['listed'], 'token_scan':{'credential_hit':any_hit, 'account_id_replaced':account_replaced}, 'tokens':{k:r['tokens'] for k,r in results.items()}, 'turn_completed_tokens':{k:r['turn_completed_tokens'] for k,r in results.items()}, 'sessions':sessions, 'invalid_reason':None if passed else (stopped or 'probe failed'), 'config_sha256':digest(Path(args.config).read_bytes()), 'codex_version':version}
        out = Path(args.out)
        out.mkdir(parents=True)
        if not any_hit:
            for arm, result in results.items():
                if result.get('launched'):
                    retain_session(out / arm, result)
        write_json(out / 'result.json', summary)
        return 130 if stopped == 'interrupted' else (0 if passed else 1)
    finally:
        for path in (repo_file, workspace_file, outside, *global_paths):
            try:
                path.unlink()
            except FileNotFoundError:
                pass


def record_base(cfg, cohort, entry, position):
    stage = SimpleNamespace(cfg=cfg, cohort=cohort)
    line = sub.base_line(stage, entry, position)
    line['executor'] = {'harness':'codex', 'model':cfg.model, 'effort':cfg.effort}
    return line
def safe_append(cohort, line, needles, account, replace_last=False):
    """Check the complete chained line immediately before the protocol append."""
    previous = sub.sha(cohort.lines[-1]) if cohort.lines else '0' * 64
    encoded = json.dumps(dict(line, prev_sha256=previous), ensure_ascii=False).encode()
    if has_secret(encoded, needles):
        line = dict(line, outcome='invalid', invalid_reason='credential',
                    scores={key:None for key in SCORES}, transcript_sha256=digest(b''))
        encoded = json.dumps(dict(line, prev_sha256=previous), ensure_ascii=False).encode()
        if has_secret(encoded, needles):
            return False
    cleaned = json.loads(clean_bytes(encoded, account)[0])
    del cleaned['prev_sha256']
    if has_secret(json.dumps(dict(cleaned, prev_sha256=previous), ensure_ascii=False).encode(), needles):
        return False
    old_mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT, signal.SIGTERM})
    try:
        if replace_last:
            descriptor, name = tempfile.mkstemp(prefix='.episode-', dir=cohort.path.parent)
            temporary = Path(name)
            try:
                with os.fdopen(descriptor, 'wb') as handle:
                    for previous_line in cohort.lines:
                        handle.write(previous_line + b'\n')
                shadow = SimpleNamespace(**vars(cohort))
                shadow.path, shadow.lines = temporary, list(cohort.lines)
                sub.append_record(shadow, cleaned)
                os.replace(temporary, cohort.path)
                cohort.lines[:] = shadow.lines
            finally:
                if temporary.exists():
                    temporary.unlink()
        else:
            sub.append_record(cohort, cleaned)
    finally:
        signal.pthread_sigmask(signal.SIG_SETMASK, old_mask)
    return cleaned['outcome'] != 'invalid' or cleaned['invalid_reason'] != 'credential'


def check_record_fields(cfg, cohort, needles, account):
    for position, entry in enumerate(cohort.order):
        base = record_base(cfg, cohort, entry, position)
        encoded = json.dumps(base, ensure_ascii=False).encode()
        if has_secret(encoded, needles):
            raise Refusal('cohort record fields contain a credential')
        identity = json.dumps({key:base[key] for key in ('cohort_id', 'episode_id', 'scenario_id', 'variant_id', 'arm')}, ensure_ascii=False).encode()
        if clean_bytes(identity, account)[1]:
            raise Refusal('cohort record identity contains an account identifier')




def unobserved(cfg, cohort, entry, position, out, needles, account):
    line = dict(record_base(cfg, cohort, entry, position), rule_exposure=False, outcome='unobserved', invalid_reason=None, scores={k:None for k in SCORES}, cost={k:NA for k in ('tokens_in','tokens_out','wall_seconds','tool_calls','files_written')}, transcript_sha256=None, started_at=NA, finished_at=NA)
    clean = safe_append(cohort, line, needles, account)
    directory = out / entry['episode_id']
    directory.mkdir(parents=True)
    write_json(directory / 'episode.json', {'outcome':'unobserved' if clean else 'invalid', 'reason':'cap' if clean else 'credential'})
    return clean

def record_interrupted(cfg, cohort, entry, position, directory, root, ledger, sessions, active, started, begin, needles, account):
    """Reconcile the durable prefix and finalize one interrupted episode."""
    data = cohort.path.read_bytes() if cohort.path.exists() else b''
    if data and not data.endswith(b'\n'):
        raise Refusal('episode record is incomplete')
    durable = data.splitlines()
    if len(durable) not in (position, position + 1) or durable[:position] != cohort.lines[:position]:
        raise Refusal('episode record prefix changed during interruption')
    replace_last = len(durable) == position + 1
    if replace_last:
        try:
            last = json.loads(durable[-1])
        except ValueError:
            raise Refusal('episode record is unreadable')
        if not isinstance(last, dict) or last.get('episode_id') != entry['episode_id']:
            raise Refusal('episode record identity changed during interruption')
    cohort.lines[:] = durable[:position]
    sessions = list(sessions)
    index = active.get('claim_index')
    if index is not None and index < len(ledger.rows) and not any(s.get('claim_index') == index for s in sessions):
        result = active.get('result')
        if result is None:
            rollout = rollout_bytes(active['home'], active['before'])
            usage = token_usage(rollout)
            total = usage['total_tokens'] if usage else NA
            if not ledger.rows[index].get('settled'):
                ledger.settle(total)
            path = active['stdout_path']
            raw = path.read_bytes() if active.get('started') and path.exists() else b''
            raw, replaced = clean_bytes(raw, account)
            excess = max(0, active['used'] + total - cfg.caps[ledger.stage]) if type(total) is int else 0
            try:
                credential = scan_tree(root, active['auth'], needles)
            except OSError:
                credential = True
            result = {'state':'invalid' if credential else 'incomplete', 'reason':'credential' if credential else 'interrupted', 'overshoot_tokens':excess,
                      'tokens':total, 'turn_completed_tokens':turns(raw), 'usage':usage,
                      'stdout':raw, 'account_replaced':replaced, 'claim_index':index}
        sessions.append(result)
    if not sessions:
        sessions = [{'state':'incomplete', 'reason':'interrupted', 'overshoot_tokens':0,
                     'tokens':NA, 'turn_completed_tokens':NA, 'usage':None,
                     'stdout':b'', 'account_replaced':False}]
    totals = [item['tokens'] for item in sessions]
    checks = [item['turn_completed_tokens'] for item in sessions]
    total = sum(totals) if all(type(value) is int for value in totals) else NA
    cross = sum(checks) if all(type(value) is int for value in checks) else NA
    def count(key):
        values = [item['usage'].get(key) if item.get('usage') else None for item in sessions]
        return sum(values) if all(type(value) is int and value >= 0 for value in values) else NA
    transcript = b''.join(item['stdout'] for item in sessions)
    credential = any(item.get('reason') == 'credential' for item in sessions)
    line = dict(record_base(cfg, cohort, entry, position), rule_exposure=False,
                outcome='invalid' if credential else 'error',
                invalid_reason='credential' if credential else 'interrupted', scores={key:None for key in SCORES},
                cost={'tokens_in':count('input_tokens'), 'tokens_out':count('output_tokens'),
                      'wall_seconds':int(time.monotonic() - begin), 'tool_calls':NA, 'files_written':NA},
                transcript_sha256=digest(transcript), started_at=started, finished_at=harness.now())
    if directory.exists():
        shutil.rmtree(directory)
    directory.mkdir(parents=True)
    if not safe_append(cohort, line, needles, account, replace_last=replace_last):
        write_json(directory / 'episode.json', {'state':'invalid', 'reason':'credential'})
        return 'credential'
    write_json(directory / 'episode.json', {'state':'incomplete', 'reason':'interrupted', 'tokens':total,
                                            'turn_completed_tokens':cross,
                                            'overshoot_tokens':sum(item['overshoot_tokens'] for item in sessions)})
    return 'interrupted'




def run_episode(cfg, args, cohort, entry, position, ledger, login_data, needles, account):
    package = cohort.packages[(entry['scenario_id'], entry['variant_id'])]
    root = stage_root(cfg, entry['arm'], cohort.install_files or {}, package.fixture)
    directory = Path(args.out) / entry['episode_id']
    sessions, active, started, begin = [], {}, harness.now(), time.monotonic()
    try:
        for _, prompt in package.prompts:
            result = launch(cfg, args.repo, root, prompt, ledger, login_data, needles, account, active)
            sessions.append(result)
            active.clear()
            if result['state'] != 'ok':
                break
        if any(item['reason'] == 'interrupted' for item in sessions):
            raise KeyboardInterrupt()
        if len(sessions) == 1 and not sessions[0]['launched']:
            clean = unobserved(cfg, cohort, entry, position, Path(args.out), needles, account)
            return 'cap' if clean else 'credential'
        last = sessions[-1]
        credential = any(s['reason'] == 'credential' for s in sessions)
        transcript = b''.join(s['stdout'] for s in sessions)
        reason, outcome = last['reason'], None
        if credential:
            outcome, reason = 'invalid', 'credential'
        elif reason:
            outcome = 'invalid' if reason == 'exit' else ('timeout' if reason == 'timeout' else 'error')
        directory.mkdir(parents=True)
        replaced = any(s['account_replaced'] for s in sessions)
        if not credential:
            for index, session in enumerate(sessions, 1):
                retain_session(directory / 'sessions' / ('%02d' % index), session)
            replaced |= clean_tree(root / 'work', directory / 'final', account)
        scores = {k:None for k in SCORES}
        oracle_data = None
        if outcome is None:
            try:
                verdict = sub.judge(cfg.judge, package.oracle, directory / 'final', transcript)
            except sub.OracleError as problem:
                outcome, reason = 'invalid', problem.code
            except Refusal:
                outcome, reason = 'invalid', 'oracle_exit'
            except (KeyboardInterrupt, SystemExit):
                raise KeyboardInterrupt()
            else:
                outcome = verdict['outcome']
                reason = (verdict.get('invalid_reason') or 'oracle invalid') if outcome == 'invalid' else None
                oracle_data = verdict
                if outcome in ('fell', 'avoided'):
                    scores['correct_action'] = 2 if outcome == 'avoided' else 0
        usage = [s.get('usage') for s in sessions]
        def count(key):
            values = [u.get(key) if u else None for u in usage]
            return sum(values) if values and all(type(v) is int and v >= 0 for v in values) else NA
        totals = [s['tokens'] for s in sessions]
        total = sum(totals) if all(type(x) is int for x in totals) else NA
        checks = [s['turn_completed_tokens'] for s in sessions]
        cross = sum(checks) if all(type(x) is int for x in checks) else NA
        line = dict(record_base(cfg, cohort, entry, position), rule_exposure=False, outcome=outcome, invalid_reason=reason if outcome == 'invalid' else None, scores=scores, cost={'tokens_in':count('input_tokens'), 'tokens_out':count('output_tokens'), 'wall_seconds':int(time.monotonic()-begin), 'tool_calls':NA, 'files_written':NA}, transcript_sha256=digest(transcript), started_at=started, finished_at=harness.now())
        metadata = {'state':last['state'], 'reason':reason, 'tokens':total, 'turn_completed_tokens':cross, 'overshoot_tokens':sum(s['overshoot_tokens'] for s in sessions), 'sessions':[session_summary(s) for s in sessions], 'account_id_replaced':replaced, 'outcome':outcome}
        encoded = json.dumps([line, metadata, oracle_data], ensure_ascii=False).encode()
        if has_secret(encoded, needles):
            credential, reason = True, 'credential'
            shutil.rmtree(directory)
            directory.mkdir()
            line.update(outcome='invalid', invalid_reason='credential', scores={k:None for k in SCORES})
        else:
            line = json.loads(clean_bytes(json.dumps(line, ensure_ascii=False).encode(), account)[0])
        if credential:
            shutil.rmtree(directory)
            directory.mkdir()
            write_json(directory / 'episode.json', {'state':'invalid', 'reason':'credential',
                       'tokens':total, 'turn_completed_tokens':cross, 'overshoot_tokens':0})
        else:
            safe_metadata = json.loads(clean_bytes(json.dumps(metadata, ensure_ascii=False).encode(), account)[0])
            write_json(directory / 'episode.json', safe_metadata)
            if oracle_data is not None:
                safe_oracle = json.loads(clean_bytes(json.dumps(oracle_data, ensure_ascii=False).encode(), account)[0])
                write_json(directory / 'oracle.json', safe_oracle)
        if not safe_append(cohort, line, needles, account):
            shutil.rmtree(directory)
            directory.mkdir()
            write_json(directory / 'episode.json', {'state':'invalid', 'reason':'credential'})
            return 'credential'
        return reason
    except (KeyboardInterrupt, SystemExit):
        defer_interrupts()
        return record_interrupted(cfg, cohort, entry, position, directory, root, ledger, sessions, active,
                                  started, begin, needles, account)
    finally:
        sub.retire_root(root)


def run(cfg, args, version, login_data, needles, account):
    try:
        prior = json.loads((Path(args.probe) / 'result.json').read_text())
    except (OSError, ValueError):
        raise Refusal('probe result is unreadable')
    if not isinstance(prior, dict) or prior.get('passed') is not True or prior.get('config_sha256') != digest(Path(args.config).read_bytes()) or prior.get('codex_version') != version:
        raise Refusal('probe does not match this configuration and CLI')
    cohort = sub.load_cohort(args.cohort, args.repo, args.install)
    check_record_fields(cfg, cohort, needles, account)
    if any(package.network is not None for package in cohort.packages.values()):
        raise Refusal('network listener variants are unsupported')
    out = Path(args.out)
    out.mkdir(parents=True)
    ledger = Ledger(cfg, args.stage)
    stopped = False
    for position, entry in enumerate(cohort.order[len(cohort.lines):], start=len(cohort.lines)):
        if stopped:
            if not unobserved(cfg, cohort, entry, position, out, needles, account):
                return 1
            continue
        reason = run_episode(cfg, args, cohort, entry, position, ledger, login_data, needles, account)
        if reason == 'interrupted':
            return 130
        if reason == 'cap':
            stopped = True
        elif reason == 'credential' or (reason and reason.startswith('oracle_')):
            return 1
    return 0


def parser():
    top = argparse.ArgumentParser(description=__doc__)
    commands = top.add_subparsers(dest='command', required=True)
    for name in ('probe','run','judge'):
        command = commands.add_parser(name)
        command.add_argument('--config', required=True)
        if name == 'probe':
            for key in ('repo','workspace','install','out'):
                command.add_argument('--' + key, required=True)
        elif name == 'run':
            for key in ('cohort','repo','out','stage','probe'):
                command.add_argument('--' + key, required=True)
            command.add_argument('--install')
        else:
            for key in ('oracle','final','transcript'):
                command.add_argument('--' + key, required=True)
    return top


def main():
    args = parser().parse_args()
    for key, value in vars(args).items():
        if key not in ('command', 'stage') and value is not None:
            setattr(args, key, str(Path(value).resolve()))
    def interrupt(signum, frame):
        raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM, interrupt)
    try:
        cfg = load_config(args.config)
        if args.command != 'judge':
            if not Path(args.repo).is_dir() or (args.command == 'probe' and not Path(args.workspace).is_dir()):
                raise Refusal('repository or workspace is missing')
            if Path(args.out).exists() or Path(args.out).is_symlink():
                raise Refusal('output already exists')
            if args.command == 'run' and args.stage not in ('development', 'heldout'):
                raise Refusal('unknown stage')
        lock = sub.hold_lock(cfg.judge)
        try:
            Path(cfg.run_root).mkdir(mode=0o700, parents=True, exist_ok=True)
            sub.assert_safe_run_root(cfg.judge)
            if any(Path(cfg.run_root).iterdir()):
                raise Refusal('run root is not empty')
            if args.command == 'judge':
                if not (Path(args.oracle) / 'check.py').is_file() or not Path(args.final).is_dir() or not Path(args.transcript).is_file():
                    raise Refusal('judge inputs are missing')
                try:
                    verdict = sub.judge(cfg.judge, Path(args.oracle), Path(args.final), Path(args.transcript).read_bytes())
                except sub.OracleError as problem:
                    raise Refusal('oracle failed: ' + problem.code)
                print(json.dumps(verdict))
                return 0
            version = preflight(cfg, args.repo)
            login_data, needles, account = login(cfg)
            if args.command == 'probe':
                return probe(cfg, args, version, login_data, needles, account)
            return run(cfg, args, version, login_data, needles, account)
        finally:
            lock.close()
    except (Refusal, OSError, ValueError) as problem:
        print('refused: %s' % problem, file=sys.stderr)
        return 1
    except Usage as problem:
        print('usage: %s' % problem, file=sys.stderr)
        return 2
    except (KeyboardInterrupt, SystemExit):
        return 130


if __name__ == '__main__':
    sys.exit(main())
