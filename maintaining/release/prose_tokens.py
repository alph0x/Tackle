"""Find glued tokens in release prose, excluding technical notation."""
import argparse
from pathlib import Path
import re
import sys

ALLOW = {'sha1', 'sha256', 'sha512', 'md5', 'utf8', 'base64', 'python3',
         'py310', 'py314', 'arm64', 'amd64', 'ipv4', 'ipv6'}
EXCLUDED = re.compile(r'`[^`]*`|\]\([^)]*\)|<[A-Za-z][A-Za-z0-9+.-]*://[^>]*>|[A-Za-z][A-Za-z0-9+.-]*://\S+')
HASH = re.compile(r'[0-9A-Fa-f]{7,}')
LETTERS_DIGITS = re.compile(r'(?:[A-Z][a-z]+|[a-z]{2,})[0-9]+')
DIGITS_LETTERS = re.compile(r'[0-9]+([a-z]{2,})')
PUNCTUATION = re.compile(r'[A-Za-z][,;][A-Za-z0-9]')


def glued_tokens(text: str) -> list[tuple[int, str, str]]:
    findings = []
    fenced = False
    for line_number, line in enumerate(text.splitlines(), 1):
        if line.strip().startswith('```'):
            fenced = not fenced
            continue
        if fenced:
            continue
        for raw in EXCLUDED.sub('', line).split():
            token = raw.lstrip('([{"\'*_').rstrip(')]}"\'*_.,;:!?')
            if HASH.fullmatch(token):
                continue
            if LETTERS_DIGITS.fullmatch(token) and token.lower() not in ALLOW:
                rule = 'letters-digits'
            else:
                match = DIGITS_LETTERS.fullmatch(token)
                if match and match.group(1) not in {'st', 'nd', 'rd', 'th'}:
                    rule = 'digits-letters'
                elif PUNCTUATION.search(token):
                    rule = 'punctuation'
                else:
                    continue
            findings.append((line_number, token, rule))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('files', nargs='+')
    args = parser.parse_args()
    paths = []
    for filename in args.files:
        try:
            paths.append(Path(filename).resolve())
        except (OSError, RuntimeError) as error:
            print(f'{filename}: {error}', file=sys.stderr)
            return 2
    found = False
    for filename, path in zip(args.files, paths):
        try:
            text = path.read_text(encoding='utf-8')
        except (OSError, UnicodeError) as error:
            print(f'{filename}: {error}', file=sys.stderr)
            return 2
        for line, token, rule in glued_tokens(text):
            print(f'{filename}:{line}: {rule}: {token}')
            found = True
    return 1 if found else 0


if __name__ == '__main__':
    raise SystemExit(main())
