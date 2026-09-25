"""A scripted stand-in for a host CLI, used by the harness tests and the fake adapter.

Usage: fake-agent --session <id> [--model <m>] [--effort <e>] [--skills <dir under HOME>] <prompt>

Each prompt line ``fake: <action> ...`` is one scripted action, run in order:
  write <path> <text>           write the text and a newline to a work-tree file
  write-home <path> <text>      the same under HOME
  read <path>                   emit the file's text
  env <path>                    write the environment as JSON to a work-tree file
  pid <path>                    write this process id to a work-tree file
  sleep <seconds>               sleep
  usage <in> <out>              report token usage in the result event
  say <text>                    emit a message event
  raw <text>                    print the text as a raw stdout line
  skill                         emit a skill-load event whether or not a skill is installed
  dispatch <role> <tier> <path> run ``tackle-dispatch`` with a work-tree prompt file
  exit <code>                   exit with that code after the result event
Without a ``skill`` line, an installed skill (HOME/<skills>/tackle/SKILL.md) is loaded when the prompt
names a planning, execution or status intent in English or Spanish. Events are JSON lines on stdout; the
last one is ``result``. The fake reads nothing outside its work tree and HOME.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

TRIGGER = re.compile(r'\b(plan|plans|planning|run|status|planific\w*|ejecut\w*|estado)\b', re.I)


def emit(event):
    print(json.dumps(event), flush=True)


def main(argv):
    parser = argparse.ArgumentParser(prog='fake-agent')
    parser.add_argument('--session', required=True)
    parser.add_argument('--model', default='n/a')
    parser.add_argument('--effort', default='n/a')
    parser.add_argument('--skills', default='.fake/skills')
    parser.add_argument('prompt')
    args = parser.parse_args(argv)
    home = Path(os.environ.get('HOME', '.'))
    emit({'type': 'start', 'session': args.session, 'cwd': os.getcwd(), 'home': str(home), 'model': args.model,
          'effort': args.effort})
    lines = [line[len('fake:'):].strip() for line in args.prompt.splitlines() if line.startswith('fake:')]
    skill = home / args.skills / 'tackle' / 'SKILL.md'
    if 'skill' not in lines and skill.is_file() and TRIGGER.search(args.prompt):
        emit({'type': 'tool', 'name': 'read'})
        emit({'type': 'skill', 'name': 'tackle', 'path': str(skill)})
    usage, tools, code = None, 0, 0
    for line in lines:
        action, _, rest = line.partition(' ')
        if action in ('write', 'write-home', 'read', 'env', 'pid', 'dispatch'):
            tools += 1
            emit({'type': 'tool', 'name': action})
        if action in ('write', 'write-home'):
            name, _, text = rest.partition(' ')
            target = (home if action == 'write-home' else Path.cwd()) / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text + '\n')
        elif action == 'read':
            emit({'type': 'read', 'path': rest, 'text': Path(rest).read_text()})
        elif action == 'env':
            Path(rest).write_text(json.dumps(dict(os.environ), sort_keys=True))
        elif action == 'pid':
            Path(rest).write_text(str(os.getpid()))
        elif action == 'sleep':
            time.sleep(float(rest))
        elif action == 'usage':
            given, produced = rest.split()
            usage = {'input_tokens': int(given), 'output_tokens': int(produced)}
        elif action == 'say':
            emit({'type': 'message', 'text': rest})
        elif action == 'raw':
            print(rest, flush=True)
        elif action == 'skill':
            emit({'type': 'skill', 'name': 'tackle', 'path': str(skill)})
        elif action == 'dispatch':
            role, tier, prompt = rest.split()
            try:
                child = subprocess.run(['tackle-dispatch', '--role', role, '--tier', tier, '--prompt-file',
                                        str(Path.cwd() / prompt)], capture_output=True, text=True)
                emit({'type': 'dispatch', 'role': role, 'exit': child.returncode, 'output': child.stdout})
            except OSError as problem:
                emit({'type': 'dispatch', 'role': role, 'exit': None, 'error': problem.__class__.__name__})
        elif action == 'exit':
            code = int(rest)
    result = {'type': 'result', 'session_id': 'fake-%s' % args.session, 'tool_calls': tools}
    if usage is not None:
        result['usage'] = usage
    emit(result)
    return code


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
