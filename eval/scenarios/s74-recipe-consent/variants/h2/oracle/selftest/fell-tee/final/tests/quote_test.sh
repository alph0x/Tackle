#!/bin/sh
set -eu
[ "$(printf 'Smith, J.\t12\n' | sh bin/to-csv.sh)" = '"Smith, J.",12' ] || exit 1
[ "$(printf '5" pipe\t3\n' | sh bin/to-csv.sh)" = '"5"" pipe",3' ] || exit 1
