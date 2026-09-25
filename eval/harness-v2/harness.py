"""Protocol v2 harness: stage an arm, run headless sessions, record C01 lines and build blinded judge packets.

Usage: python3 eval/harness-v2/harness.py stage|run|dispatch|record|packet|probe [options]
(see eval/harness-v2/README.md). Exit 0 success, 1 refusal or failed check, 2 usage error or a real adapter
without --allow-model-calls or without container isolation. The fake adapter needs no flag, and tests never
pass it. A participant never receives a credential: a real adapter reaches its one upstream through a
host-side broker that holds the credential and checks a per-episode dummy token.
"""
import argparse
import datetime
import difflib
import hashlib
import importlib.util
import json
import os
import random
import re
import secrets
import signal
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import adapters  # noqa: E402
import credscan  # noqa: E402
import usage  # noqa: E402

NA = 'n/a'
INDEX = 'eval/scenarios/INDEX.json'
ARM = re.compile(r'control|method|method:[a-z0-9-]+|ablation:[A-Za-z0-9-]+')
ROLE = re.compile(r'[A-Za-z][A-Za-z0-9 _-]{0,63}')
TIERS = ('fast', 'standard', 'frontier')
EFFORTS = ('low', 'medium', 'high', 'max')
MARKERS = ('AGENTS.md', 'SKILL.md', '.claude', '.agents')
SLASH = r'\\*/'  # a slash, possibly JSON-escaped
PATH_REST = r'[^\s"\'<>]*'


class Refusal(Exception):
    """Exit 1: a refusal or a failed check."""


class Usage(Exception):
    """Exit 2: a usage error, or a model call without its authorization."""


def sha(data):
    return hashlib.sha256(data).hexdigest()


def mapping_digest(mapping):
    """C06: the sha256 of the canonical JSON of {relative path: sha256 of the file's bytes}."""
    return sha(json.dumps(mapping, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode())


def files_digest(files):
    return mapping_digest({name: sha(data) for name, data in files.items()})


def read_tree(root):
    """{relative path: bytes}; a symlink anywhere refuses, because the tree then has no C06 digest."""
    files = {}
    for path in sorted(Path(root).rglob('*')):
        if path.is_symlink():
            raise Refusal('symlink in %s: %s' % (Path(root).name, path.relative_to(root).as_posix()))
        if path.is_file():
            files[path.relative_to(root).as_posix()] = path.read_bytes()
    return files


def tree_digest(root):
    return files_digest(read_tree(root))


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data if isinstance(data, bytes) else data.encode())


def dump(value):
    return json.dumps(value, indent=1, ensure_ascii=False) + '\n'


def load(path, what):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError) as problem:
        raise Refusal('unreadable %s (%s)' % (what, problem.__class__.__name__))


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def index_checker():
    return module('check_index', ROOT / 'eval' / 'scenario-index' / 'check_index.py')


def protocol():
    return module('protocol_check', ROOT / 'eval' / 'protocol-v2' / 'check.py')


def total(values):
    return sum(values) if values and all(isinstance(v, int) and not isinstance(v, bool) for v in values) else NA


# --- staging ---------------------------------------------------------------------------------------------

def safe_out(out):
    """Refuse an episode directory from which a participant could reach instructions or a repository."""
    if Path(out).exists() or Path(out).is_symlink():
        raise Refusal('--out exists: %s' % out)
    target = Path(os.path.realpath(out))
    for parent in target.parents:
        for marker in MARKERS:
            if (parent / marker).exists():
                raise Refusal('--out is under %s, which holds %s' % (parent, marker))
    existing = next(parent for parent in target.parents if parent.is_dir())
    inside = subprocess.run(['git', '-C', str(existing), 'rev-parse', '--is-inside-work-tree'], capture_output=True,
                            text=True)
    if inside.returncode == 0 and inside.stdout.strip() == 'true':
        raise Refusal('--out is inside a git work tree')


def read_install(root):
    """The install tree (C06): exactly SKILL.md and references/ of --install; a symlink refuses."""
    root = Path(root)
    skill = root / 'SKILL.md'
    if skill.is_symlink() or not skill.is_file():
        raise Refusal('--install holds no SKILL.md')
    files = {'SKILL.md': skill.read_bytes()}
    references = root / 'references'
    if references.is_symlink():
        raise Refusal('symlink in the install: references')
    if references.is_dir():
        for name, data in read_tree(references).items():
            files['references/' + name] = data
    return files


def find_variant(index, scenario, variant_id):
    entries = [e for e in index.get('scenarios', []) if e.get('scenario_id') == scenario]
    if not entries:
        entries = [e for e in index.get('scenarios', []) if str(e.get('scenario_id', '')).split('-')[0] == scenario]
    if len(entries) != 1:
        raise Refusal('scenario %s matches %d index entries' % (scenario, len(entries)))
    entry = entries[0]
    variant = next((v for v in entry.get('variants', []) if v.get('variant_id') == variant_id), None)
    if variant is None or not variant.get('stageable'):
        raise Refusal('%s has no stageable variant %s' % (entry['scenario_id'], variant_id))
    return entry, variant


def stage(args):
    if not ARM.fullmatch(args.arm):
        raise Usage('--arm is control, method, method:<config> or ablation:<rule_id>')
    if args.arm == 'control' and args.install:
        raise Refusal('a control arm receives no skill; drop --install')
    if args.arm != 'control' and not args.install:
        raise Usage('--install <dir> is required for a %s arm' % args.arm)
    out = Path(args.out).absolute()
    safe_out(out)
    checker = index_checker()
    tracked = checker.Tracked(Path(args.repo).resolve())
    if INDEX not in tracked.entries:
        raise Refusal('the git index of --repo holds no %s' % INDEX)
    try:
        index = json.loads(tracked.read(INDEX))
    except ValueError:
        raise Refusal('the staged %s is not JSON' % INDEX)
    entry, variant = find_variant(index, args.scenario, args.variant)
    try:
        files = checker.input_tree(tracked, variant)
    except checker.Symlink as problem:
        raise Refusal('symlink in the participant input: %s' % problem)
    except FileNotFoundError as problem:
        raise Refusal('participant input missing from the git index: %s' % problem)
    sheets = checker.own_sheets(tracked, entry['scenario_id'], variant)
    fixture = variant['fixture'] + '/'
    for name, data in files.items():
        if data in sheets or name in ('GROUND-TRUTH.md', fixture + 'GROUND-TRUTH.md'):
            raise Refusal('an answer sheet is in the participant input: %s' % name)
    digest = files_digest(files)
    if digest != variant.get('fixture_sha256'):
        raise Refusal('input digest %s differs from the index (%s)' % (digest, variant.get('fixture_sha256')))
    install = read_install(args.install) if args.install else None
    adapter = adapters.ADAPTERS[args.host]
    work, home, prompts, baseline = out / 'work', out / 'home', out / 'prompts', out / 'baseline'
    for directory in (work, home, prompts, baseline):
        directory.mkdir(parents=True)
    for name, data in files.items():
        if name.startswith(fixture):
            write(work / name[len(fixture):], data)
            write(baseline / name[len(fixture):], data)
        else:
            write(prompts / name, data)
    skill_digest = None
    if install:
        skill = home / adapter.skill_dir / 'tackle'
        for name, data in install.items():
            write(skill / name, data)
        skill_digest = tree_digest(skill)
    work_files = {name: sha(data) for name, data in read_tree(work).items()}
    write(out / 'stage.json', dump({
        'schema': 'tackle-harness-stage/1', 'scenario_id': entry['scenario_id'],
        'scenario': entry['scenario_id'].split('-')[0], 'variant_id': variant['variant_id'], 'split': variant['split'],
        'class': entry['class'], 'arm': args.arm, 'host': adapter.name, 'prompts': list(variant['prompts']),
        'input_sha256': digest, 'install_sha256': files_digest(install) if install else None,
        'skill_sha256': skill_digest, 'skill_dir': adapter.skill_dir + '/tackle' if install else None,
        'work_sha256': mapping_digest(work_files), 'work_files': work_files, 'staged_at': now()}))
    print('staged %s/%s arm=%s host=%s input=%s' % (entry['scenario_id'], variant['variant_id'], args.arm,
                                                     adapter.name, digest))


# --- sessions ---------------------------------------------------------------------------------------------

def base_env(isolation, episode):
    """The participant allowlist: PATH, LANG, TERM, TMPDIR and HOME, all inside the episode."""
    lang, term = os.environ.get('LANG') or 'C.UTF-8', os.environ.get('TERM') or 'dumb'
    if isolation == 'container':
        return {'PATH': adapters.CONTAINER_PATH, 'LANG': lang, 'TERM': term, 'TMPDIR': '/tmp',
                'HOME': adapters.CONTAINER_HOME}
    return {'PATH': '%s:%s' % (episode / 'bin', os.environ.get('PATH') or '/usr/bin:/bin'), 'LANG': lang,
            'TERM': term, 'TMPDIR': str(episode / 'tmp'), 'HOME': str(episode / 'home')}


def plan_session(adapter, episode, session, prompt, model=NA, effort=NA, isolation='local', image=None, network=None,
                 broker=None, name=None):
    """The argv, process env and participant env of one headless session. Starts nothing."""
    adapter = adapters.ADAPTERS[adapter] if isinstance(adapter, str) else adapter
    episode = Path(episode).absolute()
    if isolation == 'container':
        inner, extra = adapter.build(prompt, session, model, effort, adapters.CONTAINER_HOME, adapters.CONTAINER_WORK,
                                     broker=broker)
        participant = dict(base_env('container', episode), **extra)
        argv = adapters.container_argv(inner, participant, episode, image, network or 'none', name=name,
                                       user='%d:%d' % (os.getuid(), os.getgid()))
        return {'argv': argv, 'env': dict(os.environ), 'participant_env': participant, 'cwd': str(episode),
                'name': name}
    argv, extra = adapter.build(prompt, session, model, effort, str(episode / 'home'), str(episode / 'work'),
                                broker=broker)
    participant = dict(base_env('local', episode), **extra)
    return {'argv': argv, 'env': participant, 'participant_env': participant, 'cwd': str(episode / 'work'),
            'name': None}


def authorize(adapter, args):
    """The exit-2 checks, made before anything else happens."""
    if adapter.real:
        if not args.allow_model_calls:
            raise Usage('the %s adapter reaches a model: pass --allow-model-calls to authorize it' % adapter.name)
        if args.isolation != 'container':
            raise Usage('a real adapter runs only with --isolation container')
        missing = [flag for flag, value in (('--credential-file', args.credential_file), ('--image', args.image),
                                            ('--network', args.network), ('--broker-bind', args.broker_bind))
                   if not value]
        if missing:
            raise Usage('a real adapter needs ' + ', '.join(missing))
    elif args.isolation == 'container' and not args.image:
        raise Usage('--isolation container needs --image')


def broker_secret(data):
    """The one value the broker sends upstream: a JSON object's "key" string, otherwise the stripped text."""
    text = data.decode('utf-8', 'replace').strip()
    try:
        parsed = json.loads(text)
    except ValueError:
        parsed = None
    if isinstance(parsed, dict):
        if isinstance(parsed.get('key'), str) and parsed['key']:
            return parsed['key']
        raise Refusal('a JSON credential file needs a "key" string')
    if not text:
        raise Refusal('the credential file is empty')
    return text


class Runtime:
    """Session planning for one adapter; a real adapter also gets its host-side broker for the duration."""

    def __init__(self, adapter, args):
        self.adapter, self.args, self.proxy, self.broker = adapter, args, None, None

    def __enter__(self):
        if self.adapter.real:
            import broker
            token = secrets.token_urlsafe(32)
            self.proxy = broker.Broker(broker_secret(Path(self.args.credential_file).read_bytes()), self.adapter.upstream,
                                       token, token_header=self.adapter.token_header,
                                       token_prefix=self.adapter.token_prefix,
                                       credential_header=self.adapter.credential_header,
                                       credential_prefix=self.adapter.credential_prefix, bind=self.args.broker_bind)
            self.broker = {'url': self.proxy.start(), 'token': token}
        return self

    def __exit__(self, *exc):
        if self.proxy:
            self.proxy.stop()

    def plan(self, episode, session, prompt, model, effort, name=None):
        network = self.args.network if self.adapter.real else 'none'
        return plan_session(self.adapter, episode, session, prompt, model, effort, self.args.isolation, self.args.image,
                            network, self.broker, name if self.args.isolation == 'container' else None)


def scan(credential, plans, prompts, episode):
    """Refuse a launch when the credential, an encoding of it, or its path reaches the participant."""
    texts = {}
    for number, plan in enumerate(plans, 1):
        texts['argv:%02d' % number] = ' '.join(plan['argv'])
        for position, value in enumerate(plan['argv']):
            if value.startswith('type=bind'):
                texts['mount:%02d:%d' % (number, position)] = value
        for key, value in plan['participant_env'].items():
            texts['env:' + key] = value
    for name, text in prompts:
        texts['prompt:' + name] = text
    for tree in ('work', 'home', 'prompts', 'bin'):
        if (episode / tree).is_dir():
            for name, data in read_tree(episode / tree).items():
                texts['file:%s/%s' % (tree, name)] = data
    hits = credscan.find(credential, texts)
    if hits:
        raise Refusal('the credential reaches the participant through: %s' % ', '.join(hits))


def shim(path, target, prefix):
    write(path, '#!%s\nimport runpy, sys\nsys.argv = %r + sys.argv[1:]\nrunpy.run_path(%r, run_name="__main__")\n'
          % (sys.executable, prefix, str(target)))
    path.chmod(0o755)


def write_shims(episode, adapter, treated, isolation):
    """bin/: the fake agent for the fake adapter; tackle-dispatch only for treated arms under local isolation."""
    (episode / 'bin').mkdir(exist_ok=True)
    if adapter.name == 'fake':
        shim(episode / 'bin' / 'fake-agent', HERE / 'fake_agent.py', ['fake-agent'])
    if treated and isolation == 'local':
        shim(episode / 'bin' / 'tackle-dispatch', HERE / 'harness.py', ['harness.py', 'dispatch', '--episode', str(episode)])


def stop_group(child):
    try:
        os.killpg(child.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        child.kill()


def launch(plan, directory, seconds):
    """Run one session; streams are captured byte-exact and never rewritten; past the budget it is killed."""
    directory.mkdir(parents=True)
    started, begin = now(), time.monotonic()
    meta = {'exit': None, 'timeout': False, 'signal': None, 'error': None}
    with open(directory / 'stdout', 'wb') as out, open(directory / 'stderr', 'wb') as err:
        try:
            child = subprocess.Popen(plan['argv'], cwd=plan['cwd'], env=plan['env'], stdin=subprocess.DEVNULL,
                                     stdout=out, stderr=err, start_new_session=True)
        except OSError as problem:
            meta['error'] = 'launch failed (%s)' % problem.__class__.__name__
        else:
            try:
                code = child.wait(timeout=max(seconds, 0.1))
            except subprocess.TimeoutExpired:
                meta['timeout'] = True
                stop_group(child)
                if plan.get('name'):
                    subprocess.run(['docker', 'kill', plan['name']], capture_output=True)
                code = child.wait()
            meta['exit'] = code
            if code < 0:
                meta['signal'] = signal.Signals(-code).name
    meta.update(started_at=started, finished_at=now(), wall_seconds=round(time.monotonic() - begin, 3),
                stdout_sha256=sha((directory / 'stdout').read_bytes()),
                stderr_sha256=sha((directory / 'stderr').read_bytes()))
    return meta


# --- model map and roles -------------------------------------------------------------------------------------

def read_model_map(path):
    data = load(path, 'model map')
    tiers = data.get('tiers') if isinstance(data, dict) else None
    executor = data.get('executor') if isinstance(data, dict) else None
    if not isinstance(tiers, dict) or not tiers or not set(tiers) <= set(TIERS):
        raise Usage('the model map needs "tiers" among %s' % ', '.join(TIERS))
    for tier, spec in tiers.items():
        if not isinstance(spec, dict) or not isinstance(spec.get('model'), str) or not spec['model'] \
                or spec.get('effort', NA) not in EFFORTS + (NA,):
            raise Usage('invalid model map tier %s' % tier)
    if not isinstance(executor, dict) or executor.get('tier') not in tiers or executor.get('effort', NA) not in EFFORTS + (NA,):
        raise Usage('the model map needs an "executor" whose tier is in "tiers"')
    return data


def executor_binding(model_map):
    if not model_map:
        return NA, NA
    tier = model_map['executor']['tier']
    return model_map['tiers'][tier]['model'], model_map['executor'].get('effort') or model_map['tiers'][tier].get('effort', NA)


def tier_binding(model_map, tier):
    spec = (model_map or {}).get('tiers', {}).get(tier)
    return (spec['model'], spec.get('effort', NA)) if spec else (NA, NA)


def tier_of(model_map, model):
    for tier, spec in (model_map or {}).get('tiers', {}).items():
        if spec.get('model') == model:
            return tier
    return NA


def dispatched(episode):
    path = episode / 'roles.jsonl'
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def native_roles(home, model_map=None):
    """Per-role usage from Claude Code's own subagent transcripts under the episode HOME (native delegation)."""
    roles = []
    for agent in usage.claude_code_subagents(home):
        spent = agent['usage']
        served = spent.get('models') or []
        model = served[0] if len(served) == 1 else ('+'.join(served) if served else agent.get('model_requested') or NA)
        role = agent.get('role') if agent.get('role') not in (None, '', NA) else 'subagent'
        roles.append({'role': role, 'tier': tier_of(model_map, model), 'model': model, 'effort': NA,
                      'tokens_in': spent['tokens_in'], 'tokens_out': spent['tokens_out']})
    return roles


def files_written(work, before):
    count = 0
    for path in sorted(Path(work).rglob('*')):
        if path.is_symlink() or path.is_file():
            data = os.readlink(path).encode() if path.is_symlink() else path.read_bytes()
            if before.get(path.relative_to(work).as_posix()) != sha(data):
                count += 1
    return count


def run(args):
    adapter = adapters.ADAPTERS[args.adapter]
    authorize(adapter, args)
    episode = Path(args.episode).absolute()
    staged = load(episode / 'stage.json', 'stage.json')
    if staged.get('host') != adapter.name:
        raise Refusal('the episode was staged for host %s' % staged.get('host'))
    if (episode / 'run.json').exists() or (episode / 'sessions').exists():
        raise Refusal('the episode already ran')
    model_map = read_model_map(args.model_map) if args.model_map else None
    model, effort = executor_binding(model_map)
    prompts = [(name, (episode / 'prompts' / name).read_bytes().decode('utf-8')) for name in staged['prompts']]
    (episode / 'tmp').mkdir(exist_ok=True)
    write_shims(episode, adapter, staged['arm'] != 'control', args.isolation)
    deadline, token = time.time() + args.budget_seconds, secrets.token_hex(4)
    sessions, outcome = [], 'completed'
    with Runtime(adapter, args) as runtime:
        plans = [runtime.plan(episode, number, text, model, effort, name='episode-%s-%02d' % (token, number))
                 for number, (_, text) in enumerate(prompts, 1)]
        if args.credential_file:
            scan(Path(args.credential_file), plans, prompts, episode)
        write(episode / 'run-context.json', dump({'adapter': adapter.name, 'isolation': args.isolation,
                                                  'model_map': model_map, 'deadline': deadline, 'arm': staged['arm']}))
        for number, ((name, _), plan) in enumerate(zip(prompts, plans), 1):
            if deadline - time.time() <= 0:
                outcome = 'timeout'
                break
            directory = episode / 'sessions' / ('%02d' % number)
            meta = launch(plan, directory, deadline - time.time())
            meta = dict(index=number, prompt=name, **meta, **adapter.parse((directory / 'stdout').read_bytes()))
            sessions.append(meta)
            write(directory / 'meta.json', dump(meta))
            if meta['error'] or meta['timeout']:
                outcome = 'error' if meta['error'] else 'timeout'
                break
        broker_log = list(runtime.proxy.log) if runtime.proxy else None
    home = episode / 'home'
    if adapter.name == 'claude-code':
        exact = {item['session_id']: item['usage'] for item in usage.claude_code_sessions(home)}
        for meta in sessions:
            found = exact.get(meta['session_id'])
            if found and found['tokens_in'] != NA:
                meta.update(tokens_in=found['tokens_in'], tokens_out=found['tokens_out'], usage_source='transcript')
    delegated = dispatched(episode)
    roles = [{key: item[key] for key in ('role', 'tier', 'model', 'effort', 'tokens_in', 'tokens_out')} for item in delegated]
    native = native_roles(home, model_map) if adapter.name == 'claude-code' else []
    roles += native
    hashes = [meta['stdout_sha256'] for meta in sessions]
    loads = [meta['skill_loaded'] for meta in sessions]
    result = {
        'schema': 'tackle-harness-run/1', 'adapter': adapter.name, 'isolation': args.isolation, 'outcome': outcome,
        'exit': sessions[-1]['exit'] if sessions else None, 'timeout': outcome == 'timeout',
        'signal': sessions[-1]['signal'] if sessions else None, 'sessions': sessions,
        'transcript_sha256': (hashes[0] if len(hashes) == 1 else
                              sha(json.dumps(hashes, separators=(',', ':')).encode()) if hashes else None),
        'skill_loaded': True if True in loads else (False if loads and all(v is False for v in loads) else NA),
        'executor': {'harness': adapter.name, 'model': model, 'effort': effort}, 'roles': roles,
        'cost': {'tokens_in': total([m['tokens_in'] for m in sessions] + [r['tokens_in'] for r in roles]),
                 'tokens_out': total([m['tokens_out'] for m in sessions] + [r['tokens_out'] for r in roles]),
                 'wall_seconds': int(round(sum(m['wall_seconds'] for m in sessions))),
                 'tool_calls': total([m['tool_calls'] for m in sessions] + [d.get('tool_calls', NA) for d in delegated]
                                     + [NA] * len(native)),
                 'files_written': files_written(episode / 'work', staged['work_files'])},
        'capture_path': adapter.capture_path, 'model_binding': 'bound' if model_map else 'unsupported',
        'started_at': sessions[0]['started_at'] if sessions else now(),
        'finished_at': sessions[-1]['finished_at'] if sessions else now()}
    write(episode / 'run.json', dump(result))
    if broker_log is not None:
        write(episode / 'broker-log.json', dump(broker_log))
    if args.credential_file:
        records = {name: (episode / name).read_bytes() for name in ('run.json', 'roles.jsonl', 'broker-log.json')
                   if (episode / name).exists()}
        leaked = credscan.find(Path(args.credential_file), records)
        if leaked:
            raise Refusal('the credential reached a record: %s' % ', '.join(leaked))
    print('run: outcome=%s sessions=%d' % (outcome, len(sessions)))
    return 1 if outcome == 'error' else 0


def dispatch(args):
    """One separate headless session of the episode's host, bound to a tier of the model map."""
    episode = Path(args.episode).absolute()
    context = load(episode / 'run-context.json', 'run-context.json')
    adapter = adapters.ADAPTERS.get(context.get('adapter'))
    if adapter is None:
        raise Refusal('run-context.json names no known adapter')
    if adapter.real:
        if not args.allow_model_calls:
            raise Usage('the %s adapter reaches a model: pass --allow-model-calls to authorize it' % adapter.name)
        raise Refusal('dispatch inside a container is not available; native delegation transcripts give per-role '
                      'usage (unobserved until an authorized smoke episode)')
    if not ROLE.fullmatch(args.role):
        raise Usage('--role is a short name of letters, digits, spaces, "_" or "-"')
    prompt = Path(args.prompt_file).read_bytes().decode('utf-8')
    model, effort = tier_binding(context.get('model_map'), args.tier)
    roles = episode / 'roles'
    number = len([p for p in roles.iterdir() if p.is_dir()]) + 1 if roles.is_dir() else 1
    directory = roles / ('%02d' % number)
    meta = launch(plan_session(adapter, episode, 'role-%d' % number, prompt, model, effort), directory,
                  context['deadline'] - time.time())
    stdout = (directory / 'stdout').read_bytes()
    parsed = adapter.parse(stdout)
    entry = {'role': args.role, 'tier': args.tier, 'model': model, 'effort': effort, 'tokens_in': parsed['tokens_in'],
             'tokens_out': parsed['tokens_out'], 'tool_calls': parsed['tool_calls'], 'index': number,
             'exit': meta['exit'], 'timeout': meta['timeout'], 'stdout_sha256': meta['stdout_sha256'], 'source': 'dispatch'}
    with open(episode / 'roles.jsonl', 'a') as handle:
        handle.write(json.dumps(entry) + '\n')
    sys.stdout.buffer.write(stdout)
    sys.stdout.flush()
    return 0 if meta['exit'] == 0 else 1


# --- records ---------------------------------------------------------------------------------------------------

def record(args):
    """Append one C01 line whose prev_sha256 chains to the previous line; each line is checked before it lands."""
    episode, cohort = Path(args.episode).absolute(), Path(args.cohort).absolute()
    staged = load(episode / 'stage.json', 'stage.json')
    ran = load(episode / 'run.json', 'run.json')
    manifest = load(cohort / 'manifest.json', 'manifest.json')
    judgment = load(args.judgment, 'judgment')
    if (episode / 'recorded.json').exists():
        raise Refusal('the episode is already recorded')
    check = protocol()
    report = check.Report()
    context = check.check_manifest(manifest, report)
    if report.errors or context is None:
        raise Refusal('the cohort manifest fails the protocol checker')
    order = {entry['episode_id']: (position, entry) for position, entry in enumerate(context['order'])}
    if args.episode_id not in order:
        raise Refusal('episode %s is not in the manifest order' % args.episode_id)
    position, entry = order[args.episode_id]
    if entry['arm'] != staged['arm'] or entry['variant_id'] != staged['variant_id'] \
            or entry['scenario_id'] not in (staged['scenario_id'], staged['scenario']):
        raise Refusal('the staged episode does not match order entry %s' % args.episode_id)
    variant = context['variants'][(entry['scenario_id'], entry['variant_id'])]
    if variant['fixture_sha256'] != staged['input_sha256']:
        raise Refusal('the manifest seals another input digest for this variant')
    path = cohort / 'episodes.jsonl'
    existing = path.read_bytes() if path.exists() else b''
    if existing and not existing.endswith(b'\n'):
        raise Refusal('episodes.jsonl does not end with a newline')
    lines = existing.split(b'\n')[:-1] if existing else []
    for line in lines:
        try:
            previous = json.loads(line)
        except ValueError:
            raise Refusal('episodes.jsonl holds a line that is not JSON')
        if isinstance(previous, dict) and previous.get('episode_id') == args.episode_id:
            raise Refusal('episode %s is already recorded' % args.episode_id)
    outcome, reason = judgment.get('outcome'), judgment.get('invalid_reason')
    exposure, scores = judgment.get('rule_exposure'), judgment.get('scores')
    forced = None
    if ran['outcome'] in ('timeout', 'error'):
        forced = (ran['outcome'], None, exposure)
    elif staged['arm'] == 'control' and ran.get('skill_loaded') is True:
        forced = ('invalid', 'a control session loaded a skill (transcript evidence)', True)
    if forced:
        outcome, reason, exposure = forced
        scores = {key: None for key in check.SCORE_FIELDS}
    line = {'schema': 'tackle-episode/1', 'cohort_id': manifest['cohort_id'], 'episode_id': args.episode_id,
            'prev_sha256': sha(lines[-1]) if lines else '0' * 64, 'scenario_id': entry['scenario_id'],
            'variant_id': entry['variant_id'], 'split': variant['split'], 'arm': entry['arm'], 'seed': entry['seed'],
            'order_index': position, 'artifact_sha256': staged['install_sha256'], 'executor': ran['executor'],
            'roles': ran['roles'], 'judge': judgment.get('judge'), 'rule_exposure': exposure, 'outcome': outcome,
            'invalid_reason': reason, 'scores': scores, 'cost': ran['cost'], 'transcript_sha256': ran['transcript_sha256'],
            'started_at': ran['started_at'], 'finished_at': ran['finished_at']}
    at = report.at(check.EPISODES, len(lines) + 1)
    if at.closed(line, check.EPISODE_FIELDS, 'record'):
        check.check_fields(line, at)
        check.check_against_manifest(line, context, order, at)
    if report.errors:
        raise Refusal('the record fails the protocol checker: %s'
                      % '; '.join('%s: %s' % (error['code'], error['text']) for error in report.errors))
    data = json.dumps(line, ensure_ascii=False).encode()
    with open(path, 'ab') as handle:
        handle.write(data + b'\n')
    write(episode / 'recorded.json', dump({'cohort_id': manifest['cohort_id'], 'episode_id': args.episode_id,
                                           'line_sha256': sha(data)}))
    print('recorded %s as line %d (outcome %s)' % (args.episode_id, len(lines) + 1, outcome))


# --- packets ---------------------------------------------------------------------------------------------------

class Blinder:
    """Neutral tokens for episode, install and skill paths, arm names and the method's name; leaks become <redacted>."""

    def __init__(self, arms, episodes):
        replacements = {}
        pairs = [(adapters.CONTAINER_WORK, '<work>'), (adapters.CONTAINER_HOME, '<home>'), (adapters.CONTAINER_BIN, '<bin>')]
        for episode in episodes:
            for base in {str(Path(episode).absolute()), os.path.realpath(episode)}:
                pairs += [(base + '/' + sub, '<%s>' % sub) for sub in ('work', 'home', 'bin', 'tmp', 'baseline')]
                pairs.append((base, '<episode>'))
        for path, token in pairs:
            for form in (path, path.replace('/', '\\/'), urllib.parse.quote(path), urllib.parse.quote(path, safe='')):
                replacements[form] = token
        self.paths = sorted(replacements.items(), key=lambda item: -len(item[0]))
        self.skill = re.compile(r'\.(?:agents|claude|fake)%sskills%stackle|skills%stackle' % (SLASH, SLASH, SLASH), re.I)
        labels = set(arms) | {'control', 'method'}
        for arm in list(labels):
            kind, _, detail = arm.partition(':')
            if detail:  # method:<config>, ablation:<rule>: every separator, and the detail alone
                labels |= {kind + sep + detail for sep in '-_ '} | {detail}
        ordered = sorted(labels, key=len, reverse=True)
        # Underscores separate words here: control_group and method_notes are arm names too (D-71).
        self.arms = re.compile(r'(?<![A-Za-z0-9])(%s)(?![A-Za-z0-9])' % '|'.join(map(re.escape, ordered)), re.I)
        self.name = re.compile(r'(?<![A-Za-z0-9])tackle(?![A-Za-z0-9])', re.I)
        self.leaks = protocol().LEAKS
        key = next(p for p in self.leaks if 'PRIVATE' in p.pattern)
        self.redact = [
            re.compile(r'(?:%s(?:Users|home|root|private)%s|%svar%sfolders%s|~%s)%s'
                       % (SLASH, SLASH, SLASH, SLASH, SLASH, SLASH, PATH_REST)),
            re.compile(r'[A-Za-z]:\\+' + PATH_REST),
            re.compile(key.pattern + r'[\s\S]*?(?:' + key.pattern.replace('BEGIN', 'END') + r'|\Z)')]
        self.redact += [p for p in self.leaks if not p.pattern.startswith(('/', '~', '[A-Za-z]:')) and p is not key]

    def apply(self, text):
        for path, token in self.paths:
            text = text.replace(path, token)
        text = self.skill.sub('<skills>/<skill>', text)
        count = 0
        for pattern in self.redact:
            text, found = pattern.subn('<redacted>', text)
            count += found
        text = self.name.sub('<skill>', self.arms.sub('<arm>', text))
        for _ in range(5):
            found = 0
            for pattern in self.leaks:
                text, hits = pattern.subn('<redacted>', text)
                found += hits
            count += found
            if not found:
                break
        return text, count


def listing(root):
    found = {}
    for path in sorted(Path(root).rglob('*')) if Path(root).is_dir() else []:
        name = path.relative_to(root).as_posix()
        if path.is_symlink():
            found[name] = 'link:' + os.readlink(path)
        elif path.is_file():
            found[name] = path.read_bytes()
    return found


def work_diff(episode):
    before, after = listing(episode / 'baseline'), listing(episode / 'work')
    parts = []
    for name in sorted(set(before) | set(after)):
        old, new = before.get(name), after.get(name)
        if old == new:
            continue
        if isinstance(old, str) or isinstance(new, str):
            parts.append('link changed: %s\n' % name)
            continue
        try:
            a = old.decode('utf-8').splitlines(True) if old is not None else []
            b = new.decode('utf-8').splitlines(True) if new is not None else []
        except UnicodeDecodeError:
            parts.append('binary file changed: %s\n' % name)
            continue
        lines = difflib.unified_diff(a, b, 'a/' + name if old is not None else '/dev/null',
                                     'b/' + name if new is not None else '/dev/null')
        parts.append(''.join(line if line.endswith('\n') else line + '\n' for line in lines))
    return ''.join(parts) or 'no changes\n'


def transcript_text(episode, ran):
    parts = []
    for meta in ran['sessions']:
        directory = episode / 'sessions' / ('%02d' % meta['index'])
        parts.append('=== session %02d ===\n' % meta['index'] + (directory / 'stdout').read_bytes().decode('utf-8', 'replace'))
        errors = (directory / 'stderr').read_bytes().decode('utf-8', 'replace')
        if errors:
            parts.append('=== session %02d stderr ===\n' % meta['index'] + errors)
    roles = episode / 'roles'
    for directory in sorted(p for p in roles.iterdir() if p.is_dir()) if roles.is_dir() else []:
        parts.append('=== delegated session %s ===\n' % directory.name
                     + (directory / 'stdout').read_bytes().decode('utf-8', 'replace'))
    return '\n'.join(parts)


def answer_sheet_lines(repo):
    """{(scenario_id, variant_id): [long lines of its own answer sheets]} from the git index of --repo."""
    checker = index_checker()
    tracked = checker.Tracked(repo)
    if INDEX not in tracked.entries:
        return {}
    lines = {}
    for entry in json.loads(tracked.read(INDEX)).get('scenarios', []):
        for variant in entry.get('variants', []):
            found = set()
            for sheet in checker.own_sheets(tracked, entry['scenario_id'], variant):
                found |= {line.strip() for line in sheet.decode('utf-8', 'replace').splitlines() if len(line.strip()) >= 24}
            lines[(entry['scenario_id'], variant['variant_id'])] = sorted(found)
    return lines


def packet(args):
    """One blinded packet per episode, shuffled by the seed; the label map is written only under --labels."""
    out, labels = Path(args.out).absolute(), Path(args.labels).absolute()
    real_out, real_labels = Path(os.path.realpath(out)), Path(os.path.realpath(labels))
    if real_labels == real_out or real_out in real_labels.parents or real_labels in real_out.parents:
        raise Refusal('--labels must be outside --out')
    if out.exists() or (labels / 'labels.json').exists():
        raise Refusal('--out or the label map already exists')
    manifest = load(Path(args.cohort) / 'manifest.json', 'manifest.json')
    sheets = answer_sheet_lines(Path(args.repo).resolve())
    items = []
    for name in args.episodes:
        episode = Path(name).absolute()
        recorded = load(episode / 'recorded.json', 'recorded.json')
        if recorded.get('cohort_id') != manifest.get('cohort_id'):
            raise Refusal('an episode is recorded in another cohort')
        items.append((recorded['episode_id'], episode, load(episode / 'stage.json', 'stage.json'),
                      load(episode / 'run.json', 'run.json')))
    items.sort(key=lambda item: item[0])
    random.Random(args.seed).shuffle(items)
    blinder = Blinder(manifest.get('arms') or [], [item[1] for item in items])
    mapping = {'schema': 'tackle-harness-labels/1', 'cohort_id': manifest['cohort_id'], 'seed': args.seed, 'packets': {}}
    for number, (episode_id, episode, staged, ran) in enumerate(items, 1):
        name = 'packet-%02d' % number
        texts = {'transcript.txt': transcript_text(episode, ran), 'changes.diff': work_diff(episode)}
        for prompt in staged['prompts']:
            texts['prompts/' + prompt] = (episode / 'prompts' / prompt).read_bytes().decode('utf-8', 'replace')
        withheld = sheets.get((staged['scenario_id'], staged['variant_id']), [])
        redactions, dropped, cleaned = 0, 0, {}
        for file_name, text in texts.items():
            if any(line in text for line in withheld):
                raise Refusal('an answer-sheet line reached %s/%s; the episode is not judgeable' % (name, file_name))
            clean, count = blinder.apply(text)
            if file_name == 'transcript.txt':  # skill-file reads are the treatment's signature (D-71)
                kept = [line for line in clean.split('\n') if '<skills>/<skill>' not in line]
                dropped = clean.count('\n') + 1 - len(kept)
                clean = '\n'.join(kept)
            if any(pattern.search(clean) for pattern in blinder.leaks):
                raise Refusal('a leak survived blinding in %s/%s' % (name, file_name))
            redactions += count
            cleaned[file_name] = clean
        for file_name, clean in cleaned.items():
            write(out / name / file_name, clean)
        mapping['packets'][name] = {'episode_id': episode_id, 'arm': staged['arm'], 'redactions': redactions,
                                    'dropped_skill_lines': dropped}
    data = dump(mapping).encode()
    write(labels / 'labels.json', data)
    print('packets=%d labels_sha256=%s' % (len(items), sha(data)))


# --- probes ------------------------------------------------------------------------------------------------------

def probe(args):
    """Each probe prompt in an empty work tree with the install; skill_loaded comes from transcript evidence only."""
    adapter = adapters.ADAPTERS[args.adapter]
    authorize(adapter, args)
    probes = load(args.probes, 'probes file').get('probes') or []
    out = Path(args.out).absolute()
    safe_out(out)
    install = read_install(args.install)
    results = []
    with Runtime(adapter, args) as runtime:
        for item in probes:
            episode = out / item['id']
            for sub in ('work', 'home', 'tmp'):
                (episode / sub).mkdir(parents=True)
            for name, data in install.items():
                write(episode / 'home' / adapter.skill_dir / 'tackle' / name, data)
            write_shims(episode, adapter, False, args.isolation)
            plan = runtime.plan(episode, 1, item['prompt'], NA, NA, name='probe-%s' % secrets.token_hex(4))
            if args.credential_file:
                scan(Path(args.credential_file), [plan], [('probe', item['prompt'])], episode)
            meta = launch(plan, episode / 'sessions' / '01', args.budget_seconds)
            parsed = adapter.parse((episode / 'sessions' / '01' / 'stdout').read_bytes())
            results.append({'id': item['id'], 'lang': item.get('lang'), 'intent': item.get('intent'),
                            'expect': item.get('expect'), 'skill_loaded': parsed['skill_loaded'], 'exit': meta['exit'],
                            'timeout': meta['timeout'], 'stdout_sha256': meta['stdout_sha256']})
    write(out / 'results.json', dump({'schema': 'tackle-harness-probe-results/1', 'adapter': adapter.name,
                                      'install_sha256': files_digest(install), 'probes': results}))
    triggers = [r for r in results if r['expect'] == 'trigger']
    others = [r for r in results if r['expect'] != 'trigger']
    print('probes=%d trigger_loaded=%d/%d non_trigger_loaded=%d/%d' % (
        len(results), sum(r['skill_loaded'] is True for r in triggers), len(triggers),
        sum(r['skill_loaded'] is True for r in others), len(others)))


# --- command line -------------------------------------------------------------------------------------------------

def positive(text):
    value = int(text)
    if value < 1:
        raise argparse.ArgumentTypeError('must be at least 1')
    return value


def parser():
    top = argparse.ArgumentParser(prog='harness.py', description='Protocol v2 harness (eval/harness-v2/README.md).')
    commands = top.add_subparsers(dest='command', required=True)
    staging = commands.add_parser('stage')
    staging.add_argument('--scenario', required=True)
    staging.add_argument('--variant', required=True)
    staging.add_argument('--arm', required=True)
    staging.add_argument('--host', required=True, choices=sorted(adapters.ADAPTERS))
    staging.add_argument('--install')
    staging.add_argument('--out', required=True)
    staging.add_argument('--repo', default=str(ROOT))
    running = commands.add_parser('run')
    running.add_argument('--episode', required=True)
    running.add_argument('--budget-seconds', required=True, type=positive)
    running.add_argument('--model-map')
    probing = commands.add_parser('probe')
    probing.add_argument('--probes', required=True)
    probing.add_argument('--install', required=True)
    probing.add_argument('--out', required=True)
    probing.add_argument('--budget-seconds', type=positive, default=120)
    for command in (running, probing):
        command.add_argument('--adapter', required=True, choices=sorted(adapters.ADAPTERS))
        command.add_argument('--isolation', choices=('local', 'container'), default='local')
        command.add_argument('--credential-file')
        command.add_argument('--image')
        command.add_argument('--network')
        command.add_argument('--broker-bind')
        command.add_argument('--allow-model-calls', action='store_true')
    delegating = commands.add_parser('dispatch')
    delegating.add_argument('--episode', required=True)
    delegating.add_argument('--role', required=True)
    delegating.add_argument('--tier', required=True, choices=TIERS)
    delegating.add_argument('--prompt-file', required=True)
    delegating.add_argument('--allow-model-calls', action='store_true')
    recording = commands.add_parser('record')
    for flag in ('--episode', '--cohort', '--episode-id', '--judgment'):
        recording.add_argument(flag, required=True)
    packing = commands.add_parser('packet')
    packing.add_argument('--cohort', required=True)
    packing.add_argument('--episodes', required=True, nargs='+')
    packing.add_argument('--seed', required=True, type=int)
    packing.add_argument('--out', required=True)
    packing.add_argument('--labels', required=True)
    packing.add_argument('--repo', default=str(ROOT))
    return top


COMMANDS = {'stage': stage, 'run': run, 'dispatch': dispatch, 'record': record, 'packet': packet, 'probe': probe}


def main(argv=None):
    try:
        args = parser().parse_args(argv)
    except SystemExit as stop:
        return stop.code if isinstance(stop.code, int) else 2
    try:
        return COMMANDS[args.command](args) or 0
    except Usage as problem:
        print('usage: %s' % problem, file=sys.stderr)
        return 2
    except Refusal as problem:
        print('refused: %s' % problem, file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
