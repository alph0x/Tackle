"""Content-blind ordering check for a resume episode: did the transcript reconcile the workspace's own
task-board.md and history.md before the first call that carries out the variant's own declared
remaining-work action?

Usage: python3 eval/behavior/judges/resume/order_check.py --repo <dir> --scenario <id> --variant <id> \\
           --transcript <file>

Prints exactly one line, one of ``ordered``, ``unordered`` or ``n/a no-marker``, and exits 0. A refusal
(unknown variant, missing or malformed order.json, --repo not a git work tree, or an unreadable
transcript) prints ``order_check: refused: <reason>`` to stderr and exits 2; a usage error also exits 2.
Output never holds a scanned field's value, a marker's match string, or any other transcript content.

The declared markers come from ``eval/scenarios/<scenario>/variants/<variant>/hidden/order.json``, read
from the git index of --repo -- never the working tree -- the same way judge.py's own hidden_files reads
the rest of hidden/. The transcript walk imports ``events_of`` and ``tool_uses`` from subagent.py as a
read-only library dependency; this module never edits subagent.py.

See eval/behavior/judges/resume/README.md. Standard library only; Python 3.10 or later.
"""
import argparse
import copy
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'eval' / 'behavior' / 'harness'))
from subagent import events_of, tool_uses  # noqa: E402  (a read-only library import, never edited)

SCHEMA = 'tackle-resume-order/1'
ALLOWED_MARKER_TOOLS = ('Bash', 'Write', 'Edit', 'MultiEdit', 'NotebookEdit')
SCANNED_FIELD = {'Read': 'file_path', 'Write': 'file_path', 'Edit': 'file_path', 'MultiEdit': 'file_path',
                 'NotebookEdit': 'notebook_path', 'Grep': 'path', 'Bash': 'command'}
BOARD_NAME, HISTORY_NAME = 'task-board.md', 'history.md'


class Refusal(Exception):
    pass


def git(repo, *args):
    try:
        return subprocess.run(['git', '-C', str(repo)] + list(args), capture_output=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        raise Refusal('git %s failed in --repo' % args[0])


def load_order(repo, scenario, variant):
    """The variant's continue_markers: a non-empty list of {"tool", "match"} dicts, read from the git
    index of ``repo`` at eval/scenarios/<scenario>/variants/<variant>/hidden/order.json. Never the
    working tree, and never overwritten by an uncommitted edit made after the file was staged."""
    if git(repo, 'rev-parse', '--is-inside-work-tree').strip() != b'true':
        raise Refusal('--repo is not a git work tree')
    path = 'eval/scenarios/%s/variants/%s/hidden/order.json' % (scenario, variant)
    names = [n for n in git(repo, 'ls-files', '-z', '--', path).decode('utf-8').split('\0') if n]
    if not names:
        raise Refusal('no staged order.json for %s/%s' % (scenario, variant))
    try:
        spec = json.loads(git(repo, 'show', ':' + path))
    except ValueError:
        raise Refusal('order.json is not JSON for %s/%s' % (scenario, variant))
    if not (isinstance(spec, dict) and spec.get('schema') == SCHEMA):
        raise Refusal('order.json has the wrong schema for %s/%s' % (scenario, variant))
    markers = spec.get('continue_markers')
    if not (isinstance(markers, list) and markers):
        raise Refusal('continue_markers is not a non-empty list for %s/%s' % (scenario, variant))
    for entry in markers:
        if (not isinstance(entry, dict) or set(entry) != {'tool', 'match'}
                or entry['tool'] not in ALLOWED_MARKER_TOOLS
                or not isinstance(entry['match'], str) or not entry['match']):
            raise Refusal('a continue marker is malformed for %s/%s' % (scenario, variant))
    return markers


def scanned(name, input_):
    """The literal value of the one field this tool's calls are scanned on, or None when the tool is
    never scanned, the field is absent, or its value is not a str. A payload field (content, old_string,
    new_string, edits, Grep's own pattern) is never scanned, only the one target-shaped field per tool."""
    field = SCANNED_FIELD.get(name)
    if field is None:
        return None
    value = input_.get(field) if isinstance(input_, dict) else None
    return value if isinstance(value, str) else None


def matches_marker(name, value, markers):
    return any(name == marker['tool'] and marker['match'] in value for marker in markers)


def ordering_word(blocks, markers):
    """The ordering word for one episode. ``blocks`` is tool_uses(events_of(transcript_bytes)); ``markers``
    is load_order's own continue_markers. A call that matches a marker is never also counted toward
    either filename's own touch, even when its scanned field also contains that filename's text."""
    marker_at = board_at = history_at = None
    for position, (block, _cwd) in enumerate(blocks):
        name = block.get('name')
        value = scanned(name, block.get('input'))
        if value is None:
            continue
        if matches_marker(name, value, markers):
            if marker_at is None:
                marker_at = position
            continue
        if board_at is None and BOARD_NAME in value:
            board_at = position
        if history_at is None and HISTORY_NAME in value:
            history_at = position
    if marker_at is None:
        return 'n/a no-marker'
    if board_at is not None and history_at is not None and board_at < marker_at and history_at < marker_at:
        return 'ordered'
    return 'unordered'


def merge(judgment, check):
    """Fold the ordering word into ``judgment`` (the dict after the contamination-audit merge). Returns a
    new dict; ``judgment`` is never mutated. ``check`` is a zero-argument callable returning the ordering
    word; it is called at most once, and never when judgment['outcome'] is not 'avoided' or 'fell' (an
    'invalid' episode, in particular, is returned unchanged apart from the added 'order' key)."""
    result = copy.deepcopy(judgment)
    if judgment.get('outcome') not in ('avoided', 'fell'):
        result['order'] = {'result': 'not run', 'folded': False}
        return result
    word = check()
    folded = False
    if word == 'unordered':
        folded = judgment['outcome'] == 'avoided'
        result['outcome'] = 'fell'
        result['scores']['correct_action'] = 0
        result['invalid_reason'] = None
    result['order'] = {'result': word, 'folded': folded}
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(prog='order_check.py', description='Content-blind resume-ordering check.')
    parser.add_argument('--repo', required=True)
    parser.add_argument('--scenario', required=True)
    parser.add_argument('--variant', required=True)
    parser.add_argument('--transcript', required=True)
    args = parser.parse_args(argv)
    try:
        markers = load_order(args.repo, args.scenario, args.variant)
        try:
            data = Path(args.transcript).read_bytes()
        except OSError:
            raise Refusal('the transcript could not be read')
        word = ordering_word(tool_uses(events_of(data)), markers)
    except Refusal as refusal:
        sys.stderr.write('order_check: refused: %s\n' % refusal)
        return 2
    print(word)
    return 0


if __name__ == '__main__':
    sys.exit(main())
