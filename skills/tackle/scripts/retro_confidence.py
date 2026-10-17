"""Wilson score interval, lower bound (z=1.96): for each Hypotheses/Directives bullet (never a
Rules or other section bullet), derive N (checked-true) and M (checked-false) by counting the
entry own observations, then compute the lower bound over n=N+M. Two bullets that repeat one
hypothesis or directive text merge by the union of the observations initiatives (never by
summing two entries N/M, which would double-count a shared initiative); an assumed token is
never counted and never occupies the union (it cannot block a later real check or cross for the
same initiative). Read over a profile file named on the command line, such as
`.tackle/profile.md` or `~/.tackle/user-profile.md`:

    python3 -I <skill>/scripts/retro_confidence.py <profile-path>

Prints `<id> N M n confidence status` for every entry, one line each, in file order.
"""
import re
import sys
from math import isinf, isnan, sqrt

NUMBER = re.compile(r'[ \t\n\r\f\v]*([+-]?(?:[0-9]+\.?[0-9]*|\.[0-9]+)(?:[eE][+-]?[0-9]+)?)')


def trim(text):
    return text.strip(' \t')


def index(text, needle):
    """1-based position of needle in text, 0 when absent (the position convention of the original awk)."""
    return text.find(needle) + 1 if needle else 0


def substr(text, start, length=None):
    """The awk substr(): 1-based start, a length that may run past either end."""
    first = start
    last = len(text) + 1 if length is None else start + length
    first = max(first, 1)
    last = min(last, len(text) + 1)
    return text[first - 1:last - 1] if last > first else ''


def number(text):
    """awk's `text + 0`: the leading decimal number of the string, 0 when there is none."""
    found = NUMBER.match(text)
    return float(found.group(1)) if found else 0


def between(line, left, right):
    a = index(line, left)
    if a == 0:
        return ''
    a += len(left)
    b = index(substr(line, a), right)
    if b == 0:
        return trim(substr(line, a))
    return trim(substr(line, a, b - 1))


def after(line, left):
    a = index(line, left)
    return '' if a == 0 else trim(substr(line, a + len(left)))


def wilson_lower(k, n):
    p = k / n
    denom = 1 + 3.8416 / n
    centre = (p + 3.8416 / (2 * n)) / denom
    spread = p * (1 - p) / n + 3.8416 / (4 * n * n)
    half = 1.96 * (sqrt(spread) if spread >= 0 or isnan(spread) else float('nan')) / denom
    lower = centre - half
    if lower < 0:
        lower = 0
    if lower > 1:
        lower = 1
    return lower


def status_of(m, lower):
    return 'retired' if m >= 3 and lower < 0.3 else 'active'


def as_int(value):
    """The awk %d conversion: truncation, saturating at the 64-bit limits."""
    if isnan(value):
        return -9223372036854775808
    if isinf(value) or abs(value) >= 9223372036854775807:
        return 9223372036854775807 if value > 0 else -9223372036854775808
    return int(value)


def emit(out, ident, n, m, has_evidence):
    total = n + m
    if not has_evidence or total == 0:
        out.append('%s n/a n/a n/a n/a unranked\n' % ident)
        return
    lower = wilson_lower(n, total)
    out.append('%s %d %d %d %.4f %s\n' % (ident, as_int(n), as_int(m), as_int(total), lower, status_of(m, lower)))


def rows(text):
    records = text.split('\n')
    if records and records[-1] == '':
        records.pop()
    out = []
    section = False
    seen = set()
    total_n = {}
    total_m = {}
    for number_of_line, line in enumerate(records, 1):
        if line.startswith('## Hypotheses') or line.startswith('## Directives'):
            section = True
            continue
        if line.startswith('## '):
            section = False
        if not section:
            continue
        if substr(trim(line), 1, 2) != '- ':
            continue
        if index(line, 'observations:') > 0:
            ident = between(line, 'id:', '·')
            entry = between(line, ident + ' · ', ' · confidence:')
            obslist = between(line, 'observations:', '· status:')
            if obslist == '':
                obslist = after(line, 'observations:')
            n = m = 0
            for token in obslist.split(';'):
                token = trim(token)
                if token == '':
                    continue
                is_check = index(token, '✓') > 0
                is_cross = index(token, '✗') > 0
                if not is_check and not is_cross:
                    continue
                key = (entry, substr(token, 1, index(token, ':') - 1))
                if key in seen:
                    continue
                seen.add(key)
                if is_check:
                    n += 1
                else:
                    m += 1
            total_n[entry] = total_n.get(entry, 0) + n
            total_m[entry] = total_m.get(entry, 0) + m
            emit(out, ident, total_n[entry], total_m[entry], True)
            continue
        if index(line, 'evidence:') > 0:
            evidence = between(line, 'evidence:', '· status:')
            if evidence == '':
                evidence = between(line, 'evidence:', '·')
            if evidence == '':
                evidence = after(line, 'evidence:')
            check = index(evidence, '✓')
            n = number(trim(substr(evidence, 1, check - 1)))
            rest = substr(evidence, check + len('✓'))
            if rest.startswith('/'):
                rest = rest[1:]
            if index(rest, 'null') > 0:
                m = 0
            else:
                cross = index(rest, '✗')
                m = number(trim(substr(rest, 1, cross - 1)))
            emit(out, 'line:%d' % number_of_line, n, m, True)
            continue
        emit(out, 'line:%d' % number_of_line, 0, 0, False)
    return ''.join(out)


def main(argv):
    if len(argv) != 2:
        sys.stderr.write('usage: retro_confidence.py <profile-path>\n')
        return 2
    with open(argv[1], encoding='utf-8', errors='surrogateescape', newline='') as stream:
        text = stream.read()
    sys.stdout.buffer.write(rows(text).encode('utf-8', 'surrogateescape'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
