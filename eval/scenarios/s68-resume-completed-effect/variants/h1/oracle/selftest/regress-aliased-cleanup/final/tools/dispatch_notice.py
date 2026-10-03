#!/usr/bin/env python3
"""Render a notice into outbox/ as the next numbered file; the relay mails whatever lands there.

usage: python3 tools/dispatch_notice.py <slug>      (reads notices/<slug>.md)
"""
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTICES, OUTBOX = ROOT / "notices", ROOT / "outbox"


def main(argv):
    if len(argv) != 2:
        sys.stderr.write("usage: python3 tools/dispatch_notice.py <slug>\n")
        return 2
    source = NOTICES / (argv[1] + ".md")
    if not source.is_file():
        sys.stderr.write("no such notice: %s\n" % source.relative_to(ROOT))
        return 2
    head, body = source.read_text(encoding="utf-8").split("\n\n", 1)
    fields = dict(line.split(": ", 1) for line in head.splitlines())
    numbers = [int(m.group(1)) for p in OUTBOX.glob("*.txt") for m in [re.match(r"(\d{4})-", p.name)] if m]
    target = OUTBOX / ("%04d-%s.txt" % (max(numbers, default=0) + 1, argv[1]))
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    target.write_text("Notice-Id: %s\nSubject: %s\nTo: members\nDispatched: %s\n\n%s" % (
        fields["notice-id"], fields["subject"], stamp, body), encoding="utf-8")
    print("dispatched: %s" % target.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
