"""Report near-duplicate sentence units across Markdown files: the single duplicate detector (D-74).

Usage:
  python3 eval/hot-path/duplicates.py --repo <dir> --chain run
  python3 eval/hot-path/duplicates.py --repo <dir> --files <path> [<path> ...]

`--chain run` is the RUN card (references/guides/run-card.md), references/guides/run.md and every
references/recipes/*.md. `--files` paths are relative to --repo.

A unit is one sentence of prose outside code fences, or one table row. Headings, blank lines, HTML
comments and anchor lines are not units. Units with fewer than 8 words, counted after markup (`|`,
backticks, emphasis, link targets) is removed, are not compared. Rows of the same table are never
paired with each other; a row still pairs with prose or with a row of another table. Every other pair
whose word 3-gram Jaccard similarity is at least 0.5 prints as
`duplicate <file>:<line> ~ <file>:<line> j=<value>`, then `duplicates=<k>` prints.

Exit 0 when k = 0, 1 when k > 0, 2 on a usage error or a missing file. Standard library only.
"""
import argparse
import bisect
import re
import sys
from pathlib import Path

MIN_WORDS = 8
THRESHOLD = 0.5
FENCE = re.compile(r'^\s{0,3}(`{3,}|~{3,})')
HEADING = re.compile(r'^\s{0,3}#{1,6}(\s|$)')
ANCHOR_LINE = re.compile(r'^\s*<a\s+id="[^"]*"\s*>\s*</a>\s*$')
LIST_MARKER = re.compile(r'\s*(?:[-*+]|\d+[.)])\s+')
DELIMITER_CELL = re.compile(r':?-+:?')
BOUNDARY = re.compile(r'(?<=[.?!]) (?=[A-Z`*0-9])')
LINK = re.compile(r'!?\[([^\]]*)\]\([^)]*\)')
MARKUP = re.compile(r'[|`*_]')
EDGE_PUNCTUATION = '.,;:!?()[]{}<>"\'“”‘’—–-/\\'


class Unit:
    """One sentence or table row: its 1-based start line, its text and, for a row, its table's id."""

    __slots__ = ('line', 'text', 'table')

    def __init__(self, line, text, table=None):
        self.line, self.text, self.table = line, text, table

    def __repr__(self):
        return 'Unit(%d, %r, table=%r)' % (self.line, self.text, self.table)


def table_cells(line):
    body = line.strip()[1:]
    if body.endswith('|') and not body.endswith('\\|'):
        body = body[:-1]
    return [cell.strip() for cell in re.split(r'(?<!\\)\|', body)]


def is_delimiter(line):
    return line.lstrip().startswith('|') and all(DELIMITER_CELL.fullmatch(cell) for cell in table_cells(line))


def blocks(lines):
    """Yield ('prose', [(line, text), ...]) for each paragraph or list item, and ('row', table_id, line,
    text) for each table row, skipping fenced code, headings, comments and anchor lines."""
    current, fence, in_comment, table, tables = None, None, False, None, 0
    for index, raw in enumerate(lines):
        number, text = index + 1, raw.strip()
        if fence:
            marker = FENCE.match(raw)
            if marker and marker.group(1)[0] == fence[0] and len(marker.group(1)) >= fence[1] \
                    and not raw.strip()[len(marker.group(1)):].strip():
                fence = None
            continue
        if in_comment:
            in_comment = '-->' not in text
            continue
        marker = FENCE.match(raw)
        is_row = text.startswith('|')
        if not is_row:
            table = None
        if marker or not text or HEADING.match(raw) or ANCHOR_LINE.match(raw) or text.startswith('<!--') or is_row:
            if current:
                yield ('prose', current)
            current = None
            if marker:
                fence = (marker.group(1)[0], len(marker.group(1)))
            elif text.startswith('<!--'):
                in_comment = '-->' not in text[4:]
            elif is_row:
                if table is None:
                    tables += 1
                    table = tables
                if not is_delimiter(raw):
                    yield ('row', table, number, ' '.join(text.split()))
            continue
        item = LIST_MARKER.match(raw)
        if item:
            if current:
                yield ('prose', current)
            current = [(number, raw[item.end():])]
        elif current is None:
            current = [(number, raw)]
        else:
            current.append((number, raw))
    if current:
        yield ('prose', current)


def units(text):
    """Split Markdown text into units, in document order."""
    found = []
    for block in blocks(text.split('\n')):
        if block[0] == 'row':
            found.append(Unit(block[2], block[3], block[1]))
            continue
        starts, parts, offset = [], [], 0
        for number, piece in block[1]:
            words = ' '.join(piece.split())
            if not words:
                continue
            starts.append(offset)
            parts.append((number, words))
            offset += len(words) + 1
        joined = ' '.join(words for _, words in parts)
        begin = 0
        for end in [match.start() for match in BOUNDARY.finditer(joined)] + [len(joined)]:
            sentence = joined[begin:end].strip()
            if sentence:
                found.append(Unit(parts[bisect.bisect_right(starts, begin) - 1][0], sentence))
            begin = end + 1
    return found


def words(text):
    """Normalized words of a unit: link targets and markup removed, lowercased, edge punctuation
    stripped; a token without a letter or digit is not a word."""
    text = MARKUP.sub(' ', LINK.sub(r'\1', text)).lower()
    tokens = (token.strip(EDGE_PUNCTUATION) for token in text.split())
    return [token for token in tokens if any(character.isalnum() for character in token)]


def trigrams(tokens):
    return {tuple(tokens[index:index + 3]) for index in range(len(tokens) - 2)}


def jaccard(left, right):
    union = left | right
    return len(left & right) / len(union) if union else 0.0


def pairs(entries):
    """entries: [(file, Unit)]. Return [(j, (file, line), (file, line))] for every reportable pair."""
    grams, index = [], {}
    for position, (name, unit) in enumerate(entries):
        tokens = words(unit.text)
        gram_set = trigrams(tokens) if len(tokens) >= MIN_WORDS else set()
        grams.append(gram_set)
        for gram in gram_set:
            index.setdefault(gram, []).append(position)
    candidates = set()
    for positions in index.values():
        for first_index, first in enumerate(positions):
            for second in positions[first_index + 1:]:
                candidates.add((first, second))
    found = []
    for first, second in sorted(candidates):
        (left_name, left), (right_name, right) = entries[first], entries[second]
        if left.table is not None and left_name == right_name and left.table == right.table:
            continue
        value = jaccard(grams[first], grams[second])
        if value >= THRESHOLD:
            found.append((value, (left_name, left.line), (right_name, right.line)))
    return found


def chain_files(repo, chain):
    if chain != 'run':
        raise ValueError('unknown chain: ' + chain)
    names = ['references/guides/run-card.md', 'references/guides/run.md']
    recipes = repo / 'references/recipes'
    if recipes.is_dir():
        names += sorted(path.relative_to(repo).as_posix() for path in recipes.glob('*.md') if path.is_file())
    return names


def main(argv=None):
    parser = argparse.ArgumentParser(description='Report near-duplicate sentence units.')
    parser.add_argument('--repo', required=True, type=Path)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--chain', choices=['run'])
    group.add_argument('--files', nargs='+')
    args = parser.parse_args(argv)
    repo = args.repo
    names = chain_files(repo, args.chain) if args.chain else list(args.files)
    entries = []
    for name in names:
        path = repo / name
        if not path.is_file():
            print('error: missing file: ' + name, file=sys.stderr)
            return 2
        entries.extend((name, unit) for unit in units(path.read_text(encoding='utf-8')))
    found = pairs(entries)
    for value, (left_name, left_line), (right_name, right_line) in found:
        print('duplicate %s:%d ~ %s:%d j=%.2f' % (left_name, left_line, right_name, right_line, value))
    print('duplicates=%d' % len(found))
    return 1 if found else 0


if __name__ == '__main__':
    sys.exit(main())
