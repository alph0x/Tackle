"""Coverage units of SKILL.md and the historical-record projection behind the rule ledger (LEDGER.md).

Usage (from any directory; standard library only):
  python3 eval/rules/inventory.py units --repo <dir>              every unit: SKILL.md:<line><TAB><sentence>
  python3 eval/rules/inventory.py uncovered --repo <dir>          units no ledger entry names
  python3 eval/rules/inventory.py sync --repo <dir> --check|--write
      compare (or rewrite) each rule's historical list against historical-index.json
Exit 0 on success, 1 when --check finds stale lists or the inputs are unreadable, 2 on usage errors.
"""
import argparse
import bisect
import json
import re
import sys
from pathlib import Path

SECTIONS = ('Public surface', 'PLAN and RUN', 'Compatibility and state', 'Core conventions', 'Output')
KEY_LENGTH = 48
LEDGER = Path('eval/rules/ledger.json')
INDEX = Path('eval/rules/historical-index.json')
LIST_MARKER = re.compile(r'\s*(?:[-*+]|\d+[.)])\s+')
DELIMITER_CELL = re.compile(r':?-+:?')
BOUNDARY = re.compile(r'(?<=[.?!]) (?=[A-Z`*0-9])')
OUTCOMES = ('fell', 'avoided', 'partial', 'placeholder', 'absent')
COMPARISONS = ('no-skill', 'ablation', 'prior-version', 'method-only')


class UnitError(ValueError):
    """SKILL.md cannot be split into coverage units (a listed section is missing or repeated)."""


def key(sentence):
    return sentence[:KEY_LENGTH]


def table_cells(line):
    body = line.strip()[1:]
    if body.endswith('|') and not body.endswith('\\|'):
        body = body[:-1]
    return [cell.strip() for cell in re.split(r'(?<!\\)\|', body)]


def is_delimiter(line):
    return line.lstrip().startswith('|') and all(DELIMITER_CELL.fullmatch(c) for c in table_cells(line))


def blocks(lines):
    """Yield (section, [(line_no, text), ...]) for each paragraph, list item and table body row."""
    section, current, seen, in_comment = None, None, set(), False
    for index, raw in enumerate(lines):
        number, text = index + 1, raw.strip()
        if in_comment:
            in_comment = '-->' not in text
            continue
        if re.match(r'#{1,2} ', raw):
            if current:
                yield section, current
            current = None
            name = raw.split(' ', 1)[1].strip()
            section = name if raw.startswith('## ') and name in SECTIONS else None
            if section:
                if section in seen:
                    raise UnitError('duplicate section: ' + section)
                seen.add(section)
            continue
        if section is None:
            continue
        ignored = not text or text.startswith('#') or text.startswith('<a id=')
        if text.startswith('<!--'):
            ignored, in_comment = True, '-->' not in text
        if ignored or text.startswith('|'):
            if current:
                yield section, current
            current = None
            if text.startswith('|') and not is_delimiter(raw):
                following = lines[index + 1] if index + 1 < len(lines) else ''
                if not is_delimiter(following):
                    yield section, [(number, ' '.join(table_cells(raw)))]
            continue
        marker = LIST_MARKER.match(raw)
        if marker:
            if current:
                yield section, current
            current = [(number, raw[marker.end():])]
        elif current is None:
            current = [(number, raw)]
        else:
            current.append((number, raw))
    if current:
        yield section, current
    missing = [name for name in SECTIONS if name not in seen]
    if missing:
        raise UnitError('missing section: ' + ', '.join(missing))


def units(text):
    """Return the coverage units of a SKILL.md text: dicts with line, section, sentence and key."""
    found = []
    for section, pieces in blocks(text.split('\n')):
        starts, parts, offset = [], [], 0
        for number, piece in pieces:
            words = ' '.join(piece.split())
            if not words:
                continue
            starts.append(offset)
            parts.append((number, words))
            offset += len(words) + 1
        joined = ' '.join(words for _, words in parts)
        begin = 0
        for end in [m.start() for m in BOUNDARY.finditer(joined)] + [len(joined)]:
            sentence = joined[begin:end].strip()
            if sentence:
                number = parts[bisect.bisect_right(starts, begin) - 1][0]
                found.append({'line': number, 'section': section, 'sentence': sentence, 'key': key(sentence)})
            begin = end + 1
    return found


def historical_label(baseline, candidate, contamination):
    """Map one historical comparison to a protocol v2 label: the first matching rule wins."""
    if contamination:
        return 'contaminated'
    if {baseline, candidate} & {'placeholder', 'absent'}:
        return 'unobserved'
    if candidate == 'fell' and baseline == 'avoided':
        return 'method-worse'
    if baseline == 'avoided' and candidate == 'avoided':
        return 'inert'
    if baseline == 'fell' and candidate == 'avoided':
        return 'discriminates'
    return 'inconclusive'


def expected_seeds(baseline_seeds, candidate_seeds):
    observed = {s for s in (baseline_seeds, candidate_seeds) if s}
    return observed.pop() if len(observed) == 1 else 'n/a'


def projection(index, scenarios):
    """The historical list a rule must carry: every index entry for one of its evidence scenarios."""
    rows = [{'record': record, 'label': entry['recorded_label'], 'seeds': entry['seeds']}
            for record, entries in index['records'].items() for entry in entries
            if entry['scenario_id'] in scenarios]
    return sorted(rows, key=lambda row: (row['record'], row['label'], str(row['seeds'])))


def dump(value):
    return json.dumps(value, indent=2, ensure_ascii=False) + '\n'


def load(repo, relative):
    return json.loads((repo / relative).read_text(encoding='utf-8'))


def command_units(repo, uncovered_only):
    found = units((repo / 'SKILL.md').read_text(encoding='utf-8'))
    named = set()
    if uncovered_only:
        ledger = load(repo, LEDGER)
        named = {u for rule in ledger['rules'] for u in rule['units']} | {n['unit'] for n in ledger['non_normative']}
    for unit in found:
        if unit['key'] not in named:
            print('SKILL.md:%d\t%s' % (unit['line'], unit['sentence']))
    return 0


def command_sync(repo, write):
    ledger, index = load(repo, LEDGER), load(repo, INDEX)
    stale = []
    for rule in ledger['rules']:
        fresh = projection(index, set(rule['evidence']['scenarios']))
        if rule['historical'] != fresh:
            stale.append(rule['rule_id'])
            rule['historical'] = fresh
    if write:
        (repo / LEDGER).write_text(dump(ledger), encoding='utf-8')
        return 0
    for rule_id in stale:
        print('%s: historical is stale' % rule_id)
    return 1 if stale else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description='Coverage units and historical lists of the rule ledger.')
    parser.add_argument('command', choices=('units', 'uncovered', 'sync'))
    parser.add_argument('--repo', required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--check', action='store_true')
    mode.add_argument('--write', action='store_true')
    args = parser.parse_args(argv)
    repo = Path(args.repo)
    if not repo.is_dir():
        print('usage: --repo must be a directory: %s' % repo, file=sys.stderr)
        return 2
    if args.command == 'sync' and not (args.check or args.write):
        print('usage: sync needs --check or --write', file=sys.stderr)
        return 2
    try:
        if args.command == 'sync':
            return command_sync(repo, args.write)
        return command_units(repo, args.command == 'uncovered')
    except (OSError, ValueError, KeyError, TypeError) as error:
        print('error: %s' % error, file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
