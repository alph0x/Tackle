"""Shared mechanics for lint tests; cases and expected outcomes stay with each suite.

Import the shipped extractor and verdict rather than mirroring their implementation.
The independent extractor contract tests remain in eval/run/execution.
"""
import hashlib
import importlib.util
import re
import subprocess
from pathlib import Path

from maintaining.install_root import current_root

ROOT = Path(__file__).resolve().parents[2]
INSTALL = current_root(ROOT)


def lint_namespace():
    path = INSTALL / 'scripts/lint_runner.py'
    spec = importlib.util.spec_from_file_location('lint_test_support', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if 'canonical_rows' not in vars(module):
        raise ValueError('expected the shipped lint script to define canonical_rows')
    return vars(module)


def lint_rows(slug, source=None):
    if source is None:
        source = (INSTALL / 'references/guides/lint-spec.md').read_bytes()
    return lint_namespace()['canonical_rows'](source, hashlib.sha256(source).hexdigest(), slug)


def literal_command(number, source=None, *, single_backtick=False):
    """Copy the documented cell verbatim, including its code-span padding and slug.

    Keep the single-delimiter behavior of the older literal-command suites until
    their own extractor contract is changed. Compiled-row callers use lint_rows.
    """
    if source is None:
        source = (INSTALL / 'references/guides/lint-spec.md').read_text(encoding='utf-8')
    for line in source.splitlines():
        if line.startswith(f'| {number} ·'):
            cell = line.split(' | ', 2)[1]
            return cell[1:-1] if single_backtick else cell.strip('`')
    raise AssertionError(f'canonical lint row {number} not found')


def write_files(workspace, files):
    for relative, content in files.items():
        destination = workspace / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding='utf-8')


def brief_base(identity, clause=None, template=None):
    """Shared substitutions only; suites keep their different field/continuation rules."""
    if template is None:
        template = (INSTALL / 'references/task.tmpl.md').read_text()
    text = template.replace('T-0N', identity).replace('t-0n', identity.lower())
    if clause:
        cid, digest = clause
        # Generate the synthetic fixture reference; it is not workspace provenance.
        revision = 'rev 1 ({}-{:02d})'.format('D', 1)
        return (text.replace('{{clause id}}', cid).replace('{{revision}}', revision)
                .replace('{{hash of the exact clause bytes}}', digest))
    return re.sub(r'- \*\*\{\{clause id\}\}.*?\}\}\.\n', '', text, count=1, flags=re.S)


def run_lint_row(root, number, *, slug, source=None, script=False, timeout=10,
                 text=False, env=None):
    command = lint_rows(slug, source)[number]['command']
    if script:
        path = Path(root) / ('row-%02d.sh' % number)
        path.write_bytes(command)
        argv = ['sh', str(path)]
    else:
        argv = ['sh', '-c', command.decode()]
    return subprocess.run(argv, cwd=root, capture_output=True, timeout=timeout,
                          text=text, env=env)
