"""Write a sanitized copy of a record: recognized paths, addresses and keys are replaced, nothing else changes.

Usage: python3 eval/records/sanitize.py <source> <destination>
Exit 0 written, 1 refused (nothing written), 2 usage. The leak patterns are the ones
``eval/protocol-v2/check.py`` applies to episode records (PROTOCOL.md section 2, "Leaks").
"""
import hashlib
import importlib.util
import re
import sys
from pathlib import Path

USAGE = 'usage: sanitize.py <source> <destination>'
REPLACEMENTS = [
    (re.compile(r'/private/var/folders/[^\s`"\')\]]+|/var/folders/[^\s`"\')\]]+'), '<tmp>'),
    (re.compile(r'/(?:Users|home)/[^/\s`"\')\]]+|/root(?=/|\b)'), '<home>'),
    (re.compile(r'~/'), '<home>/'),
    (re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'), '<email>'),
    (re.compile(r'sk-[A-Za-z0-9]{20,}'), '<secret>'),
    (re.compile(r'\b[A-Za-z]:\\[^\s`"\')\]]*'), '<path>'),
]


def leak_patterns():
    path = Path(__file__).resolve().parents[1] / 'protocol-v2' / 'check.py'
    spec = importlib.util.spec_from_file_location('protocol_v2_check', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.LEAKS


def sanitize(text):
    count = 0
    for pattern, replacement in REPLACEMENTS:
        text, n = pattern.subn(replacement, text)
        count += n
    return text, count


def main(argv):
    if len(argv) != 2:
        print(USAGE, file=sys.stderr)
        return 2
    source, destination = Path(argv[0]), Path(argv[1])
    if not source.is_file():
        print(USAGE, file=sys.stderr)
        return 2
    text = source.read_text(encoding='utf-8')
    leaks = leak_patterns()
    if any(pattern.search(text) for pattern in leaks if 'PRIVATE' in pattern.pattern):
        print('refused: a private-key block cannot be sanitized', file=sys.stderr)
        return 1
    result, count = sanitize(text)
    remaining = [pattern.pattern for pattern in leaks if pattern.search(result)]
    if remaining:
        print('refused: unrecognized leak remains: %s' % ', '.join(remaining), file=sys.stderr)
        return 1
    data = result.encode('utf-8')
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(destination, 'xb') as handle:
            handle.write(data)
    except FileExistsError:
        print('refused: destination exists: %s' % destination, file=sys.stderr)
        return 1
    print('sanitized replacements=%d sha256=%s' % (count, hashlib.sha256(data).hexdigest()))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
