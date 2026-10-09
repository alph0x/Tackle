#!/bin/sh
set -eu
got=$(sh bin/supplement.sh IV)
[ "$got" = "300" ] || { echo "IV: got $got"; exit 1; }
got=$(sh bin/supplement.sh EH)
[ "$got" = "0" ] || { echo "area without a supplement: got $got"; exit 1; }
