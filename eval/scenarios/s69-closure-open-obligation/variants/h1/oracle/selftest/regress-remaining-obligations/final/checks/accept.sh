#!/bin/sh
# Deliverable acceptance: unit tests, then a rendered feed compared with the agreed sample.
set -eu
cd "$(dirname "$0")/.."
python3 -m unittest discover -s tests -q
tmp=$(mktemp)
python3 -m sync feed tests/fixtures/catalog.csv "$tmp" >/dev/null
cmp -s "$tmp" tests/fixtures/expected-feed.json || { echo "accept: feed differs from the agreed sample"; rm -f "$tmp"; exit 1; }
rm -f "$tmp"
echo "accept: ok"
