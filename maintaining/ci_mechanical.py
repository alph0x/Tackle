#!/usr/bin/env python3
"""Run the documented mechanical workflow step at a task boundary."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys

STEP = 'Run the documented mechanical release checks'
TRACE = b'__ci_mechanical_trace__ '


def block(workflow):
    lines = workflow.splitlines()
    matches = []
    scalar_indent = None
    for i, line in enumerate(lines):
        indent = len(line) - len(line.lstrip())
        if scalar_indent is not None:
            if not line.strip() or indent > scalar_indent:
                continue
            if line.lstrip().startswith('#'):
                continue
            scalar_indent = None
        if re.fullmatch(r'\s*- name:\s*' + re.escape(STEP) + r'\s*', line):
            matches.append(i)
        if re.fullmatch(r'\s*(?:-\s+)?[^#:\n]+:\s*[|>](?:[+-]?[1-9]?|[1-9][+-]?)\s*(?:#.*)?', line):
            scalar_indent = indent
    if len(matches) != 1:
        raise ValueError('expected exactly one mechanical workflow step')
    i = matches[0] + 1
    step_indent = len(lines[matches[0]]) - len(lines[matches[0]].lstrip())
    while i < len(lines):
        line = lines[i]
        if line.lstrip().startswith('#'):
            i += 1
            continue
        if line.strip() and len(line) - len(line.lstrip()) <= step_indent:
            break
        match = re.fullmatch(r'(\s*)run:\s*\|[-+]?\s*', line)
        if match and len(match[1]) == step_indent + 2:
            indent = len(match[1])
            result = []
            i += 1
            while i < len(lines):
                line = lines[i]
                if line.strip() and len(line) - len(line.lstrip()) <= indent:
                    break
                result.append(line)
                i += 1
            nonempty = [len(line) - len(line.lstrip()) for line in result if line.strip()]
            if not nonempty:
                raise ValueError('empty mechanical workflow block')
            common = min(nonempty)
            return [line[common:] if line.strip() else '' for line in result]
        i += 1
    raise ValueError('mechanical workflow step has no literal run block')


def tracked_check(check):
    command = ['git', 'ls-files', '-z']
    if check == 'count':
        command += ['--', 'skills/tackle']
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE)
    except FileNotFoundError:
        print('git: not found', file=sys.stderr)
        return 127
    if result.returncode:
        return result.returncode
    paths = [path for path in result.stdout.split(b'\0') if path]
    if check == 'count':
        if len(paths) != 86:
            print(f'expected 86 tracked installable files; found {len(paths)}', file=sys.stderr)
            return 1
    else:
        for path in paths:
            if os.path.basename(path) in (b'tackle', b'tackle-check') and os.path.exists(path):
                print(f'unexpected tracked wrapper: {os.fsdecode(path)}', file=sys.stderr)
                return 1
    return 0


def main():
    parser = argparse.ArgumentParser()
    def path_argument(value):
        if not value:
            raise argparse.ArgumentTypeError('empty path argument: --repo')
        return Path(value)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--repo', type=path_argument)
    mode.add_argument('--tracked-check', choices=('wrappers', 'count'))
    args = parser.parse_args()
    if args.tracked_check:
        return tracked_check(args.tracked_check)
    if not args.repo.is_absolute():
        args.repo = Path(os.path.abspath(args.repo))
    try:
        lines = block((args.repo / '.github/workflows/ci.yml').read_text(encoding='utf-8'))
        script = 'set -eu\n' + '\n'.join(lines) + '\n'
        env = os.environ.copy()
        env['PS4'] = TRACE.decode('ascii')
        result = subprocess.run(['sh', '-x', '-c', script], cwd=args.repo,
                                env=env, stderr=subprocess.PIPE)
        last_command = b''
        for line in result.stderr.splitlines(keepends=True):
            trace = re.match(rb'^_*' + re.escape(TRACE), line)
            if trace:
                last_command = line[trace.end():].rstrip(b'\r\n')
            else:
                sys.stderr.buffer.write(line)
        if result.returncode:
            sys.stderr.buffer.write(b'ci_mechanical: failed (exit %d) at: ' % result.returncode
                                    + last_command + b'\n')
        return result.returncode
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
