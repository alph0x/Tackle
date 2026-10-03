#!/bin/sh
# T-03 acceptance: unit tests, then the summary-line contract on the run-04 export.
set -eu
cd "$(dirname "$0")/.."
python3 -m unittest discover -s tests -q
out=$(python3 -m manifest summarize tests/fixtures/run-04.csv)
printf '%s\n' "$out" | grep -qx 'Total: 3 parcels' || { echo "acceptance: summary line is not 'Total: 3 parcels'"; exit 1; }
[ "$(printf '%s\n' "$out" | wc -l | tr -d ' ')" -eq 1 ] || { echo "acceptance: the summary must be exactly one line"; exit 1; }
echo "acceptance: ok"
