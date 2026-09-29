"""Account for every sentence unit removed from a ledger `home` or `mirrors` file since a base
revision: a second, independent mechanical check beside check_ledger.py's own rule-level gate.

Usage: python3 eval/rules/check_unit_diff.py --repo <dir> --base <rev>|auto

At every run, the covered file set is the union of: every rule's `home` (a retired `path@tag:line`
form excluded) and every `mirrors` entry's path, across the ledger at the resolved base and the one
on disk in `--repo`; plus every such path named by *any* commit that ever touched
`eval/rules/ledger.json`, reachable from HEAD (`historical_covered_files`) -- coverage is sticky:
once any committed ledger version names a file, it stays covered even after every current rule stops
naming it. For each covered file, independently: strip a leading YAML frontmatter block (a `---`
line, any lines, a closing `---` line, both at column 0), split the remainder with
`eval/install/reading-budget/duplicates.py`'s `units()` plus this file's own `fenced_block_units` (one unit per
fenced code block, the whole span), and split the frontmatter block itself with
`frontmatter_units` (one unit per non-blank content line, at its true absolute line number) --
then collapse whitespace and take the multiset difference (base minus candidate) by exact text,
never by line number. One record for a given removed unit discharges every occurrence of it removed
at that path, however many times.

Auto-match, one live branch, forever: compute the **shipped** unit pool (this file's own splitter,
the same one used everywhere else below, over `SKILL.md` plus every tracked `references/**`
Markdown file, at the candidate). A removed unit whose
collapsed text is an exact member of that pool, at or above `duplicates.py`'s own `MIN_WORDS` floor,
auto-closes with no committed record, printed `auto-matched (shipped): <path>:<line> -> shipped
tree`. Every other removed unit -- including one whose only match lives in maintainer-only material
(`MAINTAINING.md`, `maintaining/**`) -- needs a disposition record: this tool never looks at
maintainer-only material when deciding whether something auto-closes, in this commit or any commit
after it. A relocation record kept by an earlier task, if one exists, is purely a one-time,
workspace-local aid to drafting a disposition; it is never consulted here.

Dispositions (`eval/rules/unit-dispositions.json`, schema `tackle-unit-dispositions/1`, `records`
list). Each record: `{path, line, unit_sha256, disposition, destination, note,
destination_unit_sha256}` (an optional `dropped`, `[{token, reason}]`, excuses a specific dropped
normative token with a reason). `unit_sha256`/`destination_unit_sha256` are the sha256 of collapsed
text, never raw text -- the real removed text is re-derived at check time by re-splitting
`git show <base>:<path>` and matching the hash, so a record is a location-plus-hash citation, never a
transcript. `line` is a base-era citation only; a record is matched to a removed unit by
`(path, unit_sha256)`.

- `home` -- still present in that file: `destination` null or equal to `path`; `unit_sha256` matches
  an exact member of `path`'s current unit set.
- `reworded` -- a declared mapping to new text at a named place (the same file or another one):
  `note` is the new sentence and must be a substring of `destination`'s current raw text (whitespace
  collapsed on both sides).
- `merged` -- moved to a *different* named place that still holds it: `destination_unit_sha256` must
  hash an exact member of `destination`'s current unit set.
- `ruled` -- non-normative, with a reason in `note`; no destination, no mechanical check of the
  claim.

For `reworded`/`merged`, token preservation is checked live: every normative token of the
(live-recovered) removed text -- the fixed list this repository's sibling rule-diff tools already
use (numbers, a short curated word list, and actor names), reused here -- must be present in the
reworded substring (for `reworded`) or the named merged unit (for `merged`), or be listed in
`dropped` with a reason.

Before accepting any record, every freely-authored `note` and `dropped[].reason` is checked against
a disallowed-token pattern (a bare two-letter-prefixed decision/task/question-shape id, or this
initiative's own slug) -- a match refuses the whole run with a usage-shaped error naming the
offending record, never a silent commit.

Reporting (mirrors `gate-exceptions.json`'s own vocabulary), printed unconditionally, per record and
per removed unit: **applied** (the record's unit is currently removed), **dormant** (a valid record,
not currently relevant), **void** (the record's own check fails). Every removed unit that is neither
a shipped auto-match nor covered by a non-void record is an error: "removed unit with no
disposition". Every void record is its own error too.

`auto` resolves the same shape as `check_ledger.py`'s own `resolve_auto` (`:465-486`), duplicated
locally and keyed to this file's own marker (`eval/rules/unit-dispositions.json`) rather than the
rule ledger's: the most recent tag reachable from `HEAD^` whose tree contains that marker, else the
commit that first adds it. Staged but not yet committed, the search finds nothing and this tool
refuses cleanly, never a silent empty-diff pass; once that introducing commit is real, `--base auto`
resolves to it and the diff against itself is a legitimate no-op.

Exit 0 clean; exit 1 with one `error:` line per undispositioned-and-unmatched, void, or
leak-shaped-note record; exit 2 on a usage error. The repository is only read. Standard library only.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import inventory  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from maintaining.install_root import (InstallRootError, current_path,
                                      revision_path)  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'install' / 'reading-budget'))
import duplicates  # noqa: E402

DISPOSITIONS = Path('eval/rules/unit-dispositions.json')
SCHEMA = 'tackle-unit-dispositions/1'
RECORD_FIELDS = ('path', 'line', 'unit_sha256', 'disposition', 'destination', 'note', 'destination_unit_sha256')
OPTIONAL_RECORD_FIELDS = ('dropped',)
DISPOSITION_VALUES = ('home', 'reworded', 'merged', 'ruled')
MIN_WORDS = duplicates.MIN_WORDS
SHA256 = re.compile(r'[0-9a-f]{64}')
# A bare two-letter-prefixed decision/task/question-shape id (never mid-word, never followed by a
# colon -- an ISO timestamp such as this suite's own fixtures write is not one either way), or this
# initiative's own slug substring, built at runtime so this file's own source never spells it out.
LEAK = re.compile(r'(?<![A-Za-z])[PTDQRCM]-?[0-9]{2}(?!:)|' + 'tackle' + '-9')

NUMBER_WORDS = {'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5', 'six': '6',
                'seven': '7', 'eight': '8', 'nine': '9', 'ten': '10'}
WORD_TOKENS = ('must', 'never', 'only', 'every', 'all', 'each', 'not', 'no', 'exactly', 'shared')
STEM_TOKENS = {'session': 'sessions', 'interruption': 'interruptions', 'resumption': 'resumptions',
               'coordinator': 'coordinator', 'executor': 'executor', 'reviewer': 'reviewer', 'checker': 'checker',
               'auditor': 'auditor', 'owner': 'owner', 'user': 'user', 'agent': 'agent', 'human': 'human'}
TOKEN_PATTERN = re.compile(
    r"(?<![\w])(?:(at (?:most|least))|(\d+(?:\.\d+)?)|(can)not|\w+(n't)|(%s)|(%s)s?)(?![\w])" % (
        '|'.join(list(NUMBER_WORDS) + list(WORD_TOKENS)), '|'.join(STEM_TOKENS)), re.I)
LINK = re.compile(r'!?\[([^\]]*)\]\([^)]*\)')


class Report:
    def __init__(self):
        self.errors = []

    def error(self, text):
        self.errors.append(text)


class BaseError(Exception):
    """--base cannot even be resolved or read: refused cleanly, never a silent empty-diff pass."""


def is_text(value):
    return isinstance(value, str) and value.strip() != ''


def is_count(value):
    return isinstance(value, int) and not isinstance(value, bool)


def normative_tokens(text):
    """The sorted, distinct normative tokens of a text: the fixed list this repository's sibling
    rule-diff tools already use, reused here rather than re-invented."""
    plain = re.sub(r'[`*_|]', ' ', LINK.sub(r'\1', text or '')).lower()
    found = set()
    for match in TOKEN_PATTERN.finditer(plain):
        phrase, digits, cannot, contraction, word, stem = match.groups()
        if phrase:
            found.add(' '.join(phrase.split()))
        elif digits:
            found.add(digits)
        elif cannot or contraction:
            found.add('not')
        elif word:
            found.add(NUMBER_WORDS.get(word, word))
        elif stem:
            found.add(STEM_TOKENS[stem])
    return found


def collapse(text):
    return ' '.join((text or '').split())


def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def frontmatter_bounds(lines):
    """(open_index, close_index) of a leading `---`/`---` frontmatter block, both at column 0, or
    None when the text has none -- the one bound-finder `strip_frontmatter` and `frontmatter_units`
    both call, so the two can never diverge on what counts as the block."""
    if lines and lines[0].rstrip('\r') == '---':
        for index in range(1, len(lines)):
            if lines[index].rstrip('\r') == '---':
                return 0, index
    return None


def strip_frontmatter(text):
    """Mechanical and syntactic, inside this tool only: a `---` line, any lines, a closing `---`
    line, both at column 0 -- never a change to duplicates.py itself."""
    lines = text.split('\n')
    bounds = frontmatter_bounds(lines)
    if bounds is None:
        return text
    _, close = bounds
    return '\n'.join(lines[close + 1:])


def frontmatter_units(text):
    """One Unit per non-blank frontmatter content line (the `---` delimiters themselves excluded --
    pure syntax, not content), at its true absolute line number counted from the top of the file.
    The frontmatter analogue of a table row: one atomic line is one unit, never sentence-split and
    never glommed with a neighbor. A blank line inside the block contributes nothing."""
    lines = text.split('\n')
    bounds = frontmatter_bounds(lines)
    if bounds is None:
        return []
    open_index, close_index = bounds
    units = []
    for index in range(open_index + 1, close_index):
        raw = lines[index]
        if raw.strip():
            units.append(duplicates.Unit(index + 1, raw))
    return units


def fenced_block_units(text):
    """One Unit per fenced code block in `text` (opening fence line through closing fence line
    inclusive, as the unit's own text -- fence markers and any info string included, never
    stripped), mirroring `duplicates.blocks()`'s own per-line precedence exactly: fence-state
    checked first, then HTML-comment state, then a fresh fence/comment start -- using
    `duplicates.FENCE` itself, never a re-derived pattern. A fence-shaped line inside an HTML
    comment is never mistaken for a boundary, and an opening fence never closed before EOF
    contributes no unit, matching `blocks()`'s own silent handling of both."""
    units = []
    fence, in_comment = None, False
    start, block_lines = None, []
    for index, raw in enumerate(text.split('\n')):
        stripped = raw.strip()
        if fence:
            block_lines.append(raw)
            marker = duplicates.FENCE.match(raw)
            if marker and marker.group(1)[0] == fence[0] and len(marker.group(1)) >= fence[1] \
                    and not raw.strip()[len(marker.group(1)):].strip():
                units.append(duplicates.Unit(start, '\n'.join(block_lines)))
                fence, block_lines = None, []
            continue
        if in_comment:
            in_comment = '-->' not in stripped
            continue
        marker = duplicates.FENCE.match(raw)
        if marker:
            fence, start, block_lines = (marker.group(1)[0], len(marker.group(1))), index + 1, [raw]
            continue
        if stripped.startswith('<!--'):
            in_comment = '-->' not in stripped[4:]
    return units


def file_units(text):
    stripped = strip_frontmatter(text)
    return duplicates.units(stripped) + fenced_block_units(stripped) + frontmatter_units(text)


def git_text(repo, *args):
    result = subprocess.run(['git', '-C', str(repo)] + list(args), capture_output=True, text=True)
    return result.returncode, result.stdout.strip()


def git_show(repo, rev, path):
    physical = revision_path(repo, rev, path)
    result = subprocess.run(['git', '-C', str(repo), 'show', '%s:%s' % (rev, physical)],
                            capture_output=True, text=True)
    return result.stdout if result.returncode == 0 else None


def read_current(repo, path):
    target = current_path(repo, path)
    return target.read_text(encoding='utf-8') if target.is_file() else None


def tracked_md(repo, prefix):
    logical_prefix = Path(prefix).as_posix()
    prefixes = [logical_prefix]
    if logical_prefix == 'references' or logical_prefix.startswith('references/'):
        prefixes.append('skills/tackle/' + logical_prefix)
    result = subprocess.run(['git', '-C', str(repo), 'ls-files', '--', *prefixes],
                            capture_output=True, text=True)
    if result.returncode != 0:
        return []
    tracked = set()
    for line in result.stdout.splitlines():
        if line.startswith('skills/tackle/'):
            line = line[len('skills/tackle/'):]
        if line.endswith('.md') and (line == logical_prefix or line.startswith(logical_prefix + '/')):
            tracked.add(line)
    return sorted(tracked)


def covered_files(ledger):
    """Every rule's home (a retired path@tag:line form excluded) and every mirrors entry's path."""
    files = set()
    rules = ledger.get('rules') if isinstance(ledger, dict) else None
    for rule in rules if isinstance(rules, list) else []:
        if not isinstance(rule, dict):
            continue
        home = rule.get('home')
        if isinstance(home, str) and ':' in home and '@' not in home:
            files.add(home.rsplit(':', 1)[0])
        mirrors = rule.get('mirrors')
        for mirror in mirrors if isinstance(mirrors, list) else []:
            if isinstance(mirror, str) and ':' in mirror:
                files.add(mirror.rsplit(':', 1)[0])
    return files


def historical_covered_files(repo):
    """The union of `covered_files()` over every commit that ever touched `eval/rules/ledger.json`,
    reachable from HEAD: coverage is sticky, so a file dropped by every *current* ledger stays
    accounted for as long as any committed ledger version once named it. A commit whose
    `eval/rules/ledger.json` fails to parse as JSON contributes nothing to the union (skipped, never
    a crash) -- a conservative default, since this is a best-effort sticky addition, never a
    correctness-critical structural check."""
    code, out = git_text(repo, 'log', '--format=%H', '--', str(inventory.LEDGER))
    files = set()
    if code != 0:
        return files
    for commit in out.splitlines():
        commit = commit.strip()
        if not commit:
            continue
        text = git_show(repo, commit, str(inventory.LEDGER))
        if text is None:
            continue
        try:
            historical_ledger = json.loads(text)
        except ValueError:
            continue
        files |= covered_files(historical_ledger)
    return files


def resolve_auto(repo):
    """The same shape as check_ledger.py's own resolve_auto, duplicated locally and keyed to this
    file's own marker rather than the rule ledger's."""
    spec, seen = 'HEAD^', set()
    while True:
        code, commit = git_text(repo, 'rev-parse', spec)
        if code != 0 or not commit or commit in seen:
            break
        seen.add(commit)
        code, tag = git_text(repo, 'describe', '--tags', '--abbrev=0', commit)
        if code != 0 or not tag:
            break
        code, _ = git_text(repo, 'cat-file', '-e', '%s:%s' % (tag, DISPOSITIONS))
        if code == 0:
            return tag
        spec = tag + '^'
    code, out = git_text(repo, 'log', '--diff-filter=A', '--format=%H', '--', str(DISPOSITIONS))
    lines = [line for line in out.splitlines() if line.strip()]
    if code != 0 or not lines:
        raise BaseError('--base auto: no commit adds %s' % DISPOSITIONS)
    return lines[-1]  # git log lists newest first; the last line is the oldest (first) add


def resolve_base(repo, base_arg):
    if base_arg == 'auto':
        return resolve_auto(repo)
    code, resolved = git_text(repo, 'rev-parse', base_arg)
    if code != 0 or not resolved:
        raise BaseError('--base: %s does not resolve to a revision' % base_arg)
    return base_arg


def removed_units_for_file(base_text, candidate_text):
    """[(line, text)]: one entry per distinct removed text, base line of its first base occurrence."""
    base_units = file_units(base_text) if base_text is not None else []
    candidate_units = file_units(candidate_text) if candidate_text is not None else []
    base_counter = Counter(collapse(unit.text) for unit in base_units)
    candidate_counter = Counter(collapse(unit.text) for unit in candidate_units)
    removed = base_counter - candidate_counter
    first_line = {}
    for unit in base_units:
        text = collapse(unit.text)
        first_line.setdefault(text, unit.line)
    return [(first_line[text], text) for text in removed]


def shipped_pool(repo):
    pool = set()
    for path in ['SKILL.md'] + tracked_md(repo, 'references'):
        text = read_current(repo, path)
        if text is None:
            continue
        for unit in file_units(text):
            pool.add(collapse(unit.text))
    return pool


def current_unit_hashes(repo, path):
    """{sha256(collapsed text): collapsed text} for path's current (working-tree) unit set."""
    text = read_current(repo, path)
    if text is None:
        return {}
    found = {}
    for unit in file_units(text):
        collapsed_text = collapse(unit.text)
        found[sha(collapsed_text)] = collapsed_text
    return found


def leak_texts(record):
    dropped = record.get('dropped')
    texts = [record.get('note')]
    for entry in dropped if isinstance(dropped, list) else []:
        if isinstance(entry, dict):
            texts.append(entry.get('reason'))
    return [text for text in texts if isinstance(text, str)]


def check_tokens(removed_text, destination_text, dropped):
    excused = set()
    for entry in dropped if isinstance(dropped, list) else []:
        if isinstance(entry, dict) and isinstance(entry.get('token'), str) and is_text(entry.get('reason')):
            excused.add(entry['token'])
    missing = normative_tokens(removed_text) - normative_tokens(destination_text) - excused
    return sorted(missing)


def recover_removed_text(repo, base_rev, path, unit_sha256):
    base_text = git_show(repo, base_rev, path)
    if base_text is None:
        return None
    for unit in file_units(base_text):
        text = collapse(unit.text)
        if sha(text) == unit_sha256:
            return text
    return None


def validate_record(repo, base_rev, record):
    """(ok, reason). reason is None on success, else why the record is void (or refused)."""
    if not isinstance(record, dict):
        return False, 'record must be an object'
    unknown = set(record) - set(RECORD_FIELDS) - set(OPTIONAL_RECORD_FIELDS)
    missing = [name for name in RECORD_FIELDS if name not in record]
    if unknown or missing:
        return False, 'expected exactly %s (optionally dropped)' % (RECORD_FIELDS,)
    for text in leak_texts(record):
        if LEAK.search(text):
            return False, 'note or a dropped reason contains a disallowed token'
    path, line, unit_sha256 = record['path'], record['line'], record['unit_sha256']
    disposition = record['disposition']
    destination, note, destination_unit_sha256 = record['destination'], record['note'], record['destination_unit_sha256']
    dropped = record.get('dropped') or []
    if not is_text(path) or not is_count(line) or line < 1:
        return False, 'path must be text and line a positive integer'
    if not isinstance(unit_sha256, str) or not SHA256.fullmatch(unit_sha256):
        return False, 'unit_sha256 must be 64 lowercase hex digits'
    if disposition not in DISPOSITION_VALUES:
        return False, 'disposition must be one of %s' % (DISPOSITION_VALUES,)
    if isinstance(dropped, list):
        for entry in dropped:
            if not (isinstance(entry, dict) and set(entry) == {'token', 'reason'} and is_text(entry.get('token'))
                    and is_text(entry.get('reason'))):
                return False, 'dropped entries must be {token, reason} objects'
    else:
        return False, 'dropped must be a list when present'
    # The removed text is only ever needed to compute the *original* unit's own normative tokens,
    # for the reworded/merged token-preservation check below. A record's own structural validity
    # (destination resolves, a hash-named unit still exists) never depends on recovering it:
    # `base_rev` is this run's own resolved base, which -- forever after this task's own commit,
    # once a later tag exists and `--base auto` walks forward past it -- will no longer reach back
    # to whatever revision a long-past removal's text last existed in. A record whose own removed
    # text cannot be recovered from *this* base simply cannot be part of *this* run's removed set
    # either (both are read from the same base), so it is dormant, never void, on that account
    # alone; only a genuine structural break (below) makes it void.
    removed_text = recover_removed_text(repo, base_rev, path, unit_sha256)

    if disposition == 'home':
        if destination not in (None, path) or note is not None or destination_unit_sha256 is not None:
            return False, 'home: destination must be null or equal to path; note/destination_unit_sha256 null'
        if unit_sha256 not in current_unit_hashes(repo, path):
            return False, 'home: unit_sha256 is not a current unit of %s' % path
        return True, None

    if disposition == 'reworded':
        if not is_text(destination) or not is_text(note) or destination_unit_sha256 is not None:
            return False, 'reworded: destination and note are required; destination_unit_sha256 null'
        dest_text = read_current(repo, destination)
        if dest_text is None:
            return False, 'reworded: destination does not resolve: %s' % destination
        if collapse(note) not in collapse(dest_text):
            return False, "reworded: note is not a substring of destination's current text"
        if removed_text is not None:
            missing = check_tokens(removed_text, note, dropped)
            if missing:
                return False, 'reworded: destination drops normative token(s): %s' % ', '.join(missing)
        return True, None

    if disposition == 'merged':
        if not is_text(destination) or destination == path:
            return False, 'merged: destination must name a different place'
        if not isinstance(destination_unit_sha256, str) or not SHA256.fullmatch(destination_unit_sha256):
            return False, 'merged: destination_unit_sha256 must be 64 lowercase hex digits'
        dest_units = current_unit_hashes(repo, destination)
        dest_unit_text = dest_units.get(destination_unit_sha256)
        if dest_unit_text is None:
            return False, 'merged: destination_unit_sha256 is not a current unit of %s' % destination
        if removed_text is not None:
            missing = check_tokens(removed_text, dest_unit_text, dropped)
            if missing:
                return False, 'merged: destination drops normative token(s): %s' % ', '.join(missing)
        return True, None

    if disposition == 'ruled':
        if destination is not None or destination_unit_sha256 is not None:
            return False, 'ruled: destination and destination_unit_sha256 must be null'
        if not is_text(note):
            return False, 'ruled: note (a reason) is required'
        return True, None

    return False, 'unhandled disposition'  # pragma: no cover (DISPOSITION_VALUES already excludes this)


def load_dispositions(report, repo):
    path = repo / DISPOSITIONS
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except ValueError:
        report.error('%s: invalid JSON' % DISPOSITIONS)
        return []
    if not isinstance(data, dict) or data.get('schema') != SCHEMA or not isinstance(data.get('records'), list):
        report.error('%s: expected {"schema": "%s", "records": [...]}' % (DISPOSITIONS, SCHEMA))
        return []
    return data['records']


def run(report, repo, base_arg):
    """Returns the printed lines (auto-match, per-record state); appends every error to report."""
    resolved_base = resolve_base(repo, base_arg)
    lines = ['base: %s' % resolved_base]

    candidate_ledger_path = repo / inventory.LEDGER
    candidate_ledger = json.loads(candidate_ledger_path.read_text(encoding='utf-8')) if candidate_ledger_path.is_file() else {}
    base_ledger_text = git_show(repo, resolved_base, str(inventory.LEDGER))
    base_ledger = json.loads(base_ledger_text) if base_ledger_text is not None else {}
    files = covered_files(base_ledger) | covered_files(candidate_ledger) | historical_covered_files(repo)

    removed = {}  # (path, unit_sha256) -> (line, text)
    for path in sorted(files):
        base_text = git_show(repo, resolved_base, path)
        candidate_text = read_current(repo, path)
        for line, text in removed_units_for_file(base_text, candidate_text):
            removed[(path, sha(text))] = (line, text)

    pool = shipped_pool(repo)
    auto_matched = set()
    for (path, digest), (line, text) in sorted(removed.items(), key=lambda item: (item[0][0], item[1][0])):
        if text in pool and len(duplicates.words(text)) >= MIN_WORDS:
            auto_matched.add((path, digest))
            lines.append('auto-matched (shipped): %s:%d -> shipped tree' % (path, line))

    records = load_dispositions(report, repo)
    covered = {}
    for position, record in enumerate(records):
        owner = '%s[%d]' % (DISPOSITIONS, position)
        ok, reason = validate_record(repo, resolved_base, record)
        key = (record.get('path'), record.get('unit_sha256')) if isinstance(record, dict) else (None, None)
        if not ok:
            lines.append('%s: void (%s)' % (owner, key[0]))
            report.error('%s: void: %s' % (owner, reason))
            if key not in covered or covered[key] != 'ok':
                covered[key] = 'void'
            continue
        state = 'applied' if key in removed else 'dormant'
        lines.append('%s: %s (%s)' % (owner, state, key[0]))
        covered[key] = 'ok'

    for (path, digest), (line, text) in sorted(removed.items(), key=lambda item: (item[0][0], item[1][0])):
        if (path, digest) in auto_matched:
            continue
        if covered.get((path, digest)) != 'ok':
            report.error('removed unit with no disposition: %s:%d' % (path, line))

    return lines


def main(argv=None):
    parser = argparse.ArgumentParser(description='Account for every sentence unit removed from a ledger home or mirrors file.')
    parser.add_argument('--repo', required=True)
    parser.add_argument('--base', required=True, metavar='<rev>|auto')
    args = parser.parse_args(argv)
    repo = Path(args.repo)
    if not repo.is_dir():
        print('usage: --repo must be a directory: %s' % repo, file=sys.stderr)
        return 2
    report = Report()
    lines = []
    try:
        lines = run(report, repo, args.base)
    except (BaseError, InstallRootError) as problem:
        report.error(str(problem))
    for line in lines:
        print(line)
    for error in report.errors:
        print('error: ' + error)
    return 1 if report.errors else 0


if __name__ == '__main__':
    sys.exit(main())
