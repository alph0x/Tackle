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


def _brief_declarations(text):
    lines = text.splitlines(keepends=True)
    offsets = []
    position = 0
    for line in lines:
        offsets.append(position)
        position += len(line)
    offsets.append(position)
    masked = list(lines)

    def mask_line(index):
        masked[index] = ''.join(char if char in '\r\n' else '\x00' for char in lines[index])

    fences = {}
    i = 0
    while i < len(lines):
        opening = re.match(r'^ {0,3}(`{3,}|~{3,})([^\n]*)$', lines[i].rstrip('\r\n'))
        if not opening:
            i += 1
            continue
        marker, info = opening.group(1), opening.group(2).strip()
        char = marker[0]
        closing = re.compile(r'^ {0,3}' + re.escape(char) + r'{' + str(len(marker)) + r',}[ \t]*$')
        j = i + 1
        while j < len(lines) and not closing.match(lines[j].rstrip('\r\n')):
            j += 1
        end = min(j + 1, len(lines))
        for k in range(i, end):
            mask_line(k)
        fences[i] = (end, char, info, j < len(lines), ''.join(lines[i + 1:j]))
        i = end

    declarations = []
    errors = []
    headings = []
    section = 0
    section_bounds = [0]
    label = r'(?:required[ \t]+command|command|check|run)'
    label_re = re.compile(r'^[ \t]{0,3}(?:[-*+][ \t]+)?(?:\*\*[ \t]*(?P<bold>' + label + r')[ \t]*:?[ \t]*\*\*[ \t]*:|\*\*[ \t]*(?P<boldcolon>' + label + r')[ \t]*:[ \t]*\*\*|(?P<plain>' + label + r')[ \t]*:)[ \t]*(?P<rest>.*)$', re.I)
    other_bold = re.compile(r'^[ \t]{0,3}[-*+][ \t]+\*\*')
    inline = re.compile(r'^`([^`\n]+)`(?!`)')
    ordered = re.compile(r'^[ \t]{0,3}\d+[.)][ \t]+(?:(?:[^`\n:]+):[ \t]*)?`([^`\n]+)`(?!`)')
    bare = re.compile(r'^[ \t]{0,3}(?:[-*+][ \t]+)?`([^`\n]+)`(?!`)(.*)$')

    def legacy_python(command):
        return bool(re.match(r'^python3[ \t]+', command) and re.search(r'(?:^|\s)(?:\S+\.py(?:\s|$)|-m\s+\S+)', command))

    def add(start, end, command, suffix='', subjects=None, diagnostic_lines=None):
        declarations.append({
            'start': offsets[start], 'end': offsets[end], 'section': section,
            'line': start + 1, 'command': command, 'suffix': suffix,
            'subjects': subjects if subjects is not None else [command],
            'diagnostic_lines': diagnostic_lines if diagnostic_lines is not None else [command],
        })

    i = 0
    while i < len(lines):
        line = lines[i].rstrip('\r\n')
        if i in fences:
            end, char, info, complete, body = fences[i]
            special = bool(headings and headings[-1][1])
            shell = info in ('sh', 'shell', 'bash', 'zsh')
            if char == '~' and shell and special:
                errors.append({'kind': 'command-binding', 'detail': 'line %d: tilde shell fence is not admitted' % (i + 1)})
            elif char == '`' and shell and complete:
                script = body.strip()
                physical = body.splitlines()
                logical = []
                pending = []
                for part in physical:
                    pending.append(part)
                    if not part.rstrip().endswith('\\'):
                        logical.append('\n'.join(pending))
                        pending = []
                if pending:
                    logical.append('\n'.join(pending))
                candidates = [part.strip() for part in logical if part.strip() and not part.lstrip().startswith('#')]
                subjects = [part for part in candidates if legacy_python(part)]
                add(i, end, script, subjects=subjects or [script], diagnostic_lines=candidates)
            i = end
            continue
        heading = re.match(r'^ {0,3}(#{1,6})[ \t]+(.*?)[ \t]*$', line)
        if heading:
            level = len(heading.group(1))
            title = re.sub(r'[ \t]+#+[ \t]*$', '', heading.group(2))
            title = re.sub(r'[ \t]*<!--[\s\S]*?-->[ \t]*$', '', title)
            title = re.sub(r'^\s*\d+(?:\.\d+)*[.)]?[ \t]+', '', title).strip()
            while headings and headings[-1][0] >= level:
                headings.pop()
            family = None
            if re.fullmatch(r'acceptance and recovery(?:\s*:\s*.*)?', title, re.I):
                family = 'acceptance'
            elif re.fullmatch(r'required (?:mechanical )?checks?(?:\s*:\s*.*)?', title, re.I):
                family = 'required'
            elif headings:
                family = headings[-1][1]
            headings.append((level, family))
            section += 1
            section_bounds.append(offsets[i])
            i += 1
            continue
        if re.match(r'^(?: {4}|\t)', line):
            mask_line(i)
            i += 1
            continue
        family = headings[-1][1] if headings else None
        match = label_re.match(line)
        if match:
            rest = match.group('rest')
            command = inline.match(rest)
            if command:
                add(i, i + 1, command.group(1), rest[command.end():])
                mask_line(i)
            elif re.match(r'^review\s*:', rest, re.I) and (match.group('bold') or match.group('boldcolon') or match.group('plain')).lower() == 'check':
                pass
            elif not rest.strip():
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                fence = fences.get(j)
                if not fence or fence[1] != '`' or fence[2] not in ('sh', 'shell', 'bash', 'zsh') or not fence[3]:
                    errors.append({'kind': 'command-binding', 'detail': 'line %d: command introducer requires a complete shell fence' % (i + 1)})
                mask_line(i)
            else:
                errors.append({'kind': 'command-binding', 'detail': 'line %d: invalid command declaration' % (i + 1)})
            i += 1
            continue
        if other_bold.match(line):
            i += 1
            continue
        match = ordered.match(line) if family else None
        if match:
            add(i, i + 1, match.group(1), line[match.end():])
            mask_line(i)
            i += 1
            continue
        match = bare.match(line)
        if match:
            command, suffix = match.group(1), match.group(2)
            bullet = bool(re.match(r'^[ \t]{0,3}[-*+][ \t]+', line))
            if family == 'required' or (not suffix.strip() and ((bullet and family) or legacy_python(command))):
                add(i, i + 1, command, suffix)
                mask_line(i)
        i += 1
    section_bounds.append(len(text))
    return declarations, errors, ''.join(masked), section_bounds


def command_bindings(text, findings):
    if not re.search(r'(?im)^\s*[-*]\s*\*\*Detail\*\*\s*:\s*full\s*$', text):
        return
    declarations, errors, prose, bounds = _brief_declarations(text)
    findings.extend(errors)

    def paragraphs(value):
        parts = []
        for part in re.split(r'\n\s*\n', value):
            cleaned = part.replace('\x00', '').strip()
            if cleaned:
                parts.append(cleaned)
        return parts

    shared_prose = list(prose)
    for item in declarations:
        suffix = item['suffix']
        if suffix:
            line_end = item['start'] + len(text[item['start']:item['end']].rstrip('\r\n'))
            shared_prose[line_end - len(suffix):line_end] = suffix
    shared = '\n\n'.join(part for part in paragraphs(''.join(shared_prose)) if re.search(r'(?i)\bcommon\b|\ball required mechanical checks\b|\b(?:default )?(?:cwd|working directory) for every command\b', part))

    def applicable(value, command):
        result = []
        for paragraph in paragraphs(value):
            scopes = re.findall(r'(?i)\bfor\s+`([^`]+)`\s+only\s*:', paragraph)
            if scopes and any(scope != command for scope in scopes):
                continue
            result.append(paragraph)
        return '\n\n'.join(result)

    def has_cwd(value):
        for line in value.splitlines():
            match = re.search(r'(?i)\b(?:cwd|working directory)\b', line)
            if not match:
                continue
            tail = line[match.end():]
            if re.search(r'(?i)\b(?:not supplied|not specified|not provided|unknown|tbd|none)\b', tail):
                continue
            if re.search(r'`[^`\n]+`|(?:^|[\s:])(?:/|\./|\.\./)\S+', tail):
                return True
            if re.search(r'(?i)(?:\*\*)?\s*:\s*[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*\s*[.;]?\s*$', tail):
                return True
        return False

    def has_pass(value):
        return bool(re.search(r'(?i)\b(?:native pass condition|require[sd]?|pass(?:es|ing)?)\b[^\n]*(?:\b(?:exit(?:\s+status)?|return code)\s*\d+\b|\b(?:command\s+)?exits?\s+successfully\b)', value))

    def words_for(command):
        try:
            return shlex.split(command)
        except ValueError:
            return command.split()

    def command_path(command):
        words = words_for(command)
        scripts = [word for word in words if word.endswith(('.py', '.sh'))]
        return scripts[-1] if scripts else words[0] if words else ''

    names = [Path(command_path(subject)).stem for item in declarations for subject in item['subjects']]

    def has_evidence(value, command):
        evidence = r'(?i)\b(?:evidence destination|observe[dr]?|observer|record(?:s|ed)?|evidence suffix(?:es)?)\b[^\n]*(?:`[^`]+`|/\S+|\bsuffix(?:es)?\b)'
        root = r'(?i)\b(?:evidence\s+)?records?\s+root\b'
        for line in value.splitlines():
            for part in line.split(';'):
                if re.search(evidence, part) and not re.search(root, part):
                    return True
            if not re.search(root, line) or not re.search(evidence, line):
                continue
            path = command_path(command)
            name = Path(path).stem if path else ''
            if not name or names.count(name) != 1:
                continue
            mappings = re.findall(r'(?i)(?<![\w./-])`?([\w./-]+)`?\s+uses\s+`?([\w][\w./-]*)`?', line)
            if mappings:
                matches = [record.rstrip('.') for key, record in mappings if key in (name, Path(path).name)]
                if len(matches) == 1 and sum(record.rstrip('.') == matches[0] for _, record in mappings) == 1:
                    return True
                continue
            records = re.search(r'(?i)\bwith\b(.*?)\brecords\b', line)
            if records and re.search(r'(?<![\w-])' + re.escape(name) + r'(?![\w-])', records.group(1)):
                return True
        return False

    for index, item in enumerate(declarations):
        section = item['section']
        previous_item = next((other for other in reversed(declarations[:index]) if other['section'] == section and other['end'] <= item['start']), None)
        previous = previous_item['end'] if previous_item else bounds[section]
        following = next((other['start'] for other in declarations[index + 1:] if other['section'] == section and other['start'] >= item['end']), bounds[section + 1])
        before_prose = prose[previous:item['start']]
        before = paragraphs(before_prose)
        if (previous_item
                and '\n' not in text[previous_item['start']:previous_item['end']].rstrip('\r\n')
                and not re.match(r'[ \t]*\r?\n', before_prose)):
            before = before[1:]
        after = paragraphs(prose[item['end']:following])
        context = '\n\n'.join((shared, before[-1] if before else '', item['suffix'], after[0] if after else ''))
        for subject in item['subjects']:
            local = applicable(context, subject)
            missing = [name for name, present in (('cwd', has_cwd(local)), ('native pass', has_pass(local)), ('evidence', has_evidence(local, subject))) if not present]
            if missing:
                findings.append({'kind': 'command-binding', 'detail': 'line %d: %s: missing %s' % (item['line'], subject, ', '.join(missing))})


def commands(text, findings):
    command_bindings(text, findings)
    if re.search(r'(?im)^\s*[-*]\s*\*\*Detail\*\*\s*:\s*full\s*$', text):
        declarations, _, _, _ = _brief_declarations(text)
        candidates = [line for item in declarations for line in item['diagnostic_lines']]
    else:
        blocks = re.findall(r'```[^\n]*\n(.*?)```', text, re.S)
        spans = re.findall(r'(?<!`)`([^`\n]+)`(?!`)', re.sub(r'```[^\n]*\n.*?```', '', text, flags=re.S))
        candidates = spans + [line for block in blocks for line in block.splitlines()]
    for line in candidates:
        try:
            lexer = shlex.shlex(line, posix=True, punctuation_chars=True)
            lexer.whitespace_split = True
            words = list(lexer)
        except ValueError:
            words = line.split()
        if not any(Path(word).name.startswith('python') for word in words):
            continue
        for i, word in enumerate(words):
            if word == '-m' and words[i + 1:i + 2] == ['unittest']:
                rest = words[i + 2:]
                j = 0
                while j < len(rest) and rest[j].startswith('-'):
                    j += 2 if rest[j] == '-k' else 1
                if j < len(rest) and rest[j] != 'discover':
                    findings.append({'kind': 'unittest-path-form', 'detail': line.strip()})
            if word == '--changed':
                following = []
                for candidate in words[i + 1:]:
                    if candidate.startswith('-') or candidate in (';', '&&', '|', '>'):
                        break
                    following.append(candidate)
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
