#!/bin/sh
# Deliverable acceptance: unit tests, then the week's reminders rendered and compared with the agreed sample.
set -eu
cd "$(dirname "$0")/.."
python3 -m unittest discover -s tests -q
tmp=$(mktemp)
python3 -m reminders week tests/fixtures/shifts.csv "$tmp" >/dev/null
cmp -s "$tmp" tests/fixtures/expected-reminders.txt || { echo "accept: reminders differ from the agreed sample"; rm -f "$tmp"; exit 1; }
rm -f "$tmp"
echo "accept: ok"
