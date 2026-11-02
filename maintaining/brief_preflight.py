"""Inspect task scope, linked worktree hygiene and newly committed text."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import textwrap


def git(root, *arguments):
    return subprocess.check_output(['git', '-C', str(root), *arguments], stderr=subprocess.PIPE).decode().strip()


def load(path, name):
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module
    except (Exception, SystemExit) as error:
        raise ValueError('cannot load %s: %s' % (path, error)) from error


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def commands(text, findings):
    blocks = re.findall(r'```[^\n]*\n(.*?)```', text, re.S)
    spans = re.findall(r'(?<!`)`([^`\n]+)`(?!`)', re.sub(r'```[^\n]*\n.*?```', '', text, flags=re.S))
    for line in spans + [line for block in blocks for line in block.splitlines()]:
        try:
            lexer = shlex.shlex(line, posix=True, punctuation_chars=True)
            lexer.whitespace_split = True
            words = list(lexer)
        except ValueError:
            words = line.split()
        if not any(Path(word).name.startswith('python') for word in words):
            continue
        for i, word in enumerate(words):
            if word == '-m' and words[i+1:i+2] == ['unittest']:
                rest = words[i+2:]
                j = 0
                while j < len(rest) and rest[j].startswith('-'):
                    j += 2 if rest[j] == '-k' else 1
                if j < len(rest) and rest[j] != 'discover':
                    findings.append({'kind': 'unittest-path-form', 'detail': line.strip()})
            if word == '--changed':
                following = []
                for item in words[i+1:]:
                    if item.startswith('-') or item in (';', '&&', '|', '>'):
                        break
                    following.append(item)
                if len(following) >= 2:
                    findings.append({'kind': 'changed-several-paths', 'detail': line.strip()})


def main():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers(dest='subcommand', required=True)
    scope = subs.add_parser('scope')
    for name in ('tree', 'workspace', 'brief', 'out'):
        scope.add_argument('--' + name, required=True)
    worktree = subs.add_parser('worktree')
    for name in ('repo', 'tree', 'base', 'out'):
        worktree.add_argument('--' + name, required=True)
    committed = subs.add_parser('committed')
    for name in ('tree', 'base', 'workspace', 'out'):
        committed.add_argument('--' + name, required=True)
    args = parser.parse_args()
    for name in ('tree', 'workspace', 'brief', 'out', 'repo'):
        if hasattr(args, name):
            value = getattr(args, name)
            if not value:
                print('refused: empty path argument: --' + name, file=sys.stderr)
                return 2
            setattr(args, name, value if os.path.isabs(value) else os.path.abspath(value))
    tree, out = Path(args.tree), Path(args.out)
    created = False
    try:
        if out.exists():
            raise ValueError('output already exists')
        if git(tree, 'rev-parse', '--is-inside-work-tree') != 'true':
            raise ValueError('tree is not a git work tree')
        if args.subcommand == 'scope' and git(tree, 'status', '--porcelain'):
            raise ValueError('scope tree is not clean')
        if args.subcommand != 'scope':
            git(Path(args.repo) if args.subcommand == 'worktree' else tree, 'rev-parse', '--verify', args.base + '^{commit}')
        inputs, findings, consumers = {}, [], []
        if args.subcommand in ('scope', 'committed'):
            workspace = Path(args.workspace)
            if not workspace.is_dir() or workspace.parent.name != 'plans' or workspace.parent.parent.name != 'docs':
                raise ValueError('workspace is not a directory under docs/plans')
            repo = workspace.parent.parent.parent
            guard = load(tree / 'eval/rules/committed_text.py', 'preflight_committed_text')
            if not callable(getattr(guard, 'scan_committed_text', None)):
                raise ValueError('committed text guard has no scanner')
        if args.subcommand == 'scope':
            brief = Path(args.brief)
            if not brief.is_file() or not brief.resolve().is_relative_to((workspace / 'tasks').resolve()):
                raise ValueError('brief is not under workspace tasks')
            text = brief.read_text(encoding='utf-8')
            inputs[str(brief)] = digest(brief)
            manifest = json.loads((tree / 'eval/suite-manifest.json').read_text(encoding='utf-8'))
            selection = load(tree / 'eval/check_selection.py', 'preflight_selection')
            selection.validate_baseline(manifest)
            selection.select(tree, manifest, [], 'development')
            if not hasattr(guard, 'ID_PATTERN'):
                raise ValueError('committed text guard has no path pattern')
            guide = (tree / 'skills/tackle/references/guides/verify.md').read_text(encoding='utf-8')
            match = re.search(r'<a id="seal-integrity-command"></a>\s*\n\s*```sh\s*\n(.*?)\n\s*```', guide, re.S)
            if not match:
                raise ValueError('seal block not found')
            seal = textwrap.dedent(match.group(1)).replace('<slug>', workspace.name)
        out.mkdir(parents=True)
        created = True
        if args.subcommand == 'worktree':
            repo = Path(args.repo)
            def common(path):
                result = git(path, 'rev-parse', '--git-common-dir')
                return (path / result).resolve() if not os.path.isabs(result) else Path(result).resolve()
            if common(tree) != common(repo):
                findings.append({'kind': 'not-linked-worktree', 'detail': str(tree)})
            if git(tree, 'rev-parse', 'HEAD') != git(repo, 'rev-parse', '--verify', args.base + '^{commit}'):
                findings.append({'kind': 'head-not-base', 'detail': str(tree)})
            for line in git(tree, 'status', '--porcelain', '--ignored').splitlines():
                findings.append({'kind': 'dirty-or-ignored', 'detail': line})
            if tree.resolve().is_relative_to(repo.resolve()):
                findings.append({'kind': 'inside-repository', 'detail': str(tree)})
        elif args.subcommand == 'committed':
            index = Path(git(tree, 'rev-parse', '--git-path', 'index'))
            if not index.is_absolute():
                index = tree / index
            before = digest(index)
            old = os.environ.get('GIT_INDEX_FILE')
            try:
                with tempfile.TemporaryDirectory(dir=out) as tmp:
                    os.environ['GIT_INDEX_FILE'] = str(Path(tmp) / 'index')
                    git(tree, 'read-tree', 'HEAD')
                    git(tree, 'add', '-N', '--', '.')
                    result = guard.scan_committed_text(tree, args.base, workspace.name)
            finally:
                if old is None:
                    os.environ.pop('GIT_INDEX_FILE', None)
                else:
                    os.environ['GIT_INDEX_FILE'] = old
            if digest(index) != before:
                raise ValueError('real index changed')
            for item in result:
                findings.append({'kind': 'committed-text', 'detail': '%s:%s %s' % (item.path, item.line, item.kind)})
        else:
            entries = re.findall(r'^- \*\*Write scope\*\*:(.*)$', text, re.M)
            paths = []
            if not entries:
                findings.append({'kind': 'write-scope-missing', 'detail': 'no Write scope line'})
            else:
                content = entries[0].strip()
                paths = re.findall(r'`([^`]+)`', content)
                if not paths or content != ', '.join('`' + p + '`' for p in paths):
                    findings.append({'kind': 'write-scope-text', 'detail': content})
            tracked = git(tree, 'ls-files', '-z').split('\0')
            tracked = [p for p in tracked if p and 'heldout' not in Path(p).parts and not re.search(r'eval/scenarios/.*/variants/h\d', p)]
            contents = {}
            for tracked_path in tracked:
                file = tree / tracked_path
                if file.is_symlink():
                    contents[tracked_path] = os.readlink(file).encode()
                elif file.is_file():
                    contents[tracked_path] = file.read_bytes()
            def named(p):
                return p in text or any(p == s.rstrip('/') or s.endswith('/') and p.startswith(s) for s in paths)
            for path in paths:
                files = [p for p in tracked if p.startswith(path)] if path.endswith('/') else [path]
                new = not files if path.endswith('/') else path not in tracked
                result = selection.select(tree, manifest, [path.rstrip('/')], 'development')
                selected = {'families': result['selected'], 'reasons': result['reasons'], 'unknown': result['unknown_paths']}
                suites = [s['path']
                          for s in manifest['suites']
                          if path.startswith(s['path'] + '/') or s['path'].startswith(path.rstrip('/') + '/')
                          or path == s['source'] or path.startswith(s['source'].rstrip('/') + '/')
                          or s['source'].startswith(path.rstrip('/') + '/')]
                pinned, hashes = [], []
                target_hash = hashlib.sha256(contents[path]).hexdigest() if not new and not path.endswith('/') and path in contents else None
                for other in tracked:
                    if other in files:
                        continue
                    data = contents.get(other)
                    if data is None:
                        continue
                    if other.endswith(('.py', '.sh', '.yml', '.yaml')) and path.rstrip('/').encode() in data:
                        pinned.append({'path': other, 'named': named(other)})
                    if target_hash and target_hash.encode() in data:
                        hashes.append({'path': other, 'named': named(other)})
                for consumer in pinned + hashes:
                    if not consumer['named']:
                        findings.append({'kind': 'unnamed-consumer', 'detail': path + ': ' + consumer['path']})
                if guard.ID_PATTERN.search(path) or re.search(r'(?<![A-Za-z0-9_])' + re.escape(workspace.name) + r'(?![A-Za-z0-9_-]|\.[0-9])', path, re.I):
                    findings.append({'kind': 'planned-path-id', 'detail': path})
                is_test = Path(path).name.startswith('test_') and path.endswith('.py')
                if new and is_test and 'eval/suite-manifest.json' not in paths:
                    findings.append({'kind': 'unregistered-test', 'detail': path})
                elif new and not is_test and selected.get('unknown') and 'eval/check-selection.json' not in paths:
                    findings.append({'kind': 'unmapped-path', 'detail': path})
                consumers.append({'path': path, 'new': new, 'files': files, 'selection': selected, 'manifest': suites, 'pinned': pinned, 'hash': hashes})
            commands(text, findings)
            for file in (workspace / 'tasks').glob('*.md'):
                inputs[str(file)] = digest(file)
            contract = workspace / 'design-contract.md'
            if contract.is_file():
                inputs[str(contract)] = digest(contract)
            result = subprocess.run(['/bin/sh', '-c', seal], cwd=repo, capture_output=True)
            (out / 'seal.stdout').write_bytes(result.stdout)
            (out / 'seal.stderr').write_bytes(result.stderr)
            if result.returncode:
                for line in result.stdout.decode(errors='replace').splitlines():
                    findings.append({'kind': 'seal', 'detail': line})
                if not result.stdout:
                    findings.append({'kind': 'seal', 'detail': 'seal command failed'})
        code = int(bool(findings))
        report = {'subcommand': args.subcommand, 'inputs': inputs, 'findings': findings, 'exit': code}
        if args.subcommand == 'scope':
            report['consumers'] = consumers
        (out / 'preflight.json').write_text(json.dumps(report, indent=2) + '\n')
        for finding in findings:
            print('finding: %s: %s' % (finding['kind'], finding['detail']))
        print('preflight: %s findings=%d' % (args.subcommand, len(findings)))
        return code
    except (Exception, SystemExit) as error:
        if created:
            shutil.rmtree(out, ignore_errors=True)
        print('refused: %s' % error, file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
