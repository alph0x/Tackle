"""Run local release phases using a per-release configuration."""
import argparse, hashlib, importlib.util, json, os, pathlib, re, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent
TOOLS = HERE
spec = importlib.util.spec_from_file_location('support', HERE / 'release_support.py')
support = importlib.util.module_from_spec(spec)
spec.loader.exec_module(support)
spec = importlib.util.spec_from_file_location('config', HERE / 'config.py')
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)

D23_FILES = ['eval/tests/product/migration/test_compact_migration.py', 'eval/tests/product/migration/test_v101_v102_checklist.py',
             'eval/tests/product/migration/test_v90_v91_checklist.py', 'eval/tests/product/templates/test_history_and_obligation_templates.py']


def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def git(repo, *args):
    return subprocess.run(['git', *args], cwd=repo, capture_output=True, text=True)


class Phase:
    def __init__(self, a):
        self.a = a
        self.repo = pathlib.Path(a.repo).resolve()
        name = a.phase + (f'-{a.role}' if a.role else '') + (f'-{a.part}' if a.part else '') + \
            (f'-{a.label}' if a.label else '') + (f'-a{a.attempt}' if a.attempt else '')
        self.out = pathlib.Path(a.records).resolve() / name
        if self.out.exists():
            sys.exit(f'destination exists: {self.out}')
        self.out.mkdir(parents=True)
        self.results, self.ok = [], True

    def run(self, name, argv, expect=0, env=None, timeout=2400):
        # Inherit TMPDIR: a temporary directory inside the records root lies inside the Tackle repository, where tests
        # that create temporary Git trees would find the parent repository (rehearsal-02).
        if env is None:
            env = dict(os.environ)
        r = support.capture(name, argv, str(self.repo), str(self.out), env=env, timeout=timeout)
        good = r['complete'] and r['native_exit'] == expect
        self.results.append({'name': name, 'argv': argv, 'cwd': str(self.repo), 'native_exit': r['native_exit'],
                             'timeout': r['timeout'], 'complete': r['complete'], 'expected': expect, 'met': good})
        self.ok = self.ok and good
        print(f"{name}: native_exit={r['native_exit']} expected={expect} met={good}", flush=True)
        return r

    def fact(self, name, value, good):
        self.results.append({'name': name, 'value': value, 'met': bool(good)})
        self.ok = self.ok and bool(good)
        print(f'{name}: {value} met={bool(good)}', flush=True)

    def finish(self):
        (self.out / 'phase.json').write_text(json.dumps({'phase': self.a.phase, 'part': self.a.part,
                                                         'label': self.a.label, 'ok': self.ok, 'results': self.results}, indent=1) + '\n')
        sys.exit(0 if self.ok else 1)


def accepted_dir(records, base):
    """The accepted directory of a phase: RECORDS/<base> or its highest accepted RECORDS/<base>-aN repeat."""
    root = pathlib.Path(records).resolve()
    found = []
    for d in root.glob(base + '*'):
        m = re.fullmatch(re.escape(base) + r'(?:-a(\d+))?', d.name)
        if m and (d / 'phase.json').is_file() and json.loads((d / 'phase.json').read_text()).get('ok'):
            found.append((int(m.group(1) or 0), d))
    if not found:
        sys.exit(f'no accepted {base} phase in {root}')
    return max(found)[1]


def accepted(records, phase, name):
    return json.loads((accepted_dir(records, phase) / name).read_text())


def candidate(a):
    return accepted(a.records, 'candidate', 'candidate.json')['candidate']


def tool(p, name, script, *extra):
    c = candidate(p.a)
    p.fact('candidate is HEAD', c, git(p.repo, 'rev-parse', 'HEAD').stdout.strip() == c)
    p.run(name, [PY310, '-I', '-B', str(TOOLS / script), '--config', p.a.config, '--repo', str(p.repo), *extra[0], '--candidate', c, *extra[1],
                 '--records', str(p.out / name), *extra[2]], timeout=3600)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', required=True)
    ap.add_argument('--phase', required=True)
    ap.add_argument('--repo', required=True)
    ap.add_argument('--records', required=True)
    ap.add_argument('--part', choices=['format', 'stamp', 'changelog', 'migrate', 'readme'])
    ap.add_argument('--label', choices=['py310', 'py314'])
    ap.add_argument('--attempt', type=int, default=0)
    ap.add_argument('--role', choices=['reviewer'])
    a = ap.parse_args()
    a.config = str(pathlib.Path(a.config).resolve())
    cfg = config.load(a.config)
    global WS, MAIN, BRANCH, PY310, PY314, PARTS, ORDER
    WS = pathlib.Path(cfg['workspace'])
    MAIN, BRANCH = cfg['base'], cfg['branch']
    PY310, PY314 = (cfg['runtimes'][x]['path'] for x in ('py310', 'py314'))
    ORDER = cfg['parts']
    paths = {
        'format': ['eval/rules/unit-dispositions.json'],
        'stamp': ['eval/rules/unit-dispositions.json', 'skills/tackle/SKILL.md', 'skills/tackle/references/AGENTS.tmpl.md', 'skills/tackle/references/README.tmpl.md'],
        'changelog': ['CHANGELOG.md', 'eval/records/claims.json', cfg['record']['destination']],
        'migrate': ['MAINTAINING.md', 'eval/rules/unit-dispositions.json', 'maintaining/check_migration_catalog.py', 'skills/tackle/references/guides/migrate.md', 'skills/tackle/references/guides/migration-catalog.json', 'skills/tackle/scripts/README.md', 'skills/tackle/scripts/migrate/compact.py'],
        'readme': ['README.md'],
    }
    PARTS = {k: (config.titles(cfg)[k], v) for k, v in paths.items()}
    if a.part and a.part not in ORDER:
        ap.error('part is not enabled in config')
    p = Phase(a)
    ph = a.phase
    ws = ['--workspace', str(WS)]
    ver = ['--version', cfg['version']]

    if ph == 'preflight':
        p.fact('configuration sha256', sha(a.config), True)
        for key in ('changelog', 'record'):
            observed = sha(cfg[key]['path'])
            p.fact(key + ' sha256', observed, observed == cfg[key]['sha256'])
        head = git(p.repo, 'rev-parse', 'HEAD').stdout.strip()
        main_head = git(p.repo, 'rev-parse', 'main').stdout.strip()
        p.fact('main at the pinned base', main_head, main_head == MAIN)
        detached = git(p.repo, 'symbolic-ref', '-q', 'HEAD').returncode
        p.fact('checkout detached at main', [head, detached], head == MAIN and detached == 1)
        p.fact('clean checkout', git(p.repo, 'status', '--porcelain').stdout or 'clean', git(p.repo, 'status', '--porcelain').stdout == '')
        p.fact('release branch absent', BRANCH, git(p.repo, 'show-ref', '--verify', '--quiet', f'refs/heads/{BRANCH}').returncode == 1)
        p.fact('tag absent', 'v' + cfg['version'], git(p.repo, 'show-ref', '--verify', '--quiet', 'refs/tags/v' + cfg['version']).returncode == 1)
        for label in ('py310', 'py314'):
            actual = support.probe(cfg['runtimes'][label]['path'])['version']
            p.fact('runtime ' + label, actual, config.runtime_ok(cfg, label, actual))
        if p.ok:
            (p.out / 'base.json').write_text(json.dumps({'base': MAIN}, indent=1) + '\n')
    elif ph == 'branch':
        accepted(a.records, 'preflight', 'base.json')
        p.run('switch', ['git', 'switch', '-c', BRANCH, MAIN])
        p.fact('on release branch', git(p.repo, 'symbolic-ref', '--short', 'HEAD').stdout.strip(),
               git(p.repo, 'symbolic-ref', '--short', 'HEAD').stdout.strip() == BRANCH)
    elif ph == 'part':
        if not a.part:
            sys.exit('part needs --part')
        title, paths = PARTS[a.part]
        done = git(p.repo, 'log', '--format=%s', f'{MAIN}..HEAD').stdout.split('\n')[::-1]
        done = [x for x in done if x]
        want = [PARTS[x][0] for x in ORDER[:ORDER.index(a.part)]]
        p.fact('earlier parts committed in order', done, done == want)
        p.fact('on release branch', git(p.repo, 'symbolic-ref', '--short', 'HEAD').stdout.strip(),
               git(p.repo, 'symbolic-ref', '--short', 'HEAD').stdout.strip() == BRANCH)
        p.fact('clean before part', git(p.repo, 'status', '--porcelain').stdout or 'clean', git(p.repo, 'status', '--porcelain').stdout == '')
        if not p.ok:
            p.finish()
        parent = git(p.repo, 'rev-parse', 'HEAD').stdout.strip()
        edit = [PY310, '-I', '-B', str(TOOLS / 'release_edit.py'), '--repo', str(p.repo), *ws, '--candidate', parent,
                '--version', cfg['version'], '--from-version', cfg['from_version'], '--config', a.config, '--part', a.part]
        p.run('apply', edit + ['--records', str(p.out / 'receipt')])
        after = {k: sha(p.repo / k) for k in paths}
        p.run('second', edit + ['--records', str(p.out / 'receipt-second')], expect=1)
        p.fact('second application changed nothing', 'unchanged', {k: sha(p.repo / k) for k in paths} == after)
        p.run('stage', ['git', 'add', '--', *paths])
        status = git(p.repo, 'status', '--porcelain').stdout.splitlines()
        p.fact('only the part paths are staged', status, sorted(x[3:] for x in status) == sorted(paths) and all(x[1] == ' ' for x in status))
        if not p.ok:
            p.finish()
        p.run('commit', ['git', '-c', 'commit.gpgsign=false', 'commit', '-q', '-m', title])
        head = git(p.repo, 'rev-parse', 'HEAD').stdout.strip()
        p.fact('commit parent', git(p.repo, 'rev-parse', 'HEAD^').stdout.strip(), git(p.repo, 'rev-parse', 'HEAD^').stdout.strip() == parent)
        body = git(p.repo, 'log', '-1', '--format=%B', head).stdout
        p.fact('title-only message', body, body.rstrip('\n') == title)
        changed = git(p.repo, 'diff', '--name-only', parent, head).stdout.split()
        p.fact('commit changes exactly the part paths', changed, sorted(changed) == sorted(paths))
        p.fact('committed bytes are the applied bytes', 'match', all(sha(p.repo / k) == v for k, v in after.items()))
        p.fact('clean after commit', git(p.repo, 'status', '--porcelain').stdout or 'clean', git(p.repo, 'status', '--porcelain').stdout == '')
    elif ph == 'candidate':
        head = git(p.repo, 'rev-parse', 'HEAD').stdout.strip()
        titles = [x for x in git(p.repo, 'log', '--format=%s', f'{MAIN}..HEAD').stdout.split('\n') if x][::-1]
        p.fact('part commits in order', titles, titles == [PARTS[x][0] for x in ORDER])
        p.fact('first parent chain from main', git(p.repo, 'rev-list', '--first-parent', '--count', f'{MAIN}..HEAD').stdout.strip(),
               git(p.repo, 'merge-base', '--is-ancestor', MAIN, head).returncode == 0
               and git(p.repo, 'rev-list', '--count', f'{MAIN}..HEAD').stdout.strip() == str(len(ORDER)))
        p.fact('clean candidate', git(p.repo, 'status', '--porcelain').stdout or 'clean', git(p.repo, 'status', '--porcelain').stdout == '')
        p.run('rev-parse', ['git', 'rev-parse', 'HEAD'])
        if p.ok:
            changed = sorted(git(p.repo, 'diff', '--name-only', 'v' + cfg['from_version'], head).stdout.split())
            (p.out / 'candidate.json').write_text(json.dumps({'candidate': head, 'base': MAIN, 'changed_since_release': changed}, indent=1) + '\n')
    elif ph == 'self-lint':
        tool(p, 'self-lint', 'self_lint.py', ws, ver, ['--interpreter', PY310])
    elif ph == 'catalog':
        tool(p, 'catalog', 'catalog_checks.py', ws, ver, ['--interpreter', PY310])
    elif ph == 'workspace-rows':
        tool(p, 'workspace-rows', 'workspace_sweep.py', ws, ver, [])
    elif ph == 'sweep':
        # MAINTAINING release sweep step 6: M = nine self-lint gates + one catalog gate + each gating workspace.
        c = candidate(a)
        p.run('whitespace-since-release', ['git', 'diff', '--check', 'v' + cfg['from_version'], c])
        lint = json.loads((accepted_dir(a.records, 'self-lint') / 'self-lint' / 'results.json').read_text())
        gates = [g for g in lint['gates'] if re.search(r'gate-\d+\.sh$', g['argv'][-1])]
        p.fact('nine self-lint gates', len(gates), len(gates) == 9)
        catalog = json.loads((accepted_dir(a.records, 'catalog') / 'catalog' / 'results.json').read_text())
        rows = json.loads((accepted_dir(a.records, 'workspace-rows') / 'workspace-rows' / 'workspace-sweep' / 'results.json').read_text())
        gating = [w for w in rows if w.get('gating')]
        p.fact('gating workspaces', [w['workspace'] for w in gating], [w['workspace'] for w in gating] == cfg['gating_workspaces'])
        # Release completion remains pending.
        satisfied = sum(1 for g in gates if g['passed']) + (1 if catalog['passed'] else 0)
        total = len(gates) + 1 + len(gating)
        sweep = {'candidate': c, 'N': satisfied, 'M': total, 'gates_passed': sum(1 for g in gates if g['passed']),
                 'catalog_passed': catalog['passed'],
                 'workspaces': {w['workspace']: {'mandatory_rows_pass': w.get('mandatory_pass'),
                                                 'done_signal_and_global_acceptance': 'pending release completion'}
                                for w in gating},
                 'line': f'sweep: {satisfied}/{total} gates passed'}
        p.fact('mandatory rows of gating workspaces', {w['workspace']: w.get('mandatory_pass') for w in gating},
               all(w.get('mandatory_pass') for w in gating))
        p.fact('sweep at the owner pause', sweep['line'], satisfied == total - len(gating) and sweep['line'] == cfg['expected_sweep'])
        (p.out / 'sweep.json').write_text(json.dumps(sweep, indent=1) + '\n')
    elif ph == 'registry':
        if not a.label:
            sys.exit('registry needs --label')
        changed = accepted(a.records, 'candidate', 'candidate.json')['changed_since_release']
        extra = ['--interpreter', PY310 if a.label == 'py310' else PY314, '--label', a.label]
        for path in changed:
            extra += ['--changed', path]
        tool(p, a.label, 'full_registry.py', ws, ver, extra)
        metas = list((p.out / a.label).glob('*.metadata.json'))
        p.fact('one registry metadata', [m.name for m in metas], len(metas) == 1)
        if len(metas) == 1:
            m = json.loads(metas[0].read_text())
            p.fact('registry passed and complete', {k: m.get(k) for k in ('passed', 'complete', 'exit', 'timeout', 'tests')},
                   m.get('passed') is True and m.get('complete') is True and m.get('exit') == 0 and m.get('timeout') is False)
            p.fact('registry candidate', [m.get('revision'), m.get('revision_after')], m.get('revision') == m.get('revision_after') == candidate(a))
    elif ph == 'ci-replay':
        metas = {}
        for label in ('py310', 'py314'):
            found = list((accepted_dir(a.records, f'registry-{label}') / label).glob('*.metadata.json'))
            p.fact(f'{label} registry record', [str(x) for x in found], len(found) == 1)
            metas[label] = str(found[0]) if found else ''
        tool(p, 'ci-replay', 'ci_replay.py', ws, ver, ['--registry310', metas['py310'], '--registry314', metas['py314'],
                                                      '--interpreter310', PY310, '--interpreter314', PY314])
    elif ph == 'committed-text':
        tool(p, 'committed-text', 'committed_guard_strict.py', [], ['--base', 'v' + cfg['from_version'], '--initiative', cfg['initiative']], [])
    elif ph == 'install-local':
        tool(p, 'install-local', 'install_local.py', ws, ver, [])
    elif ph == 'notes':
        tool(p, 'notes', 'verify_release_notes.py', ws, ver, [])
        res = p.out / 'notes' / 'results.json'
        if res.is_file():
            r = json.loads(res.read_text())
            p.fact('notes hash', r.get('notes_sha256'), r.get('notes_sha256') == sha(p.out / 'notes' / 'release-notes.md'))
    elif ph == 'sentinel':
        name = '.sentinel-release-reviewer'
        try:
            (p.out / name).write_text('sentinel\n')
            p.fact(f'write allowed {p.out / name}', 'written', True)
        except OSError as error:
            p.fact(f'write allowed {p.out / name}', str(error), False)
        for target in (WS.parent / name, WS / 'tasks' / name, p.repo / name):
            try:
                target.write_text('sentinel\n')
                p.fact(f'write refused {target}', 'WRITTEN: channel wider than authority', False)
            except OSError as error:
                p.fact(f'write refused {target}', type(error).__name__, True)
    elif ph == 'review':
        c = candidate(a)
        p.fact('candidate is HEAD', c, git(p.repo, 'rev-parse', 'HEAD').stdout.strip() == c)
        p.fact('clean candidate', git(p.repo, 'status', '--porcelain').stdout or 'clean', git(p.repo, 'status', '--porcelain').stdout == '')
        titles = [x for x in git(p.repo, 'log', '--format=%s', f'{MAIN}..{c}').stdout.split('\n') if x][::-1]
        p.fact('part commits in order', titles, titles == [PARTS[x][0] for x in ORDER])
        for name in D23_FILES:
            base = subprocess.check_output(['git', 'show', f'{MAIN}:{name}'], cwd=p.repo)
            got = subprocess.check_output(['git', 'show', f'{c}:{name}'], cwd=p.repo)
            p.fact(f'protected file {name}', 'equal' if got == base else 'DIFFERS', got == base)
        p.run('units', [PY310, '-I', '-B', 'eval/rules/check_unit_diff.py', '--repo', '.', '--base', 'auto'])
        p.run('ledger', [PY310, '-I', '-B', 'eval/rules/check_ledger.py', '--repo', '.', '--gate', 'auto'])
        text = (p.out / 'ledger.stdout').read_text()
        p.fact('ledger delta', re.findall(r'gate: .*', text), cfg['expected_ledger_gate'] in text.splitlines())
        notes = accepted_dir(a.records, 'notes') / 'notes'
        r = json.loads((notes / 'results.json').read_text())
        p.fact('notes hash', r.get('notes_sha256'), r.get('notes_sha256') == sha(notes / 'release-notes.md') and r.get('candidate') == c)
    else:
        sys.exit(f'unknown phase {ph}')
    p.finish()


if __name__ == '__main__':
    main()
