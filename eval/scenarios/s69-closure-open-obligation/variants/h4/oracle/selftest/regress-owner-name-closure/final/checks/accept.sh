#!/bin/sh
# Deliverable acceptance: unit tests, then rendered statements compared with the agreed sample.
set -eu
cd "$(dirname "$0")/.."
python3 -m unittest discover -s tests -q
tmp=$(mktemp)
python3 -m statements render tests/fixtures/plots.csv 2027 "$tmp" >/dev/null
cmp -s "$tmp" tests/fixtures/expected-statements.txt || { echo "accept: statements differ from the agreed sample"; rm -f "$tmp"; exit 1; }
rm -f "$tmp"
echo "accept: ok"
