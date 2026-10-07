#!/bin/sh
# Deliverable acceptance: unit tests, then rendered notices compared with the agreed wording samples.
set -eu
cd "$(dirname "$0")/.."
python3 -m unittest discover -s tests -q
tmp=$(mktemp -d)
python3 -m notices render tests/fixtures/loans.json 2026-09-01 "$tmp" >/dev/null
diff -r "$tmp" tests/fixtures/expected >/dev/null || { echo "accept: notices differ from the agreed samples"; rm -rf "$tmp"; exit 1; }
rm -rf "$tmp"
echo "accept: ok"
