#!/bin/sh
set -eu
[ "$(sh bin/hours.sh ana tests/data/week.csv)" = 1185 ] || { echo "ana: expected 1185"; exit 1; }
