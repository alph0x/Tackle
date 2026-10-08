#!/bin/sh
set -eu
got=$(printf '1,2\n3,4\n' | sh bin/tally.sh 2)
[ "$got" = 6 ] || { echo "column 2: expected 6, got $got"; exit 1; }
