#!/bin/sh
# T-04 verification: the unit tests, then a smoke run of the command on week 38.
set -eu
cd "$(dirname "$0")/.."
python3 -m unittest discover -s tests -q
python3 -m rollup zones tests/fixtures/week-38.csv > /dev/null
echo "verify: ok"
