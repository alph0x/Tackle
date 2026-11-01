"""Check the parcel report's consumer contract and keep its run ledger."""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pkg.report import parcel_count

marker = Path('.cache/project/consumers.jsonl')
marker.parent.mkdir(parents=True, exist_ok=True)
with marker.open('a', encoding='utf-8') as stream:
    stream.write(json.dumps({'run': os.getpid(), 'item': 'pkg/report.py'}) + '\n')
try:
    assert parcel_count('parcel,12') == 1
except (AssertionError, TypeError, KeyError, IndexError):
    print('parcel report consumer failed', file=sys.stderr)
    sys.exit(1)
