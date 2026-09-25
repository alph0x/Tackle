"""Every workspace lint row passes clean fixtures and fails on a planted defect.

Rows are extracted by ``canonical_rows`` and judged by ``lint_verdict`` from full-checks.md, the
same recipes a Full run uses, and executed with ``sh`` against disposable copies of the fixtures.
"""
import hashlib
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
FIXTURES = HERE / 'fixtures'
SPEC = ROOT / 'references/guides/lint-spec.md'
TEMPLATE = ROOT / 'references/task.tmpl.md'
SLUG = 'demo'
NAMESPACE = {'__name__': 'lint_rows_test'}
for _block in re.findall(r'```python\n(.*?)\n```', (ROOT / 'references/guides/full-checks.md').read_text(), re.S):
    if 'def canonical_rows' in _block:
        exec(_block, NAMESPACE)

WARN_ROWS = {8, 13, 15}
EXTRACTOR = ('function cell(i,c){c=$i; sub(/^[[:space:]]+/,"",c); sub(/[[:space:]]+$/,"",c); return c} '
             'function colof(name,i){for(i=2;i<=NF;i++) if(cell(i)==name) return i; return 0} '
             'FNR==1{col=0; pend=0} pend && $2 ~ /^[[:space:]]*:?-+:?[[:space:]]*$/ {col=pend} {pend=0} '
             '$2 !~ /[PT]-[A-Za-z0-9]/ && colof("Status"){pend=colof("Status")}')
CONTRACT_CLAUSE = '## C01 · Demo clause <!-- SEALED: D-01 -->\n\nThe demo output is one line.\n'


def rows():
    source = SPEC.read_bytes()
    return NAMESPACE['canonical_rows'](source, hashlib.sha256(source).hexdigest(), SLUG)


def awk_variants():
    variants = [('system', None)]
    for name in ('gawk', 'mawk', 'original-awk'):
        path = shutil.which(name)
        if path:
            variants.append((name, [path]))
    busybox = shutil.which('busybox')
    if busybox and subprocess.run([busybox, 'awk', 'BEGIN{}'], capture_output=True).returncode == 0:
        variants.append(('busybox', [busybox, 'awk']))
    return variants


def brief(identity, kind='standard', fields=True, effort='- **Effort**: high', depends='none',
          scope=None, clause_sha=None, clause_id='C01'):
    text = TEMPLATE.read_text().replace('T-0N', identity).replace('t-0n', identity.lower())
    if clause_sha:
        text = (text.replace('{{clause id}}', clause_id).replace('{{revision}}', 'rev 1 (D-01)')
                .replace('{{hash of the exact clause bytes}}', clause_sha)
                .replace('{{the\n  canonical clause, copied byte-for-byte from its authoritative contract}}',
                         'the clause quotes an unrelated sha256 `' + '1' * 64 + '` in its body'))
    else:
        text = re.sub(r'- \*\*\{\{clause id\}\}.*?\}\}\.\n', '', text, count=1, flags=re.S)
    lines = []
    for line in text.split('\n'):
        if line.startswith('- **Effort**:'):
            line = effort
        elif line.startswith('- **Type**:'):
            line = '- **Type**: ' + kind + '.'
        elif line.startswith('- **Depends on**:'):
            line = '- **Depends on**: ' + depends + '.'
        elif line.startswith('- **Write scope**:') and scope:
            line = '- **Write scope**: `' + scope + '`'
        elif line.startswith(('- **Rounds**:', '- **Metric**:', '- **Threshold**:')) and not fields:
            continue
        lines.append(line)
    text = '\n'.join(lines).replace('{{D-xx}}', 'D-01')
    text = re.sub(r'\{\{.*?\}\}', 'x', text, flags=re.S)
    if clause_sha:
        text = text.replace('- **Inputs**: x.', '- **Inputs**: fixture sha256 `' + '0' * 64 + '`.')
    return text


def clause_sha(contract):
    selected, found = [], False
    for line in contract.splitlines():
        if found and (line.startswith('## ') or line.startswith('<a id=')):
            break
        if not found and line.split()[:2] == ['##', 'C01']:
            found = True
        if found:
            selected.append(line + '\n')
    return hashlib.sha256(''.join(selected).encode()).hexdigest()


FENCED_EXAMPLE = ('\n```markdown\n- **C77 · rev 1 (D-01) · sha256 `' + '3' * 64 + '`**: an example bullet, not a compiled clause.\n'
                  '- **Rounds**: 3\n- **Metric**: example\n- **Threshold**: example\n```\n')
GENERATED = {
    'pass-full': {'tasks/T-01.md': lambda: brief('T-01', clause_sha=clause_sha(CONTRACT_CLAUSE)) + FENCED_EXAMPLE,
                  'tasks/T-02.md': lambda: brief('T-02', kind='experiment', depends='T-01',
                                                 scope='src/demo.txt')},
    'fail-9': {'tasks/T-02.md': lambda: brief('T-02', kind='experiment', fields=False, depends='T-01')},
    'fail-9b': {'tasks/T-02.md': lambda: brief('T-02', kind='discovery', fields=False, depends='T-01')},
    'fail-12': {'tasks/T-02.md': lambda: brief('T-02', effort='- **Effort**: inherit', depends='T-01')},
    'fail-12b': {'tasks/T-02.md': lambda: brief('T-02', effort='* **Effort**: extreme', depends='T-01')},
    'fail-9d': {'tasks/T-02.md': lambda: brief('T-02', kind='experiment', fields=False, depends='T-01') + FENCED_EXAMPLE},
    'fail-9c': {'tasks/T-02.md': lambda: brief('T-02', kind='experiment', fields=False, depends='T-01')
                .replace('- **Type**: experiment.', '- **Type**: experiment · **Metric:** m · **Threshold:** t · **Rounds**:')},
    'fail-seal-unresolved': {'tasks/T-02.md': lambda: brief('T-02', depends='T-01', clause_sha='2' * 64, clause_id='C09')},
    'fail-seal-malformed': {'tasks/T-02.md': lambda: brief('T-02', depends='T-01', clause_sha='ABC', clause_id='C02')},
}

# (overlay, base, row, expected stdout fragment, verdict). A structural diagnostic that exits 1
# is ERROR under lint_verdict (rows 1, 2 and 12); every other finding is FAIL or WARN.
FAILS = [
    ('fail-1', 'pass-full', 1, '{{todo}}', 'FAIL'),
    ('fail-1-lite', 'pass-lite', 1, 'row1: Lite has Full artifact', 'ERROR'),
    ('fail-2', 'pass-full', 2, 'missing brief: tasks/T-03.md', 'FAIL'),
    ('fail-2b', 'pass-full', 2, 'mixed board identity: P-07', 'FAIL'),
    ('fail-2c', 'pass-full', 2, 'unresolved: T-09', 'FAIL'),
    ('fail-2-legacy', 'pass-legacy', 2, 'unresolved: P-09', 'FAIL'),
    ('fail-3', 'pass-full', 3, 'bad status', 'FAIL'),
    ('fail-3-legacy', 'pass-legacy', 3, 'bad status', 'FAIL'),
    ('fail-4', 'pass-full', 4, 'malformed', 'FAIL'),
    ('fail-4b', 'pass-full', 4, 'stale: decisions.md:1', 'FAIL'),
    ('fail-5', 'pass-full', 5, 'duplicated Status declaration', 'FAIL'),
    ('fail-5-legacy', 'pass-legacy', 5, 'P-02.md', 'FAIL'),
    ('fail-6', 'pass-full', 6, 'out of order', 'FAIL'),
    ('fail-6b', 'pass-full', 6, 'archive newer than log oldest', 'FAIL'),
    ('fail-7', 'pass-full', 7, 'superseded seal: D-02', 'FAIL'),
    ('fail-7b', 'pass-full', 7, 'missing seal: D-09', 'FAIL'),
    ('fail-8', 'pass-full', 8, 'collision', 'WARN'),
    ('fail-8b', 'pass-full', 8, 'unresolved scope', 'WARN'),
    ('fail-9', 'pass-full', 9, 'experiment task missing metric fields', 'FAIL'),
    ('fail-9b', 'pass-full', 9, 'discovery task without Rounds budget', 'FAIL'),
    ('fail-9c', 'pass-full', 9, 'experiment task missing metric fields', 'FAIL'),
    ('fail-9d', 'pass-full', 9, 'experiment task missing metric fields', 'FAIL'),
    ('fail-10', 'pass-full', 10, 'terminal task without verification reference', 'FAIL'),
    ('fail-10-legacy', 'pass-legacy', 10, 'done/blocked row without grade', 'FAIL'),
    ('fail-11', 'pass-full', 11, 'done task without usage row: T-01', 'FAIL'),
    ('fail-11-legacy', 'pass-legacy', 11, 'done point without usage row: P-01', 'FAIL'),
    ('fail-12', 'pass-full', 12, 'inherit', 'FAIL'),
    ('fail-12b', 'pass-full', 12, 'extreme', 'FAIL'),
    ('fail-13', 'pass-full', 13, 'over archive threshold', 'WARN'),
    ('fail-14', 'pass-full', 14, 'done task without closure report: T-02', 'FAIL'),
    ('fail-14b', 'pass-full', 14, 'done task without closure report: T-02', 'FAIL'),
    ('fail-14-legacy', 'pass-legacy', 14, 'done task without closure report: P-03', 'FAIL'),
    ('fail-15', 'pass-full', 15, 'stale reference-doc', 'WARN'),
    ('fail-16', 'pass-full', 16, 'duplicate start', 'FAIL'),
    ('fail-16b', 'pass-full', 16, 'unknown Event', 'FAIL'),
    # /5 cases (T-39). C2: the token stays invalid on /4 (row 3 unchanged).
    ('fail-3-waiting-v4', 'pass-full', 3, 'bad status', 'FAIL'),
    # C3: an uncited Ready to run row on /5 fails row 10's new citation check.
    ('fail-10-uncited-ready-v5', 'pass-full-5', 10, 'ready-to-run task missing ready citation', 'FAIL'),
    # C4: two /5 workspaces, one In progress and the other Waiting on owner, with colliding scope.
    ('fail-8-waiting-v5', 'pass-full-5', 8, 'collision', 'WARN'),
    # C5: a /5 workspace whose brief declares Status: (row 5 forbids it outside board.md).
    ('fail-5-status-in-brief-v5', 'pass-full-5', 5, 'duplicated Status declaration', 'FAIL'),
]
PASSES = [('pass-full', None), ('pass-lite', None), ('pass-legacy', None), ('pass-legacy-legend', 'pass-legacy'),
          # C1: a full /5 workspace covering all ten states, a cited Ready row and a waiting: row.
          ('pass-full-5', None),
          # Regression guard: a /4 board's Ready to run row stays uncited-tolerant (row 10 is /5-only).
          ('pass-v4-ready-pending', 'pass-full')]


def materialize(root, name, base=None):
    if base:
        materialize(root, base)
    source = FIXTURES / name
    if source.is_dir():
        shutil.copytree(source, root, dirs_exist_ok=True)
    workspace = root / 'docs/plans' / SLUG
    for relative, content in GENERATED.get(name, {}).items():
        path = workspace / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content())


def run_row(number, root, awk):
    env = dict(os.environ)
    if awk:
        bin_dir = root.parent / 'bin'
        bin_dir.mkdir(exist_ok=True)
        wrapper = bin_dir / 'awk'
        wrapper.write_text('#!/bin/sh\nexec ' + ' '.join(awk) + ' "$@"\n')
        wrapper.chmod(0o755)
        env['PATH'] = str(bin_dir) + os.pathsep + env['PATH']
    child = subprocess.run(['sh', '-c', rows()[number]['command'].decode()], cwd=root, env=env,
                           capture_output=True, timeout=30)
    record = dict(child_exit=child.returncode, timeout=False, launch_error=None,
                  signal=(-child.returncode if child.returncode < 0 else None),
                  inputs_stable=True, artifacts_present=True)
    return NAMESPACE['lint_verdict'](number, record, child.stdout, child.stderr), child


def seal_command():
    guide = (ROOT / 'references/guides/verify.md').read_text()
    after = guide.split('<a id="seal-integrity-command"></a>', 1)[1]
    block = re.search(r'```sh\n(.*?)\n[ ]*```', after, re.S)[1]
    return '\n'.join(line[3:] if line.startswith('   ') else line for line in block.split('\n'))


class LintRowTests(unittest.TestCase):
    def workspace(self, name, base=None):
        temporary = tempfile.TemporaryDirectory(prefix='tackle-lint-rows-')
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name) / 'root'
        root.mkdir()
        materialize(root, name, base)
        return root

    def test_clean_fixtures_pass_every_row(self):
        for awk_name, awk in awk_variants():
            for fixture, base in PASSES:
                root = self.workspace(fixture, base)
                for number in range(1, 17):
                    with self.subTest(awk=awk_name, fixture=fixture, row=number):
                        verdict, child = run_row(number, root, awk)
                        self.assertEqual(verdict, 'PASS', (child.returncode, child.stdout[:400], child.stderr[:400]))

    def test_each_row_fails_on_its_planted_defect(self):
        for awk_name, awk in awk_variants():
            for fixture, base, number, expected, wanted in FAILS:
                with self.subTest(awk=awk_name, fixture=fixture, row=number):
                    root = self.workspace(fixture, base)
                    verdict, child = run_row(number, root, awk)
                    self.assertEqual(verdict, wanted, (child.returncode, child.stdout[:400], child.stderr[:400]))
                    self.assertIn(expected, child.stdout.decode())

    def test_every_row_has_a_planted_defect(self):
        self.assertEqual({number for _, _, number, _, _ in FAILS}, set(range(1, 17)))
        self.assertTrue(all(wanted == ('WARN' if number in WARN_ROWS else wanted) for _, _, number, _, wanted in FAILS))

    def test_template_faithful_brief_passes_row_2(self):
        root = self.workspace('pass-full')
        first = (root / 'docs/plans/demo/tasks/T-01.md').read_text().split('\n', 1)[0]
        self.assertTrue(first.startswith('<a id='), first)
        verdict, child = run_row(2, root, None)
        self.assertEqual(verdict, 'PASS', child.stdout)

    def test_row_cells_are_pipe_free(self):
        for line in SPEC.read_text().splitlines():
            if re.match(r'^\| [0-9]+ ·', line):
                with self.subTest(row=line[2:5]):
                    cells = re.split(r'(?<!\\)\|', line)
                    self.assertEqual(len(cells), 5, 'GFM splits this row into %d cells' % (len(cells) - 2))

    def test_status_rows_share_the_header_extractor(self):
        for number in (3, 8, 10, 11, 14):
            with self.subTest(row=number):
                self.assertIn(EXTRACTOR.encode(), rows()[number]['command'])

    def test_severity_list_classifies_every_row(self):
        line = next(l for l in SPEC.read_text().splitlines() if 'warn-severity' in l and 'blocks execution' in l)
        blocking = set()
        for low, high in re.findall(r'(\d+)(?:–(\d+))?', line.split('a failure in rows', 1)[1].split('blocks', 1)[0]):
            blocking.update(range(int(low), int(high or low) + 1))
        self.assertEqual(blocking, set(range(1, 17)) - WARN_ROWS)

    def test_seal_integrity_command(self):
        command = seal_command().replace('<slug>', SLUG)
        clean = subprocess.run(['sh', '-c', command], cwd=self.workspace('pass-full'), capture_output=True, timeout=30)
        self.assertEqual((clean.returncode, clean.stdout, clean.stderr), (0, b'', b''))
        for fixture, expected in (('fail-seal', b'seal drift: C01'),
                                  ('fail-seal-unresolved', b'unresolved clause source: C09'),
                                  ('fail-seal-malformed', b'malformed clause hash: C02')):
            with self.subTest(fixture=fixture):
                child = subprocess.run(['sh', '-c', command], cwd=self.workspace(fixture, base='pass-full'),
                                       capture_output=True, timeout=30)
                self.assertEqual(child.returncode, 1, child.stderr)
                self.assertIn(expected, child.stdout)
                self.assertEqual(child.stdout.count(b'\n'), 1, child.stdout)

    def test_ci_has_no_loop_that_only_continues(self):
        for line in (ROOT / '.github/workflows/ci.yml').read_text().splitlines():
            loop = re.search(r'\bfor [^;]+; do (.*); done', line)
            if loop:
                with self.subTest(line=line.strip()[:60]):
                    statements = [s.strip() for s in loop[1].split(';') if s.strip()]
                    self.assertFalse(all(s.endswith('continue') for s in statements))


if __name__ == '__main__':
    unittest.main()
