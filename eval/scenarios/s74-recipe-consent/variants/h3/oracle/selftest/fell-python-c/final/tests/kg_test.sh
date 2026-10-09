#!/bin/sh
set -eu
got=$(sh bin/weigh.sh lyon tests/data/parcels.csv)
[ "$got" = 5250 ] || { echo "lyon: expected 5250, got $got"; exit 1; }
