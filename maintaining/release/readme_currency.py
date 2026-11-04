"""Check README install counts and script inventory against the tracked candidate."""
import argparse
from pathlib import Path
import re
import subprocess
import sys


def problems(repo: Path) -> list[str]:
    tracked = subprocess.check_output(
        ['git', '-C', str(repo), 'ls-tree', '-r', '--name-only', '-z', 'HEAD', 'skills/tackle']
    ).decode('utf-8', errors='surrogateescape').split('\0')
    tracked = [path for path in tracked if path]
    expected = set()
    prefix = 'skills/tackle/scripts/'
    for path in tracked:
        if path.startswith(prefix):
            first, separator, _ = path[len(prefix):].partition('/')
            if first != 'README.md':
                expected.add(first + ('/' if separator else ''))

    text = (repo / 'README.md').read_text()
    errors = []
    for sentence in (f'with {len(tracked)} installation-relative files',
                     f'against the {len(tracked)} expected files'):
        if sentence not in text:
            errors.append('missing count sentence: ' + sentence)
    listed = set()
    in_table_section = False
    for line in text.splitlines():
        if line == '### What the scripts do':
            in_table_section = True
        elif in_table_section and re.match(r'^#{1,6}\s', line):
            break
        elif in_table_section and line.startswith('|'):
            listed.update(span for span in re.findall(r'`([^`]+)`', line)
                          if span.endswith(('.py', '/')))
    errors.extend('missing script: ' + name for name in sorted(expected - listed))
    errors.extend('unexpected script: ' + name for name in sorted(listed - expected))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True, type=Path)
    args = parser.parse_args()
    repo = args.repo.resolve()
    try:
        errors = problems(repo)
    except (OSError, subprocess.CalledProcessError) as exc:
        print(exc, file=sys.stderr)
        return 2
    for error in errors:
        print(error)
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
