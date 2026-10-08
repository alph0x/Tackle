#!/bin/sh
set -eu
got=$(printf 'rent\t1200\n' | sh bin/to-csv.sh)
[ "$got" = "rent,1200" ] || { echo "plain line: got $got"; exit 1; }
got=$(printf 'a\tb\tc\n' | sh bin/to-csv.sh)
[ "$got" = "a,b,c" ] || { echo "three fields: got $got"; exit 1; }
