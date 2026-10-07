"""Fixed synthetic command and filesystem control; no native CLI sandbox claim."""
import argparse
import errno
import json
import os
from pathlib import Path
import socket
import sys


def main():
    if sys.argv[1:] == ['echo']:
        sys.stdout.write('command-output\n')
        sys.stderr.write('command-error\n')
        return 0
    parser = argparse.ArgumentParser()
    parser.add_argument('--inside', required=True)
    parser.add_argument('--outside', required=True)
    parser.add_argument('--network-result', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    inside, outside = Path(args.inside), Path(args.outside)
    facts = {'scope': 'synthetic kernel/tool-wrapper control only', 'outside_attempted': True}
    try:
        descriptor = os.open(outside, os.O_RDONLY)
    except OSError as error:
        facts['outside_errno'] = error.errno
        facts['outside_denied'] = True
    else:
        os.close(descriptor)
        facts['outside_errno'] = None
        facts['outside_denied'] = False
    try:
        descriptor = os.open(outside, os.O_WRONLY)
    except OSError as error:
        facts['outside_write_errno'] = error.errno
        facts['outside_write_denied'] = True
    else:
        os.close(descriptor)
        facts['outside_write_errno'] = None
        facts['outside_write_denied'] = False
    facts['inside_before'] = inside.read_text()
    inside.write_text('inside-after\n')
    facts['inside_after'] = inside.read_text()
    # Acquire and close our own port; a bound but unlistened port may time out on macOS.
    with socket.socket() as held:
        held.bind(('127.0.0.1', 0))
        endpoint = held.getsockname()
    with socket.socket() as attempted:
        attempted.settimeout(1)
        try:
            attempted.connect(endpoint)
        except OSError as error:
            refused = error.errno == errno.ECONNREFUSED
            network = {'attempted': True, 'errno': error.errno, 'refused': refused,
                       'outcome': 'observed_refusal' if refused else 'unsupported',
                       'scope': 'owned closed loopback port; no external isolation claim'}
        else:
            network = {'attempted': True, 'errno': None, 'refused': False, 'outcome': 'unsupported'}
    Path(args.network_result).write_text(json.dumps(network) + '\n')
    Path(args.out).write_text(json.dumps(facts) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
