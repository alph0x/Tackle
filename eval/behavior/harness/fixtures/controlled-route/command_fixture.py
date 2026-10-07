#!/usr/bin/env python3
"""Exact command modes for the local fixture worker."""
import json
from pathlib import Path
import sys
import time


def main():
    if len(sys.argv) not in (2, 3):
        return 8
    mode = sys.argv[1]
    if len(sys.argv) == 3 and (mode != 'read_archive_prefix' or sys.argv[2] != 'history-archive.md'):
        return 8
    definitions = json.loads(Path(__file__).with_name('streams.json').read_text())
    if mode in definitions['streams']:
        streams = definitions['streams'][mode]
        sys.stdout.write(streams['stdout'])
        sys.stderr.write(streams['stderr'])
        return streams['exit']
    if mode == 'read_archive_prefix':
        if len(sys.argv) != 3:
            return 8
        sys.stdout.buffer.write(Path('history-archive.md').read_bytes()[:128])
        return 0
    if mode == 'delay':
        time.sleep(.06)
        Path('delayed.txt').write_text('after delay\n')
        return 0
    if mode == 'owned_helper':
        time.sleep(.08)
        Path('owned-helper.txt').write_text('owned handle finished\n')
        return 0
    return 8


if __name__ == '__main__':
    raise SystemExit(main())
