#!/bin/sh
# List the outbox files that carry a notice id; exit 0 when there is at least one.
set -u
cd "$(dirname "$0")/.."
[ $# -eq 1 ] || { echo "usage: sh tools/outbox_check.sh <notice-id>" >&2; exit 2; }
grep -l "^Notice-Id: $1\$" outbox/*.txt
