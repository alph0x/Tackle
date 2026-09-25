"""Measure the mandatory reading of one Full task's RUN chain (T-33, R11).

Usage: python3 eval/hot-path/load_chain.py --repo <dir> [--card <path>]

The RUN chain is SKILL.md, the RUN card (default references/guides/run-card.md), every file or
anchored section the card links outside its `## Depth (on demand)` section, and
references/task.tmpl.md as the brief proxy. The Depth section runs from that heading to the next
heading of level 1 or 2; a link inside it is read on demand and is not counted. A link without an
anchor adds its whole file, a link with an anchor adds that section: from the anchored heading (or the
first heading after an explicit `<a id>` anchor) to the next heading of the same or a higher level.
Each file or line is counted once. Links are inline `[text](target)`, reference-style `[text][ref]`
and `<a href>`; links inside code fences, external links and links to the card itself are ignored.

Words are counted as `wc -w` counts them under LC_CTYPE=C on the host that measured the brief
(macOS): maximal runs of bytes other than space, tab, newline, vertical tab, form feed and carriage
return. (GNU wc skips non-printable bytes and can count fewer.)

Prints `run-chain words=<n> card=<m> mandatory=<paths>` (comma-separated, in reading order) and exits
0, or 1 when n > 4000 or m > 800. Exit 2: usage error, a missing file, or a link or anchor that does not
resolve. Standard library only.
"""
import argparse
import re
import sys
from pathlib import Path

CHAIN_LIMIT, CARD_LIMIT = 4000, 800
CARD = 'references/guides/run-card.md'
ENTRY, BRIEF_PROXY = 'SKILL.md', 'references/task.tmpl.md'
DEPTH_HEADING = '## Depth (on demand)'
WORD = re.compile(rb'[^ \t\n\v\f\r]+')
FENCE = re.compile(r'^\s{0,3}(`{3,}|~{3,})')
HEADING = re.compile(r'^\s{0,3}(#{1,6})(?:\s+(.*?))?\s*#*\s*$')
INLINE = re.compile(r'(?<!!)\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+"[^"]*")?\s*\)')
REFERENCE_USE = re.compile(r'(?<!!)\[([^\]]+)\]\[([^\]]*)\]')
REFERENCE_DEFINITION = re.compile(r'^\s{0,3}\[([^\]]+)\]:\s*<?(\S+?)>?(?:\s.*)?$')
HREF = re.compile(r'<a\s[^>]*href="([^"]+)"', re.I)
EXPLICIT_ANCHOR = re.compile(r'<a\s+[^>]*id="([^"]+)"', re.I)
EXTERNAL = re.compile(r'^[a-z][a-z0-9+.-]*:', re.I)


class ChainError(Exception):
    """The chain cannot be measured: a missing file or an unresolved link or anchor."""


def count_words(data):
    return len(WORD.findall(data))


def unfenced(lines):
    """Yield (index, line) for every line outside code fences."""
    fence = None
    for index, line in enumerate(lines):
        marker = FENCE.match(line)
        if fence:
            if marker and marker.group(1)[0] == fence[0] and len(marker.group(1)) >= fence[1]:
                fence = None
            continue
        if marker:
            fence = (marker.group(1)[0], len(marker.group(1)))
            continue
        yield index, line


def headings(lines):
    """[(index, level, text)] of ATX headings outside code fences."""
    found = []
    for index, line in unfenced(lines):
        match = HEADING.match(line)
        if match:
            found.append((index, len(match.group(1)), (match.group(2) or '').strip()))
    return found


def slugify(text):
    text = re.sub(r'[^\w\s-]', '', text.strip().lower())
    return ''.join('-' if character.isspace() else character for character in text)


def depth_range(lines):
    """(start, end) line indexes of the Depth section, or None."""
    marks = headings(lines)
    for position, (index, level, _) in enumerate(marks):
        if lines[index].strip() == DEPTH_HEADING:
            end = next((later for later, later_level, _ in marks[position + 1:] if later_level <= 2), len(lines))
            return index, end
    return None


def mandatory_targets(card_text):
    """Link targets that appear outside the Depth section and outside code fences, in order."""
    lines = card_text.split('\n')
    depth = depth_range(lines)
    definitions = {}
    for _, line in unfenced(lines):
        match = REFERENCE_DEFINITION.match(line)
        if match:
            definitions[match.group(1).strip().lower()] = match.group(2)
    targets = []
    for index, line in unfenced(lines):
        if depth and depth[0] <= index < depth[1]:
            continue
        if REFERENCE_DEFINITION.match(line):
            continue
        found = [(match.start(), match.group(1)) for match in INLINE.finditer(line)]
        found += [(match.start(), match.group(1)) for match in HREF.finditer(line)]
        for match in REFERENCE_USE.finditer(line):
            label = (match.group(2) or match.group(1)).strip().lower()
            if label not in definitions:
                raise ChainError('undefined reference link [%s] on card line %d' % (label, index + 1))
            found.append((match.start(), definitions[label]))
        targets.extend(target for _, target in sorted(found))
    return targets


def section_lines(lines, fragment, name):
    """Line indexes of the section an anchor names."""
    marks = headings(lines)
    start = None
    for index, line in unfenced(lines):
        if fragment in EXPLICIT_ANCHOR.findall(line):
            start = index
            break
    if start is None:
        start = next((index for index, _, text in marks if slugify(text) == fragment), None)
    if start is None:
        raise ChainError('anchor missing: %s#%s' % (name, fragment))
    heading = next(((index, level) for index, level, _ in marks if index >= start), None)
    if heading is None:
        return set(range(start, len(lines)))
    end = next((index for index, level, _ in marks if index > heading[0] and level <= heading[1]), len(lines))
    return set(range(start, end))


def measure(repo, card=CARD):
    repo = Path(repo).resolve()
    for name in (ENTRY, card, BRIEF_PROXY):
        if not (repo / name).is_file():
            raise ChainError('missing file: ' + name)
    card_path = (repo / card).resolve()
    card_bytes = card_path.read_bytes()
    counted = {(repo / ENTRY).resolve(), card_path, (repo / BRIEF_PROXY).resolve()}
    words = count_words((repo / ENTRY).read_bytes()) + count_words(card_bytes) + \
        count_words((repo / BRIEF_PROXY).read_bytes())
    order, selected = [], {}
    for target in mandatory_targets(card_bytes.decode('utf-8')):
        if EXTERNAL.match(target) or target.startswith('#'):
            continue
        path_part, _, fragment = target.partition('#')
        path = (card_path.parent / path_part).resolve()
        if not path.is_relative_to(repo):
            raise ChainError('link leaves the repository: ' + target)
        if not path.is_file():
            raise ChainError('link target missing: ' + target)
        if path in counted:
            continue
        lines = path.read_bytes().split(b'\n')
        text_lines = [line.decode('utf-8') for line in lines]
        wanted = section_lines(text_lines, fragment, path.relative_to(repo).as_posix()) if fragment \
            else set(range(len(lines)))
        label = path.relative_to(repo).as_posix() + ('#' + fragment if fragment else '')
        if path not in selected:
            selected[path] = set()
        if not wanted <= selected[path]:
            selected[path] |= wanted
            order.append(label)
    for path, wanted in selected.items():
        lines = path.read_bytes().split(b'\n')
        words += sum(count_words(lines[index]) for index in wanted)
    mandatory = [ENTRY, Path(card).as_posix()] + order + [BRIEF_PROXY]
    return words, count_words(card_bytes), mandatory


def main(argv=None):
    parser = argparse.ArgumentParser(description='Measure the RUN chain.')
    parser.add_argument('--repo', required=True, type=Path)
    parser.add_argument('--card', default=CARD, help='the card path, relative to --repo (default: %(default)s)')
    args = parser.parse_args(argv)
    try:
        words, card_words, mandatory = measure(args.repo, args.card)
    except (ChainError, OSError, UnicodeDecodeError) as error:
        print('error: %s' % error, file=sys.stderr)
        return 2
    print('run-chain words=%d card=%d mandatory=%s' % (words, card_words, ','.join(mandatory)))
    return 1 if words > CHAIN_LIMIT or card_words > CARD_LIMIT else 0


if __name__ == '__main__':
    sys.exit(main())
