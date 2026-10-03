```python
import bisect
import re

LIMIT = 25
LANGUAGES = {'en', 'es'}
VAGUE = {
    'en': [
        r'leverag(?:e|es|ed|ing)', r'utili[sz](?:e|es|ed|ing)', r'various', r'robust', r'synerg(?:y|ies|istic)',
        r'seamless(?:ly)?', r'holistic(?:ally)?', r'cutting-edge', r'best-in-class', r'game-changing',
        r'delv(?:e|es|ed|ing)', r'myriad', r'plethora', r'etc', r'and so on', r'and so forth', r'and more(?=\s*(?:[.,;:!?)]|$))',
        r'in order to', r'a number of(?!\s*\d)', r'a wide range of', r'a variety of', r'it is worth noting',
        r'it should be noted', r'needless to say', r'at the end of the day', r'basically', r'essentially',
        r'really', r'very', r'stuff', r'and the like',
    ],
    'es': [
        r'vari[oa]s', r'diversos', r'diversas', r'robust[oa]s?', r'sinergias?', r'etc', r'etcétera',
        r'y así sucesivamente', r'y demás', r'con el fin de', r'un gran número de', r'una amplia gama de',
        r'cabe destacar', r'vale la pena mencionar', r'ni qué decir tiene', r'al final del día', r'básicamente',
        r'esencialmente', r'realmente', r'muy', r'cosas', r'de vanguardia',
    ],
}
VAGUE_RE = {
    language: re.compile(r'(?<!\w)(?:%s)(?!\w)' % '|'.join(words), re.IGNORECASE)
    for language, words in VAGUE.items()
}
END = re.compile(r'[.!?:;]+["\'”’)\]*_]*(?=\s|$)')
HEADING = re.compile(r'^\s{0,3}#{1,6}(?:\s+|$)')
ITEM = re.compile(r'^\s*(?:[-*+]|\d+[.)])\s+')
INLINE_CODE = re.compile(r'(`+)(?:(?!\1).)+?\1')
QUOTED = re.compile(r'(?<!\w)"[^"\n]*"(?!\w)|“[^”\n]*”')
LINK_TARGET = re.compile(r'\]\([^)]*\)')
ANCHOR = re.compile(r'\s*<a\b[^>]*>(?:\s*</a>)?')
ID = re.compile(r'^(?:[A-Za-z]{1,4}-\d+(?:\.\d+)*|[0-9a-f]{32,}|v?\d+(?:\.\d+)+)$')


def clean(line):
    line = INLINE_CODE.sub(' ', line)
    line = QUOTED.sub(' ', line)
    return LINK_TARGET.sub(']', line)


def count_words(sentence):
    total = 0
    for token in sentence.split():
        token = token.strip('*_()[]{}<>,.!?:;')
        if token and any(ch.isalnum() for ch in token) and not ID.match(token):
            total += 1
    return total


def blocks(text):
    """Yield (kind, [(line_number, cleaned_text), ...]) for each run of text that one sentence may span."""
    run = []
    kind = 'text'
    fence = None
    comment = False

    def flush():
        nonlocal run, kind
        if run:
            yield kind, run
        run = []
        kind = 'text'

    for number, raw in enumerate(text.splitlines(), 1):
        stripped = raw.strip()
        if fence:
            if re.fullmatch(re.escape(fence[0]) + '{%d,}' % len(fence), stripped):
                fence = None
            continue
        if comment:
            if '-->' not in stripped:
                continue
            comment = False
            raw = stripped = stripped.split('-->', 1)[1].strip()
            yield from flush()
        elif stripped.startswith('<!--'):
            yield from flush()
            if '-->' not in stripped:
                comment = True
                continue
            raw = stripped = stripped.split('-->', 1)[1].strip()
        elif stripped.startswith(('<a ', '<a>')):
            yield from flush()
            raw = ANCHOR.sub('', raw, count=1)
            stripped = raw.strip()
        marker = re.match(r'(`{3,}|~{3,})', stripped)
        if marker:
            yield from flush()
            fence = marker.group(1)
            continue
        if not stripped or stripped.startswith('>'):
            yield from flush()
            continue
        if HEADING.match(raw):
            yield from flush()
            yield 'heading', [(number, clean(HEADING.sub('', raw)))]
            continue
        if stripped.startswith('|'):
            yield from flush()
            yield 'table', [(number, clean(raw))]
            continue
        if ITEM.match(raw):
            yield from flush()
            raw = ITEM.sub('', raw, count=1)
        run.append((number, clean(raw)))
    yield from flush()


def findings(text, language):
    """Return the long sentences and vague words of a text as dicts with line, kind and detail."""
    language = (language or '').lower()[:2]
    result = []
    for kind, lines in blocks(text):
        joined = ''
        starts = []
        for number, content in lines:
            starts.append((len(joined), number))
            joined += content + '\n'
        offsets = [start for start, _ in starts]

        def line_at(position):
            return starts[bisect.bisect_right(offsets, position) - 1][1]

        if kind != 'table':
            begin = 0
            for match in list(END.finditer(joined)) + [None]:
                stop = match.end() if match else len(joined)
                sentence = joined[begin:stop]
                words = count_words(sentence)
                if words > LIMIT:
                    first = begin + len(sentence) - len(sentence.lstrip())
                    result.append({'line': line_at(first), 'kind': 'long-sentence',
                                   'detail': '%d words, limit %d' % (words, LIMIT)})
                begin = stop
        if language in VAGUE_RE:
            for match in VAGUE_RE[language].finditer(joined):
                result.append({'line': line_at(match.start()), 'kind': 'vague',
                               'detail': match.group(0)})
    return sorted(result, key=lambda item: (item['line'], item['kind']))
```
