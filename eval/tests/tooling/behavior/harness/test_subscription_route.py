"""End-to-end checks of the subscription route: run, probe and judge.

Nothing here starts a real CLI, sandbox or model. A stub ``claude`` and a fake ``sandbox-exec`` from
``eval/behavior/harness/fixtures/subscription-route`` are copied into a scratch directory, and the route runs as
a subprocess on a PATH built from scratch (the fake launcher only), so the suite passes on Linux and macOS with
no skip. Synthetic scenario packages, a synthetic skill tree and a synthetic token are built at run time. The
consumer is the protocol checker: the stub cohort must pass ``eval/protocol-v2/check.py``. The token variable's
name is assembled by concatenation, and no assertion echoes a credential. Like the route's own run root, the
temporary directory must sit outside the home directory, with no agent instructions in any directory above it.
"""
import base64
import fcntl
import hashlib
import importlib.util
import json
import os
import re
import secrets
import shlex
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parents[5] / 'eval/behavior/harness'
ROOT = HERE.parents[2]
ROUTE = HERE / 'subscription_route.py'
FIXTURES = HERE / 'fixtures' / 'subscription-route'
CHECK = ROOT / 'eval' / 'protocol-v2' / 'check.py'
sys.path.insert(0, str(HERE))
try:
    import subscription_route as route
except ImportError:  # the module may not exist yet: each test that needs it still fails on its own
    route = None

SEP = '/'
HOME_PREFIX = SEP + 'Users' + SEP
TOKEN_VARIABLE = 'CLAUDE_CODE_' + 'OAUTH_TOKEN'  # never spelled out: the credential guard scans this file
DENIED_READS = [SEP + name for name in ('Users', 'private/tmp', 'Volumes', 'private/var/folders', 'private/var/tmp')]
CHILD_ENV = {'PATH', 'HOME', 'TMPDIR', 'LANG', 'TERM', 'NO_COLOR', 'DISABLE_TELEMETRY', 'DISABLE_ERROR_REPORTING',
             'DISABLE_AUTOUPDATER', 'CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC', 'CLAUDE_CODE_TMPDIR', TOKEN_VARIABLE}
# Variables a platform or interpreter adds inside any child process; the route does not pass them.
PLATFORM_ENV = {'__CF_USER_TEXT_ENCODING', 'LC_CTYPE'}
SCORES = ('correct_action', 'evidence', 'verification_honesty', 'report_quality')
NO_SCORES = {name: None for name in SCORES}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def digest_files(files):
    """Tree digest over {relative path: bytes}, written independently of the route."""
    mapping = {name: sha(data) for name, data in files.items()}
    return sha(json.dumps(mapping, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode())


def dir_files(root):
    files = {}
    for path in sorted(Path(root).rglob('*')):
        if path.is_file() and not path.is_symlink():
            files[path.relative_to(root).as_posix()] = path.read_bytes()
    return files


def write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data if isinstance(data, bytes) else data.encode())


def load(path):
    return json.loads(Path(path).read_text())


def lines(path):
    path = Path(path)
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


def protocol_leaks():
    """The episode-record leak patterns, imported from the protocol checker rather than restated."""
    spec = importlib.util.spec_from_file_location('protocol_check', CHECK)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.LEAKS


def make_script(source, destination):
    """Copy a fixture script with a shebang that names this interpreter, so no PATH lookup is needed."""
    body = Path(source).read_text().split('\n', 1)[1]
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text('#!%s\n%s' % (sys.executable, body))
    destination.chmod(0o755)


def token_forms(token):
    raw = token.encode()
    standard = base64.b64encode(raw).decode()
    return [token, standard, standard.rstrip('='), base64.urlsafe_b64encode(raw).decode(), raw.hex(), raw.hex().upper(),
            urllib.parse.quote(token, safe=''), json.dumps(token)[1:-1]]


def rule_prefix(rule):
    """The directory a Read(//dir/**) or Edit(//dir/**) rule covers, or None for any other rule."""
    match = re.fullmatch(r'(?:Read|Edit)\(/(/.+)/\*\*\)', rule)
    return match.group(1) if match else None


def covers(prefix, path):
    """Whether path lies in the tree that prefix names, with symlinked spellings (/tmp, /var) resolved on both sides."""
    prefix, path = os.path.realpath(prefix), os.path.realpath(path)
    return path == prefix or path.startswith(prefix.rstrip(SEP) + SEP)


def wait_for(found, timeout=30):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        value = found()
        if value:
            return value
        time.sleep(0.05)
    raise AssertionError('timed out waiting')


class Env:
    """A disposable instrument environment: stub CLI, fake launcher, token, configuration and synthetic packages."""

    def __init__(self, token=None):
        self.tmp = Path(os.path.realpath(tempfile.mkdtemp(prefix='sub-route-')))
        self.bin, self.cli_dir = self.tmp / 'bin', self.tmp / 'cli'
        self.stub, self.launcher = self.cli_dir / 'claude', self.bin / 'sandbox-exec'
        make_script(FIXTURES / 'claude', self.stub)
        make_script(FIXTURES / 'sandbox-exec', self.launcher)
        # The oracle interpreter is a wrapper in the scratch tree, so the suite does not depend on where Python lives.
        self.oracle_python = self.tmp / 'tools' / 'oracle-python'
        write(self.oracle_python, '#!/bin/sh\nexec %s "$@"\n' % shlex.quote(sys.executable))
        self.oracle_python.chmod(0o755)
        self.token = token or 'syn-' + secrets.token_hex(24)
        self.token_file = self.tmp / 'secrets' / 'token.txt'
        write(self.token_file, self.token + '\n')
        self.token_file.chmod(0o644)
        self.repo, self.cohort, self.out = self.tmp / 'repo', self.tmp / 'cohort', self.tmp / 'out'
        self.run_root, self.state = self.tmp / 'runroot', self.tmp / 'state'
        self.config_path, self.install = self.tmp / 'config' / 'route.json', self.tmp / 'install'
        self.sheet = 'ANSWER-SHEET-SENTINEL-' + secrets.token_hex(8)
        self.marker = self.tmp / 'oracle-ran.txt'
        for name in ('tmp', 'home', 'emptybin'):
            (self.tmp / name).mkdir()
        self.repo.mkdir()
        self.cohort.mkdir()
        self.digests, self.order = {}, []
        self.install_digest = self.make_install()
        self.write_config()

    def close(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def make_install(self):
        files = {'SKILL.md': '---\nname: tackle\ndescription: Synthetic skill for route checks.\n---\nBody.\n',
                 'references/guides/one.md': '# One\n', 'references/two.md': '# Two\n'}
        for name, text in files.items():
            write(self.install / name, text)
        return digest_files({name: text.encode() for name, text in files.items()})

    def config(self):
        return {'schema': 'tackle-route-config/1',
                'cli': {'path': str(self.stub), 'sha256': sha(self.stub.read_bytes()), 'version': '0.0.0 (stub)'},
                'model': 'stub-model', 'run_root': str(self.run_root), 'token_file': str(self.token_file),
                'state_dir': str(self.state), 'cli_tmp_limit': 4096,
                'caps': {'total_usd': 50, 'episode': {'usd': 1.0, 'seconds': 60, 'turns': 10}, 'stages': {'stage': 20},
                         'probe': {'total_usd': 4, 'child_usd': 1.0, 'child_seconds': 60, 'child_turns': 12}},
                'oracle': {'python': str(self.oracle_python), 'seconds': 30, 'denied_prefixes': self.denied_prefixes()},
                'launcher': str(self.launcher)}

    def denied_prefixes(self):
        """The built-in denied trees minus those holding this scratch tree, where the fake launcher's interpreter wrapper lives."""
        trees = [SEP + 'Users'] + [SEP + name for name in ('private/tmp', 'tmp', 'Volumes', 'private/var/folders', 'var/folders',
                                                           'private/var/tmp')]
        return [tree for tree in trees if not covers(tree, self.tmp)]

    def write_config(self, cfg=None):
        write(self.config_path, json.dumps(cfg or self.config(), indent=1))

    def package(self, scenario, variant, prompts=(('task.md', 'Do the task.\n'),), fixture=None, oracle=None):
        """A synthetic scenario package under the repo: answer sheets and the oracle beside input/, as a committed one has them."""
        base = self.repo / 'eval' / 'scenarios' / scenario
        variant_dir = base / 'variants' / variant
        write(base / 'GROUND-TRUTH.md', self.sheet + '\n')
        write(variant_dir / 'GROUND-TRUTH.md', self.sheet + '\n')
        files = {}
        for name, text in prompts:
            write(variant_dir / 'input' / name, text)
            files[name] = text.encode()
        for name, text in (fixture or {'mode.txt': 'ok'}).items():
            write(variant_dir / 'input' / 'fixture' / name, text)
            files['fixture/' + name] = text.encode()
        (variant_dir / 'oracle').mkdir(parents=True, exist_ok=True)
        shutil.copy(FIXTURES / 'oracle' / 'check.py', variant_dir / 'oracle' / 'check.py')
        write(variant_dir / 'oracle' / 'data.json', json.dumps(oracle or {}))
        self.digests[(scenario, variant)] = digest_files(files)
        return self.digests[(scenario, variant)]

    def seal_cohort(self, order, cohort_id='syn-cohort', install_digest=None, tamper=None):
        """Write manifest.json for order = [(episode_id, scenario, variant, arm, seed)]."""
        self.order = order
        arms = sorted({entry[3] for entry in order})
        seeds = sorted({entry[4] for entry in order})
        variants = sorted({(entry[1], entry[2]) for entry in order})
        body = {
            'schema': 'tackle-cohort/1', 'cohort_id': cohort_id,
            'hypothesis': 'With the method, the agent falls into the trap less often than with the control.',
            'primary_metric': 'fall rate', 'decision_rule': 'protocol v2 labels', 'n_min': 1, 'seeds': seeds,
            'variants': [{'scenario_id': s, 'variant_id': v, 'split': 'held-out' if v.startswith('h') else 'development',
                          'class': 'outcome-trap', 'fixture_sha256': self.digests[(s, v)]} for s, v in variants],
            'arms': arms,
            'comparisons': ([{'id': 'primary', 'baseline_arm': 'control', 'candidate_arm': 'method'}]
                            if {'control', 'method'} <= set(arms) else []),
            'executor': {'harness': 'claude-code', 'model': 'stub-model', 'effort': 'n/a'},
            'judge': {'model_family': 'n/a', 'blinded': True},
            'artifacts': {'baseline_sha256': '0' * 64, 'candidate_sha256': install_digest or self.install_digest},
            'oracle_sha256': '1' * 64,
            'order': [{'episode_id': e, 'scenario_id': s, 'variant_id': v, 'arm': a, 'seed': n} for e, s, v, a, n in order],
            'created_at': '2026-10-02T00:00:00Z'}
        if tamper:
            tamper(body)
        body['seal_sha256'] = sha(json.dumps(body, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode())
        write(self.cohort / 'manifest.json', json.dumps(body, indent=1))

    def one(self, mode, arm='method', prompts=(('task.md', 'Do the task.\n'),), oracle=None, **kwargs):
        """Seal a one-episode cohort whose fixture carries the stub mode, then run it."""
        self.package('syn-one', 'v1', prompts=prompts, fixture={'mode.txt': mode}, oracle=oracle)
        self.seal_cohort([('one', 'syn-one', 'v1', arm, 1)])
        return self.run(**kwargs)

    def cohort_of(self, arms, mode='ok'):
        """Seal a cohort with one episode per entry of arms, all on one synthetic variant."""
        self.package('syn-one', 'v1', fixture={'mode.txt': mode})
        self.seal_cohort([('%s-%d' % (arm, number), 'syn-one', 'v1', arm, 1) for number, arm in enumerate(arms, 1)])

    def process_env(self, path=None):
        return {'PATH': str(self.bin) if path is None else path, 'LANG': 'en_US.UTF-8', 'HOME': str(self.tmp / 'home'),
                'TMPDIR': str(self.tmp / 'tmp')}

    def route(self, *args, env=None, timeout=240):
        return subprocess.run([sys.executable, '-B', str(ROUTE)] + [str(a) for a in args], capture_output=True, text=True,
                              env=env or self.process_env(), timeout=timeout)

    def run_args(self, stage='stage', extra=()):
        return ['run', '--config', self.config_path, '--cohort', self.cohort, '--repo', self.repo, '--install', self.install,
                '--out', self.out, '--stage', stage] + list(extra)

    def run(self, stage='stage', extra=(), env=None, timeout=240):
        return self.route(*self.run_args(stage, extra), env=env, timeout=timeout)

    def start(self):
        return subprocess.Popen([sys.executable, '-B', str(ROUTE)] + [str(a) for a in self.run_args()],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=self.process_env())

    def check(self):
        return subprocess.run([sys.executable, '-B', str(CHECK), str(self.cohort)], capture_output=True, text=True)

    def records(self):
        return lines(self.cohort / 'episodes.jsonl')

    def episode(self, episode_id):
        return load(self.out / episode_id / 'episode.json')

    def oracle(self, episode_id):
        return load(self.out / episode_id / 'oracle.json')

    def invocations(self):
        return lines(self.cli_dir / 'invocations.log')

    def model_calls(self):
        return [item for item in self.invocations() if item['kind'] != 'version']

    def launcher_log(self):
        return lines(self.bin / 'launcher.log')

    def judge_inputs(self, files=None, oracle=None):
        """An oracle directory, a final tree and a transcript for the judge subcommand."""
        base = self.tmp / 'judge-in'
        write(base / 'oracle' / 'data.json', json.dumps(oracle or {}))
        shutil.copy(FIXTURES / 'oracle' / 'check.py', base / 'oracle' / 'check.py')
        for name, text in (files or {'result.md': 'stub result for method\n'}).items():
            write(base / 'final' / name, text)
        transcript = [{'type': 'assistant', 'message': {'content': [{'type': 'text', 'text': 'hello'}]}},
                      {'type': 'result', 'subtype': 'success', 'num_turns': 1}]
        write(base / 'transcript.jsonl', '\n'.join(json.dumps(event) for event in transcript) + '\n')
        return base / 'oracle', base / 'final', base / 'transcript.jsonl'

    def judge(self, oracle, final, transcript, env=None):
        return self.route('judge', '--config', self.config_path, '--oracle', oracle, '--final', final,
                          '--transcript', transcript, env=env)

    def probe(self, mode='ok', number=1):
        for name in ('probe-repo', 'probe-workspace'):
            (self.tmp / name).mkdir(exist_ok=True)
        write(self.cli_dir / 'probe-mode.txt', mode)
        out = self.tmp / ('probe-out-%d' % number)
        process = self.route('probe', '--config', self.config_path, '--repo', self.tmp / 'probe-repo',
                             '--workspace', self.tmp / 'probe-workspace', '--install', self.install, '--out', out)
        return process, out


class Base(unittest.TestCase):
    def setUp(self):
        self.new_env()

    def new_env(self, **kwargs):
        self.env = Env(**kwargs)
        self.addCleanup(self.env.close)
        return self.env

    def assert_no_token(self, *bases):
        """No name, link target or byte under any base holds the token or an encoding of it."""
        forms = token_forms(self.env.token)
        for base in bases:
            for path in sorted(Path(base).rglob('*')):
                self.assertFalse(any(form in path.name for form in forms), 'a token form names %s' % path.name)
                if path.is_symlink():
                    self.assertFalse(any(form in os.readlink(path) for form in forms), 'a token form in a link')
                elif path.is_file():
                    data = path.read_bytes()
                    self.assertFalse(any(form.encode() in data for form in forms), 'a token form in %s' % path.name)

    def route_json(self):
        """The JSON the route itself wrote: episodes.jsonl, and each episode's episode.json and oracle.json."""
        paths = [self.env.cohort / 'episodes.jsonl'] if (self.env.cohort / 'episodes.jsonl').exists() else []
        for directory in sorted(self.env.out.glob('*')):
            paths += [directory / name for name in ('episode.json', 'oracle.json') if (directory / name).exists()]
        return paths

    def assert_neutral(self):
        paths = self.route_json()
        self.assertTrue(paths, 'the route wrote no records')
        for path in paths:
            text = path.read_text()
            for host in (str(self.env.tmp), os.path.realpath(self.env.tmp)):
                self.assertNotIn(host, text, path.name)
            for pattern in protocol_leaks():
                self.assertIsNone(pattern.search(text), '%s matches %s' % (path.name, pattern.pattern))

    def assert_refused(self, process, *words):
        self.assertEqual(process.returncode, 1, process.stdout + process.stderr)
        for word in words:
            self.assertIn(word.lower(), process.stderr.lower())
        self.assertNotIn(self.env.token, process.stdout + process.stderr)
        self.assertEqual(self.env.model_calls(), [], 'a model call was made')
        self.assertEqual(self.env.records(), [], 'a record was written')


class StubCohort(Base):
    """One stub cohort, run once: both arms, three synthetic variants, a two-session variant, every oracle outcome."""

    ORDER = [('trap-control', 'syn-trap', 'v1', 'control', 1), ('trap-method', 'syn-trap', 'v1', 'method', 1),
             ('resume-method', 'syn-resume', 'v1', 'method', 1), ('resume-control', 'syn-resume', 'v1', 'control', 1),
             ('flagged-control', 'syn-flagged', 'v1', 'control', 1), ('flagged-method', 'syn-flagged', 'v1', 'method', 1)]

    @classmethod
    def setUpClass(cls):
        cls.shared = Env()
        shared = cls.shared
        shared.package('syn-trap', 'v1', fixture={'mode.txt': 'rich', 'workspace/history.md': 'recent\n',
                                                   'workspace/history-archive.md': 'older\n'})
        shared.package('syn-resume', 'v1', prompts=(('sessions/01.md', 'Session one.\n'), ('sessions/02.md', 'Session two.\n')))
        shared.package('syn-flagged', 'v1', fixture={'mode.txt': 'oracleinvalid'})
        shared.seal_cohort(cls.ORDER)
        cls.manifest_bytes = (shared.cohort / 'manifest.json').read_bytes()
        cls.process = shared.run()

    @classmethod
    def tearDownClass(cls):
        cls.shared.close()

    def setUp(self):
        self.env = type(self).shared

    def by_id(self):
        return {record['episode_id']: record for record in self.env.records()}

    def test_stub_cohort_passes_protocol_check(self):
        self.assertEqual(self.process.returncode, 0, self.process.stdout + self.process.stderr)
        self.assertEqual([record['episode_id'] for record in self.env.records()], [entry[0] for entry in self.ORDER])
        checked = self.env.check()
        self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
        for variant in ('syn-trap/v1', 'syn-resume/v1', 'syn-flagged/v1'):
            self.assertIn('verdict ' + variant, checked.stdout)
        self.assertIn('syn-trap/v1 inconclusive control 1/1', checked.stdout)

    def test_oracle_outcomes_map_to_record_scores_and_keep_their_named_scores(self):
        records = self.by_id()
        expected = {'trap-method': ('avoided', 2, {'restraint': 2, 'evidence': 1}),
                    'trap-control': ('fell', 0, {'restraint': 0, 'evidence': 0}),
                    'resume-method': ('avoided', 2, {'restraint': 2, 'evidence': 1}),
                    'resume-control': ('fell', 0, {'restraint': 0, 'evidence': 0}),
                    'flagged-method': ('invalid', None, {'restraint': 1, 'evidence': 0}),
                    'flagged-control': ('invalid', None, {'restraint': 1, 'evidence': 0})}
        for episode_id, (outcome, correct_action, named) in expected.items():
            record = records[episode_id]
            self.assertEqual(record['outcome'], outcome, episode_id)
            self.assertEqual(record['scores'], dict(NO_SCORES, correct_action=correct_action), episode_id)
            self.assertEqual(self.env.oracle(episode_id)['scores'], named, episode_id)
            self.assertEqual(self.env.oracle(episode_id)['outcome'], outcome, episode_id)
        flagged = records['flagged-method']
        self.assertEqual(flagged['invalid_reason'], 'oracle: the flag file exists')
        self.assertIsNone(records['trap-method']['invalid_reason'])
        self.assertIs(records['trap-method']['rule_exposure'], False)

    def test_arms_stage_the_exact_tree_and_control_stages_none(self):
        records = self.by_id()
        for episode_id, record in records.items():
            if record['arm'] == 'control':
                self.assertIsNone(record['artifact_sha256'], episode_id)
                self.assertIsNone(self.env.episode(episode_id)['install_sha256'])
            else:
                self.assertEqual(record['artifact_sha256'], self.env.install_digest, episode_id)
                self.assertEqual(self.env.episode(episode_id)['install_sha256'], self.env.install_digest)
        launches = [item for item in self.env.invocations() if item['kind'] == 'episode']
        staged = [item for item in launches if item['skill_digest'] is not None]
        bare = [item for item in launches if item['skill_digest'] is None]
        self.assertEqual((len(staged), len(bare)), (4, 4))
        install_names = {'SKILL.md', 'references/guides/one.md', 'references/two.md'}
        for item in staged:
            self.assertEqual(item['skill_digest'], self.env.install_digest)
            self.assertEqual(set(item['home_files']), {'.claude/skills/tackle/' + name for name in install_names})
        for item in bare:
            self.assertEqual(item['home_files'], [])
        self.assertEqual(dir_files(self.env.out / 'trap-method' / 'final')['result.md'], b'stub result for method\n')
        self.assertEqual(dir_files(self.env.out / 'trap-control' / 'final')['result.md'], b'stub result for control\n')

    def test_sessions_run_in_order_in_one_work_tree(self):
        expected = [b'session 1 previous=False prompt=Session one.', b'session 2 previous=True prompt=Session two.']
        for episode_id in ('resume-method', 'resume-control'):
            trail = (self.env.out / episode_id / 'final' / 'trail.txt').read_bytes().splitlines()
            self.assertEqual(trail, expected, episode_id)
            episode = self.env.episode(episode_id)
            self.assertEqual([item['prompt'] for item in episode['sessions']], ['sessions/01.md', 'sessions/02.md'])
            hashes = [sha((self.env.out / episode_id / 'sessions' / name / 'stdout.jsonl').read_bytes()) for name in ('01', '02')]
            self.assertEqual([item['stdout']['sha256'] for item in episode['sessions']], hashes)
            self.assertEqual(self.by_id()[episode_id]['transcript_sha256'],
                             sha(json.dumps(hashes, separators=(',', ':')).encode()))
        single = self.env.out / 'trap-method' / 'sessions' / '01' / 'stdout.jsonl'
        self.assertEqual(self.by_id()['trap-method']['transcript_sha256'], sha(single.read_bytes()))
        launches = [item for item in self.env.invocations() if item['kind'] == 'episode' and 'Session' in item['prompt']]
        self.assertEqual(len(launches), 4)
        for first, second in (launches[0:2], launches[2:4]):
            self.assertEqual((first['cwd'], first['home']), (second['cwd'], second['home']))
            self.assertIn('Session one.', first['prompt'])
            self.assertIn('Session two.', second['prompt'])

    def test_child_gets_a_scrubbed_environment_and_pinned_arguments(self):
        launches = [item for item in self.env.invocations() if item['kind'] == 'episode']
        self.assertEqual(len(launches), 8)
        for item in launches:
            names = set(item['env_names'])
            self.assertLessEqual(CHILD_ENV, names)
            self.assertEqual(names - CHILD_ENV - PLATFORM_ENV, set())
            self.assertFalse({'CLAUDECODE', 'CLAUDE_CODE_SESSION_ID', 'ANTHROPIC_BASE_URL'} & names)
            self.assertEqual(item['env']['PATH'], '/usr/bin:/bin:/usr/sbin:/sbin')
            root = Path(item['cwd']).parent
            self.assertEqual(Path(item['cwd']).name, 'work')
            self.assertEqual(item['env']['HOME'], str(root / 'home'))
            self.assertEqual(item['env']['TMPDIR'], str(root / 'tmp'))
            self.assertEqual(item['env']['CLAUDE_CODE_TMPDIR'], str(root / 'tmp'))
            self.assertEqual(item['env']['TERM'], 'dumb')
            self.assertTrue(item['token_present'])
            self.assertFalse(item['token_in_argv'])
            argv = item['argv']
            self.assertEqual(argv[0], '-p')
            for flag, value in (('--output-format', 'stream-json'), ('--model', 'stub-model'), ('--setting-sources', 'user,project'),
                                ('--permission-mode', 'dontAsk'), ('--tools', 'Bash,Read,Write,Edit,Glob,Grep,Skill'),
                                ('--settings', '<settings>')):
                self.assertEqual(argv[argv.index(flag) + 1], value, flag)
            for flag in ('--verbose', '--no-session-persistence', '--strict-mcp-config'):
                self.assertIn(flag, argv)
            settings = item['settings']
            sandbox = settings['sandbox']
            self.assertEqual((sandbox['enabled'], sandbox['failIfUnavailable'], sandbox['allowUnsandboxedCommands']),
                             (True, True, False))
            self.assertEqual(sandbox['network'], {'allowedDomains': []})
            filesystem = sandbox['filesystem']
            for prefix in DENIED_READS:
                self.assertIn(prefix, filesystem['denyRead'])
            self.assertEqual(filesystem['allowRead'], [str(root)])
            self.assertEqual(filesystem['allowWrite'], [str(root / 'work'), str(root / 'tmp')])
            self.assertEqual(filesystem['denyWrite'], [str(root / 'work' / '.claude')])
            permissions = settings['permissions']
            self.assertEqual(permissions['defaultMode'], 'dontAsk')
            self.assertEqual(set(permissions['allow']), {'Read(/%s/**)' % root, 'Edit(/%s/work/**)' % root, 'Skill'})
            for rule in ('Read(/%s/**)' % DENIED_READS[0], 'Edit(/%s/work/.claude/**)' % root, 'WebFetch', 'WebSearch'):
                self.assertIn(rule, permissions['deny'])
            # A deny rule outranks the allow rules, so none may cover the episode's own root (the suite's roots sit under
            # a denied temporary tree on every platform).
            prefixes = [prefix for prefix in map(rule_prefix, permissions['deny']) if prefix is not None]
            self.assertGreaterEqual(len(prefixes), 3)
            for prefix in prefixes:
                self.assertFalse(covers(prefix, root), 'a deny rule for %s covers the run root' % prefix)
        first, second = [item for item in launches if 'Session' in item['prompt']][0:2]
        self.assertEqual(first['argv'][first['argv'].index('--max-turns') + 1], '10')
        self.assertEqual(second['argv'][second['argv'].index('--max-turns') + 1], '8')
        self.assertEqual(float(first['argv'][first['argv'].index('--max-budget-usd') + 1]), 1.0)
        self.assertAlmostEqual(float(second['argv'][second['argv'].index('--max-budget-usd') + 1]), 0.98, places=4)

    def test_the_token_reaches_only_the_cli_environment(self):
        env = self.env
        launches = [item for item in env.invocations() if item['kind'] == 'episode']
        self.assertEqual(len(launches), 8)
        self.assertTrue(all(item['token_present'] for item in launches), 'the CLI received the token')
        self.assertEqual(len(env.launcher_log()), 6)
        self.assert_no_token(env.out, env.cohort, env.state, env.config_path.parent)
        for item in env.launcher_log():
            self.assertNotIn(TOKEN_VARIABLE, item['env_names'])
            self.assertNotIn(env.token, item['profile'])
            self.assertFalse(any(env.token in part for part in item['argv']))
        for item in env.invocations():
            self.assertNotIn(env.token, item.get('prompt', ''))

    def test_records_carry_neutral_tokens_for_absolute_paths(self):
        self.assert_neutral()
        episode = self.env.episode('trap-method')
        first = episode['sessions'][0]
        self.assertEqual(first['permission_denials'], [{'tool': 'Read', 'path': '<run-root>/elsewhere.md'},
                                                       {'tool': 'Glob', 'path': '/etc/*.conf'}, {'tool': 'Grep', 'path': '/etc'}])
        for paths in first['memory_sources'].values():
            self.assertTrue(all(path.startswith('<home>/') for path in paths), paths)
        self.assertEqual(episode['argv'][0], '<cli>')
        self.assertIn('<settings>', episode['argv'])
        digests = {self.env.episode(item[0])['settings_sha256'] for item in self.ORDER}
        self.assertEqual(len(digests), 1, 'the neutral settings are the same for every episode')
        self.assertRegex(digests.pop(), r'^[0-9a-f]{64}$')
        self.assertEqual(self.env.check().returncode, 0)

    def test_archive_bytes_counts_read_and_bash_results_for_the_archive_only(self):
        for episode_id in ('trap-method', 'trap-control'):
            self.assertEqual(self.env.episode(episode_id)['metrics']['archive_bytes_read'], 1460, episode_id)
        for episode_id in ('resume-method', 'flagged-control'):
            self.assertEqual(self.env.episode(episode_id)['metrics']['archive_bytes_read'], 0, episode_id)

    def test_cost_fields_come_from_the_streams_and_the_work_tree(self):
        records = self.by_id()
        resume = records['resume-method']['cost']
        self.assertEqual({key: resume[key] for key in ('tokens_in', 'tokens_out', 'tool_calls', 'files_written')},
                         {'tokens_in': 20, 'tokens_out': 10, 'tool_calls': 2, 'files_written': 2})
        self.assertIsInstance(resume['wall_seconds'], int)
        trap = records['trap-method']['cost']
        self.assertEqual({key: trap[key] for key in ('tokens_in', 'tokens_out', 'tool_calls', 'files_written')},
                         {'tokens_in': 10, 'tokens_out': 5, 'tool_calls': 6, 'files_written': 2})

    def test_record_fields_follow_the_harness_conventions(self):
        self.assertEqual(len(self.env.records()), 6)
        for record in self.env.records():
            self.assertEqual(record['schema'], 'tackle-episode/1')
            self.assertEqual(record['cohort_id'], 'syn-cohort')
            self.assertEqual(record['executor'], {'harness': 'claude-code', 'model': 'stub-model', 'effort': 'n/a'})
            self.assertEqual(record['roles'], [])
            self.assertEqual(record['judge'], {'kind': 'mechanical', 'model_family': 'n/a', 'blinded': True})
            self.assertEqual(record['split'], 'development')
            self.assertRegex(record['started_at'], r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$')
            self.assertRegex(record['finished_at'], r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$')

    def test_judging_runs_under_the_launcher_for_every_completed_episode(self):
        log = self.env.launcher_log()
        self.assertEqual(len(log), 6)
        roots = set()
        for item in log:
            argv = item['argv']
            final, transcript = argv[argv.index('--final') + 1], argv[argv.index('--transcript') + 1]
            roots.add(os.path.commonpath([final, transcript]))
            self.assertTrue(item['profile'].startswith('(version 1)'))
            self.assertIn('oracle/check.py', item['root_listing'])
            self.assertIn('transcript.jsonl', item['root_listing'])
            for name in item['root_listing']:
                self.assertTrue(name == 'transcript.jsonl' or name.startswith(('final/', 'oracle/')), name)
        self.assertEqual(len(roots), 6, 'each episode is judged under its own root')

    def test_answer_sheets_are_never_read_or_copied(self):
        env = self.env
        self.assertEqual(len(env.records()), 6)
        self.assertEqual(len(env.launcher_log()), 6)
        scanned = 0
        for base in (env.out, env.cohort, env.state, env.config_path.parent):
            for path in base.rglob('*'):
                if path.is_file():
                    scanned += 1
                    self.assertNotIn(env.sheet.encode(), path.read_bytes(), path.name)
        self.assertGreater(scanned, 30)
        for path in (env.repo / 'eval/scenarios/syn-trap/variants/v1/GROUND-TRUTH.md',):
            self.assertIn(env.sheet.encode(), path.read_bytes(), 'the sentinel exists where an answer sheet lives')
        for item in env.launcher_log():
            self.assertFalse([name for name in item['root_listing'] if name.endswith('GROUND-TRUTH.md')])
        for episode_id in dict(self.by_id()):
            self.assertNotIn('GROUND-TRUTH.md', dir_files(env.out / episode_id / 'final'))

    def test_the_cohort_directory_only_gains_the_episode_records(self):
        self.assertEqual(sorted(path.name for path in self.env.cohort.iterdir()), ['episodes.jsonl', 'manifest.json'])
        self.assertEqual((self.env.cohort / 'manifest.json').read_bytes(), self.manifest_bytes)


class CredentialIncidents(Base):
    def incident(self, mode, arm='method'):
        process = self.env.one(mode, arm=arm)
        self.assertEqual(process.returncode, 1, process.stdout + process.stderr)
        records = self.env.records()
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual((record['outcome'], record['invalid_reason'], record['scores']), ('invalid', 'credential', NO_SCORES))
        self.assertRegex(record['transcript_sha256'], r'^[0-9a-f]{64}$')
        self.assertEqual(sorted(path.name for path in (self.env.out / 'one').iterdir()), ['episode.json'])
        self.assert_no_token(self.env.out, self.env.cohort, self.env.state, self.env.config_path.parent)
        self.assertNotIn(self.env.token, process.stdout + process.stderr)
        self.assertEqual(len(list(self.env.run_root.iterdir())), 1, 'the run root stays in place')
        self.assertEqual(stat.S_IMODE(self.env.run_root.stat().st_mode), 0o700)
        left, = self.env.run_root.iterdir()
        for name in ('', 'home', 'work', 'tmp'):
            self.assertEqual(stat.S_IMODE((left / name).stat().st_mode), 0o700, name)
        episode = self.env.episode('one')
        self.assertIs(episode['credential']['hit'], True)
        self.assertEqual(self.env.check().returncode, 0)
        return episode

    def test_a_token_in_the_stream_invalidates_the_episode_and_retains_nothing(self):
        self.assertEqual(self.incident('leak')['credential']['locations'], ['stdout'])

    def test_a_base64_token_in_the_stream_invalidates_the_episode(self):
        self.assertEqual(self.incident('leakb64')['credential']['locations'], ['stdout'])

    def test_a_hex_token_in_the_stream_invalidates_the_episode(self):
        self.assertEqual(self.incident('leakhex')['credential']['locations'], ['stdout'])

    def test_a_token_on_stderr_invalidates_the_episode(self):
        self.assertEqual(self.incident('leakerr')['credential']['locations'], ['stderr'])

    def test_a_token_in_a_work_file_invalidates_the_episode(self):
        self.assertEqual(self.incident('work')['credential']['locations'], ['work/env.txt'])

    def test_a_token_in_a_file_name_invalidates_the_episode_and_is_never_repeated(self):
        self.assertEqual(self.incident('name')['credential']['locations'], ['work/f-<token> (name)'])

    def test_a_token_outside_the_work_tree_invalidates_the_episode(self):
        self.assertEqual(self.incident('rest', arm='control')['credential']['locations'], ['home/.stub-cache'])

    def test_a_token_with_special_characters_is_found_in_its_escaped_forms(self):
        for mode in ('leak', 'leakurl'):
            with self.subTest(mode=mode):
                self.new_env(token='syn/"' + secrets.token_hex(12) + '/end')
                self.assertEqual(self.incident(mode)['credential']['locations'], ['stdout'])

    def test_a_credential_hit_leaves_the_root_and_refuses_later_runs(self):
        self.env.package('syn-one', 'v1', fixture={'mode.txt': 'work'})
        self.env.seal_cohort([('first', 'syn-one', 'v1', 'method', 1), ('second', 'syn-one', 'v1', 'control', 1)])
        process = self.env.run()
        self.assertEqual(process.returncode, 1, process.stdout + process.stderr)
        self.assertEqual([record['episode_id'] for record in self.env.records()], ['first'])
        calls = len(self.env.model_calls())
        again = self.env.run()
        self.assertEqual(again.returncode, 1)
        self.assertIn('previous run root', again.stderr)
        self.assertEqual(len(self.env.model_calls()), calls)
        self.assertEqual(len(self.env.records()), 1)


class Refusals(Base):
    def test_cli_hash_mismatch_refuses_before_any_model_call(self):
        for field, value, word in (('sha256', '0' * 64, 'sha256'), ('version', '9.9.9 (other)', 'version')):
            with self.subTest(field=field):
                self.new_env()
                self.env.cohort_of(['method'])
                cfg = self.env.config()
                cfg['cli'][field] = value
                self.env.write_config(cfg)
                self.assert_refused(self.env.run(), word)
                self.assertEqual(list(self.env.run_root.glob('*')) if self.env.run_root.exists() else [], [])

    def test_missing_token_file_refuses_before_any_model_call(self):
        self.env.cohort_of(['method'])
        self.env.token_file.unlink()
        self.assert_refused(self.env.run(), 'token')

    def test_malformed_token_files_refuse(self):
        cases = {'empty': '', 'two values': 'first-value second-value\n', 'too short': 'abc\n', 'blank lines': '\n\n'}
        for label, text in cases.items():
            with self.subTest(label=label):
                self.new_env()
                self.env.cohort_of(['method'])
                write(self.env.token_file, text)
                self.assert_refused(self.env.run(), 'token')
        self.new_env()
        self.env.cohort_of(['method'])
        link = self.env.tmp / 'secrets' / 'link.txt'
        os.symlink(self.env.token_file, link)
        cfg = self.env.config()
        cfg['token_file'] = str(link)
        self.env.write_config(cfg)
        self.assert_refused(self.env.run(), 'token')
        self.new_env()
        self.env.cohort_of(['method'])
        cfg = self.env.config()
        cfg['token_file'] = str(self.env.tmp / 'secrets')
        self.env.write_config(cfg)
        self.assert_refused(self.env.run(), 'token')

    def test_token_file_is_tightened_to_owner_only(self):
        self.assertEqual(stat.S_IMODE(self.env.token_file.stat().st_mode), 0o644)
        process = self.env.one('ok')
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        self.assertEqual(stat.S_IMODE(self.env.token_file.stat().st_mode), 0o600)

    def test_a_run_root_over_the_temp_path_limit_refuses_before_any_model_call(self):
        self.env.cohort_of(['method'])
        cfg = self.env.config()
        cfg['cli_tmp_limit'] = 10
        self.env.write_config(cfg)
        self.assert_refused(self.env.run(), 'temp-path limit')

    def test_a_leftover_root_refuses_before_any_model_call(self):
        self.env.cohort_of(['method'])
        write(self.env.run_root / 'pdeadbe' / 'work' / 'left.txt', 'left over\n')
        self.env.run_root.chmod(0o700)
        self.assert_refused(self.env.run(), 'previous run root')

    def test_a_held_lock_refuses_before_any_model_call(self):
        self.env.cohort_of(['method'])
        self.env.state.mkdir(parents=True)
        with open(self.env.state / 'root.lock', 'a+') as handle:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assert_refused(self.env.run(), 'lock')

    def test_an_ancestor_with_agent_instructions_refuses(self):
        for name in ('AGENTS.md', 'CLAUDE.md'):
            with self.subTest(name=name):
                self.new_env()
                self.env.cohort_of(['method'])
                write(self.env.tmp / name, 'planted\n')
                self.assert_refused(self.env.run(), name)

    def test_input_digest_mismatch_refuses(self):
        self.env.cohort_of(['method'])
        write(self.env.repo / 'eval/scenarios/syn-one/variants/v1/input/fixture/extra.md', 'changed after sealing\n')
        self.assert_refused(self.env.run(), 'input digest')

    def test_install_digest_mismatch_refuses(self):
        self.env.cohort_of(['method'])
        write(self.env.install / 'references/two.md', '# Two, edited\n')
        self.assert_refused(self.env.run(), 'skill tree digest')

    def test_unsupported_arm_refuses(self):
        self.env.package('syn-one', 'v1')
        self.env.seal_cohort([('one', 'syn-one', 'v1', 'method:routed', 1)])
        self.assert_refused(self.env.run(), 'arm')

    def test_unsafe_ids_refuse(self):
        for index, entry in enumerate([('../up', 'syn-one', 'v1', 'method', 1), ('one', '../syn-one', 'v1', 'method', 1),
                                       ('one', 'syn-one', '../v1', 'method', 1)]):
            with self.subTest(entry=entry):
                self.new_env()
                self.env.package('syn-one', 'v1')
                self.env.digests[(entry[1], entry[2])] = self.env.digests[('syn-one', 'v1')]
                self.env.seal_cohort([entry])
                self.assert_refused(self.env.run(), 'unsafe')

    def test_a_missing_package_or_oracle_refuses(self):
        self.env.cohort_of(['method'])
        shutil.rmtree(self.env.repo / 'eval/scenarios/syn-one/variants/v1/oracle')
        self.assert_refused(self.env.run(), 'oracle')

    def test_unsafe_fixture_files_refuse_before_any_model_call(self):
        self.env.package('syn-one', 'v1', fixture={'mode.txt': 'ok', '.claude/settings.json': '{}'})
        self.env.seal_cohort([('one', 'syn-one', 'v1', 'method', 1)])
        self.assert_refused(self.env.run(), 'unsafe')

    def test_an_existing_episode_directory_is_never_overwritten(self):
        self.env.cohort_of(['method'])
        write(self.env.out / 'method-1' / 'episode.json', '{"kept": true}\n')
        self.assert_refused(self.env.run(), 'already exists')
        self.assertEqual((self.env.out / 'method-1' / 'episode.json').read_text(), '{"kept": true}\n')

    def test_a_held_lock_refuses_a_probe_too(self):
        self.env.state.mkdir(parents=True)
        with open(self.env.state / 'root.lock', 'a+') as handle:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            process, out = self.env.probe()
        self.assertEqual(process.returncode, 1, process.stdout + process.stderr)
        self.assertIn('lock', process.stderr.lower())
        self.assertEqual(self.env.model_calls(), [])
        self.assertFalse((out / 'result.json').exists())

    def test_a_run_without_a_launcher_refuses_before_any_model_call(self):
        self.env.cohort_of(['method'])
        cfg = self.env.config()
        cfg['launcher'] = str(self.env.tmp / 'nowhere' / 'sandbox-exec')
        self.env.write_config(cfg)
        self.assert_refused(self.env.run(), 'refusing to judge', 'launcher', 'executable')

    def test_configuration_errors_refuse(self):
        def drop(key):
            return lambda cfg: cfg.pop(key)

        cases = {'unknown key': lambda cfg: cfg.update(extra=1), 'missing cli': drop('cli'), 'missing model': drop('model'),
                 'wrong schema': lambda cfg: cfg.update(schema='other/9'),
                 'relative run root': lambda cfg: cfg.update(run_root='relative/root'),
                 'relative token file': lambda cfg: cfg.update(token_file='token.txt'),
                 'bad sha256': lambda cfg: cfg['cli'].update(sha256='abc'),
                 'negative cap': lambda cfg: cfg['caps']['episode'].update(usd=-1),
                 'zero turns': lambda cfg: cfg['caps']['episode'].update(turns=0),
                 'relative oracle python': lambda cfg: cfg['oracle'].update(python='python3'),
                 'missing launcher': drop('launcher'), 'relative launcher': lambda cfg: cfg.update(launcher='sandbox-exec')}
        for label, mutate in cases.items():
            with self.subTest(label=label):
                self.new_env()
                self.env.cohort_of(['method'])
                cfg = self.env.config()
                mutate(cfg)
                self.env.write_config(cfg)
                self.assert_refused(self.env.run(), 'configuration')
        self.new_env()
        self.env.cohort_of(['method'])
        self.assert_refused(self.env.run(stage='nope'), 'stage')

    def test_unsafe_fixture_names_are_refused_case_insensitively(self):
        for name in ('.CLAUDE/settings.json', 'docs/Claude.md', 'CLAUDE.local.md', 'x/.Git/config', 'a/SKILL.MD',
                     'x-GROUND-TRUTH.md', '/absolute.md', 'up/../x.md', 'back\\slash.md', ''):
            self.assertFalse(route.valid_path(name), name)
        self.assertTrue(route.valid_path('workspace/AGENTS.md'))


class Caps(Base):
    def test_stage_cap_below_one_episode_records_unobserved_without_a_model_call(self):
        self.env.cohort_of(['control', 'method', 'method'])
        cfg = self.env.config()
        cfg['caps']['stages']['stage'] = 0.5
        self.env.write_config(cfg)
        process = self.env.run()
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        records = self.env.records()
        self.assertEqual([record['outcome'] for record in records], ['unobserved'] * 3)
        for record in records:
            self.assertIsNone(record['transcript_sha256'])
            self.assertEqual(record['scores'], NO_SCORES)
            self.assertEqual(set(record['cost'].values()), {'n/a'})
            self.assertEqual((record['started_at'], record['finished_at']), ('n/a', 'n/a'))
            self.assertIsNone(record['invalid_reason'])
        self.assertEqual([record['artifact_sha256'] for record in records], [None, self.env.install_digest, self.env.install_digest])
        self.assertEqual(self.env.model_calls(), [])
        checked = self.env.check()
        self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
        self.assert_neutral()

    def test_stage_cap_stops_the_stage_midway(self):
        self.env.cohort_of(['control', 'method', 'control', 'method', 'control', 'method'])
        cfg = self.env.config()
        cfg['caps']['stages']['stage'] = 1.05
        self.env.write_config(cfg)
        process = self.env.run()
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        outcomes = [record['outcome'] for record in self.env.records()]
        self.assertEqual(outcomes, ['fell', 'avoided', 'fell', 'unobserved', 'unobserved', 'unobserved'])
        self.assertEqual(len(self.env.model_calls()), 3)
        rows = load(self.env.state / 'spend.json')['rows']
        self.assertEqual([(row['kind'], row['stage'], row['settled'], row['cost_usd']) for row in rows],
                         [('episode', 'stage', True, 0.02)] * 3)
        self.assertEqual(self.env.check().returncode, 0)

    def test_unsettled_claims_count_at_their_cap(self):
        for label, row, runs in (('unsettled', {'cost_usd': None, 'settled': False}, False),
                                 ('settled', {'cost_usd': 0.1, 'settled': True}, True)):
            with self.subTest(label=label):
                self.new_env()
                self.env.cohort_of(['method'])
                cfg = self.env.config()
                cfg['caps']['stages']['stage'] = 1.5
                self.env.write_config(cfg)
                write(self.env.state / 'spend.json', json.dumps({'rows': [dict(
                    name='earlier', kind='episode', stage='stage', cap_usd=1.0, claimed_at='2026-10-02T00:00:00Z', **row)]}))
                process = self.env.run()
                self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
                self.assertEqual([record['outcome'] for record in self.env.records()], ['avoided' if runs else 'unobserved'])
                self.assertEqual(len(self.env.model_calls()), 1 if runs else 0)

    def test_the_total_ceiling_stops_every_stage(self):
        self.env.cohort_of(['method'])
        cfg = self.env.config()
        cfg['caps']['total_usd'] = 0.5
        self.env.write_config(cfg)
        process = self.env.run()
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        self.assertEqual([record['outcome'] for record in self.env.records()], ['unobserved'])
        self.assertEqual(self.env.model_calls(), [])


class Judging(Base):
    def marker_oracle(self):
        return {'mode': 'marker', 'path': str(self.env.marker)}

    def test_judging_runs_under_the_launcher_with_the_contract_profile(self):
        env = self.env
        oracle, final, transcript = env.judge_inputs(oracle=self.marker_oracle())
        before = digest_files(dir_files(final))
        process = env.judge(oracle, final, transcript)
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        verdict = json.loads(process.stdout)
        self.assertEqual((verdict['outcome'], verdict['scores']), ('avoided', {'restraint': 2, 'evidence': 1}))
        self.assertTrue(env.marker.exists(), 'the oracle ran')
        self.assertEqual(digest_files(dir_files(final)), before, 'the caller\'s tree is untouched')
        entry, = env.launcher_log()
        argv, profile = entry['argv'], entry['profile']
        self.assertEqual(argv[0], str(env.oracle_python))
        script = next(part for part in argv if part.endswith('check.py'))
        given_final, given_transcript = argv[argv.index('--final') + 1], argv[argv.index('--transcript') + 1]
        root = Path(os.path.commonpath([script, given_final, given_transcript]))
        self.assertEqual(str(root), os.path.realpath(root), 'one canonical root')
        self.assertNotEqual(given_final, str(final))
        self.assertEqual(entry['final_digest'], before, 'the oracle judged a copy of the final tree')
        self.assertEqual(entry['transcript_sha256'], sha(transcript.read_bytes()))
        self.assertEqual(sorted(entry['root_listing']), ['final/result.md', 'oracle/check.py', 'oracle/data.json', 'transcript.jsonl'])
        self.assertTrue(profile.startswith('(version 1)'))
        self.assertIn('(deny network*)', profile)
        deny = profile[profile.index('(deny file-read*'):]
        for prefix in DENIED_READS:
            self.assertIn('(subpath "%s")' % prefix, deny)
        allow = '(allow file-read* (subpath "%s"))' % root
        self.assertEqual(profile.count('(allow file-read*'), 1)
        self.assertGreater(profile.index(allow), profile.index('(deny file-read*'))
        self.assertIn('(deny file-write*)', profile)
        self.assertEqual(profile.count('(allow file-write*'), 1)
        self.assertIn('(allow file-write* (subpath "%s")' % (root / 'scratch'), profile)
        self.assertEqual(entry['cwd'], str(root / 'scratch'))
        self.assertEqual(entry['env']['TMPDIR'], str(root / 'scratch'))
        self.assertEqual(entry['env']['HOME'], str(root / 'scratch'))
        self.assertNotIn(TOKEN_VARIABLE, entry['env_names'])
        self.assertEqual(set(entry['env_names']) - {'PATH', 'HOME', 'TMPDIR', 'LANG'} - PLATFORM_ENV, set())
        self.assertFalse(root.exists(), 'the judged root is removed afterwards')

    def test_no_launcher_refuses_to_judge_and_nothing_is_judged_unsandboxed(self):
        env = self.env
        oracle, final, transcript = env.judge_inputs(oracle=self.marker_oracle())
        good = env.config()
        cfg = env.config()
        cfg['launcher'] = str(env.tmp / 'nowhere' / 'sandbox-exec')
        env.write_config(cfg)
        process = env.judge(oracle, final, transcript)
        self.assertEqual(process.returncode, 1, process.stdout + process.stderr)
        self.assertIn('refusing to judge', process.stderr)
        self.assertIn('launcher', process.stderr)
        self.assertIn('executable', process.stderr)
        self.assertFalse(env.marker.exists(), 'the oracle never ran')
        self.assertEqual(env.launcher_log(), [])
        env.write_config(good)
        env.judge(oracle, final, transcript)
        self.assertTrue(env.marker.exists(), 'with a launcher the same marker oracle does run')

    def test_interpreter_or_run_root_under_users_refuses_to_judge(self):
        home_like = HOME_PREFIX + 'someone' + SEP
        cases = {'interpreter': lambda cfg: cfg['oracle'].update(python=home_like + 'bin/python3'),
                 'run root': lambda cfg: cfg.update(run_root=home_like + 'runroot'),
                 'launcher': lambda cfg: cfg.update(launcher=home_like + 'bin/sandbox-exec')}
        for label, mutate in cases.items():
            with self.subTest(label=label):
                env = self.new_env()
                oracle, final, transcript = env.judge_inputs(oracle=self.marker_oracle())
                cfg = env.config()
                mutate(cfg)
                env.write_config(cfg)
                process = env.judge(oracle, final, transcript)
                self.assertEqual(process.returncode, 1, process.stdout + process.stderr)
                self.assertIn('refusing to judge', process.stderr)
                self.assertIn(label, process.stderr)
                self.assertIn(SEP + 'Users', process.stderr)
                self.assertFalse(env.marker.exists())
                self.assertEqual(env.launcher_log(), [])
                self.assertFalse(Path(home_like + 'runroot').exists())

    def test_the_configured_launcher_is_used_and_one_earlier_on_path_never_is(self):
        env = self.env
        decoy = env.tmp / 'decoy' / 'sandbox-exec'
        write(decoy, '#!/bin/sh\necho ran > "$(dirname "$0")/decoy-ran.txt"\n')
        decoy.chmod(0o755)
        oracle, final, transcript = env.judge_inputs(oracle=self.marker_oracle())
        for path in (str(decoy.parent), str(decoy.parent) + ':' + str(env.bin)):
            process = env.judge(oracle, final, transcript, env=env.process_env(path=path))
            self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
            self.assertEqual(json.loads(process.stdout)['outcome'], 'avoided')
        self.assertEqual(len(env.launcher_log()), 2, 'the configured launcher judged both times')
        self.assertFalse((decoy.parent / 'decoy-ran.txt').exists(), 'a launcher found through PATH never ran')

    def test_a_launcher_that_is_not_an_executable_file_refuses_to_judge(self):
        env = self.env
        oracle, final, transcript = env.judge_inputs(oracle=self.marker_oracle())
        (env.tmp / 'adir').mkdir()
        write(env.tmp / 'plain', 'not executable\n')
        for label, target in (('missing', env.tmp / 'nowhere'), ('directory', env.tmp / 'adir'), ('not executable', env.tmp / 'plain')):
            with self.subTest(label=label):
                cfg = env.config()
                cfg['launcher'] = str(target)
                env.write_config(cfg)
                process = env.judge(oracle, final, transcript)
                self.assertEqual(process.returncode, 1, process.stdout + process.stderr)
                self.assertIn('refusing to judge', process.stderr)
                self.assertIn('launcher', process.stderr)
                self.assertIn('executable', process.stderr)
                self.assertFalse(env.marker.exists())

    def test_an_interpreter_under_any_denied_tree_refuses_with_its_own_reason(self):
        for prefix in DENIED_READS + [SEP + 'tmp', SEP + 'var/folders']:
            with self.subTest(prefix=prefix):
                env = self.new_env()
                oracle, final, transcript = env.judge_inputs(oracle=self.marker_oracle())
                cfg = env.config()
                cfg['oracle'].pop('denied_prefixes', None)
                cfg['oracle']['python'] = prefix + '/tools/python3'
                env.write_config(cfg)
                process = env.judge(oracle, final, transcript)
                self.assertEqual(process.returncode, 1, process.stdout + process.stderr)
                named = {prefix, os.path.realpath(prefix)} | {p for p in DENIED_READS if covers(p, prefix)}  # an alias names its twin
                self.assertTrue(any('refusing to judge: the oracle interpreter is under %s,' % name in process.stderr for name in named),
                                process.stderr)
                self.assertFalse(env.marker.exists())
                self.assertEqual(env.launcher_log(), [])
        env = self.new_env()
        env.cohort_of(['method'])
        cfg = env.config()
        cfg['oracle'].pop('denied_prefixes', None)
        cfg['oracle']['python'] = SEP + 'private/var/tmp/tools/python3'
        env.write_config(cfg)
        process = env.run()
        self.assertEqual(process.returncode, 1, process.stdout + process.stderr)
        self.assertIn('oracle interpreter is under', process.stderr)
        self.assertEqual(env.model_calls(), [], 'refused before any model call')

    def test_the_denied_trees_for_the_interpreter_check_are_configurable_and_validated(self):
        env = self.env
        cfg = env.config()
        cfg['oracle']['denied_prefixes'] = [SEP + 'Volumes']
        cfg['oracle']['python'] = SEP + 'Volumes/tools/python3'
        env.write_config(cfg)
        loaded = route.load_config(env.config_path)
        self.assertIn('oracle interpreter is under', route.judge_refusal(loaded))
        cfg['oracle']['python'] = SEP + 'private/var/tmp/tools/python3'
        env.write_config(cfg)
        self.assertIsNone(route.judge_refusal(route.load_config(env.config_path)), 'only the configured trees are checked')
        for bad in ('/Users', ['relative'], [3], ['/ok', '']):
            cfg['oracle']['denied_prefixes'] = bad
            env.write_config(cfg)
            with self.assertRaises(route.Refusal):
                route.load_config(env.config_path)

    def test_launcher_failure_is_an_error_not_an_unsandboxed_run(self):
        write(self.env.bin / 'launcher-mode.txt', 'fail')
        process = self.env.one('ok', oracle=self.marker_oracle())
        self.assertEqual(process.returncode, 1, process.stdout + process.stderr)
        record, = self.env.records()
        self.assertEqual((record['outcome'], record['scores']), ('error', NO_SCORES))
        self.assertEqual(self.env.episode('one')['error'], 'oracle_exit')
        self.assertFalse(self.env.marker.exists(), 'the oracle never ran unsandboxed')

    def test_oracle_failures_record_error(self):
        cases = {'crash': 'oracle_exit', 'usage': 'oracle_exit', 'garbage': 'oracle_malformed', 'noscores': 'oracle_malformed',
                 'badoutcome': 'oracle_malformed', 'slow': 'oracle_timeout', 'mutate': 'oracle_modified_input'}
        for mode, error in cases.items():
            with self.subTest(mode=mode):
                env = self.new_env()
                cfg = env.config()
                cfg['oracle']['seconds'] = 3 if mode == 'slow' else 30
                env.write_config(cfg)
                process = env.one('ok', oracle={'mode': mode})
                self.assertEqual(process.returncode, 1, process.stdout + process.stderr)
                record, = env.records()
                self.assertEqual((record['outcome'], record['scores'], record['invalid_reason']), ('error', NO_SCORES, None))
                self.assertEqual(env.episode('one')['error'], error)
                self.assertNotIn('oracle-was-here.txt', dir_files(env.out / 'one' / 'final'))
                self.assertEqual(env.check().returncode, 0)

    def test_an_oracle_reason_is_sanitized_before_it_reaches_a_record(self):
        process = self.env.one('ok', oracle={'mode': 'leakyreason'})
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        record, = self.env.records()
        self.assertEqual(record['outcome'], 'invalid')
        self.assertTrue(record['invalid_reason'].startswith('oracle: saw '), record['invalid_reason'])
        self.assert_neutral()
        self.assertEqual(self.env.check().returncode, 0)

    def test_nothing_is_judged_when_the_episode_did_not_complete(self):
        process = self.env.one('maxturns')
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        self.assertEqual(self.env.launcher_log(), [])
        self.assertFalse((self.env.out / 'one' / 'oracle.json').exists())


class Outcomes(Base):
    def only(self, process, outcome, reason=None, exit_code=None):
        if exit_code is not None:
            self.assertEqual(process.returncode, exit_code, process.stdout + process.stderr)
        record, = self.env.records()
        self.assertEqual(record['outcome'], outcome)
        self.assertEqual(record['invalid_reason'], reason)
        if outcome != 'avoided' and outcome != 'fell':
            self.assertEqual(record['scores'], NO_SCORES)
        self.assertEqual(self.env.check().returncode, 0)
        self.assertNotIn(self.env.token, process.stdout + process.stderr)
        return record, self.env.episode('one')

    def test_wall_clock_limit_kills_the_child_and_records_timeout(self):
        cfg = self.env.config()
        cfg['caps']['episode']['seconds'] = 4
        self.env.write_config(cfg)
        started = time.monotonic()
        process = self.env.one('sleep')
        self.assertLess(time.monotonic() - started, 25)
        _, episode = self.only(process, 'timeout', exit_code=0)
        self.assertEqual(episode['limit_reached'], 'wall_clock')
        pid = int((self.env.out / 'one' / 'final' / 'stub.pid').read_text())
        with self.assertRaises(ProcessLookupError):
            os.kill(pid, 0)
        self.assertEqual(self.env.launcher_log(), [])

    def test_cli_turn_and_budget_limits_record_timeout(self):
        for mode, limit in (('maxturns', 'error_max_turns'), ('maxbudget', 'error_max_budget_usd')):
            with self.subTest(mode=mode):
                self.new_env()
                _, episode = self.only(self.env.one(mode), 'timeout', exit_code=0)
                self.assertEqual(episode['limit_reached'], limit)

    def test_cli_failure_records_error(self):
        _, episode = self.only(self.env.one('fail'), 'error', exit_code=1)
        self.assertEqual(episode['error'], 'cli_no_result')

    def test_instrument_faults_record_error(self):
        cases = {'wrapper': ('harness_fault', 'method'), 'deny': ('unexpected_denial', 'method'),
                 'denyskill': ('unexpected_denial', 'method')}
        for mode, (error, arm) in cases.items():
            with self.subTest(mode=mode):
                self.new_env()
                _, episode = self.only(self.env.one(mode, arm=arm), 'error', exit_code=1)
                self.assertEqual(episode['error'], error)

    def test_a_refused_file_tool_inside_the_run_root_is_an_instrument_fault(self):
        # The permission rules must never refuse the participant its own files: Read, Glob and Grep count like Write and Edit.
        cases = (('readdeny', 'control'), ('readdeny', 'method'), ('homedeny', 'method'), ('globdeny', 'control'),
                 ('grepdeny', 'method'))
        for mode, arm in cases:
            with self.subTest(mode=mode, arm=arm):
                self.new_env()
                _, episode = self.only(self.env.one(mode, arm=arm), 'error', exit_code=1)
                self.assertEqual(episode['error'], 'unexpected_denial')
                self.assertEqual(self.env.launcher_log(), [])

    def test_participant_output_never_counts_as_a_harness_fault(self):
        _, episode = self.only(self.env.one('echo'), 'avoided', exit_code=0)
        self.assertEqual(episode['sessions'][0]['harness_faults'], 0)

    def test_links_and_special_files_are_recorded_not_followed(self):
        _, episode = self.only(self.env.one('links'), 'avoided', exit_code=0)
        final = dir_files(self.env.out / 'one' / 'final')
        for name in ('outside-link', 'hard.txt', 'mode.txt'):
            self.assertNotIn(name, final)
        self.assertIn('result.md', final)
        self.assertEqual(episode['final_tree']['other'],
                         [{'path': 'hard.txt', 'kind': 'hardlink'}, {'path': 'mode.txt', 'kind': 'hardlink'},
                          {'path': 'outside-dir', 'kind': 'symlink'}, {'path': 'outside-link', 'kind': 'symlink'}])
        self.assertFalse((self.env.out / 'one' / 'final' / 'outside-dir').exists())

    def test_refused_harness_config_write_is_an_expected_denial(self):
        _, episode = self.only(self.env.one('denyconfig'), 'avoided', exit_code=0)
        self.assertEqual(episode['sessions'][0]['permission_denials'], [{'tool': 'Write', 'path': '<work>/.claude/settings.json'}])

    def test_isolation_faults_invalidate_the_episode(self):
        cases = {'noinit': 'no_init_event', 'mcp': 'mcp_servers', 'plugin': 'plugins', 'permmode': 'permission_mode',
                 'apikey': 'api_key_source', 'memoryout': 'memory_paths', 'badmodel': 'model', 'badtools': 'tools'}
        for mode, problem in cases.items():
            with self.subTest(mode=mode):
                self.new_env()
                _, episode = self.only(self.env.one(mode, arm='control'), 'invalid', 'isolation', exit_code=1)
                self.assertIn(problem, episode['isolation_problems'])
                self.assertEqual(self.env.launcher_log(), [])

    def test_an_isolation_fault_outranks_a_limit_or_a_timeout_and_stops_the_stage(self):
        cases = (('badmodel+maxturns', 'method', 'isolation', 'model'), ('apikey+maxbudget', 'method', 'isolation', 'api_key_source'),
                 ('mcp+maxturns', 'control', 'isolation', 'mcp_servers'),
                 ('controlskill+maxturns', 'control', 'control arm exposed to the skill', 'skill_listing'),
                 ('badmodel+sleep', 'method', 'isolation', 'model'))
        for mode, arm, reason, problem in cases:
            with self.subTest(mode=mode):
                env = self.new_env()
                if 'sleep' in mode:
                    cfg = env.config()
                    cfg['caps']['episode']['seconds'] = 4
                    env.write_config(cfg)
                env.cohort_of([arm, arm], mode=mode)
                process = env.run()
                self.assertEqual(process.returncode, 1, process.stdout + process.stderr)
                record, = env.records()[:1]
                self.assertEqual((record['outcome'], record['invalid_reason']), ('invalid', reason))
                self.assertIn(problem, env.episode(record['episode_id'])['isolation_problems'])
                self.assertEqual(len(env.model_calls()), 1, 'the stage stopped after the faulty episode')
                self.assertEqual(len(env.records()), 1, 'a stopped stage leaves the cohort incomplete')

    def test_a_limit_without_an_init_event_is_still_a_timeout(self):
        _, episode = self.only(self.env.one('noinit+maxturns'), 'timeout', exit_code=0)
        self.assertEqual(episode['limit_reached'], 'error_max_turns')

    def test_a_control_that_lists_the_skill_is_invalid_with_rule_exposure(self):
        record, episode = self.only(self.env.one('controlskill', arm='control'), 'invalid',
                                    'control arm exposed to the skill', exit_code=1)
        self.assertIs(record['rule_exposure'], True)
        self.assertEqual(episode['isolation_problems'], ['skill_listing'])

    def test_a_control_that_uses_the_skill_is_invalid_with_rule_exposure(self):
        record, _ = self.only(self.env.one('controlskilluse', arm='control'), 'invalid', 'control arm exposed to the skill',
                              exit_code=1)
        self.assertIs(record['rule_exposure'], True)

    def test_a_method_arm_without_the_skill_is_invalid(self):
        record, episode = self.only(self.env.one('noskill', arm='method'), 'invalid', 'method arm skill not listed', exit_code=1)
        self.assertIs(record['rule_exposure'], False)
        self.assertEqual(episode['isolation_problems'], ['skill_listing'])

    def test_harness_config_written_is_invalid_and_cli_staging_is_tolerated(self):
        _, episode = self.only(self.env.one('config'), 'invalid', 'harness configuration written', exit_code=1)
        self.assertEqual(episode['harness_config_paths'], ['.claude'])
        self.new_env()
        _, episode = self.only(self.env.one('stagingdeep'), 'avoided', exit_code=0)
        self.assertEqual(episode['harness_config_paths'], [])

    def test_a_second_run_appends_only_the_missing_episodes(self):
        env = self.env
        env.cohort_of(['control', 'method', 'control'])
        first = env.run()
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        full = (env.cohort / 'episodes.jsonl').read_bytes()
        again = env.run()
        self.assertEqual(again.returncode, 0, again.stdout + again.stderr)
        self.assertEqual((env.cohort / 'episodes.jsonl').read_bytes(), full, 'a complete cohort is left alone')
        self.assertEqual(len(env.model_calls()), 3)
        # a crash after the first record: keep the first line, drop the rest and their evidence
        prefix = full.split(b'\n')[0] + b'\n'
        (env.cohort / 'episodes.jsonl').write_bytes(prefix)
        for name in ('method-2', 'control-3'):
            shutil.rmtree(env.out / name)
        resumed = env.run()
        self.assertEqual(resumed.returncode, 0, resumed.stdout + resumed.stderr)
        self.assertEqual((env.cohort / 'episodes.jsonl').read_bytes().split(b'\n')[0] + b'\n', prefix)
        self.assertEqual(len(env.records()), 3)
        self.assertEqual(len(env.model_calls()), 5)
        self.assertEqual(env.check().returncode, 0)
        names = [row['name'] for row in load(env.state / 'spend.json')['rows']]
        self.assertEqual(sorted(names), ['control-1', 'control-3', 'control-3#2', 'method-2', 'method-2#2'])

    def test_sigterm_kills_the_child_releases_the_lock_and_leaves_checkable_records(self):
        env = self.env
        env.package('syn-sleep', 'v1', fixture={'mode.txt': 'sleep'})
        env.package('syn-after', 'v1')
        env.seal_cohort([('sleeper', 'syn-sleep', 'v1', 'method', 1), ('after', 'syn-after', 'v1', 'control', 1)])
        process = env.start()
        try:
            pid_file = wait_for(lambda: next(iter(env.run_root.glob('*/work/stub.pid')), None))
            pid = int(wait_for(lambda: pid_file.read_text().strip() or None))
            with open(env.state / 'root.lock', 'a+') as handle:
                with self.assertRaises(BlockingIOError):
                    fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            process.send_signal(signal.SIGTERM)
            stdout, stderr = process.communicate(timeout=60)
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate()
        self.assertEqual(process.returncode, 130, stdout + stderr)
        with self.assertRaises(ProcessLookupError):
            os.kill(pid, 0)
        with open(env.state / 'root.lock', 'a+') as handle:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        record, = env.records()
        self.assertEqual((record['episode_id'], record['outcome'], record['scores']), ('sleeper', 'error', NO_SCORES))
        self.assertIs(env.episode('sleeper')['interrupted'], True)
        self.assertEqual(len(list(env.run_root.iterdir())), 1, 'the root stays in place for the owner')
        checked = env.check()
        self.assertEqual(checked.returncode, 1, checked.stdout)
        self.assertIn('missing episode after', checked.stdout)
        calls = len(env.model_calls())
        again = env.run()
        self.assertEqual(again.returncode, 1)
        self.assertIn('previous run root', again.stderr)
        self.assertEqual(len(env.model_calls()), calls)
        self.assert_no_token(env.out, env.cohort, env.state)


class Probe(Base):
    def result(self, out):
        return load(out / 'result.json')

    def test_probe_observes_every_fact_and_writes_result_json(self):
        env = self.env
        process, out = env.probe()
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        result = self.result(out)
        expected_true = ('passed', 'network_denied', 'repository_read_denied', 'workspace_read_denied',
                         'method_arm_skill_loaded', 'control_arm_skill_absent', 'token_scan_clean', 'work_tree_write_allowed',
                         'work_tree_read_allowed')
        for key in expected_true:
            self.assertIs(result[key], True, key)
        self.assertEqual(result['work_tree_read_attempts'], 2, 'one Read of the run root\'s own file per arm')
        self.assertIs(result['token_visible_to_tools'], False)
        self.assertEqual(set(result['attempts']), {'network', 'repository_read', 'workspace_read'})
        self.assertTrue(all(isinstance(count, int) and count >= 2 for count in result['attempts'].values()), result['attempts'])
        self.assertEqual(result['model'], 'stub-model')
        self.assertAlmostEqual(result['cost_usd'], 0.10, places=6)
        calls = env.model_calls()
        self.assertEqual([item['kind'] for item in calls], ['probe', 'probe'])
        inside = [item['cwd'] + SEP + 'probe-inside.txt' for item in calls]
        self.assertEqual(len(set(inside)), 2, 'each arm is asked about the file in its own root')
        for item, path in zip(calls, inside):
            self.assertIn('\n- %s\n' % path, item['prompt'])
            self.assertIn('echo INSIDE-', item['prompt'])
        self.assertEqual(sorted(item['skill_digest'] is not None for item in calls), [False, True])
        staged = next(item for item in calls if item['skill_digest'])
        self.assertEqual(staged['skill_digest'], env.install_digest)
        self.assertEqual(staged['settings']['sandbox']['network'], {'allowedDomains': []})
        for name in ('probe-repo', 'probe-workspace'):
            self.assertEqual(list((env.tmp / name).iterdir()), [], 'the probe removes its sentinels')
        self.assert_no_token(out, env.state)
        text = (out / 'result.json').read_text()
        for pattern in protocol_leaks():
            self.assertIsNone(pattern.search(text), pattern.pattern)
        self.assertNotIn(str(env.tmp), text)

    def test_probe_denial_needs_a_recorded_refused_attempt(self):
        cases = {'nonet': ('network_denied', 'network'), 'norepo': ('repository_read_denied', 'repository_read'),
                 'noworkspace': ('workspace_read_denied', 'workspace_read')}
        for mode, (flag, attempt) in cases.items():
            with self.subTest(mode=mode):
                env = self.new_env()
                process, out = env.probe(mode)
                self.assertEqual(process.returncode, 1, process.stdout + process.stderr)
                result = self.result(out)
                self.assertIs(result[flag], False)
                self.assertEqual(result['attempts'][attempt], 0)
                self.assertIs(result['passed'], False)

    def test_probe_requires_the_run_roots_own_files_to_be_writable_and_readable(self):
        cases = {'noinsideread': ('work_tree_read_allowed', 0), 'insidedenied': ('work_tree_read_allowed', 2),
                 'insidewrong': ('work_tree_read_allowed', 2), 'insideerror': ('work_tree_read_allowed', 2),
                 'insidewritefail': ('work_tree_write_allowed', 2)}
        for mode, (flag, attempts) in cases.items():
            with self.subTest(mode=mode):
                env = self.new_env()
                process, out = env.probe(mode)
                self.assertEqual(process.returncode, 1, process.stdout + process.stderr)
                result = self.result(out)
                self.assertIs(result[flag], False)
                self.assertIs(result['passed'], False)
                self.assertEqual(result['work_tree_read_attempts'], attempts)
                for key in ('network_denied', 'repository_read_denied', 'workspace_read_denied', 'token_scan_clean'):
                    self.assertIs(result[key], True, key)

    def test_probe_fails_when_the_network_is_open_or_a_sentinel_is_readable(self):
        cases = {'netopen': 'network_denied', 'netpartial': 'network_denied', 'repoleak': 'repository_read_denied',
                 'workspaceleak': 'workspace_read_denied'}
        for mode, flag in cases.items():
            with self.subTest(mode=mode):
                env = self.new_env()
                process, out = env.probe(mode)
                self.assertEqual(process.returncode, 1, process.stdout + process.stderr)
                result = self.result(out)
                self.assertIs(result[flag], False)
                self.assertIs(result['passed'], False)
                self.assertGreaterEqual(result['attempts'][{'network_denied': 'network', 'repository_read_denied': 'repository_read',
                                                            'workspace_read_denied': 'workspace_read'}[flag]], 1)
                for name in ('probe-repo', 'probe-workspace'):
                    self.assertEqual(list((env.tmp / name).iterdir()), [])

    def test_probe_learns_token_visibility_by_count_only(self):
        env = self.env
        process, out = env.probe('visible')
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        result = self.result(out)
        self.assertIs(result['token_visible_to_tools'], True)
        self.assertIs(result['passed'], True)
        self.assertIs(result['token_scan_clean'], True)
        self.assert_no_token(out, env.state)
        self.assertNotIn(env.token, process.stdout + process.stderr)

    def test_a_probe_whose_attempts_are_unrecorded_cannot_observe_the_token(self):
        env = self.env
        process, out = env.probe('notoken')
        self.assertEqual(process.returncode, 1, process.stdout + process.stderr)
        result = self.result(out)
        self.assertIsNone(result['token_visible_to_tools'])
        self.assertIs(result['passed'], False)

    def test_probe_costs_count_against_the_total_probe_cap(self):
        env = self.env
        cfg = env.config()
        cfg['caps']['probe'].update(total_usd=0.12, child_usd=0.06)
        env.write_config(cfg)
        first, out = env.probe(number=1)
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        self.assertAlmostEqual(self.result(out)['cost_usd'], 0.10, places=6)
        self.assertEqual(len(env.model_calls()), 2)
        second, out_two = env.probe(number=2)
        self.assertEqual(second.returncode, 1, second.stdout + second.stderr)
        self.assertIn('cap', second.stderr)
        self.assertEqual(len(env.model_calls()), 2, 'no further model call')
        self.assertFalse((out_two / 'result.json').exists())
        rows = load(env.state / 'spend.json')['rows']
        self.assertEqual([(row['kind'], row['stage'], row['settled']) for row in rows], [('probe', 'probe', True)] * 2)


class Components(Base):
    def test_archive_bytes_counts_read_and_bash_results_for_the_archive_only_in_a_stream(self):
        def use(use_id, name, tool_input):
            return {'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'id': use_id, 'name': name, 'input': tool_input}]}}

        def got(use_id, content):
            return {'type': 'user', 'message': {'content': [{'type': 'tool_result', 'tool_use_id': use_id, 'content': content}]}}

        events = [use('a', 'Read', {'file_path': 'ws/history-archive.md'}), got('a', 'x' * 10),
                  use('b', 'Read', {'file_path': 'ws/history-archive.md'}),
                  got('b', [{'type': 'text', 'text': 'yy'}, {'type': 'text', 'text': 'zzz'}]),
                  use('c', 'Bash', {'command': "sed -n '1,5p' ws/history-archive.md"}), got('c', 'w' * 7),
                  use('d', 'Bash', {'command': 'cat ws/history.md'}), got('d', 'n' * 99),
                  use('e', 'Read', {'file_path': 'ws/history.md'}), got('e', 'n' * 55),
                  use('f', 'Bash', {'command': 'grep a ws/history-archive.md ws/history.md'}), got('f', 'g' * 20),
                  use('g', 'Read', {'file_path': 'ws/history-archive.md'}), got('g', 'é' * 4),
                  use('h', 'Grep', {'pattern': 'a', 'path': 'ws/history-archive.md'}), got('h', 'q' * 500),
                  got('orphan', 'o' * 1000)]
        raw = ('\n'.join(json.dumps(event) for event in events) + '\nthis line is not json\n').encode()
        self.assertEqual(route.archive_bytes_read(raw), 10 + 5 + 7 + 20 + 8)
        self.assertEqual(route.archive_bytes_read(b''), 0)

    def test_scan_covers_names_links_contents_encodings_and_chunk_boundaries(self):
        token = 'syn/"' + secrets.token_hex(12) + '/end'
        root = self.env.tmp / 'scan'
        forms = token_forms(token)
        for number, form in enumerate(forms):
            write(root / ('form-%d.txt' % number), 'before %s after\n' % form)
        write(root / 'straddle.bin', b'a' * (route.SCAN_CHUNK - 6) + token.encode() + b'b' * 50)
        write(root / 'clean.txt', 'nothing here\n')
        os.symlink('target-' + token, root / 'link')
        hits = route.token_hits(root, token)
        self.assertEqual(sorted(hits), sorted(['form-%d.txt' % n for n in range(len(forms))] + ['straddle.bin', 'link (link target)']))
        self.assertFalse(any(token in hit for hit in hits), 'a hit never repeats the token')
        plain = secrets.token_hex(12)
        named = self.env.tmp / 'scan-names'
        write(named / ('f-' + plain), 'x')
        write(named / 'sub' / 'clean.txt', 'x')
        self.assertEqual(route.token_hits(named, plain), ['f-<token> (name)'])
        self.assertEqual(route.token_hits(self.env.tmp / 'scan-names' / 'sub', plain), [])

    def test_harness_config_paths_tolerate_cli_staging_at_any_depth(self):
        work = self.env.tmp / 'w'
        (work / '.claude/.cc-writes').mkdir(parents=True)
        (work / 'svc/.claude/.cc-writes').mkdir(parents=True)
        self.assertEqual(route.harness_config_paths(work), [])
        (work / 'svc/.claude/settings.json').write_text('{}')
        self.assertEqual(route.harness_config_paths(work), ['svc/.claude'])
        (work / 'svc/.claude/settings.json').unlink()
        (work / '.claude/settings.json').write_text('{}')
        self.assertEqual(route.harness_config_paths(work), ['.claude'])
        (work / 'docs/.Claude').mkdir(parents=True)
        self.assertEqual(route.harness_config_paths(work), ['.claude', 'docs/.Claude'])

    def test_the_file_tool_deny_rules_leave_the_run_root_open_wherever_it_sits(self):
        everywhere = [SEP + 'Users'] + [SEP + name for name in ('private/tmp', 'tmp', 'Volumes', 'private/var/folders', 'var/folders', 'private/var/tmp')]
        production = Path('/private/var/tmp/tcr/p000000')  # the layout of the run configuration: a denied tree holds the root
        settings = route.sandbox_settings(production)
        deny = settings['permissions']['deny']
        self.assertEqual([rule for rule in deny if rule.startswith('Read(')],
                         ['Read(//Users/**)', 'Read(//private/tmp/**)', 'Read(//tmp/**)', 'Read(//Volumes/**)',
                          'Read(//private/var/folders/**)', 'Read(//var/folders/**)'])
        self.assertEqual([rule for rule in deny if rule.startswith('Edit(')],
                         ['Edit(//private/var/tmp/tcr/p000000/work/.claude/**)', 'Edit(//Users/**)', 'Edit(//private/tmp/**)'])
        self.assertEqual(settings['permissions']['allow'], ['Read(//private/var/tmp/tcr/p000000/**)',
                                                           'Edit(//private/var/tmp/tcr/p000000/work/**)', 'Skill'])
        filesystem = settings['sandbox']['filesystem']
        self.assertEqual(filesystem['denyRead'], everywhere, 'the sandbox keeps every tree: allowRead re-allows the root')
        self.assertEqual(filesystem['allowRead'], [str(production)])
        volumes = route.sandbox_settings(Path('/Volumes/data/tcr/p000000'))['permissions']['deny']
        self.assertEqual([rule for rule in volumes if rule.startswith('Read(')],
                         ['Read(//Users/**)', 'Read(//private/tmp/**)', 'Read(//tmp/**)', 'Read(//private/var/folders/**)',
                          'Read(//var/folders/**)', 'Read(//private/var/tmp/**)'])
        users = route.sandbox_settings(Path(HOME_PREFIX + 'someone/tcr/p000000'))['permissions']['deny']
        self.assertNotIn('Read(//Users/**)', users)
        self.assertNotIn('Edit(//Users/**)', users)
        self.assertIn('Edit(//private/tmp/**)', users)

    def test_refused_file_tools_inside_the_run_root_are_found_and_outside_ones_are_not(self):
        root = Path('/private/var/tmp/tcr/p000001')

        def faults(*items, arm='method'):
            return route.unexpected_denials([{'tool': tool, 'path': path} for tool, path in items], root, arm)

        inside = str(root)
        self.assertEqual(faults(('Read', inside + '/work/a.md')), ['Read in run root'])
        self.assertEqual(faults(('Read', inside + SEP + 'home' + '/.claude/skills/tackle/SKILL.md')), ['Read in run root'])
        self.assertEqual(faults(('Glob', inside + '/work')), ['Glob in run root'])
        self.assertEqual(faults(('Grep', '')), ['Grep in run root'], 'a search without a path runs in the work directory')
        self.assertEqual(faults(('Read', 'notes/a.md'), ('Read', '~/x.md')), ['Read in run root'] * 2, 'relative to the work directory')
        self.assertEqual(faults(('Read', inside + '/work/.claude/settings.json')), ['Read in run root'])
        self.assertEqual(faults(('Read', inside.upper() + '/WORK/A.MD')), ['Read in run root'], 'the volume ignores case')
        self.assertEqual(faults(('Read', inside + '/work/../../elsewhere.md')), [], 'normalized, it leaves the root')
        self.assertEqual(faults(('Read', '/private/var/tmp/tcr/elsewhere.md'), ('Read', inside + '-other/x.md')), [])
        self.assertEqual(faults(('Read', HOME_PREFIX + 'someone/notes.md'), ('Glob', '/etc/*.conf'), ('Grep', '/etc')), [])
        self.assertEqual(faults(('Write', inside + '/work/.claude/settings.json')), [], 'refused on purpose')
        self.assertEqual(faults(('Write', inside + '/work/x.txt'), ('Edit', '')), ['Write in workspace', 'Edit in workspace'])
        self.assertEqual(faults(('Skill', '')), ['Skill'])
        self.assertEqual(faults(('Skill', ''), arm='control'), [])

    def test_denial_paths_come_from_the_file_or_the_search_path(self):
        def denial(tool, **given):
            return {'tool_name': tool, 'tool_use_id': 'use', 'tool_input': given}

        denials = [denial('Read', file_path='/a/b.md'), denial('Write', file_path='/a/w.md'), denial('Glob', pattern='*.md', path='/a'),
                   denial('Glob', pattern='/etc/*.conf'), denial('Glob', pattern='*.md'), denial('Grep', pattern='x', path='/g'),
                   denial('Grep', pattern='/not-a-path'), denial('Bash', command='ls')]
        raw = json.dumps({'type': 'result', 'subtype': 'success', 'is_error': False, 'permission_denials': denials}).encode()
        self.assertEqual([(d['tool'], d['path']) for d in route.parse_stream(raw)['denials']],
                         [('Read', '/a/b.md'), ('Write', '/a/w.md'), ('Glob', '/a'), ('Glob', '/etc/*.conf'), ('Glob', ''),
                          ('Grep', '/g'), ('Grep', ''), ('Bash', '')])

    def test_general_credential_invariant_names_the_broker_routes(self):
        import harness

        def sentences(text, phrase):
            return [part for part in re.split(r'(?<=[.!?])\s+', ' '.join(text.split())) if re.search(phrase, part, re.I)]

        readme = (HERE / 'README.md').read_text()
        documents = ((readme, r'no credential is .*passed into a participant'),
                     (harness.__doc__, r'participant never receives a credential'),
                     ((ROOT / 'eval' / 'README.md').read_text(), r'no credential reaches a participant'))
        for text, phrase in documents:
            found = sentences(text, phrase)
            self.assertTrue(found, phrase)
            for sentence in found:
                self.assertIn('broker routes', sentence, 'the general invariant must say which routes it covers')
        self.assertNotIn("the model's tools never receive a credential", readme.lower())


if __name__ == '__main__':
    unittest.main()
