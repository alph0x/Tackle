#!/bin/sh
set -eu
got=$(sh bin/premium.sh 0)
[ "$got" = "0" ] || { echo "zero value: got $got"; exit 1; }
got=$(sh bin/premium.sh 1999)
case $got in ''|*[!0-9]*) echo "not an integer: $got"; exit 1 ;; esac
if sh bin/premium.sh 500001 >/dev/null 2>&1; then echo "over the limit was priced"; exit 1; fi
