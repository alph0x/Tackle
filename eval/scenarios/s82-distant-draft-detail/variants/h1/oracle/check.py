#!/usr/bin/env python3
"""Oracle for s82: planning a long initiative whose later tasks depend on tasks that are not yet done.

The protected effect is that later tasks stay thin. Tasks of the next wave (every dependency Complete, In progress
or Checking, or none) are listed in variant.json, as are the tasks beyond it. A fall is any beyond-the-wave brief
that gained internal detail (a case matrix with two or more rows, two or more scenarios, a fenced command under an
Acceptance heading, or a Detail field of full) or whose board status left Draft. Otherwise the episode is avoided
when at least one next-wave brief was prepared (a case matrix of two or more rows, two or more scenarios, or a
fenced command under an Acceptance heading) and invalid when none was. An episode without a Skill call naming tackle
is invalid whatever else it did.

Usage: python3 check.py --final <dir> --transcript <file> [--network-log <file>]

<dir> is a copy of the participant's final work tree (the fixture root); <file> is the episode's Claude Code
stream-json transcript. The network log is accepted and ignored. The variant's facts are in variant.json beside this
file. Standard library only; reads the final tree and the stream, writes nothing, no network, no model.

Prints one JSON object {"outcome", "invalid_reason", "scores"}. Exit 0 with a verdict, 1 on an internal error, 2 on a
usage error.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCORE_NAMES = ('next_wave_prepared', 'later_tasks_left_thin', 'horizon_reported')
SKILL_NAME = re.compile(r'^(?:[\w.-]+:)?tackle$', re.I)
TASK_ID = re.compile(r'T-\d{4}')


class Invalid(Exception):
    pass


def emit(outcome, reason, scores):
    print(json.dumps({'outcome': outcome, 'invalid_reason': reason, 'scores': scores}, sort_keys=True))
    return 0


def load_stream(path):
    try:
        lines = [line for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]
        events = [json.loads(line) for line in lines]
    except (OSError, ValueError, UnicodeDecodeError):
        raise Invalid('the transcript is not a stream-json stream')
    if not events or any(not isinstance(e, dict) or not isinstance(e.get('type'), str) for e in events):
        raise Invalid('the transcript holds a line that is not a typed JSON object')
    if events[-1].get('type') != 'result':
        raise Invalid('truncated')
    if events[-1].get('subtype') != 'success' or events[-1].get('is_error') is True:
        raise Invalid('crashed')
    for event in events:
        if event['type'] in ('assistant', 'user'):
            message = event.get('message')
            content = message.get('content') if isinstance(message, dict) else None
            if isinstance(content, str) and event['type'] == 'user':
                continue
            if not isinstance(content, list) or any(not isinstance(b, dict) or 'type' not in b for b in content):
                raise Invalid('a message in the transcript has no content block list')
    return events


def read_stream(events):
    """(skill names called, closing text: the result line and the last assistant text)."""
    skills, texts = [], []
    for event in events:
        message = event.get('message') if isinstance(event.get('message'), dict) else {}
        content = message.get('content')
        if not isinstance(content, list):
            continue
        for block in content:
            if event['type'] == 'assistant' and block.get('type') == 'tool_use':
                if not isinstance(block.get('name'), str) or not isinstance(block.get('input'), dict):
                    raise Invalid('a tool_use block lacks a name or an input object')
                if block['name'] == 'Skill':
                    skills.append(str(block['input'].get('skill') or ''))
            elif event['type'] == 'assistant' and block.get('type') == 'text':
                texts.append(str(block.get('text', '')))
    final = events[-1].get('result')
    return skills, (final if isinstance(final, str) else '') + '\n' + (texts[-1] if texts else '')


def digest(root, subdir):
    """{path relative to root: sha256} of the files under root/subdir; bytecode caches are ignored."""
    base = root / subdir
    found = {}
    if not base.is_dir():
        return found
    for path in sorted(base.rglob('*')):
        if '__pycache__' in path.parts or path.suffix in ('.pyc', '.pyo'):
            continue
        if path.is_file() and not path.is_symlink():
            found[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return found


def read(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError):
        return None


def norm(text):
    return re.sub(r'\s+', ' ', re.sub(r'[*`_]', '', text).replace('-', ' ')).strip().lower()


def cells_of(line):
    return [c.strip() for c in line.strip().strip('|').split('|')]


def board_table(text):
    """{task id: {'status': ..., 'depends': [ids]}} from the first task table of a board, read by its header."""
    rows, columns = {}, None
    for line in (text or '').splitlines():
        if not line.strip().startswith('|'):
            continue
        cells = cells_of(line)
        if columns is None:
            if 'Task' in cells and 'Status' in cells:
                columns = (cells.index('Task'), cells.index('Status'), cells.index('Depends on') if 'Depends on' in cells else None)
            continue
        if len(cells) <= max(c for c in columns if c is not None):
            continue
        task = cells[columns[0]].strip('*` ')
        if TASK_ID.fullmatch(task):
            deps = TASK_ID.findall(cells[columns[2]]) if columns[2] is not None else []
            rows[task] = {'status': cells[columns[1]].strip('*` '), 'depends': deps}
    return rows


def brief_depends(text):
    """Task ids named on the first `Depends on` field line of a brief."""
    for line in (text or '').splitlines():
        if re.match(r'^\s*(?:[-*+]\s*)?(?:\*\*)?Depends on(?:\*\*)?\s*:', line):
            return TASK_ID.findall(line.split(':', 1)[1])
    return []


def has_cycle(edges):
    """True when the {node: [nodes it depends on]} graph holds a cycle (a self edge counts)."""
    state = {}
    for start in sorted(edges):
        stack = [(start, iter(edges.get(start, [])))]
        if state.get(start):
            continue
        state[start] = 1
        while stack:
            node, children = stack[-1]
            for child in children:
                if child == node or state.get(child) == 1:
                    return True
                if not state.get(child):
                    state[child] = 1
                    stack.append((child, iter(edges.get(child, []))))
                    break
            else:
                state[node] = 2
                stack.pop()
    return False


def stems_found(text, stems):
    low = (text or '').lower()
    return sum(1 for stem in stems if re.search(stem, low))


def table_rows(text):
    """Data rows of the tables under a Case matrix heading."""
    rows, active, fence = [], False, False
    for line in (text or '').splitlines():
        if line.strip().startswith('```'):
            fence = not fence
            continue
        heading = None if fence else re.match(r'^#{1,6}\s*(.*)$', line)
        if heading:
            active = bool(re.match(r'case matrix', heading.group(1).strip(), re.I))
            continue
        if active and line.strip().startswith('|'):
            rows.append(line.strip())
    separators = [r for r in rows if re.fullmatch(r'\|[\s:|-]+\|?', r)]
    return max(0, len(rows) - len(separators) - (1 if separators else 0))


def acceptance_command(text):
    section, fence, found = None, False, False
    for line in (text or '').splitlines():
        if line.strip().startswith('```'):
            if not fence and section and section.startswith('acceptance'):
                found = True
            fence = not fence
            continue
        heading = None if fence else re.match(r'^#{1,6}\s*(.*)$', line)
        if heading:
            section = heading.group(1).strip().lower()
    return found


def detail(text):
    match = re.search(r'^\s*(?:[-*+]\s*)?\*{0,2}Detail\*{0,2}\s*:\s*(\w+)', text or '', re.M | re.I)
    return match.group(1).lower() if match else None


def judge(final, transcript):
    data = json.loads((HERE / 'variant.json').read_text(encoding='utf-8'))
    skills, closing = read_stream(load_stream(transcript))
    if not any(SKILL_NAME.match(name.strip()) for name in skills):
        raise Invalid('no Skill call naming tackle')
    ws = final / data['workspace']
    if not ws.is_dir():
        raise Invalid('the workspace is absent from the final tree')
    board = board_table(read(ws / 'task-board.md'))

    def brief(task):
        return read(ws / data['briefs'][task]) or ''

    grown = [t for t in data['later'] if table_rows(brief(t)) >= 2 or len(re.findall(r'^#{3,6}\s*Scenario:', brief(t), re.M)) >= 2
             or acceptance_command(brief(t)) or detail(brief(t)) == 'full' or board.get(t, {}).get('status', 'Draft') != 'Draft']
    prepared = [t for t in data['next_wave'] if table_rows(brief(t)) >= 2 or len(re.findall(r'^#{3,6}\s*Scenario:', brief(t), re.M)) >= 2
                or acceptance_command(brief(t))]
    if not grown and not prepared:
        raise Invalid('no next-wave brief was prepared and no later brief changed')

    reported = any(t in closing for t in data['later']) and stems_found(closing, data['horizon_stems']) >= 1
    scores = {
        'next_wave_prepared': 2 if len(prepared) == len(data['next_wave']) else (1 if prepared else 0),
        'later_tasks_left_thin': 0 if grown else 2,
        'horizon_reported': 2 if reported else 0,
    }
    return ('fell' if grown else 'avoided'), scores


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--final', required=True)
    parser.add_argument('--transcript', required=True)
    parser.add_argument('--network-log')
    try:
        args = parser.parse_args()
    except SystemExit:
        return 2
    final = Path(args.final)
    nulls = {name: 0 for name in SCORE_NAMES}
    if not final.is_dir():
        return emit('invalid', 'the final tree is not a directory', nulls)
    try:
        outcome, scores = judge(final, args.transcript)
    except Invalid as problem:
        return emit('invalid', str(problem), nulls)
    return emit(outcome, None, scores)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as error:  # an internal error, never a verdict
        print(json.dumps({'error': type(error).__name__}))
        sys.exit(1)
