"""Validate model identity, tool use and write confinement in a role transcript."""
import argparse
import json
import os
import re
import shlex
import sys

FORBIDDEN_PATH = re.compile(r'/heldout(/|\b)|variants/h\d|\.tackle/secrets|\.codex/auth\.json')
NETWORK_EXECUTABLES = {'curl', 'wget', 'nc', 'ncat', 'ssh', 'scp', 'rsync'}
GIT_NETWORK = {'push', 'fetch', 'pull', 'clone'}
ASSIGNMENT = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*=')
SHELL_TOKEN = re.compile(
    r"""(?P<space>[ \t\r]+)|(?P<redirect>[0-9]*(?:<<<|<<-|<<|>>|<>|>&|<&|>|<))"""
    r"""|(?P<operator>&&|\|\||;;&|;;|;&|\|&|[;&|()\n])"""
    r"""|(?P<word>(?:[^\s;&|()<>'"\\]+|\\.|'[^']*'|"(?:\\.|[^"\\])*")+)""")


def shell_continuations(command):
    """Remove escaped newlines outside single quotes and shell comments."""
    result = []
    quote = None
    in_word = False
    i = 0
    while i < len(command):
        char = command[i]
        if quote is None and not in_word and char == '#':
            end = command.find('\n', i)
            if end < 0:
                result.append(command[i:])
                break
            result.append(command[i:end])
            i = end
            continue
        if char == '\\' and quote != "'":
            if i + 1 < len(command):
                following = command[i + 1]
                if following != '\n':
                    result.extend((char, following))
                    in_word = True
                i += 2
                continue
        elif char in ("'", '"'):
            if quote is None:
                quote = char
                in_word = True
            elif quote == char:
                quote = None
        elif quote is None:
            in_word = char not in ' \t\r\n;&|()<>'
        result.append(char)
        i += 1
    return ''.join(result)


def shell_tokens(command):
    """Retain the distinction between shell operators and quoted word data."""
    command = shell_continuations(command)
    result = []
    position = 0
    while position < len(command):
        if command[position] == '#':
            end = command.find('\n', position)
            position = len(command) if end < 0 else end
            continue
        match = SHELL_TOKEN.match(command, position)
        if match is None:
            raise ValueError('invalid shell word')
        position = match.end()
        kind = match.lastgroup
        if kind == 'space':
            continue
        raw = match.group()
        if kind == 'word':
            decoded = shlex.split(raw, comments=False, posix=True)
            if len(decoded) != 1:
                raise ValueError('invalid shell word')
            result.append((kind, decoded[0], raw))
        else:
            result.append((kind, raw, raw))
    return result


def shell_operations(command):
    """Identify direct executables without executing or expanding shell input."""
    try:
        tokens = shell_tokens(command)
    except ValueError:
        return {'unparsable'}
    # Redirection targets are data, including those before the command name.
    words = []
    i = 0
    while i < len(tokens):
        kind, value, raw = tokens[i]
        if kind == 'redirect':
            if i + 1 == len(tokens) or tokens[i + 1][0] != 'word':
                return {'unparsable'}
            i += 2
            continue
        words.append((kind, value, raw))
        i += 1
    operations = set()
    start = 0
    keywords = ('if', 'then', 'else', 'elif', 'while', 'until', 'do', '!', '{', '}')
    while start < len(words):
        while start < len(words) and (words[start][0] == 'operator'
                                      or words[start][1] in keywords and words[start][2] == words[start][1]):
            start += 1
        end = start
        while end < len(words) and words[end][0] != 'operator':
            end += 1
        segment = [word[1] for word in words[start:end]]
        start = end + 1
        i = 0
        while i < len(segment) and ASSIGNMENT.match(segment[i]):
            i += 1
        while i < len(segment) and os.path.basename(segment[i]) in ('env', 'command', 'exec'):
            wrapper = os.path.basename(segment[i])
            i += 1
            while i < len(segment):
                word = segment[i]
                if ASSIGNMENT.match(word):
                    i += 1
                elif word == '--':
                    i += 1
                    break
                elif word.startswith('-'):
                    i += 2 if wrapper == 'env' and word in ('-u', '--unset', '-C', '--chdir') else 1
                else:
                    break
        if i >= len(segment):
            continue
        executable = os.path.basename(segment[i])
        if executable in NETWORK_EXECUTABLES:
            operations.add('network')
        elif executable == 'graft':
            operations.add('graft')
        elif executable == 'git':
            i += 1
            while i < len(segment):
                word = segment[i]
                if word in ('-C', '-c', '--git-dir', '--work-tree', '--namespace', '--config-env'):
                    i += 2
                elif word.startswith('-'):
                    i += 1
                else:
                    if word in GIT_NETWORK:
                        operations.add('network')
                    break
    return operations


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('session')
    parser.add_argument('--model', required=True)
    parser.add_argument('--effort', required=True)
    parser.add_argument('--agent', required=True)
    parser.add_argument('--write-root', action='append', default=[])
    parser.add_argument('--forbid-forwarding', action='store_true')
    args = parser.parse_args()
    if not args.session or any(not root for root in args.write_root):
        print(json.dumps({'error': 'empty path argument'}))
        return 2
    args.session = args.session if os.path.isabs(args.session) else os.path.abspath(args.session)
    args.write_root = [os.path.normpath(p if os.path.isabs(p) else os.path.abspath(p)) for p in args.write_root]
    try:
        with open(args.session, encoding='utf-8') as stream:
            lines = [json.loads(line) for line in stream if line.strip()]
        if not all(isinstance(e, dict) for e in lines) or not any(e.get('type') == 'session' for e in lines):
            raise ValueError('no session entry')
    except (OSError, ValueError) as error:
        print(json.dumps({'error': str(error)}))
        return 2
    cwd = next((e.get('cwd') for e in lines if e.get('type') == 'session' and isinstance(e.get('cwd'), str)), None)
    model = effort = agent = None
    models = efforts = inits = 0
    tools, problems, forwarded = {}, [], []
    tokens = dict.fromkeys(('input', 'output', 'cacheRead', 'cacheWrite'), 0)
    usd = 0.0
    for entry in lines:
        kind = entry.get('type')
        if kind == 'session_init':
            inits += 1
            agent = entry.get('agent')
            if agent != args.agent:
                problems.append('agent %r, expected %r' % (agent, args.agent))
            if entry.get('resolvedModel') != args.model + ':' + args.effort:
                problems.append('resolved model %r' % entry.get('resolvedModel'))
        if kind == 'model_change':
            models += 1
            model = entry.get('model')
            if model != args.model:
                problems.append('model %r, expected %r' % (model, args.model))
            if entry.get('resolvedModelIsFallback') is True:
                problems.append('fallback model')
        if kind == 'thinking_level_change':
            efforts += 1
            effort = entry.get('thinkingLevel')
            if effort != args.effort:
                problems.append('effort %r, expected %r' % (effort, args.effort))
        message = entry.get('message') if isinstance(entry.get('message'), dict) else {}
        if message.get('role') == 'assistant' and message.get('provider', '') + '/' + message.get('model', '') != args.model:
            problems.append('assistant turn on %s/%s' % (message.get('provider'), message.get('model')))
        usage = message.get('usage') if isinstance(message.get('usage'), dict) else None
        if usage:
            for key in tokens:
                tokens[key] += int(usage.get(key) or 0)
            usd += float((usage.get('cost') or {}).get('total') or 0)
        for part in message.get('content') or []:
            if not isinstance(part, dict) or part.get('type') != 'toolCall':
                continue
            name, arguments = str(part.get('name')), part.get('arguments') or {}
            tools[name] = tools.get(name, 0) + 1
            if 'graft' in name.lower():
                problems.append('graft tool call: ' + name)
            if name in ('task', 'eval'):
                problems.append('forbidden tool: ' + name)
            if name in ('find', 'web_search'):
                forwarded.append(name)
            if name == 'web_search':
                problems.append('network tool: web_search')
            paths = []
            if name == 'edit':
                body = str(arguments.get('input', ''))
                paths = re.findall(r'^\[(.+?)#[0-9A-Fa-f]{4}\]\s*$', body, re.M)
                paths += [p.strip().strip('"\'') for p in re.findall(r'^MV (.+)$', body, re.M)]
            elif name == 'write':
                paths = [str(arguments.get('path', ''))]
            filtered = dict(arguments)
            if name in ('grep', 'glob', 'find') and isinstance(filtered.get('path'), str):
                filtered['path'] = ';'.join(p for p in filtered['path'].split(';') if not p.strip().startswith('!'))
            inspected = paths if name in ('write', 'edit') else filtered
            if FORBIDDEN_PATH.search(json.dumps(inspected)):
                problems.append('forbidden path in %s arguments' % name)
            for key in ('path', 'url'):
                if isinstance(filtered.get(key), str) and any(p.strip().startswith(('http://', 'https://')) for p in filtered[key].split(';')):
                    problems.append('network read in ' + name)
            command = str(arguments.get('command', '')) if name == 'bash' else ''
            operations = shell_operations(command) if command else set()
            if 'network' in operations or 'unparsable' in operations:
                problems.append('network command: ' + command[:120])
            if 'graft' in operations:
                problems.append('graft command: ' + command[:120])
            if name in ('write', 'edit'):
                if name == 'edit' and not paths:
                    problems.append('edit without a parsable target path')
                for path in paths:
                    if name == 'write' and path.startswith('agent://'):
                        continue
                    if path.startswith(('xd://', 'local://')):
                        problems.append('%s to an internal URL: %s' % (name, path))
                        continue
                    if not os.path.isabs(path):
                        if not cwd or not os.path.isabs(cwd):
                            problems.append('%s with a relative path and no session cwd: %s' % (name, path))
                            continue
                        path = os.path.join(cwd, path)
                    path = os.path.normpath(path)
                    if not any(path == root or path.startswith(root.rstrip('/') + '/') for root in args.write_root):
                        problems.append('%s outside the write roots: %s' % (name, path))
    if not models:
        problems.append('no model change recorded')
    if not efforts:
        problems.append('effort None, expected %r' % args.effort)
    if not inits:
        problems.append('no session_init entry')
    if forwarded and args.forbid_forwarding:
        problems.append('tool(s) forwarding context to another model: ' + ', '.join(sorted(set(forwarded))))
    print(json.dumps({'model': model, 'effort': effort, 'agent': agent, 'tools': tools, 'tokens': tokens, 'usd': round(usd, 6), 'forwarded': len(forwarded), 'problems': problems}))
    return int(bool(problems))


if __name__ == '__main__':
    sys.exit(main())
