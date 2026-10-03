#!/bin/sh
# Deliverable acceptance: unit tests, then a rendered export compared with the agreed sample.
set -eu
cd "$(dirname "$0")/.."
python3 -m unittest discover -s tests -q
tmp=$(mktemp)
python3 -m export roster tests/fixtures/members.json "$tmp" >/dev/null
cmp -s "$tmp" tests/fixtures/expected-roster.csv || { echo "accept: export differs from the agreed sample"; rm -f "$tmp"; exit 1; }
rm -f "$tmp"
echo "accept: ok"
