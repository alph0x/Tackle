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
    matches = [i for i, line in enumerate(lines)
               if re.fullmatch(r'\s*- name:\s*' + re.escape(STEP) + r'\s*', line)]
    if len(matches) != 1:
        raise ValueError('expected exactly one mechanical workflow step')
    i = matches[0] + 1
    step_indent = len(lines[matches[0]]) - len(lines[matches[0]].lstrip())
    while i < len(lines):
        line = lines[i]
        if line.strip() and len(line) - len(line.lstrip()) <= step_indent:
            break
        match = re.fullmatch(r'(\s*)run:\s*\|[-+]?\s*', line)
        if match:
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', required=True, type=Path)
    args = parser.parse_args()
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
